import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID, TimestampMixin


class PullRequestReview(Base, TimestampMixin):
    __tablename__ = "pull_request_reviews"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    pr_title: Mapped[str] = mapped_column(String(512), nullable=False)
    pr_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    published: Mapped[bool] = mapped_column(default=False, nullable=False)
    published_comment_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    findings: Mapped[list["ReviewFinding"]] = relationship(
        back_populates="pull_request_review", cascade="all, delete-orphan"
    )


class ReviewFinding(Base, TimestampMixin):
    __tablename__ = "review_findings"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    pull_request_review_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("pull_request_reviews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str] = mapped_column(String(512), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)

    pull_request_review: Mapped["PullRequestReview"] = relationship(back_populates="findings")
