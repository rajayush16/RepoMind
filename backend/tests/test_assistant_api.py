import subprocess
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest

from app.api.routes import assistant as assistant_routes
from app.services.indexing import pipeline
from app.services.llm.base import ChatMessage, LLMProvider

from tests.conftest import TestSessionLocal, get_test_settings


def _run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


class FakeLLMProvider(LLMProvider):
    name = "fake"
    model = "fake-model-1"

    def __init__(self, response_text: str = "The answer is right here.") -> None:
        self._response_text = response_text
        self.call_count = 0

    async def generate(self, messages: list[ChatMessage], *, max_tokens: int = 1024) -> str:
        self.call_count += 1
        return self._response_text

    async def generate_stream(
        self, messages: list[ChatMessage], *, max_tokens: int = 1024
    ) -> AsyncIterator[str]:
        self.call_count += 1
        for word in self._response_text.split(" "):
            yield word + " "


@pytest.fixture
def fixture_repo(tmp_path: Path) -> Path:
    repo_dir = tmp_path / "fixture-repo"
    repo_dir.mkdir()
    _run("git", "init", "-q", "-b", "main", cwd=repo_dir)
    _run("git", "config", "user.email", "test@example.com", cwd=repo_dir)
    _run("git", "config", "user.name", "Test", cwd=repo_dir)
    (repo_dir / "auth.py").write_text(
        "def authenticate(user):\n    return check_password(user)\n"
    )
    _run("git", "add", "-A", cwd=repo_dir)
    _run("git", "commit", "-q", "-m", "initial commit", cwd=repo_dir)
    return repo_dir


async def _register_connect_and_index(
    client: httpx.AsyncClient, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> str:
    await client.post(
        "/api/auth/register",
        json={"email": f"asst-{uuid.uuid4().hex[:8]}@example.com", "password": "correct-horse-battery"},
    )
    connect_response = await client.post(
        "/api/repositories",
        json={
            "github_repo_id": 99,
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
async def test_ask_without_configured_provider_returns_422(
    client: httpx.AsyncClient, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_connect_and_index(client, fixture_repo, monkeypatch)
    conv_response = await client.post(f"/api/repositories/{repo_id}/conversations", json={})
    conversation_id = conv_response.json()["id"]

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages", json={"question": "How does auth work?"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ask_streams_answer_and_persists_real_citations(
    client: httpx.AsyncClient, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_connect_and_index(client, fixture_repo, monkeypatch)
    conv_response = await client.post(f"/api/repositories/{repo_id}/conversations", json={})
    conversation_id = conv_response.json()["id"]

    fake_provider = FakeLLMProvider("auth.py defines authenticate at line 1.")
    monkeypatch.setattr(assistant_routes, "get_llm_provider", lambda settings: fake_provider)

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages", json={"question": "authenticate"}
    )
    assert response.status_code == 200
    assert fake_provider.call_count == 1
    assert "event: done" in response.text
    assert "auth.py" in response.text

    messages_response = await client.get(f"/api/conversations/{conversation_id}/messages")
    messages = messages_response.json()
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["provider"] == "fake"
    assert messages[1]["model"] == "fake-model-1"
    assert messages[1]["insufficient_evidence"] is False
    assert any(c["file_path"] == "auth.py" for c in messages[1]["citations"])


@pytest.mark.asyncio
async def test_ask_with_no_matching_evidence_skips_the_model_entirely(
    client: httpx.AsyncClient, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_id = await _register_connect_and_index(client, fixture_repo, monkeypatch)
    conv_response = await client.post(f"/api/repositories/{repo_id}/conversations", json={})
    conversation_id = conv_response.json()["id"]

    fake_provider = FakeLLMProvider("should never be used")
    monkeypatch.setattr(assistant_routes, "get_llm_provider", lambda settings: fake_provider)

    response = await client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"question": "zzz_no_such_symbol_exists_zzz"},
    )
    assert response.status_code == 200
    assert fake_provider.call_count == 0  # never called the model at all
    assert "couldn't find" in response.text.lower()

    messages_response = await client.get(f"/api/conversations/{conversation_id}/messages")
    messages = messages_response.json()
    assert messages[1]["insufficient_evidence"] is True
    assert messages[1]["citations"] == []
