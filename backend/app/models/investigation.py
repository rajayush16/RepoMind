import enum
import uuid

from sqlalchemy import JSON, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin


class InvestigationStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class Investigation(Base, TimestampMixin):
    __tablename__ = "investigations"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    bug_description: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    stack_trace: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[InvestigationStatus] = mapped_column(
        Enum(InvestigationStatus, name="investigation_status"),
        default=InvestigationStatus.RUNNING,
        nullable=False,
    )
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_fix: Mapped[str | None] = mapped_column(Text, nullable=True)
    potential_side_effects: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    steps: Mapped[list["InvestigationStep"]] = relationship(
        back_populates="investigation", order_by="InvestigationStep.created_at", cascade="all, delete-orphan"
    )


class InvestigationStep(Base, TimestampMixin):
    __tablename__ = "investigation_steps"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list | None] = mapped_column(JSON, nullable=True)

    investigation: Mapped["Investigation"] = relationship(back_populates="steps")
