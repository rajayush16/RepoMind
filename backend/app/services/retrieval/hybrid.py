import uuid
from dataclasses import dataclass, field

import structlog
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.indexing import CodeSymbol, IndexedFile
from app.services.graph.queries import find_symbols_by_name
from app.services.llm.embeddings import get_embedding_provider
from app.services.retrieval.qdrant_store import search_similar

logger = structlog.get_logger(__name__)

LEXICAL_LIMIT = 20
SYMBOL_LIMIT = 20
VECTOR_LIMIT = 20
GRAPH_LIMIT = 10
RRF_K = 60


@dataclass
class RetrievalResult:
    file_path: str
    symbol_name: str | None
    symbol_type: str | None
    start_line: int | None
    end_line: int | None
    snippet: str
    sources: list[str] = field(default_factory=list)
    score: float = 0.0


async def _lexical_search(db: AsyncSession, repository_id: uuid.UUID, query: str) -> list[RetrievalResult]:
    """Substring search over symbol names/signatures and file paths.

    Deliberately portable (plain LIKE) rather than Postgres-only `tsvector`/BM25
    ranking, so the same code path runs against the SQLite test harness and real
    Postgres. Documented as a fidelity trade-off in IMPLEMENTATION_PLAN.md.
    """
    like_query = f"%{query}%"
    result = await db.execute(
        select(CodeSymbol, IndexedFile.relative_path)
        .join(IndexedFile, CodeSymbol.indexed_file_id == IndexedFile.id)
        .where(
            CodeSymbol.repository_id == repository_id,
            or_(CodeSymbol.name.ilike(like_query), CodeSymbol.signature.ilike(like_query)),
        )
        .limit(LEXICAL_LIMIT)
    )
    return [
        RetrievalResult(
            file_path=path,
            symbol_name=symbol.name,
            symbol_type=symbol.symbol_type,
            start_line=symbol.start_line,
            end_line=symbol.end_line,
            snippet=symbol.signature,
            sources=["lexical"],
        )
        for symbol, path in result.all()
    ]


async def _symbol_search(db: AsyncSession, repository_id: uuid.UUID, query: str) -> list[RetrievalResult]:
    """Exact/prefix symbol-name search -- a narrower, higher-precision sibling of lexical search."""
    result = await db.execute(
        select(CodeSymbol, IndexedFile.relative_path)
        .join(IndexedFile, CodeSymbol.indexed_file_id == IndexedFile.id)
        .where(CodeSymbol.repository_id == repository_id, CodeSymbol.name.ilike(f"{query}%"))
        .limit(SYMBOL_LIMIT)
    )
    return [
        RetrievalResult(
            file_path=path,
            symbol_name=symbol.name,
            symbol_type=symbol.symbol_type,
            start_line=symbol.start_line,
            end_line=symbol.end_line,
            snippet=symbol.signature,
            sources=["symbol"],
        )
        for symbol, path in result.all()
    ]


async def _vector_search(
    settings: Settings, repository_id: uuid.UUID, query: str
) -> list[RetrievalResult]:
    provider = get_embedding_provider(settings)
    if provider is None:
        return []

    try:
        hits = await search_similar(settings, provider, str(repository_id), query, limit=VECTOR_LIMIT)
    except Exception as exc:  # noqa: BLE001
        logger.info("vector_search_skipped", reason=str(exc))
        return []

    return [
        RetrievalResult(
            file_path=hit["file_path"],
            symbol_name=hit.get("symbol_name"),
            symbol_type=hit.get("symbol_type"),
            start_line=hit.get("start_line"),
            end_line=hit.get("end_line"),
            snippet=hit.get("symbol_name", ""),
            sources=["vector"],
        )
        for hit in hits
    ]


async def _graph_search(
    settings: Settings, repository_id: uuid.UUID, query: str
) -> list[RetrievalResult]:
    try:
        matches = await find_symbols_by_name(settings, str(repository_id), query, limit=GRAPH_LIMIT)
    except Exception as exc:  # noqa: BLE001
        logger.info("graph_search_skipped", reason=str(exc))
        return []

    return [
        RetrievalResult(
            file_path=match.get("file_path", ""),
            symbol_name=match.get("name"),
            symbol_type=match.get("type"),
            start_line=match.get("start_line"),
            end_line=match.get("end_line"),
            snippet=match.get("name", ""),
            sources=["graph"],
        )
        for match in matches
    ]


def _result_key(result: RetrievalResult) -> tuple[str, str | None, int | None]:
    return (result.file_path, result.symbol_name, result.start_line)


def _reciprocal_rank_fusion(ranked_lists: list[list[RetrievalResult]]) -> list[RetrievalResult]:
    """Combine multiple ranked result lists into one, per Reciprocal Rank Fusion:
    score(d) = sum(1 / (k + rank)) across every list d appears in.
    """
    merged: dict[tuple, RetrievalResult] = {}

    for results in ranked_lists:
        for rank, result in enumerate(results, start=1):
            key = _result_key(result)
            contribution = 1.0 / (RRF_K + rank)
            if key in merged:
                merged[key].score += contribution
                merged[key].sources = list(set(merged[key].sources + result.sources))
            else:
                result.score = contribution
                merged[key] = result

    return sorted(merged.values(), key=lambda r: r.score, reverse=True)


async def hybrid_search(
    db: AsyncSession, settings: Settings, repository_id: uuid.UUID, query: str, limit: int = 20
) -> list[RetrievalResult]:
    """Fuse lexical, symbol, vector, and graph retrieval via Reciprocal Rank Fusion.

    Vector and graph retrieval are best-effort (empty list, not an error, if Qdrant/
    Neo4j/an embedding provider aren't available) -- this always returns whatever
    the Postgres-backed lexical/symbol search can find, at minimum.
    """
    lexical, symbol, vector, graph = (
        await _lexical_search(db, repository_id, query),
        await _symbol_search(db, repository_id, query),
        await _vector_search(settings, repository_id, query),
        await _graph_search(settings, repository_id, query),
    )

    fused = _reciprocal_rank_fusion([symbol, lexical, vector, graph])
    return fused[:limit]
