import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, TimestampMixin


class WorkspaceRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    is_personal: Mapped[bool] = mapped_column(default=True, nullable=False)


class WorkspaceMember(Base, TimestampMixin):
    __tablename__ = "workspace_members"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[WorkspaceRole] = mapped_column(
        Enum(WorkspaceRole, name="workspace_role"), default=WorkspaceRole.MEMBER, nullable=False
    )
