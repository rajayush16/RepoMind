import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_user_by_github_id(db: AsyncSession, github_id: str) -> User | None:
    result = await db.execute(select(User).where(User.github_id == github_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    password: str | None = None,
    name: str | None = None,
) -> User:
    user = User(
        email=email.lower(),
        name=name,
        hashed_password=hash_password(password) if password else None,
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if user is None or user.hashed_password is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
