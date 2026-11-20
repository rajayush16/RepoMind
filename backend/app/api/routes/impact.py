import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_workspace
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.models.repository import Repository
from app.models.workspace import Workspace
from app.schemas.impact import ImpactAnalysisOut
from app.services.graph.impact import analyse_change_impact

router = APIRouter(prefix="/repositories/{repository_id}/impact", tags=["impact"])


@router.get("", response_model=ImpactAnalysisOut)
async def change_impact(
    repository_id: uuid.UUID,
    symbol: str = Query(..., description="symbol name to analyse"),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ImpactAnalysisOut:
    repository = await db.get(Repository, repository_id)
    if repository is None or repository.workspace_id != workspace.id:
        raise NotFoundError("Repository not found.")

    result = await analyse_change_impact(settings, str(repository_id), symbol)
    return ImpactAnalysisOut(
        symbol_name=result.symbol_name,
        available=result.available,
        reason=result.reason,
        direct_callers=[{"name": c.get("name"), "file_path": c.get("file_path")} for c in result.direct_callers],
        dependent_files=[{"file_path": f} for f in result.dependent_files],
        risk=result.risk,
    )
