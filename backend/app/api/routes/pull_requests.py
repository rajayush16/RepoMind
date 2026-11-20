import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_current_workspace, get_decrypted_github_token
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.exceptions import NotFoundError, ServiceUnavailableError, ValidationError
from app.models.pull_request import PullRequestReview
from app.models.repository import Repository
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.pull_request import (
    PublishReviewRequest,
    PullRequestReviewOut,
    StartReviewRequest,
)
from app.services.github.client import GithubApiError, post_issue_comment
from app.workers.tasks import review_pull_request_task

router = APIRouter(tags=["pull-requests"])


async def _get_owned_repository(db: AsyncSession, workspace: Workspace, repository_id: uuid.UUID) -> Repository:
    repository = await db.get(Repository, repository_id)
    if repository is None or repository.workspace_id != workspace.id:
        raise NotFoundError("Repository not found.")
    return repository


@router.post(
    "/repositories/{repository_id}/pull-requests", response_model=PullRequestReviewOut, status_code=202
)
async def start_review(
    repository_id: uuid.UUID,
    body: StartReviewRequest,
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> PullRequestReviewOut:
    repository = await _get_owned_repository(db, workspace, repository_id)

    review = PullRequestReview(
        repository_id=repository_id,
        user_id=user.id,
        pr_number=body.pr_number,
        pr_title=f"PR #{body.pr_number}",
        pr_url=f"https://github.com/{repository.full_name}/pull/{body.pr_number}",
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    try:
        review_pull_request_task.delay(str(review.id))
    except Exception as exc:  # noqa: BLE001
        review.status = "failed"
        review.error_detail = f"Could not reach the background task broker: {exc}"
        await db.commit()
        raise ServiceUnavailableError(
            "The background task broker/worker is unavailable, or no LLM provider is "
            "configured. Make sure Redis, a Celery worker, and an LLM API key are set up."
        )

    return PullRequestReviewOut(
        id=review.id,
        repository_id=review.repository_id,
        pr_number=review.pr_number,
        pr_title=review.pr_title,
        pr_url=review.pr_url,
        status=review.status,
        summary=review.summary,
        published=review.published,
        published_comment_url=review.published_comment_url,
        error_detail=review.error_detail,
        created_at=review.created_at,
        findings=[],
    )


@router.get("/repositories/{repository_id}/pull-requests", response_model=list[PullRequestReviewOut])
async def list_reviews(
    repository_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[PullRequestReview]:
    await _get_owned_repository(db, workspace, repository_id)

    result = await db.execute(
        select(PullRequestReview)
        .where(PullRequestReview.repository_id == repository_id)
        .options(selectinload(PullRequestReview.findings))
        .order_by(PullRequestReview.created_at.desc())
    )
    return list(result.scalars().unique().all())


async def _get_owned_review(db: AsyncSession, workspace: Workspace, review_id: uuid.UUID) -> PullRequestReview:
    result = await db.execute(
        select(PullRequestReview)
        .where(PullRequestReview.id == review_id)
        .options(selectinload(PullRequestReview.findings))
    )
    review = result.scalar_one_or_none()
    if review is None:
        raise NotFoundError("Review not found.")
    await _get_owned_repository(db, workspace, review.repository_id)
    return review


@router.get("/pull-requests/{review_id}", response_model=PullRequestReviewOut)
async def get_review(
    review_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> PullRequestReview:
    return await _get_owned_review(db, workspace, review_id)


@router.post("/pull-requests/{review_id}/publish", response_model=PullRequestReviewOut)
async def publish_review(
    review_id: uuid.UUID,
    body: PublishReviewRequest,
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PullRequestReview:
    """Posts the review summary as a single GitHub comment. Never happens
    automatically -- requires both this explicit call and confirm=true, and the
    findings are always shown to the user as a preview beforehand (the frontend
    only offers this action after that preview is displayed)."""
    review = await _get_owned_review(db, workspace, review_id)

    if not body.confirm:
        raise ValidationError("Set confirm=true to publish this review to GitHub.")
    if review.status != "complete":
        raise ValidationError("This review hasn't finished generating yet.")
    if review.published:
        raise ValidationError("This review has already been published.")

    token = get_decrypted_github_token(user, settings)
    if token is None:
        raise ValidationError("GitHub is not connected for this account.")

    repository = await db.get(Repository, review.repository_id)

    comment_body = f"## RepoMind automated review\n\n{review.summary}\n\n" + "\n".join(
        f"- **{f.severity.upper()}** ({f.category}) `{f.file_path}`"
        + (f":{f.line}" if f.line else "")
        + f" -- {f.summary}"
        for f in review.findings
    )

    try:
        posted = await post_issue_comment(token, repository.owner, repository.name, review.pr_number, comment_body)
    except GithubApiError as exc:
        raise ValidationError(f"Could not post to GitHub: {exc}")

    review.published = True
    review.published_comment_url = posted.get("html_url")
    await db.commit()
    await db.refresh(review)
    return review
