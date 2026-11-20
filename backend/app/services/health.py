"""Real connectivity checks against each infrastructure dependency.

Every check attempts an actual connection with a short timeout and reports
"ok" or "unreachable: <reason>" — never a hardcoded status.
"""

import asyncio

from app.core.config import Settings

CHECK_TIMEOUT_SECONDS = 2.0


def _format_unreachable(exc: Exception) -> str:
    message = str(exc) or exc.__class__.__name__
    return f"unreachable: {message}"


async def _check_postgres(settings: Settings) -> str:
    try:
        import asyncpg

        conn = await asyncio.wait_for(
            asyncpg.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                database=settings.postgres_db,
                user=settings.postgres_user,
                password=settings.postgres_password,
                timeout=CHECK_TIMEOUT_SECONDS,
            ),
            timeout=CHECK_TIMEOUT_SECONDS,
        )
        await conn.close()
        return "ok"
    except Exception as exc:  # noqa: BLE001 - surfaced to caller as status text
        return _format_unreachable(exc)


async def _check_redis(settings: Settings) -> str:
    try:
        from redis.asyncio import from_url

        client = from_url(settings.redis_url, socket_connect_timeout=CHECK_TIMEOUT_SECONDS)
        try:
            await asyncio.wait_for(client.ping(), timeout=CHECK_TIMEOUT_SECONDS)
            return "ok"
        finally:
            await client.aclose()
    except Exception as exc:  # noqa: BLE001
        return _format_unreachable(exc)


async def _check_neo4j(settings: Settings) -> str:
    try:
        from neo4j import AsyncGraphDatabase

        driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            connection_timeout=CHECK_TIMEOUT_SECONDS,
        )
        try:
            await asyncio.wait_for(driver.verify_connectivity(), timeout=CHECK_TIMEOUT_SECONDS)
            return "ok"
        finally:
            await driver.close()
    except Exception as exc:  # noqa: BLE001
        return _format_unreachable(exc)


async def _check_qdrant(settings: Settings) -> str:
    try:
        import httpx

        async with httpx.AsyncClient(timeout=CHECK_TIMEOUT_SECONDS) as client:
            response = await client.get(f"{settings.qdrant_url}/healthz")
            if response.status_code == 200:
                return "ok"
            return f"unreachable: HTTP {response.status_code}"
    except Exception as exc:  # noqa: BLE001
        return _format_unreachable(exc)


async def check_dependencies(settings: Settings) -> dict[str, str]:
    postgres, redis, neo4j, qdrant = await asyncio.gather(
        _check_postgres(settings),
        _check_redis(settings),
        _check_neo4j(settings),
        _check_qdrant(settings),
    )
    return {
        "postgres": postgres,
        "redis": redis,
        "neo4j": neo4j,
        "qdrant": qdrant,
    }
