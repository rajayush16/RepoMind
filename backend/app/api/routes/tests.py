import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_workspace
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.exceptions import NotFoundError, ServiceUnavailableError, ValidationError
from app.models.generated_test import GeneratedTest, TestExecution
from app.models.repository import Repository
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.test_generation import GenerateTestRequest, GeneratedTestOut, TestExecutionOut
from app.services.agents.test_generation import SymbolNotFoundError, generate_test_code
from app.services.llm.registry import NoProviderConfiguredError, get_llm_provider
from app.workers.tasks import execute_generated_test_task

router = APIRouter(tags=["tests"])

SUPPORTED_FRAMEWORKS = {"pytest", "jest"}


async def _get_owned_repository(db: AsyncSession, workspace: Workspace, repository_id: uuid.UUID) -> Repository:
    repository = await db.get(Repository, repository_id)
    if repository is None or repository.workspace_id != workspace.id:
        raise NotFoundError("Repository not found.")
    return repository


@router.post("/repositories/{repository_id}/tests", response_model=GeneratedTestOut, status_code=201)
async def generate_test(
    repository_id: uuid.UUID,
    body: GenerateTestRequest,
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> GeneratedTest:
    await _get_owned_repository(db, workspace, repository_id)

    if body.framework not in SUPPORTED_FRAMEWORKS:
        raise ValidationError(
            f"Unsupported framework {body.framework!r}. Supported: {sorted(SUPPORTED_FRAMEWORKS)}."
        )

    try:
        provider = get_llm_provider(settings)
    except NoProviderConfiguredError as exc:
        raise ValidationError(f"No LLM provider configured: {exc}")

    try:
        code = await generate_test_code(
            db, provider, repository_id, body.symbol_name, body.file_path, body.framework
        )
    except SymbolNotFoundError as exc:
        raise NotFoundError(str(exc))

    generated_test = GeneratedTest(
        repository_id=repository_id,
        user_id=user.id,
        symbol_name=body.symbol_name,
        file_path=body.file_path,
        framework=body.framework,
        code=code,
    )
    db.add(generated_test)
    await db.commit()
    await db.refresh(generated_test)
    return generated_test


@router.get("/repositories/{repository_id}/tests", response_model=list[GeneratedTestOut])
async def list_generated_tests(
    repository_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> list[GeneratedTest]:
    await _get_owned_repository(db, workspace, repository_id)

    result = await db.execute(
        select(GeneratedTest)
        .where(GeneratedTest.repository_id == repository_id)
        .order_by(GeneratedTest.created_at.desc())
    )
    return list(result.scalars().all())


async def _get_owned_generated_test(
    db: AsyncSession, workspace: Workspace, generated_test_id: uuid.UUID
) -> GeneratedTest:
    generated_test = await db.get(GeneratedTest, generated_test_id)
    if generated_test is None:
        raise NotFoundError("Generated test not found.")
    await _get_owned_repository(db, workspace, generated_test.repository_id)
    return generated_test


@router.post("/generated-tests/{generated_test_id}/execute", response_model=TestExecutionOut, status_code=202)
async def execute_test(
    generated_test_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> TestExecution:
    await _get_owned_generated_test(db, workspace, generated_test_id)

    execution = TestExecution(generated_test_id=generated_test_id, status="pending")
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    try:
        execute_generated_test_task.delay(str(execution.id))
    except Exception as exc:  # noqa: BLE001
        execution.status = "sandbox_unavailable"
        execution.output = f"Could not reach the background task broker: {exc}"
        await db.commit()
        raise ServiceUnavailableError(
            "The background task broker/worker is unavailable. Make sure Redis and a "
            "Celery worker are running."
        )

    return execution


@router.get("/generated-tests/{generated_test_id}/executions/latest", response_model=TestExecutionOut)
async def latest_execution(
    generated_test_id: uuid.UUID,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
) -> TestExecution:
    await _get_owned_generated_test(db, workspace, generated_test_id)

    result = await db.execute(
        select(TestExecution)
        .where(TestExecution.generated_test_id == generated_test_id)
        .order_by(TestExecution.created_at.desc())
        .limit(1)
    )
    execution = result.scalar_one_or_none()
    if execution is None:
        raise NotFoundError("This test has not been executed yet.")
    return execution
