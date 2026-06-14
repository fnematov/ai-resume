"""org ai analysis language

Revision ID: d7b2c4e9f013
Revises: c3f1a9d8e210
Create Date: 2026-06-14 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7b2c4e9f013"
down_revision: Union[str, None] = "c3f1a9d8e210"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("ai_language", sa.String(length=8), nullable=True))


def downgrade() -> None:
    op.drop_column("organizations", "ai_language")
