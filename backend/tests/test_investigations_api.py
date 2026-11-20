import uuid

import httpx
import pytest

from app.api.routes import investigations as investigations_routes


async def _register_and_connect(client: httpx.AsyncClient) -> str:
    await client.post(
        "/api/auth/register",
        json={"email": f"inv-{uuid.uuid4().hex[:8]}@example.com", "password": "correct-horse-battery"},
    )
    response = await client.post(
        "/api/repositories",
        json={
            "github_repo_id": 123,
            "owner": "octocat",
            "name": "hello-world",
            "full_name": "octocat/hello-world",
            "default_branch": "main",
        },
    )
    return response.json()["id"]


@pytest.mark.asyncio
async def test_start_investigation_enqueues_task(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_and_connect(client)

    enqueued: list[str] = []
    monkeypatch.setattr(
        investigations_routes.investigate_bug_task, "delay", lambda iid: enqueued.append(iid)
    )

    response = await client.post(
        f"/api/repositories/{repo_id}/investigations",
        json={"bug_description": "login is broken", "error_message": "ValueError", "stack_trace": None},
    )
    assert response.status_code == 202
    body = response.json()
    assert enqueued == [body["id"]]
    assert body["status"] == "running"
    assert body["steps"] == []


@pytest.mark.asyncio
async def test_start_investigation_reports_broker_unavailable(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_and_connect(client)

    def raise_error(iid: str) -> None:
        raise ConnectionError("broker down")

    monkeypatch.setattr(investigations_routes.investigate_bug_task, "delay", raise_error)

    response = await client.post(
        f"/api/repositories/{repo_id}/investigations", json={"bug_description": "x"}
    )
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_list_and_get_investigation(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_and_connect(client)
    monkeypatch.setattr(investigations_routes.investigate_bug_task, "delay", lambda iid: None)

    create_response = await client.post(
        f"/api/repositories/{repo_id}/investigations", json={"bug_description": "bug"}
    )
    investigation_id = create_response.json()["id"]

    list_response = await client.get(f"/api/repositories/{repo_id}/investigations")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = await client.get(f"/api/investigations/{investigation_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == investigation_id
