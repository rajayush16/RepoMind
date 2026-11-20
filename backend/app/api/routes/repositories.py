import uuid

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_workspace, get_decrypted_github_token
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.repository import Repository
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.repository import AvailableGithubRepo, ConnectRepositoryRequest, RepositoryOut
from app.services.github.client import GithubApiError, list_user_repositories

router = APIRouter(prefix="/repositories", tags=["repositories"])


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
    repository = await db.get(Repository, repository_id)
    if repository is None or repository.workspace_id != workspace.id:
        raise NotFoundError("Repository not found.")

    await db.delete(repository)
    await db.commit()
