"""add roadmap column to learning_path

Revision ID: 78c23361ba42
Revises: ce9dfba078b7
Create Date: 2026-06-10 13:26:42.867285
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa




# revision identifiers, used by Alembic.
revision = '78c23361ba42'
down_revision = 'ce9dfba078b7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('learning_paths', sa.Column('roadmap', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('learning_paths', 'roadmap')

