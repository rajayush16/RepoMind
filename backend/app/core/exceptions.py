from fastapi import Request, status
from fastapi.responses import JSONResponse


class RepoMindError(Exception):
    """Base class for all application-raised errors."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "An unexpected error occurred."

    def __init__(self, detail: str | None = None) -> None:
        if detail:
            self.detail = detail
        super().__init__(self.detail)


class NotFoundError(RepoMindError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found."


class UnauthorizedError(RepoMindError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication required."


class ForbiddenError(RepoMindError):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "You do not have access to this resource."


class ValidationError(RepoMindError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Invalid request."


async def repomind_exception_handler(request: Request, exc: RepoMindError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
