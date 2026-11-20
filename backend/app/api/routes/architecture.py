import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_workspace
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.repository import Repository
from app.models.workspace import Workspace
from app.schemas.graph import GraphOut
from app.services.graph.queries import get_repository_graph

router = APIRouter(prefix="/repositories/{repository_id}/graph", tags=["architecture"])


@router.get("", response_model=GraphOut)
async def architecture_graph(
    repository_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> GraphOut:
    repository = await db.get(Repository, repository_id)
    if repository is None or repository.workspace_id != workspace.id:
        raise NotFoundError("Repository not found.")

    graph = await get_repository_graph(settings, str(repository_id))
    return GraphOut(**graph)
