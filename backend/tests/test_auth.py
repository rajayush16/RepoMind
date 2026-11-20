import httpx
import pytest


@pytest.mark.asyncio
async def test_register_creates_user_and_sets_session_cookies(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/register",
        json={"email": "ada@example.com", "password": "correct-horse-battery", "name": "Ada"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ada@example.com"
    assert body["github_connected"] is False
    assert "repomind_access_token" in response.cookies
    assert "repomind_refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_register_duplicate_email_is_rejected(client: httpx.AsyncClient) -> None:
    payload = {"email": "dup@example.com", "password": "correct-horse-battery"}
    first = await client.post("/api/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/auth/register", json=payload)
    assert second.status_code == 422


@pytest.mark.asyncio
async def test_login_with_wrong_password_is_rejected(client: httpx.AsyncClient) -> None:
    await client.post(
        "/api/auth/register",
        json={"email": "bob@example.com", "password": "correct-horse-battery"},
    )

    response = await client.post(
        "/api/auth/login", json={"email": "bob@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_authentication(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user_after_login(client: httpx.AsyncClient) -> None:
    await client.post(
        "/api/auth/register",
        json={"email": "carol@example.com", "password": "correct-horse-battery"},
    )

    response = await client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "carol@example.com"


@pytest.mark.asyncio
async def test_logout_clears_session(client: httpx.AsyncClient) -> None:
    await client.post(
        "/api/auth/register",
        json={"email": "dave@example.com", "password": "correct-horse-battery"},
    )

    logout_response = await client.post("/api/auth/logout")
    assert logout_response.status_code == 204

    me_response = await client.get("/api/auth/me")
    assert me_response.status_code == 401


@pytest.mark.asyncio
async def test_github_login_redirects_to_github_with_state(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/auth/github/login", follow_redirects=False)

    assert response.status_code in (302, 307)
    location = response.headers["location"]
    assert location.startswith("https://github.com/login/oauth/authorize")
    assert "client_id=test-client-id" in location
    assert "state=" in location
    assert "repomind_oauth_state" in response.cookies
