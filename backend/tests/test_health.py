import httpx
import pytest

from app.main import app

EXPECTED_DEPENDENCIES = {"postgres", "redis", "neo4j", "qdrant"}


@pytest.mark.asyncio
async def test_health_endpoint_reports_real_dependency_status() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] in {"ok", "degraded"}
    assert set(body["dependencies"].keys()) == EXPECTED_DEPENDENCIES
    for dependency_status in body["dependencies"].values():
        assert dependency_status == "ok" or dependency_status.startswith("unreachable:")
