import subprocess
import uuid
from pathlib import Path

import httpx
import pytest

from app.api.routes import tests as tests_routes
from app.services.indexing import pipeline

from tests.conftest import TestSessionLocal, get_test_settings
from tests.test_assistant_api import FakeLLMProvider


def _run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def fixture_repo(tmp_path: Path) -> Path:
    repo_dir = tmp_path / "fixture-repo"
    repo_dir.mkdir()
    _run("git", "init", "-q", "-b", "main", cwd=repo_dir)
    _run("git", "config", "user.email", "test@example.com", cwd=repo_dir)
    _run("git", "config", "user.name", "Test", cwd=repo_dir)
    (repo_dir / "math_utils.py").write_text("def add(a, b):\n    return a + b\n")
    _run("git", "add", "-A", cwd=repo_dir)
    _run("git", "commit", "-q", "-m", "initial commit", cwd=repo_dir)
    return repo_dir


async def _register_connect_and_index(
    client: httpx.AsyncClient, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> str:
    await client.post(
        "/api/auth/register",
        json={"email": f"gentest-{uuid.uuid4().hex[:8]}@example.com", "password": "correct-horse-battery"},
    )
    connect_response = await client.post(
        "/api/repositories",
        json={
            "github_repo_id": 200,
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
    await pipeline.run_indexing(
        uuid.UUID(repo_id), session_factory=TestSessionLocal, settings=get_test_settings()
    )
    return repo_id


@pytest.mark.asyncio
async def test_generate_test_without_provider_returns_422(
    client: httpx.AsyncClient, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_connect_and_index(client, fixture_repo, monkeypatch)

    response = await client.post(
        f"/api/repositories/{repo_id}/tests",
        json={"symbol_name": "add", "file_path": "math_utils.py", "framework": "pytest"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generate_test_rejects_unsupported_framework(
    client: httpx.AsyncClient, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_connect_and_index(client, fixture_repo, monkeypatch)
    monkeypatch.setattr(tests_routes, "get_llm_provider", lambda settings: FakeLLMProvider("ignored"))

    response = await client.post(
        f"/api/repositories/{repo_id}/tests",
        json={"symbol_name": "add", "file_path": "math_utils.py", "framework": "junit"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_generate_test_persists_code_from_fake_provider(
    client: httpx.AsyncClient, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_connect_and_index(client, fixture_repo, monkeypatch)
    fake_provider = FakeLLMProvider("def test_add():\n    assert add(1, 2) == 3\n")
    monkeypatch.setattr(tests_routes, "get_llm_provider", lambda settings: fake_provider)

    response = await client.post(
        f"/api/repositories/{repo_id}/tests",
        json={"symbol_name": "add", "file_path": "math_utils.py", "framework": "pytest"},
    )
    assert response.status_code == 201
    body = response.json()
    assert "test_add" in body["code"]

    list_response = await client.get(f"/api/repositories/{repo_id}/tests")
    assert len(list_response.json()) == 1


@pytest.mark.asyncio
async def test_generate_test_404_for_unknown_symbol(
    client: httpx.AsyncClient, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_connect_and_index(client, fixture_repo, monkeypatch)
    monkeypatch.setattr(tests_routes, "get_llm_provider", lambda settings: FakeLLMProvider("x"))

    response = await client.post(
        f"/api/repositories/{repo_id}/tests",
        json={"symbol_name": "does_not_exist", "file_path": "math_utils.py", "framework": "pytest"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_execute_test_enqueues_and_polling_works(
    client: httpx.AsyncClient, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_connect_and_index(client, fixture_repo, monkeypatch)
    fake_provider = FakeLLMProvider("def test_add():\n    assert add(1, 2) == 3\n")
    monkeypatch.setattr(tests_routes, "get_llm_provider", lambda settings: fake_provider)

    generate_response = await client.post(
        f"/api/repositories/{repo_id}/tests",
        json={"symbol_name": "add", "file_path": "math_utils.py", "framework": "pytest"},
    )
    generated_test_id = generate_response.json()["id"]

    enqueued: list[str] = []
    monkeypatch.setattr(
        tests_routes.execute_generated_test_task, "delay", lambda eid: enqueued.append(eid)
    )

    execute_response = await client.post(f"/api/generated-tests/{generated_test_id}/execute")
    assert execute_response.status_code == 202
    assert enqueued == [execute_response.json()["id"]]
    assert execute_response.json()["status"] == "pending"

    latest = await client.get(f"/api/generated-tests/{generated_test_id}/executions/latest")
    assert latest.status_code == 200
    assert latest.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_execute_test_reports_broker_unavailable(
    client: httpx.AsyncClient, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_connect_and_index(client, fixture_repo, monkeypatch)
    fake_provider = FakeLLMProvider("def test_add():\n    assert add(1, 2) == 3\n")
    monkeypatch.setattr(tests_routes, "get_llm_provider", lambda settings: fake_provider)

    generate_response = await client.post(
        f"/api/repositories/{repo_id}/tests",
        json={"symbol_name": "add", "file_path": "math_utils.py", "framework": "pytest"},
    )
    generated_test_id = generate_response.json()["id"]

    def raise_error(eid: str) -> None:
        raise ConnectionError("broker down")

    monkeypatch.setattr(tests_routes.execute_generated_test_task, "delay", raise_error)

    response = await client.post(f"/api/generated-tests/{generated_test_id}/execute")
    assert response.status_code == 503
