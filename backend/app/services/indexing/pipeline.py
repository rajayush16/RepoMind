import hashlib
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.database import AsyncSessionLocal
from app.core.security import decrypt_secret
from app.models.indexing import CodeSymbol, IndexedFile, IndexingJob, IndexingJobStatus
from app.models.repository import Repository
from app.models.user import User
from app.services.graph.builder import write_graph
from app.services.indexing.clone import CloneError, clone_repository
from app.services.indexing.filters import list_indexable_files
from app.services.llm.embeddings import get_embedding_provider
from app.services.parsing.extractor import parse_source
from app.services.parsing.types import ParsedFile
from app.services.retrieval.qdrant_store import write_embeddings

logger = structlog.get_logger(__name__)


def stable_symbol_id(relative_path: str, name: str, start_line: int) -> str:
    raw = f"{relative_path}:{name}:{start_line}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class RepositoryNotFoundError(Exception):
    pass


async def run_indexing(
    repository_id: uuid.UUID,
    *,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    settings: Settings | None = None,
) -> None:
    """Clone, parse, and persist a full index of a repository.

    Always performs a full re-index (delete-then-reinsert) rather than true
    commit-diff incremental indexing -- the spec explicitly allows this as a
    fallback, and it's the only idempotent option implemented so far (see
    IMPLEMENTATION_PLAN.md). Graph (Neo4j) and embedding (Qdrant) writes are
    best-effort: neither being unreachable, nor no embedding provider being
    configured, fails the job -- only the Postgres-backed symbol index must
    succeed for the job to be marked successful.

    `session_factory`/`settings` default to the real production ones (used by the
    Celery task, which runs outside FastAPI's request-scoped DI); tests inject a
    SQLite-backed session factory and test settings instead.
    """
    settings = settings or get_settings()
    session_factory = session_factory or AsyncSessionLocal

    async with session_factory() as db:
        repository = await db.get(Repository, repository_id)
        if repository is None:
            raise RepositoryNotFoundError(str(repository_id))

        job = IndexingJob(
            repository_id=repository_id,
            status=IndexingJobStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        db.add(job)
        repository.indexing_status = "indexing"
        await db.commit()
        await db.refresh(job)

        access_token: str | None = None
        if repository.connected_by_user_id:
            user = await db.get(User, repository.connected_by_user_id)
            if user and user.github_access_token_encrypted:
                access_token = decrypt_secret(user.github_access_token_encrypted, settings)

        clone_url = f"https://github.com/{repository.full_name}.git"

        try:
            with clone_repository(clone_url, repository.selected_branch, access_token) as (
                workdir,
                commit_sha,
            ):
                indexable_files = list_indexable_files(workdir)
                job.commit_sha = commit_sha
                job.files_discovered = len(indexable_files)
                await db.commit()

                await db.execute(delete(CodeSymbol).where(CodeSymbol.repository_id == repository_id))
                await db.execute(delete(IndexedFile).where(IndexedFile.repository_id == repository_id))
                await db.commit()

                parsed_files: list[tuple[str, str, ParsedFile]] = []
                total_symbols = 0

                for indexable in indexable_files:
                    full_path = workdir / indexable.relative_path
                    try:
                        content = full_path.read_text(encoding="utf-8", errors="replace")
                    except OSError as exc:
                        logger.warning("skip_unreadable_file", path=indexable.relative_path, error=str(exc))
                        continue

                    parsed = parse_source(content, indexable.language)

                    indexed_file = IndexedFile(
                        repository_id=repository_id,
                        relative_path=indexable.relative_path,
                        language=indexable.language,
                        size_bytes=len(content.encode("utf-8")),
                        content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                        content=content,
                        symbol_count=len(parsed.symbols),
                        last_indexed_commit_sha=commit_sha,
                    )
                    db.add(indexed_file)
                    await db.flush()

                    for symbol in parsed.symbols:
                        db.add(
                            CodeSymbol(
                                repository_id=repository_id,
                                indexed_file_id=indexed_file.id,
                                stable_symbol_id=stable_symbol_id(
                                    indexable.relative_path, symbol.name, symbol.start_line
                                ),
                                name=symbol.name,
                                symbol_type=symbol.symbol_type,
                                parent_name=symbol.parent,
                                start_line=symbol.start_line,
                                end_line=symbol.end_line,
                                signature=symbol.signature,
                            )
                        )

                    total_symbols += len(parsed.symbols)
                    parsed_files.append((indexable.relative_path, indexable.language, parsed))
                    job.files_processed += 1

                job.symbols_extracted = total_symbols
                await db.commit()

                graph_result = await write_graph(settings, str(repository_id), parsed_files)
                job.graph_relationships_written = graph_result.relationships_written
                if graph_result.skipped_reason:
                    logger.info("graph_write_skipped", reason=graph_result.skipped_reason)

                embedding_provider = get_embedding_provider(settings)
                if embedding_provider is not None:
                    embedding_result = await write_embeddings(
                        settings, embedding_provider, str(repository_id), parsed_files
                    )
                    job.embeddings_generated = embedding_result.embeddings_written
                    if embedding_result.skipped_reason:
                        logger.info("embedding_write_skipped", reason=embedding_result.skipped_reason)
                else:
                    logger.info("embedding_write_skipped", reason="no embedding provider configured")

                repository.file_count = len(indexable_files)
                repository.symbol_count = total_symbols
                repository.indexing_status = "indexed"

                job.status = IndexingJobStatus.SUCCESS
                job.finished_at = datetime.now(timezone.utc)
                await db.commit()

        except CloneError as exc:
            job.status = IndexingJobStatus.FAILED
            job.error_message = str(exc)
            job.finished_at = datetime.now(timezone.utc)
            repository.indexing_status = "failed"
            await db.commit()
        except Exception as exc:  # noqa: BLE001
            job.status = IndexingJobStatus.FAILED
            job.error_message = f"{type(exc).__name__}: {exc}"
            job.finished_at = datetime.now(timezone.utc)
            repository.indexing_status = "failed"
            await db.commit()
            raise
