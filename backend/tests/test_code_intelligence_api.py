import subprocess
import uuid
from pathlib import Path

import httpx
import pytest

from app.services.indexing import pipeline

from tests.conftest import get_test_settings


def _run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def fixture_repo(tmp_path: Path) -> Path:
    repo_dir = tmp_path / "fixture-repo"
    repo_dir.mkdir()

    _run("git", "init", "-q", "-b", "main", cwd=repo_dir)
    _run("git", "config", "user.email", "test@example.com", cwd=repo_dir)
    _run("git", "config", "user.name", "Test", cwd=repo_dir)

    (repo_dir / "app.py").write_text(
        "def helper():\n"
        "    return 1\n"
        "\n"
        "class Service:\n"
        "    def run(self):\n"
        "        return helper()\n"
    )

    _run("git", "add", "-A", cwd=repo_dir)
    _run("git", "commit", "-q", "-m", "initial commit", cwd=repo_dir)

    return repo_dir


async def _register_connect_and_index(
    client: httpx.AsyncClient, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> str:
    await client.post(
        "/api/auth/register",
        json={"email": f"ci-{uuid.uuid4().hex[:8]}@example.com", "password": "correct-horse-battery"},
    )
    connect_response = await client.post(
        "/api/repositories",
        json={
            "github_repo_id": 7,
            "owner": "octocat",
            "name": "fixture-repo",
            "full_name": "octocat/fixture-repo",
            "default_branch": "main",
        },
    )
    repo_id = connect_response.json()["id"]

    real_clone_repository = pipeline.clone_repository

    def fake_clone_repository(url: str, branch: str, access_token: str | None = None):
        return real_clone_repository(str(fixture_repo), branch, access_token)

    monkeypatch.setattr(pipeline, "clone_repository", fake_clone_repository)

    from tests.conftest import TestSessionLocal

    await pipeline.run_indexing(
        uuid.UUID(repo_id), session_factory=TestSessionLocal, settings=get_test_settings()
    )
    return repo_id


@pytest.mark.asyncio
async def test_list_files_and_get_content(
    client: httpx.AsyncClient, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_connect_and_index(client, fixture_repo, monkeypatch)

    files_response = await client.get(f"/api/repositories/{repo_id}/files")
    assert files_response.status_code == 200
    paths = {f["relative_path"] for f in files_response.json()}
    assert paths == {"app.py"}

    content_response = await client.get(
        f"/api/repositories/{repo_id}/files/content", params={"path": "app.py"}
    )
    assert content_response.status_code == 200
    assert "def helper" in content_response.json()["content"]


@pytest.mark.asyncio
async def test_get_file_content_404_for_unknown_path(
    client: httpx.AsyncClient, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_connect_and_index(client, fixture_repo, monkeypatch)

    response = await client.get(
        f"/api/repositories/{repo_id}/files/content", params={"path": "does-not-exist.py"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_symbols_filters_by_file_and_name(
    client: httpx.AsyncClient, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_connect_and_index(client, fixture_repo, monkeypatch)

    all_symbols = await client.get(f"/api/repositories/{repo_id}/symbols")
    assert {s["name"] for s in all_symbols.json()} == {"helper", "Service", "run"}

    filtered = await client.get(f"/api/repositories/{repo_id}/symbols", params={"name": "serv"})
    assert {s["name"] for s in filtered.json()} == {"Service"}


@pytest.mark.asyncio
async def test_search_finds_symbols_via_lexical_and_symbol_paths(
    client: httpx.AsyncClient, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_connect_and_index(client, fixture_repo, monkeypatch)

    response = await client.get(f"/api/repositories/{repo_id}/search", params={"q": "helper"})
    assert response.status_code == 200
    results = response.json()
    assert any(r["symbol_name"] == "helper" for r in results)
    # No Qdrant/Neo4j in this environment -- confirm those sources are absent
    # rather than silently fabricated.
    assert all("vector" not in r["sources"] and "graph" not in r["sources"] for r in results)


@pytest.mark.asyncio
async def test_architecture_graph_reports_unavailable_without_neo4j(
    client: httpx.AsyncClient, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_connect_and_index(client, fixture_repo, monkeypatch)

    response = await client.get(f"/api/repositories/{repo_id}/graph")
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["reason"]
    assert body["nodes"] == []
    assert body["edges"] == []
