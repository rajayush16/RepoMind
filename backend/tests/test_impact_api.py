import uuid

import httpx
import pytest

from app.services.graph import impact as impact_service


async def _register_and_connect(client: httpx.AsyncClient) -> str:
    await client.post(
        "/api/auth/register",
        json={"email": f"impact-{uuid.uuid4().hex[:8]}@example.com", "password": "correct-horse-battery"},
    )
    response = await client.post(
        "/api/repositories",
        json={
            "github_repo_id": 321,
            "owner": "octocat",
            "name": "hello-world",
            "full_name": "octocat/hello-world",
            "default_branch": "main",
        },
    )
    return response.json()["id"]


@pytest.mark.asyncio
async def test_impact_reports_unavailable_without_neo4j(client: httpx.AsyncClient) -> None:
    repo_id = await _register_and_connect(client)

    response = await client.get(f"/api/repositories/{repo_id}/impact", params={"symbol": "authenticate"})
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["risk"] == "unknown"
    assert body["direct_callers"] == []


@pytest.mark.asyncio
async def test_impact_reports_risk_from_caller_count(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_and_connect(client)

    async def fake_get_callers(settings, repository_id, symbol_name, limit=50):
        return [{"name": "login_handler", "file_path": "routes.py"}]

    monkeypatch.setattr(impact_service, "get_callers", fake_get_callers)

    response = await client.get(f"/api/repositories/{repo_id}/impact", params={"symbol": "authenticate"})
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert body["risk"] == "medium"
    assert body["direct_callers"] == [{"name": "login_handler", "file_path": "routes.py"}]
    assert body["dependent_files"] == [{"file_path": "routes.py"}]
