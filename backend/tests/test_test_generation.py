import subprocess
import uuid
from pathlib import Path

import pytest

from app.services.agents.test_generation import SymbolNotFoundError, generate_test_code
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


@pytest.fixture
async def indexed_repository_id(fixture_repo: Path, monkeypatch: pytest.MonkeyPatch) -> uuid.UUID:
    from app.models.repository import Repository
    from app.models.user import User
    from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole

    async with TestSessionLocal() as db:
        user = User(email=f"gen-{uuid.uuid4().hex[:8]}@example.com")
        db.add(user)
        await db.flush()
        workspace = Workspace(name="Gen Workspace", slug=f"gen-{uuid.uuid4().hex[:8]}")
        db.add(workspace)
        await db.flush()
        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=WorkspaceRole.OWNER))
        repository = Repository(
            workspace_id=workspace.id,
            connected_by_user_id=user.id,
            github_repo_id=88,
            owner="octocat",
            name="fixture-repo",
            full_name="octocat/fixture-repo",
            default_branch="main",
            selected_branch="main",
        )
        db.add(repository)
        await db.commit()
        await db.refresh(repository)
        repository_id = repository.id

    real_clone_repository = pipeline.clone_repository

    def fake_clone_repository(url: str, branch: str, access_token: str | None = None):
        return real_clone_repository(str(fixture_repo), branch, access_token)

    monkeypatch.setattr(pipeline, "clone_repository", fake_clone_repository)
    await pipeline.run_indexing(repository_id, session_factory=TestSessionLocal, settings=get_test_settings())
    return repository_id


@pytest.mark.asyncio
async def test_generate_test_code_uses_real_indexed_source(indexed_repository_id: uuid.UUID) -> None:
    fake_provider = FakeLLMProvider("def test_add():\n    assert add(1, 2) == 3\n")

    async with TestSessionLocal() as db:
        code = await generate_test_code(
            db, fake_provider, indexed_repository_id, "add", "math_utils.py", "pytest"
        )

    assert "test_add" in code


@pytest.mark.asyncio
async def test_generate_test_code_raises_for_unknown_symbol(indexed_repository_id: uuid.UUID) -> None:
    fake_provider = FakeLLMProvider("unused")

    async with TestSessionLocal() as db:
        with pytest.raises(SymbolNotFoundError):
            await generate_test_code(
                db, fake_provider, indexed_repository_id, "does_not_exist", "math_utils.py", "pytest"
            )
