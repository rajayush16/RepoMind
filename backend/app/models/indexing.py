import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, TimestampMixin


class IndexingJobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class IndexingJob(Base, TimestampMixin):
    __tablename__ = "indexing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[IndexingJobStatus] = mapped_column(
        Enum(IndexingJobStatus, name="indexing_job_status"),
        default=IndexingJobStatus.QUEUED,
        nullable=False,
    )
    commit_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)
    files_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    files_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    symbols_extracted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    graph_relationships_written: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    embeddings_generated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IndexedFile(Base, TimestampMixin):
    __tablename__ = "indexed_files"
    __table_args__ = (
        UniqueConstraint("repository_id", "relative_path", name="uq_repo_file_path"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relative_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    language: Mapped[str] = mapped_column(String(32), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_indexed_commit_sha: Mapped[str] = mapped_column(String(40), nullable=False)


class CodeSymbol(Base, TimestampMixin):
    __tablename__ = "code_symbols"
    __table_args__ = (
        UniqueConstraint("repository_id", "stable_symbol_id", name="uq_repo_stable_symbol"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    indexed_file_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("indexed_files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Deterministic id (hash of relative_path:name:start_line), stable across
    # re-indexes of the same commit so re-indexing never creates duplicate rows.
    stable_symbol_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    symbol_type: Mapped[str] = mapped_column(String(32), nullable=False)
    parent_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    signature: Mapped[str] = mapped_column(String(512), nullable=False)
