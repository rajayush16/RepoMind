"""add content column to indexed_files

Revision ID: 1f2ae4ba51cc
Revises: a35bbb58389e
Create Date: 2026-11-20 14:35:20.046810

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1f2ae4ba51cc'
down_revision: Union[str, None] = 'a35bbb58389e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("indexed_files", sa.Column("content", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("indexed_files", "content")
