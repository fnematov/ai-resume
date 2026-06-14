"""vacancy banner image

Revision ID: c3f1a9d8e210
Revises: 2ae4d27375ef
Create Date: 2026-06-13 16:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3f1a9d8e210"
down_revision: Union[str, None] = "2ae4d27375ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("vacancies", sa.Column("image_path", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("vacancies", "image_path")
