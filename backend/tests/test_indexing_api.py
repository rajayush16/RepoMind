import httpx
import pytest

from app.api.routes import repositories as repositories_routes


async def _register_and_connect(client: httpx.AsyncClient) -> str:
    await client.post(
        "/api/auth/register",
        json={"email": "indexer@example.com", "password": "correct-horse-battery"},
    )
    response = await client.post(
        "/api/repositories",
        json={
            "github_repo_id": 42,
            "owner": "octocat",
            "name": "hello-world",
            "full_name": "octocat/hello-world",
            "default_branch": "main",
        },
    )
    return response.json()["id"]


@pytest.mark.asyncio
async def test_trigger_indexing_enqueues_task_and_returns_queued_job(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_and_connect(client)

    enqueued: list[str] = []
    monkeypatch.setattr(
        repositories_routes.index_repository_task, "delay", lambda rid: enqueued.append(rid)
    )

    response = await client.post(f"/api/repositories/{repo_id}/index")
    assert response.status_code == 202
    assert enqueued == [repo_id]
    assert response.json()["status"] == "queued"


@pytest.mark.asyncio
async def test_trigger_indexing_twice_conflicts(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_and_connect(client)
    monkeypatch.setattr(repositories_routes.index_repository_task, "delay", lambda rid: None)

    first = await client.post(f"/api/repositories/{repo_id}/index")
    assert first.status_code == 202

    second = await client.post(f"/api/repositories/{repo_id}/index")
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_trigger_indexing_reports_broker_unavailable(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_and_connect(client)

    def raise_broker_error(rid: str) -> None:
        raise ConnectionError("Redis unreachable")

    monkeypatch.setattr(repositories_routes.index_repository_task, "delay", raise_broker_error)

    response = await client.post(f"/api/repositories/{repo_id}/index")
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_latest_indexing_job_404_before_any_job(client: httpx.AsyncClient) -> None:
    repo_id = await _register_and_connect(client)

    response = await client.get(f"/api/repositories/{repo_id}/indexing-jobs/latest")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_latest_indexing_job_returns_most_recent(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_and_connect(client)
    monkeypatch.setattr(repositories_routes.index_repository_task, "delay", lambda rid: None)

    await client.post(f"/api/repositories/{repo_id}/index")
    response = await client.get(f"/api/repositories/{repo_id}/indexing-jobs/latest")
    assert response.status_code == 200
    assert response.json()["repository_id"] == repo_id
    assert response.json()["status"] == "queued"
