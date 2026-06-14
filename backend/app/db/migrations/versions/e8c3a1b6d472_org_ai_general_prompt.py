"""org ai general prompt

Revision ID: e8c3a1b6d472
Revises: d7b2c4e9f013
Create Date: 2026-06-14 11:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8c3a1b6d472"
down_revision: Union[str, None] = "d7b2c4e9f013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("ai_general_prompt", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("organizations", "ai_general_prompt")
