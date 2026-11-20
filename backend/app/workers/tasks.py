import asyncio
import uuid

from app.core.config import get_settings
from app.services.agents.bug_investigation import run_investigation
from app.services.agents.pr_review import run_pr_review
from app.services.agents.test_execution import execute_generated_test
from app.services.indexing.pipeline import run_indexing
from app.services.llm.registry import get_llm_provider
from app.workers.celery_app import celery_app


@celery_app.task(name="index_repository", bind=True, max_retries=0)
def index_repository_task(self, repository_id: str) -> None:
    asyncio.run(run_indexing(uuid.UUID(repository_id)))


@celery_app.task(name="investigate_bug", bind=True, max_retries=0)
def investigate_bug_task(self, investigation_id: str) -> None:
    from app.core.database import AsyncSessionLocal

    settings = get_settings()
    provider = get_llm_provider(settings)
    asyncio.run(
        run_investigation(uuid.UUID(investigation_id), AsyncSessionLocal, settings, provider)
    )


@celery_app.task(name="review_pull_request", bind=True, max_retries=0)
def review_pull_request_task(self, review_id: str) -> None:
    from app.core.database import AsyncSessionLocal

    settings = get_settings()
    provider = get_llm_provider(settings)
    asyncio.run(run_pr_review(uuid.UUID(review_id), AsyncSessionLocal, settings, provider))


@celery_app.task(name="execute_generated_test", bind=True, max_retries=0)
def execute_generated_test_task(self, execution_id: str) -> None:
    from app.core.database import AsyncSessionLocal

    asyncio.run(execute_generated_test(uuid.UUID(execution_id), AsyncSessionLocal))
