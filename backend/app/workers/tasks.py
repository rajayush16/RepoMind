import asyncio
import uuid

from app.services.indexing.pipeline import run_indexing
from app.workers.celery_app import celery_app


@celery_app.task(name="index_repository", bind=True, max_retries=0)
def index_repository_task(self, repository_id: str) -> None:
    asyncio.run(run_indexing(uuid.UUID(repository_id)))
