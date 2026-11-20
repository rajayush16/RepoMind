from dataclasses import dataclass

import structlog
from neo4j import AsyncGraphDatabase

from app.core.config import Settings
from app.services.parsing.types import ParsedFile

logger = structlog.get_logger(__name__)

CONNECTION_TIMEOUT_SECONDS = 3.0


@dataclass
class GraphWriteResult:
    relationships_written: int
    skipped_reason: str | None = None


async def write_graph(
    settings: Settings,
    repository_id: str,
    parsed_files: list[tuple[str, str, ParsedFile]],
) -> GraphWriteResult:
    """Write File/Symbol nodes and DEFINES/IMPORTS/CALLS edges to Neo4j.

    Best-effort: any failure (most commonly Neo4j being unreachable) is caught and
    reported as a skip reason rather than failing the whole indexing job, since the
    Postgres-backed symbol index is the part of this pipeline that must succeed.
    Calls are resolved by name within the repository only (syntactic, not a full
    semantic call graph) -- documented as a known fidelity limit.
    """
    try:
        driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            connection_timeout=CONNECTION_TIMEOUT_SECONDS,
        )
    except Exception as exc:  # noqa: BLE001
        return GraphWriteResult(relationships_written=0, skipped_reason=str(exc))

    relationships_written = 0

    try:
        async with driver.session() as session:
            # Reset this repository's subgraph so re-indexing doesn't accumulate
            # stale nodes from deleted/renamed symbols.
            await session.run(
                "MATCH (n {repository_id: $repo_id}) DETACH DELETE n", repo_id=repository_id
            )

            for relative_path, language, parsed in parsed_files:
                await session.run(
                    """
                    MERGE (f:File {repository_id: $repo_id, path: $path})
                    SET f.language = $language
                    """,
                    repo_id=repository_id,
                    path=relative_path,
                    language=language,
                )
                relationships_written += 1

                for symbol in parsed.symbols:
                    stable_id = f"{relative_path}:{symbol.name}:{symbol.start_line}"
                    await session.run(
                        """
                        MERGE (s:Symbol {repository_id: $repo_id, stable_id: $stable_id})
                        SET s.name = $name, s.type = $type,
                            s.start_line = $start_line, s.end_line = $end_line,
                            s.parent = $parent
                        WITH s
                        MATCH (f:File {repository_id: $repo_id, path: $path})
                        MERGE (f)-[:DEFINES]->(s)
                        """,
                        repo_id=repository_id,
                        stable_id=stable_id,
                        name=symbol.name,
                        type=symbol.symbol_type,
                        start_line=symbol.start_line,
                        end_line=symbol.end_line,
                        parent=symbol.parent,
                        path=relative_path,
                    )
                    relationships_written += 1

                for imp in parsed.imports:
                    await session.run(
                        """
                        MERGE (m:Module {repository_id: $repo_id, name: $module})
                        WITH m
                        MATCH (f:File {repository_id: $repo_id, path: $path})
                        MERGE (f)-[:IMPORTS]->(m)
                        """,
                        repo_id=repository_id,
                        module=imp.module,
                        path=relative_path,
                    )
                    relationships_written += 1

                for call in parsed.calls:
                    if call.caller_symbol is None:
                        continue
                    await session.run(
                        """
                        MATCH (caller:Symbol {repository_id: $repo_id, name: $caller_name})
                        MERGE (callee:Symbol {repository_id: $repo_id, name: $callee_name})
                        ON CREATE SET callee.unresolved = true
                        MERGE (caller)-[:CALLS]->(callee)
                        """,
                        repo_id=repository_id,
                        caller_name=call.caller_symbol,
                        callee_name=call.callee_name,
                    )
                    relationships_written += 1

        return GraphWriteResult(relationships_written=relationships_written)
    except Exception as exc:  # noqa: BLE001
        logger.warning("graph_write_failed", error=str(exc))
        return GraphWriteResult(relationships_written=relationships_written, skipped_reason=str(exc))
    finally:
        await driver.close()
