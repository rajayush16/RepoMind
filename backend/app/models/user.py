import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    github_id: Mapped[str | None] = mapped_column(
        String(64), unique=True, index=True, nullable=True
    )
    github_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # Fernet-encrypted GitHub OAuth access token; never exposed via any API response.
    github_access_token_encrypted: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
