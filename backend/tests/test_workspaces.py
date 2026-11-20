import httpx
import pytest


@pytest.mark.asyncio
async def test_current_workspace_returns_personal_workspace(client: httpx.AsyncClient) -> None:
    await client.post(
        "/api/auth/register",
        json={"email": "ivy@example.com", "password": "correct-horse-battery", "name": "Ivy"},
    )

    response = await client.get("/api/workspaces/current")
    assert response.status_code == 200
    body = response.json()
    assert body["is_personal"] is True
    assert "Ivy" in body["name"]


@pytest.mark.asyncio
async def test_current_workspace_requires_authentication(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/workspaces/current")
    assert response.status_code == 401
