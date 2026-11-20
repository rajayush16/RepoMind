import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_current_workspace
from app.core.database import get_db
from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.models.investigation import Investigation
from app.models.repository import Repository
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.investigation import InvestigationOut, StartInvestigationRequest
from app.workers.tasks import investigate_bug_task

router = APIRouter(tags=["investigations"])


async def _get_owned_repository(db: AsyncSession, workspace: Workspace, repository_id: uuid.UUID) -> Repository:
    repository = await db.get(Repository, repository_id)
    if repository is None or repository.workspace_id != workspace.id:
        raise NotFoundError("Repository not found.")
    return repository


@router.post(
    "/repositories/{repository_id}/investigations", response_model=InvestigationOut, status_code=202
)
async def start_investigation(
    repository_id: uuid.UUID,
    body: StartInvestigationRequest,
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> InvestigationOut:
    await _get_owned_repository(db, workspace, repository_id)

    investigation = Investigation(
        repository_id=repository_id,
        user_id=user.id,
        bug_description=body.bug_description,
        error_message=body.error_message,
        stack_trace=body.stack_trace,
    )
    db.add(investigation)
    await db.commit()
    await db.refresh(investigation)

    try:
        investigate_bug_task.delay(str(investigation.id))
    except Exception as exc:  # noqa: BLE001
        investigation.status = "failed"
        investigation.error_detail = f"Could not reach the background task broker: {exc}"
        await db.commit()
        raise ServiceUnavailableError(
            "The background task broker/worker is unavailable, or no LLM provider is "
            "configured. Make sure Redis, a Celery worker, and an LLM API key are set up."
        )

    # Built from plain column attributes, not `InvestigationOut.model_validate(
    # investigation, from_attributes=True)`: that would read `.steps` off the ORM
    # object, and this `investigation` was never loaded with that relationship.
    # Touching an unloaded relationship attribute -- even just to assign `[]` to
    # it, which first loads the *current* collection to diff against -- is itself
    # a lazy load, outside the async-aware context that requires, so it raises
    # MissingGreenlet. A fresh investigation always has zero steps anyway.
    return InvestigationOut(
        id=investigation.id,
        repository_id=investigation.repository_id,
        bug_description=investigation.bug_description,
        error_message=investigation.error_message,
        stack_trace=investigation.stack_trace,
        status=investigation.status,
        root_cause=investigation.root_cause,
        confidence_explanation=investigation.confidence_explanation,
        suggested_fix=investigation.suggested_fix,
        potential_side_effects=investigation.potential_side_effects,
        error_detail=investigation.error_detail,
        created_at=investigation.created_at,
        steps=[],
    )


@router.get("/repositories/{repository_id}/investigations", response_model=list[InvestigationOut])
async def list_investigations(
    repository_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[Investigation]:
    await _get_owned_repository(db, workspace, repository_id)

    result = await db.execute(
        select(Investigation)
        .where(Investigation.repository_id == repository_id)
        .options(selectinload(Investigation.steps))
        .order_by(Investigation.created_at.desc())
    )
    return list(result.scalars().unique().all())


@router.get("/investigations/{investigation_id}", response_model=InvestigationOut)
async def get_investigation(
    investigation_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> Investigation:
    result = await db.execute(
        select(Investigation)
        .where(Investigation.id == investigation_id)
        .options(selectinload(Investigation.steps))
    )
    investigation = result.scalar_one_or_none()
    if investigation is None:
        raise NotFoundError("Investigation not found.")
    await _get_owned_repository(db, workspace, investigation.repository_id)
    return investigation
