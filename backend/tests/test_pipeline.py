import subprocess
import uuid
from pathlib import Path

import pytest
from sqlalchemy import select

from app.models.indexing import CodeSymbol, IndexedFile, IndexingJob, IndexingJobStatus
from app.models.repository import Repository
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.services.indexing import pipeline

from tests.conftest import TestSessionLocal, get_test_settings


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
    (repo_dir / "utils.js").write_text("function square(x) { return x * x; }\n")

    _run("git", "add", "-A", cwd=repo_dir)
    _run("git", "commit", "-q", "-m", "initial commit", cwd=repo_dir)

    return repo_dir


@pytest.fixture
async def seeded_repository(fixture_repo: Path) -> Repository:
    async with TestSessionLocal() as db:
        user = User(email="pipeline-owner@example.com")
        db.add(user)
        await db.flush()

        workspace = Workspace(name="Pipeline Owner's Workspace", slug=f"pipeline-{uuid.uuid4().hex[:8]}")
        db.add(workspace)
        await db.flush()
        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=WorkspaceRole.OWNER))

        repository = Repository(
            workspace_id=workspace.id,
            connected_by_user_id=user.id,
            github_repo_id=1,
            owner="octocat",
            name="fixture-repo",
            full_name="octocat/fixture-repo",
            default_branch="main",
            selected_branch="main",
            is_private=False,
        )
        db.add(repository)
        await db.commit()
        await db.refresh(repository)
        return repository


@pytest.mark.asyncio
async def test_run_indexing_persists_files_and_symbols(
    seeded_repository: Repository, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_clone_repository = pipeline.clone_repository

    def fake_clone_repository(url: str, branch: str, access_token: str | None = None):
        return real_clone_repository(str(fixture_repo), branch, access_token)

    monkeypatch.setattr(pipeline, "clone_repository", fake_clone_repository)

    await pipeline.run_indexing(
        seeded_repository.id,
        session_factory=TestSessionLocal,
        settings=get_test_settings(),
    )

    async with TestSessionLocal() as db:
        job_result = await db.execute(
            select(IndexingJob).where(IndexingJob.repository_id == seeded_repository.id)
        )
        job = job_result.scalar_one()
        assert job.status == IndexingJobStatus.SUCCESS
        assert job.files_discovered == 2
        assert job.files_processed == 2
        assert job.symbols_extracted == 4  # helper, Service, run, square
        assert job.commit_sha and len(job.commit_sha) == 40
        # Neither Neo4j nor Qdrant are reachable in this environment -- confirm the
        # job still succeeds and honestly reports nothing was written, not fake counts.
        assert job.graph_relationships_written == 0
        assert job.embeddings_generated == 0

        files_result = await db.execute(
            select(IndexedFile).where(IndexedFile.repository_id == seeded_repository.id)
        )
        files = {f.relative_path: f for f in files_result.scalars().all()}
        assert set(files.keys()) == {"app.py", "utils.js"}
        assert files["app.py"].symbol_count == 3
        assert files["utils.js"].symbol_count == 1

        symbols_result = await db.execute(
            select(CodeSymbol).where(CodeSymbol.repository_id == seeded_repository.id)
        )
        symbols = {s.name: s for s in symbols_result.scalars().all()}
        assert symbols["helper"].symbol_type == "function"
        assert symbols["Service"].symbol_type == "class"
        assert symbols["run"].symbol_type == "method"
        assert symbols["run"].parent_name == "Service"

        refreshed_repo = await db.get(Repository, seeded_repository.id)
        assert refreshed_repo.indexing_status == "indexed"
        assert refreshed_repo.file_count == 2
        assert refreshed_repo.symbol_count == 4


@pytest.mark.asyncio
async def test_run_indexing_is_idempotent_across_reindex(
    seeded_repository: Repository, fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_clone_repository = pipeline.clone_repository

    def fake_clone_repository(url: str, branch: str, access_token: str | None = None):
        return real_clone_repository(str(fixture_repo), branch, access_token)

    monkeypatch.setattr(pipeline, "clone_repository", fake_clone_repository)

    await pipeline.run_indexing(
        seeded_repository.id, session_factory=TestSessionLocal, settings=get_test_settings()
    )
    await pipeline.run_indexing(
        seeded_repository.id, session_factory=TestSessionLocal, settings=get_test_settings()
    )

    async with TestSessionLocal() as db:
        symbols_result = await db.execute(
            select(CodeSymbol).where(CodeSymbol.repository_id == seeded_repository.id)
        )
        symbols = symbols_result.scalars().all()
        assert len(symbols) == 4  # re-indexing the same commit does not duplicate rows

        jobs_result = await db.execute(
            select(IndexingJob).where(IndexingJob.repository_id == seeded_repository.id)
        )
        jobs = jobs_result.scalars().all()
        assert len(jobs) == 2
        assert all(job.status == IndexingJobStatus.SUCCESS for job in jobs)


@pytest.mark.asyncio
async def test_run_indexing_marks_job_failed_on_clone_error(
    seeded_repository: Repository, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.services.indexing.clone import CloneError

    def failing_clone(url: str, branch: str, access_token: str | None = None):
        raise CloneError("simulated clone failure")

    monkeypatch.setattr(pipeline, "clone_repository", failing_clone)

    await pipeline.run_indexing(
        seeded_repository.id, session_factory=TestSessionLocal, settings=get_test_settings()
    )

    async with TestSessionLocal() as db:
        job_result = await db.execute(
            select(IndexingJob).where(IndexingJob.repository_id == seeded_repository.id)
        )
        job = job_result.scalar_one()
        assert job.status == IndexingJobStatus.FAILED
        assert "simulated clone failure" in job.error_message

        refreshed_repo = await db.get(Repository, seeded_repository.id)
        assert refreshed_repo.indexing_status == "failed"
