from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import architecture, auth, code, health, repositories, search, workspaces
from app.core.config import get_settings
from app.core.exceptions import RepoMindError, repomind_exception_handler
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.environment)

    app = FastAPI(
        title="RepoMind API",
        description="AI-powered codebase intelligence platform.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(RepoMindError, repomind_exception_handler)

    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(repositories.router, prefix="/api")
    app.include_router(workspaces.router, prefix="/api")
    app.include_router(code.router, prefix="/api")
    app.include_router(search.router, prefix="/api")
    app.include_router(architecture.router, prefix="/api")

    return app


app = create_app()
