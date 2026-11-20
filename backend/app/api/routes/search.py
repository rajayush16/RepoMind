import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_workspace
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.repository import Repository
from app.models.workspace import Workspace
from app.schemas.search import SearchResultOut
from app.services.retrieval.hybrid import hybrid_search

router = APIRouter(prefix="/repositories/{repository_id}/search", tags=["search"])


@router.get("", response_model=list[SearchResultOut])
async def search_repository(
    repository_id: uuid.UUID,
    q: str = Query(..., min_length=1, description="search query"),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[SearchResultOut]:
    repository = await db.get(Repository, repository_id)
    if repository is None or repository.workspace_id != workspace.id:
        raise NotFoundError("Repository not found.")

    results = await hybrid_search(db, settings, repository_id, q)
    return [SearchResultOut(**result.__dict__) for result in results]
