from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.services.health import check_dependencies

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(settings: Settings = Depends(get_settings)) -> dict:
    dependencies = await check_dependencies(settings)
    overall = "ok" if all(status == "ok" for status in dependencies.values()) else "degraded"
    return {
        "status": overall,
        "environment": settings.environment,
        "dependencies": dependencies,
    }
