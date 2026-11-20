import uuid

import jwt
from fastapi import Cookie, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.core.security import TokenType, decode_token, decrypt_secret
from app.models.user import User
from app.models.workspace import Workspace
from app.services.auth.user_service import get_user_by_id
from app.services.auth.workspace_service import get_personal_workspace_for_user

ACCESS_TOKEN_COOKIE = "repomind_access_token"
REFRESH_TOKEN_COOKIE = "repomind_refresh_token"


async def get_current_user(
    repomind_access_token: str | None = Cookie(default=None, alias=ACCESS_TOKEN_COOKIE),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    if not repomind_access_token:
        raise UnauthorizedError("Not authenticated.")

    try:
        payload = decode_token(repomind_access_token, settings)
    except jwt.PyJWTError:
        raise UnauthorizedError("Invalid or expired session.")

    if payload.get("type") != TokenType.ACCESS.value:
        raise UnauthorizedError("Invalid session token.")

    user = await get_user_by_id(db, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise UnauthorizedError("Account no longer active.")
    return user


async def get_current_workspace(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    workspace = await get_personal_workspace_for_user(db, user.id)
    if workspace is None:
        raise UnauthorizedError("No workspace found for this account.")
    return workspace


def get_decrypted_github_token(user: User, settings: Settings) -> str | None:
    if not user.github_access_token_encrypted:
        return None
    return decrypt_secret(user.github_access_token_encrypted, settings)
