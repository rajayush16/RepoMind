import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, TimestampMixin


class Repository(Base, TimestampMixin):
    __tablename__ = "repositories"
    __table_args__ = (
        UniqueConstraint("workspace_id", "github_repo_id", name="uq_workspace_github_repo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    connected_by_user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    github_repo_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    default_branch: Mapped[str] = mapped_column(String(255), default="main", nullable=False)
    selected_branch: Mapped[str] = mapped_column(String(255), default="main", nullable=False)
    primary_language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Populated once the indexing pipeline (Phase 4) exists. Until then these stay at
    # their defaults -- never fabricated to make the UI look populated.
    indexing_status: Mapped[str] = mapped_column(String(32), default="not_indexed", nullable=False)
    file_count: Mapped[int] = mapped_column(default=0, nullable=False)
    symbol_count: Mapped[int] = mapped_column(default=0, nullable=False)
