from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """For code that outlives the request (e.g. a StreamingResponse generator),
    which must not depend on a `Depends(get_db)` session: FastAPI closes that
    session right after the route function *returns*, which happens before a
    streaming body is actually consumed -- using it inside the generator would
    mean writing to an already-closed session."""
    return AsyncSessionLocal
