import secrets
from urllib.parse import urlencode

import httpx

from app.core.config import Settings

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
OAUTH_SCOPES = "read:user user:email repo"


class GithubOAuthError(Exception):
    pass


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def build_authorize_url(settings: Settings, state: str) -> str:
    if not settings.github_client_id or not settings.github_oauth_callback_url:
        raise GithubOAuthError(
            "GitHub OAuth is not configured: set GITHUB_CLIENT_ID and "
            "GITHUB_OAUTH_CALLBACK_URL."
        )
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_oauth_callback_url,
        "scope": OAUTH_SCOPES,
        "state": state,
    }
    return f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code_for_token(settings: Settings, code: str) -> str:
    if not settings.github_client_id or not settings.github_client_secret:
        raise GithubOAuthError("GitHub OAuth is not configured.")

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_oauth_callback_url,
            },
        )
    response.raise_for_status()
    payload = response.json()
    if "access_token" not in payload:
        raise GithubOAuthError(f"GitHub token exchange failed: {payload}")
    return payload["access_token"]


async def fetch_github_user(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
    response.raise_for_status()
    user = response.json()

    if not user.get("email"):
        async with httpx.AsyncClient(timeout=10.0) as client:
            emails_response = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
        if emails_response.status_code == 200:
            emails = emails_response.json()
            primary = next((e for e in emails if e.get("primary")), None)
            if primary:
                user["email"] = primary["email"]

    return user
