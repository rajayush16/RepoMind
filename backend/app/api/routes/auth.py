import httpx
from fastapi import APIRouter, Cookie, Depends, Query, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE, get_current_user
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedError, ValidationError
from app.core.security import TokenType, create_token, encrypt_secret
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, UserOut
from app.services.auth.user_service import (
    authenticate_user,
    create_user,
    get_user_by_email,
    get_user_by_github_id,
)
from app.services.auth.workspace_service import create_personal_workspace
from app.services.github.oauth import (
    GithubOAuthError,
    build_authorize_url,
    exchange_code_for_token,
    fetch_github_user,
    generate_state,
)

router = APIRouter(prefix="/auth", tags=["auth"])

OAUTH_STATE_COOKIE = "repomind_oauth_state"


def _cookie_kwargs(settings: Settings) -> dict:
    return {
        "httponly": True,
        "secure": settings.environment not in ("development", "test"),
        "samesite": "lax",
        "path": "/",
    }


def _issue_session(response: Response, user: User, settings: Settings) -> None:
    access_token = create_token(user.id, TokenType.ACCESS, settings)
    refresh_token = create_token(user.id, TokenType.REFRESH, settings)
    response.set_cookie(
        ACCESS_TOKEN_COOKIE,
        access_token,
        max_age=settings.access_token_expire_minutes * 60,
        **_cookie_kwargs(settings),
    )
    response.set_cookie(
        REFRESH_TOKEN_COOKIE,
        refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        **_cookie_kwargs(settings),
    )


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        github_username=user.github_username,
        github_avatar_url=user.github_avatar_url,
        github_connected=user.github_access_token_encrypted is not None,
    )


@router.post("/register", response_model=UserOut, status_code=201)
async def register(
    body: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UserOut:
    existing = await get_user_by_email(db, body.email)
    if existing is not None:
        raise ValidationError("An account with this email already exists.")

    user = await create_user(db, email=body.email, password=body.password, name=body.name)
    await create_personal_workspace(db, user.id, body.name or body.email.split("@")[0])
    await db.commit()
    await db.refresh(user)

    _issue_session(response, user, settings)
    return _user_out(user)


@router.post("/login", response_model=UserOut)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UserOut:
    user = await authenticate_user(db, body.email, body.password)
    if user is None:
        raise UnauthorizedError("Incorrect email or password.")

    _issue_session(response, user, settings)
    return _user_out(user)


@router.post("/logout", status_code=204)
async def logout(response: Response, settings: Settings = Depends(get_settings)) -> None:
    response.delete_cookie(ACCESS_TOKEN_COOKIE, path="/")
    response.delete_cookie(REFRESH_TOKEN_COOKIE, path="/")


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return _user_out(user)


@router.get("/github/login")
async def github_login(
    response: Response, settings: Settings = Depends(get_settings)
) -> RedirectResponse:
    try:
        state = generate_state()
        url = build_authorize_url(settings, state)
    except GithubOAuthError as exc:
        raise ValidationError(str(exc))

    redirect = RedirectResponse(url)
    redirect.set_cookie(
        OAUTH_STATE_COOKIE, state, max_age=600, **_cookie_kwargs(settings)
    )
    return redirect


@router.get("/github/callback")
async def github_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    repomind_oauth_state: str | None = Cookie(default=None, alias=OAUTH_STATE_COOKIE),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    failure_redirect = f"{settings.frontend_base_url}/login?error=github_oauth_failed"

    if error or not code or not state or not repomind_oauth_state:
        return RedirectResponse(failure_redirect)
    if state != repomind_oauth_state:
        return RedirectResponse(failure_redirect)

    try:
        access_token = await exchange_code_for_token(settings, code)
        github_user = await fetch_github_user(access_token)
    except (GithubOAuthError, httpx.HTTPError):
        return RedirectResponse(failure_redirect)

    github_id = str(github_user.get("id"))
    github_email = github_user.get("email")
    github_username = github_user.get("login")
    github_avatar_url = github_user.get("avatar_url")
    encrypted_token = encrypt_secret(access_token, settings)

    user = await get_user_by_github_id(db, github_id)

    if user is None and github_email:
        user = await get_user_by_email(db, github_email)

    if user is None:
        if not github_email:
            return RedirectResponse(
                f"{settings.frontend_base_url}/login?error=github_email_missing"
            )
        user = await create_user(db, email=github_email, name=github_user.get("name"))
        await create_personal_workspace(
            db, user.id, github_user.get("name") or github_username or github_email.split("@")[0]
        )

    user.github_id = github_id
    user.github_username = github_username
    user.github_avatar_url = github_avatar_url
    user.github_access_token_encrypted = encrypted_token
    await db.commit()
    await db.refresh(user)

    redirect = RedirectResponse(f"{settings.frontend_base_url}/repositories")
    _issue_session(redirect, user, settings)
    redirect.delete_cookie(OAUTH_STATE_COOKIE, path="/")
    return redirect
