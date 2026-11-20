import structlog
from neo4j import AsyncGraphDatabase

from app.core.config import Settings

logger = structlog.get_logger(__name__)
CONNECTION_TIMEOUT_SECONDS = 3.0


class GraphUnavailableError(Exception):
    pass


def _driver(settings: Settings):
    return AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
        connection_timeout=CONNECTION_TIMEOUT_SECONDS,
    )


async def find_symbols_by_name(settings: Settings, repository_id: str, query: str, limit: int = 10) -> list[dict]:
    driver = _driver(settings)
    try:
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (f:File {repository_id: $repo_id})-[:DEFINES]->(s:Symbol)
                WHERE toLower(s.name) CONTAINS toLower($query)
                RETURN s.name AS name, s.type AS type, s.start_line AS start_line,
                       s.end_line AS end_line, f.path AS file_path
                LIMIT $limit
                """,
                repo_id=repository_id,
                query=query,
                limit=limit,
            )
            return [record.data() async for record in result]
    finally:
        await driver.close()


async def get_repository_graph(settings: Settings, repository_id: str, limit: int = 500) -> dict:
    """Nodes + edges for the architecture graph view.

    Returns {"available": False, "reason": ...} rather than raising when Neo4j is
    unreachable, so callers can render an honest empty state instead of crashing.
    """
    try:
        driver = _driver(settings)
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": str(exc), "nodes": [], "edges": []}

    try:
        async with driver.session() as session:
            files_result = await session.run(
                "MATCH (f:File {repository_id: $repo_id}) RETURN f.path AS path, f.language AS language LIMIT $limit",
                repo_id=repository_id,
                limit=limit,
            )
            files = [record.data() async for record in files_result]

            symbols_result = await session.run(
                """
                MATCH (f:File {repository_id: $repo_id})-[:DEFINES]->(s:Symbol)
                RETURN s.name AS name, s.type AS type, f.path AS file_path
                LIMIT $limit
                """,
                repo_id=repository_id,
                limit=limit,
            )
            symbols = [record.data() async for record in symbols_result]

            calls_result = await session.run(
                """
                MATCH (caller:Symbol {repository_id: $repo_id})-[:CALLS]->(callee:Symbol)
                OPTIONAL MATCH (cf:File {repository_id: $repo_id})-[:DEFINES]->(caller)
                OPTIONAL MATCH (ef:File {repository_id: $repo_id})-[:DEFINES]->(callee)
                RETURN caller.name AS caller, cf.path AS caller_file,
                       callee.name AS callee, ef.path AS callee_file
                LIMIT $limit
                """,
                repo_id=repository_id,
                limit=limit,
            )
            calls = [record.data() async for record in calls_result]

            imports_result = await session.run(
                """
                MATCH (f:File {repository_id: $repo_id})-[:IMPORTS]->(m:Module)
                RETURN f.path AS file_path, m.name AS module
                LIMIT $limit
                """,
                repo_id=repository_id,
                limit=limit,
            )
            imports = [record.data() async for record in imports_result]

        nodes = [{"id": f"file:{f['path']}", "type": "file", "label": f["path"], "language": f.get("language")} for f in files]
        nodes += [
            {"id": f"symbol:{s['file_path']}:{s['name']}", "type": "symbol", "label": s["name"], "symbolType": s["type"], "file": s["file_path"]}
            for s in symbols
        ]
        nodes += [{"id": f"module:{imp['module']}", "type": "module", "label": imp["module"]} for imp in imports]

        edges = [
            {"source": f"file:{s['file_path']}", "target": f"symbol:{s['file_path']}:{s['name']}", "type": "DEFINES"}
            for s in symbols
        ]
        edges += [
            {"source": f"file:{imp['file_path']}", "target": f"module:{imp['module']}", "type": "IMPORTS"}
            for imp in imports
        ]
        # Only emit a CALLS edge when both ends resolved to a symbol node actually
        # present above (an unresolved callee has no defining File, so no node
        # exists for it) -- an edge to a non-existent node would just be dropped
        # by the frontend anyway, so skip it here instead.
        edges += [
            {
                "source": f"symbol:{c['caller_file']}:{c['caller']}",
                "target": f"symbol:{c['callee_file']}:{c['callee']}",
                "type": "CALLS",
            }
            for c in calls
            if c.get("caller_file") and c.get("callee_file")
        ]

        return {"available": True, "reason": None, "nodes": nodes, "edges": edges}
    except Exception as exc:  # noqa: BLE001
        logger.info("graph_query_failed", error=str(exc))
        return {"available": False, "reason": str(exc), "nodes": [], "edges": []}
    finally:
        await driver.close()


async def get_callers(settings: Settings, repository_id: str, symbol_name: str, limit: int = 50) -> list[dict]:
    """Direct callers of a symbol, by name (best-effort, not fully semantic)."""
    driver = _driver(settings)
    try:
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (caller:Symbol {repository_id: $repo_id})-[:CALLS]->(callee:Symbol {repository_id: $repo_id, name: $name})
                OPTIONAL MATCH (f:File {repository_id: $repo_id})-[:DEFINES]->(caller)
                RETURN caller.name AS name, f.path AS file_path
                LIMIT $limit
                """,
                repo_id=repository_id,
                name=symbol_name,
                limit=limit,
            )
            return [record.data() async for record in result]
    finally:
        await driver.close()


async def get_dependents(settings: Settings, repository_id: str, module_name: str, limit: int = 50) -> list[dict]:
    """Files that import a given module -- used for change-impact analysis."""
    driver = _driver(settings)
    try:
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (f:File {repository_id: $repo_id})-[:IMPORTS]->(m:Module {repository_id: $repo_id, name: $module})
                RETURN f.path AS file_path
                LIMIT $limit
                """,
                repo_id=repository_id,
                module=module_name,
                limit=limit,
            )
            return [record.data() async for record in result]
    finally:
        await driver.close()
