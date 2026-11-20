"""create users workspaces workspace_members repositories

Revision ID: 9c48096e893a
Revises:
Create Date: 2026-11-20 13:31:36.820605

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9c48096e893a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

workspace_role = postgresql.ENUM("owner", "admin", "member", name="workspace_role")


def upgrade() -> None:
    workspace_role.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("github_id", sa.String(64), nullable=True),
        sa.Column("github_username", sa.String(255), nullable=True),
        sa.Column("github_avatar_url", sa.String(1024), nullable=True),
        sa.Column("github_access_token_encrypted", sa.String(1024), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_github_id", "users", ["github_id"], unique=True)

    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("is_personal", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_workspaces_slug", "workspaces", ["slug"], unique=True)

    op.create_table(
        "workspace_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", workspace_role, nullable=False, server_default="member"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
    )
    op.create_index("ix_workspace_members_workspace_id", "workspace_members", ["workspace_id"])
    op.create_index("ix_workspace_members_user_id", "workspace_members", ["user_id"])

    op.create_table(
        "repositories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "connected_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("github_repo_id", sa.BigInteger(), nullable=False),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(512), nullable=False),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column("default_branch", sa.String(255), nullable=False, server_default="main"),
        sa.Column("selected_branch", sa.String(255), nullable=False, server_default="main"),
        sa.Column("primary_language", sa.String(64), nullable=True),
        sa.Column("is_private", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("indexing_status", sa.String(32), nullable=False, server_default="not_indexed"),
        sa.Column("file_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("symbol_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("workspace_id", "github_repo_id", name="uq_workspace_github_repo"),
    )
    op.create_index("ix_repositories_workspace_id", "repositories", ["workspace_id"])
    op.create_index("ix_repositories_github_repo_id", "repositories", ["github_repo_id"])


def downgrade() -> None:
    op.drop_table("repositories")
    op.drop_table("workspace_members")
    op.drop_table("workspaces")
    op.drop_table("users")
    workspace_role.drop(op.get_bind(), checkfirst=True)
