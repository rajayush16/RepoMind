import subprocess
import uuid
from pathlib import Path

import pytest
from sqlalchemy import select

from app.models.investigation import Investigation, InvestigationStatus, InvestigationStep
from app.models.repository import Repository
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.services.agents import bug_investigation
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
    (repo_dir / "auth.py").write_text(
        "def authenticate(user):\n"
        "    return check_password(user)\n"
        "\n"
        "def check_password(user):\n"
        "    return user.password == 'hunter2'\n"
    )
    _run("git", "add", "-A", cwd=repo_dir)
    _run("git", "commit", "-q", "-m", "initial commit", cwd=repo_dir)
    return repo_dir


@pytest.fixture
async def indexed_repository(fixture_repo: Path, monkeypatch: pytest.MonkeyPatch) -> Repository:
    async with TestSessionLocal() as db:
        user = User(email=f"bug-{uuid.uuid4().hex[:8]}@example.com")
        db.add(user)
        await db.flush()
        workspace = Workspace(name="Bug Workspace", slug=f"bug-{uuid.uuid4().hex[:8]}")
        db.add(workspace)
        await db.flush()
        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=WorkspaceRole.OWNER))
        repository = Repository(
            workspace_id=workspace.id,
            connected_by_user_id=user.id,
            github_repo_id=55,
            owner="octocat",
            name="fixture-repo",
            full_name="octocat/fixture-repo",
            default_branch="main",
            selected_branch="main",
        )
        db.add(repository)
        await db.commit()
        await db.refresh(repository)

    real_clone_repository = pipeline.clone_repository

    def fake_clone_repository(url: str, branch: str, access_token: str | None = None):
        return real_clone_repository(str(fixture_repo), branch, access_token)

    monkeypatch.setattr(pipeline, "clone_repository", fake_clone_repository)
    await pipeline.run_indexing(repository.id, session_factory=TestSessionLocal, settings=get_test_settings())
    return repository


@pytest.mark.asyncio
async def test_investigation_completes_with_root_cause_from_evidence(
    indexed_repository: Repository,
) -> None:
    fake_provider = FakeLLMProvider(
        '{"root_cause": "check_password uses a hardcoded password", '
        '"confidence_explanation": "the literal hunter2 is visible in the evidence", '
        '"suggested_fix": "hash and compare passwords properly", '
        '"potential_side_effects": "none"}'
    )

    async with TestSessionLocal() as db:
        investigation = Investigation(
            repository_id=indexed_repository.id,
            user_id=indexed_repository.connected_by_user_id,
            bug_description="Login always succeeds even with the wrong password",
            error_message=None,
            stack_trace='File "auth.py", line 2, in authenticate\n  return check_password(user)',
        )
        db.add(investigation)
        await db.commit()
        await db.refresh(investigation)
        investigation_id = investigation.id

    await bug_investigation.run_investigation(
        investigation_id, TestSessionLocal, get_test_settings(), fake_provider
    )

    async with TestSessionLocal() as db:
        result = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
        investigation = result.scalar_one()
        assert investigation.status == InvestigationStatus.COMPLETE
        assert "hardcoded password" in investigation.root_cause

        steps_result = await db.execute(
            select(InvestigationStep)
            .where(InvestigationStep.investigation_id == investigation_id)
            .order_by(InvestigationStep.created_at)
        )
        stages = [s.stage for s in steps_result.scalars().all()]
        assert stages == [
            "parse_issue",
            "find_related_symbols",
            "trace_execution",
            "evaluate_causes",
            "prepare_findings",
        ]


@pytest.mark.asyncio
async def test_investigation_skips_model_when_no_evidence_found(
    indexed_repository: Repository,
) -> None:
    fake_provider = FakeLLMProvider("should never be called")

    async with TestSessionLocal() as db:
        investigation = Investigation(
            repository_id=indexed_repository.id,
            user_id=indexed_repository.connected_by_user_id,
            bug_description="zzz_completely_unrelated_nonsense_zzz",
        )
        db.add(investigation)
        await db.commit()
        await db.refresh(investigation)
        investigation_id = investigation.id

    await bug_investigation.run_investigation(
        investigation_id, TestSessionLocal, get_test_settings(), fake_provider
    )

    assert fake_provider.call_count == 0

    async with TestSessionLocal() as db:
        result = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
        investigation = result.scalar_one()
        assert investigation.status == InvestigationStatus.COMPLETE
        assert "Not enough evidence" in investigation.root_cause
