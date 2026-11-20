from fastapi import APIRouter, Depends

from app.api.deps import get_current_workspace
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceOut

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("/current", response_model=WorkspaceOut)
async def current_workspace(workspace: Workspace = Depends(get_current_workspace)) -> Workspace:
    return workspace
