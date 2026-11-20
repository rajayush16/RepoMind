import uuid

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_workspace, get_decrypted_github_token
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.exceptions import ConflictError, NotFoundError, ServiceUnavailableError, ValidationError
from app.models.indexing import IndexingJob, IndexingJobStatus
from app.models.repository import Repository
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.indexing import IndexingJobOut
from app.schemas.repository import AvailableGithubRepo, ConnectRepositoryRequest, RepositoryOut
from app.services.github.client import GithubApiError, list_user_repositories
from app.workers.tasks import index_repository_task

router = APIRouter(prefix="/repositories", tags=["repositories"])

INDEXING_IN_PROGRESS_STATUSES = {"queued", "indexing"}


@router.get("", response_model=list[RepositoryOut])
async def list_repositories(
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[Repository]:
    result = await db.execute(
        select(Repository).where(Repository.workspace_id == workspace.id)
    )
    return list(result.scalars().all())


@router.get("/github/available", response_model=list[AvailableGithubRepo])
async def list_available_github_repositories(
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[AvailableGithubRepo]:
    token = get_decrypted_github_token(user, settings)
    if token is None:
        raise ValidationError(
            "GitHub is not connected for this account. Sign in via /api/auth/github/login first."
        )

    try:
        github_repos = await list_user_repositories(token)
    except (GithubApiError, httpx.HTTPError) as exc:
        raise ValidationError(f"Could not reach GitHub: {exc}")

    connected_result = await db.execute(
        select(Repository.github_repo_id).where(Repository.workspace_id == workspace.id)
    )
    connected_ids = {row[0] for row in connected_result.all()}

    return [
        AvailableGithubRepo(
            github_repo_id=repo["id"],
            owner=repo["owner"]["login"],
            name=repo["name"],
            full_name=repo["full_name"],
            description=repo.get("description"),
            default_branch=repo.get("default_branch", "main"),
            primary_language=repo.get("language"),
            is_private=repo.get("private", False),
            already_connected=repo["id"] in connected_ids,
        )
        for repo in github_repos
    ]


@router.post("", response_model=RepositoryOut, status_code=201)
async def connect_repository(
    body: ConnectRepositoryRequest,
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> Repository:
    existing = await db.execute(
        select(Repository).where(
            Repository.workspace_id == workspace.id,
            Repository.github_repo_id == body.github_repo_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ValidationError("This repository is already connected.")

    repository = Repository(
        workspace_id=workspace.id,
        connected_by_user_id=user.id,
        github_repo_id=body.github_repo_id,
        owner=body.owner,
        name=body.name,
        full_name=body.full_name,
        description=body.description,
        default_branch=body.default_branch,
        selected_branch=body.selected_branch or body.default_branch,
        primary_language=body.primary_language,
        is_private=body.is_private,
    )
    db.add(repository)
    await db.commit()
    await db.refresh(repository)
    return repository


@router.delete("/{repository_id}", status_code=204)
async def delete_repository(
    repository_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> None:
    repository = await _get_owned_repository(db, workspace, repository_id)

    await db.delete(repository)
    await db.commit()


async def _get_owned_repository(
    db: AsyncSession, workspace: Workspace, repository_id: uuid.UUID
) -> Repository:
    repository = await db.get(Repository, repository_id)
    if repository is None or repository.workspace_id != workspace.id:
        raise NotFoundError("Repository not found.")
    return repository


@router.post("/{repository_id}/index", response_model=IndexingJobOut, status_code=202)
async def trigger_indexing(
    repository_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> IndexingJob:
    repository = await _get_owned_repository(db, workspace, repository_id)

    if repository.indexing_status in INDEXING_IN_PROGRESS_STATUSES:
        raise ConflictError("This repository is already being indexed.")

    job = IndexingJob(repository_id=repository.id)
    repository.indexing_status = "queued"
    db.add(job)
    await db.commit()
    await db.refresh(job)

    try:
        index_repository_task.delay(str(repository.id))
    except Exception as exc:  # noqa: BLE001
        job.status = IndexingJobStatus.FAILED
        job.error_message = f"Could not reach the background task broker: {exc}"
        repository.indexing_status = "failed"
        await db.commit()
        raise ServiceUnavailableError(
            "The background indexing worker/broker is unavailable. "
            "Make sure Redis and a Celery worker are running."
        )

    return job


@router.get("/{repository_id}/indexing-jobs/latest", response_model=IndexingJobOut)
async def latest_indexing_job(
    repository_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> IndexingJob:
    await _get_owned_repository(db, workspace, repository_id)

    result = await db.execute(
        select(IndexingJob)
        .where(IndexingJob.repository_id == repository_id)
        .order_by(IndexingJob.created_at.desc())
        .limit(1)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise NotFoundError("This repository has not been indexed yet.")
    return job
