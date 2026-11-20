import uuid
from dataclasses import dataclass

import structlog
from qdrant_client import AsyncQdrantClient, models

from app.core.config import Settings
from app.services.llm.embeddings import EmbeddingProvider
from app.services.parsing.types import ParsedFile

logger = structlog.get_logger(__name__)

COLLECTION_NAME = "code_symbols"
EMBEDDING_BATCH_SIZE = 64


@dataclass
class EmbeddingWriteResult:
    embeddings_written: int
    skipped_reason: str | None = None


def _chunk_text(relative_path: str, language: str, signature: str, name: str) -> str:
    return f"{relative_path} ({language})\n{signature}"


async def write_embeddings(
    settings: Settings,
    provider: EmbeddingProvider,
    repository_id: str,
    parsed_files: list[tuple[str, str, ParsedFile]],
) -> EmbeddingWriteResult:
    """Embed each extracted symbol's signature and upsert it into Qdrant.

    Best-effort, like the Neo4j graph write: Qdrant being unreachable, or the
    embedding API failing, is reported as a skip reason rather than failing the
    whole indexing job -- the Postgres-backed symbol index is the part that must
    succeed.
    """
    chunks: list[tuple[str, str]] = []  # (text, payload key info packed below)
    payloads: list[dict] = []

    for relative_path, language, parsed in parsed_files:
        for symbol in parsed.symbols:
            text = _chunk_text(relative_path, language, symbol.signature, symbol.name)
            chunks.append(text)
            payloads.append(
                {
                    "repository_id": repository_id,
                    "file_path": relative_path,
                    "language": language,
                    "symbol_name": symbol.name,
                    "symbol_type": symbol.symbol_type,
                    "start_line": symbol.start_line,
                    "end_line": symbol.end_line,
                }
            )

    if not chunks:
        return EmbeddingWriteResult(embeddings_written=0)

    try:
        client = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key, timeout=10)

        if not await client.collection_exists(COLLECTION_NAME):
            await client.create_collection(
                COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=provider.dimensions, distance=models.Distance.COSINE
                ),
            )

        await client.delete(
            COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="repository_id", match=models.MatchValue(value=repository_id)
                        )
                    ]
                )
            ),
        )

        written = 0
        for start in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
            batch_texts = chunks[start : start + EMBEDDING_BATCH_SIZE]
            batch_payloads = payloads[start : start + EMBEDDING_BATCH_SIZE]
            vectors = await provider.embed(batch_texts)

            points = [
                models.PointStruct(id=str(uuid.uuid4()), vector=vector, payload=payload)
                for vector, payload in zip(vectors, batch_payloads)
            ]
            await client.upsert(COLLECTION_NAME, points=points)
            written += len(points)

        return EmbeddingWriteResult(embeddings_written=written)
    except Exception as exc:  # noqa: BLE001
        logger.warning("embedding_write_failed", error=str(exc))
        return EmbeddingWriteResult(embeddings_written=0, skipped_reason=str(exc))


async def search_similar(
    settings: Settings,
    provider: EmbeddingProvider,
    repository_id: str,
    query: str,
    limit: int = 20,
) -> list[dict]:
    """Semantic search over a repository's indexed symbols. Raises on failure --
    callers (hybrid_search) are expected to catch and treat this as best-effort."""
    client = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key, timeout=10)

    if not await client.collection_exists(COLLECTION_NAME):
        return []

    [query_vector] = await provider.embed([query])

    hits = await client.query_points(
        COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        query_filter=models.Filter(
            must=[models.FieldCondition(key="repository_id", match=models.MatchValue(value=repository_id))]
        ),
    )
    return [hit.payload for hit in hits.points]
