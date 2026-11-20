"""create indexing_jobs indexed_files code_symbols

Revision ID: a35bbb58389e
Revises: 9c48096e893a
Create Date: 2026-11-20 14:09:25.794278

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a35bbb58389e'
down_revision: Union[str, None] = '9c48096e893a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

indexing_job_status = postgresql.ENUM(
    "queued", "running", "success", "failed", name="indexing_job_status"
)


def upgrade() -> None:
    indexing_job_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "indexing_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", indexing_job_status, nullable=False, server_default="queued"),
        sa.Column("commit_sha", sa.String(40), nullable=True),
        sa.Column("files_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("files_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("symbols_extracted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("graph_relationships_written", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embeddings_generated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_indexing_jobs_repository_id", "indexing_jobs", ["repository_id"])

    op.create_table(
        "indexed_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relative_path", sa.String(1024), nullable=False),
        sa.Column("language", sa.String(32), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("symbol_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_indexed_commit_sha", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("repository_id", "relative_path", name="uq_repo_file_path"),
    )
    op.create_index("ix_indexed_files_repository_id", "indexed_files", ["repository_id"])

    op.create_table(
        "code_symbols",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "indexed_file_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("indexed_files.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stable_symbol_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("symbol_type", sa.String(32), nullable=False),
        sa.Column("parent_name", sa.String(512), nullable=True),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("signature", sa.String(512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("repository_id", "stable_symbol_id", name="uq_repo_stable_symbol"),
    )
    op.create_index("ix_code_symbols_repository_id", "code_symbols", ["repository_id"])
    op.create_index("ix_code_symbols_indexed_file_id", "code_symbols", ["indexed_file_id"])
    op.create_index("ix_code_symbols_stable_symbol_id", "code_symbols", ["stable_symbol_id"])


def downgrade() -> None:
    op.drop_table("code_symbols")
    op.drop_table("indexed_files")
    op.drop_table("indexing_jobs")
    indexing_job_status.drop(op.get_bind(), checkfirst=True)
