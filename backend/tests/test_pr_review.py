import uuid

import pytest
from sqlalchemy import select

from app.models.pull_request import PullRequestReview, ReviewFinding
from app.models.repository import Repository
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.services.agents import pr_review as pr_review_service
from app.core.security import encrypt_secret

from tests.conftest import TestSessionLocal, get_test_settings
from tests.test_assistant_api import FakeLLMProvider

ANALYSIS_JSON = (
    '{"summary": "Mostly fine, one real bug.", "findings": ['
    '{"file_path": "app.py", "line": 12, "severity": "high", "category": "correctness", '
    '"summary": "Off-by-one in loop", "explanation": "range(n) should be range(n+1)", '
    '"suggestion": "use range(n + 1)"}]}'
)


@pytest.fixture
async def repository_with_token() -> Repository:
    settings = get_test_settings()
    async with TestSessionLocal() as db:
        user = User(email=f"pr-{uuid.uuid4().hex[:8]}@example.com")
        user.github_access_token_encrypted = encrypt_secret("fake-gh-token", settings)
        db.add(user)
        await db.flush()
        workspace = Workspace(name="PR Workspace", slug=f"pr-{uuid.uuid4().hex[:8]}")
        db.add(workspace)
        await db.flush()
        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=WorkspaceRole.OWNER))
        repository = Repository(
            workspace_id=workspace.id,
            connected_by_user_id=user.id,
            github_repo_id=1,
            owner="octocat",
            name="hello-world",
            full_name="octocat/hello-world",
            default_branch="main",
            selected_branch="main",
        )
        db.add(repository)
        await db.commit()
        await db.refresh(repository)
        return repository


@pytest.mark.asyncio
async def test_pr_review_persists_findings_from_real_diff(
    repository_with_token: Repository, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_get_pull_request(token, owner, repo, pr_number):
        assert token == "fake-gh-token"
        return {"title": "Fix loop bug", "html_url": "https://github.com/octocat/hello-world/pull/7"}

    async def fake_get_pull_request_files(token, owner, repo, pr_number):
        return [
            {
                "filename": "app.py",
                "status": "modified",
                "additions": 1,
                "deletions": 1,
                "patch": "@@ -10,3 +10,3 @@\n-for i in range(n):\n+for i in range(n):\n",
            }
        ]

    monkeypatch.setattr(pr_review_service, "get_pull_request", fake_get_pull_request)
    monkeypatch.setattr(pr_review_service, "get_pull_request_files", fake_get_pull_request_files)

    fake_provider = FakeLLMProvider(ANALYSIS_JSON)

    async with TestSessionLocal() as db:
        review = PullRequestReview(
            repository_id=repository_with_token.id,
            user_id=repository_with_token.connected_by_user_id,
            pr_number=7,
            pr_title="PR #7",
            pr_url="https://github.com/octocat/hello-world/pull/7",
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)
        review_id = review.id

    await pr_review_service.run_pr_review(review_id, TestSessionLocal, get_test_settings(), fake_provider)

    async with TestSessionLocal() as db:
        result = await db.execute(select(PullRequestReview).where(PullRequestReview.id == review_id))
        review = result.scalar_one()
        assert review.status == "complete"
        assert "one real bug" in review.summary
        assert review.pr_title == "Fix loop bug"

        findings_result = await db.execute(
            select(ReviewFinding).where(ReviewFinding.pull_request_review_id == review_id)
        )
        findings = findings_result.scalars().all()
        assert len(findings) == 1
        assert findings[0].category == "correctness"
        assert findings[0].severity == "high"


@pytest.mark.asyncio
async def test_pr_review_fails_gracefully_without_github_token(monkeypatch: pytest.MonkeyPatch) -> None:
    async with TestSessionLocal() as db:
        user = User(email=f"notoken-{uuid.uuid4().hex[:8]}@example.com")
        db.add(user)
        await db.flush()
        workspace = Workspace(name="No Token Workspace", slug=f"nt-{uuid.uuid4().hex[:8]}")
        db.add(workspace)
        await db.flush()
        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=WorkspaceRole.OWNER))
        repository = Repository(
            workspace_id=workspace.id,
            connected_by_user_id=user.id,
            github_repo_id=2,
            owner="octocat",
            name="no-token",
            full_name="octocat/no-token",
            default_branch="main",
            selected_branch="main",
        )
        db.add(repository)
        await db.commit()
        await db.refresh(repository)

        review = PullRequestReview(
            repository_id=repository.id,
            user_id=user.id,
            pr_number=1,
            pr_title="PR #1",
            pr_url="https://github.com/octocat/no-token/pull/1",
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)
        review_id = review.id

    await pr_review_service.run_pr_review(
        review_id, TestSessionLocal, get_test_settings(), FakeLLMProvider("unused")
    )

    async with TestSessionLocal() as db:
        result = await db.execute(select(PullRequestReview).where(PullRequestReview.id == review_id))
        review = result.scalar_one()
        assert review.status == "failed"
        assert "access token" in review.error_detail
