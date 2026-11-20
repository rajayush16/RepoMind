import uuid
from datetime import datetime

from pydantic import BaseModel


class IndexingJobOut(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    status: str
    commit_sha: str | None
    files_discovered: int
    files_processed: int
    symbols_extracted: int
    graph_relationships_written: int
    embeddings_generated: int
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
