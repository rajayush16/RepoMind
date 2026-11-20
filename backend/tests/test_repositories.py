import httpx
import pytest
from sqlalchemy import select

from app.api.routes import repositories as repositories_routes
from app.core.security import encrypt_secret
from app.models.user import User

from tests.conftest import TestSessionLocal, get_test_settings


async def _register(client: httpx.AsyncClient, email: str) -> None:
    response = await client.post(
        "/api/auth/register", json={"email": email, "password": "correct-horse-battery"}
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_list_repositories_is_empty_initially(client: httpx.AsyncClient) -> None:
    await _register(client, "erin@example.com")

    response = await client.get("/api/repositories")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_available_github_repos_requires_github_connection(
    client: httpx.AsyncClient,
) -> None:
    await _register(client, "frank@example.com")

    response = await client.get("/api/repositories/github/available")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_connect_list_and_delete_repository(client: httpx.AsyncClient) -> None:
    await _register(client, "grace@example.com")

    connect_response = await client.post(
        "/api/repositories",
        json={
            "github_repo_id": 123,
            "owner": "octocat",
            "name": "hello-world",
            "full_name": "octocat/hello-world",
            "default_branch": "main",
            "is_private": False,
        },
    )
    assert connect_response.status_code == 201
    repo_id = connect_response.json()["id"]

    list_response = await client.get("/api/repositories")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["full_name"] == "octocat/hello-world"

    duplicate_response = await client.post(
        "/api/repositories",
        json={
            "github_repo_id": 123,
            "owner": "octocat",
            "name": "hello-world",
            "full_name": "octocat/hello-world",
        },
    )
    assert duplicate_response.status_code == 422

    delete_response = await client.delete(f"/api/repositories/{repo_id}")
    assert delete_response.status_code == 204

    final_list = await client.get("/api/repositories")
    assert final_list.json() == []


@pytest.mark.asyncio
async def test_available_github_repos_with_connected_account(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _register(client, "heidi@example.com")

    settings = get_test_settings()
    async with TestSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "heidi@example.com"))
        user = result.scalar_one()
        user.github_access_token_encrypted = encrypt_secret("fake-github-token", settings)
        await session.commit()

    async def fake_list_user_repositories(access_token: str) -> list[dict]:
        assert access_token == "fake-github-token"
        return [
            {
                "id": 999,
                "owner": {"login": "heidi"},
                "name": "project",
                "full_name": "heidi/project",
                "description": "A test repo",
                "default_branch": "main",
                "language": "Python",
                "private": False,
            }
        ]

    monkeypatch.setattr(
        repositories_routes, "list_user_repositories", fake_list_user_repositories
    )

    response = await client.get("/api/repositories/github/available")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["full_name"] == "heidi/project"
    assert body[0]["already_connected"] is False
