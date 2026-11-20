import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, GUID, TimestampMixin


class GeneratedTest(Base, TimestampMixin):
    __tablename__ = "generated_tests"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    symbol_name: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    framework: Mapped[str] = mapped_column(String(32), nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)


class TestExecution(Base, TimestampMixin):
    __tablename__ = "test_executions"
    # Not a pytest test class -- pytest's discovery heuristic only matches on the
    # "Test" name prefix, so without this it tries (and fails) to collect this
    # SQLAlchemy model as a test.
    __test__ = False

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    generated_test_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("generated_tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # pending | running | passed | failed | sandbox_unavailable -- never "passed"
    # unless a real sandbox actually ran the test.
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
