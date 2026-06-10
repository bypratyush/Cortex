"""add structured_understanding to learner_profile

Revision ID: ce9dfba078b7
Revises: 5cc6620d7da9
Create Date: 2026-06-10 13:11:23.414719
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa




# revision identifiers, used by Alembic.
revision = 'ce9dfba078b7'
down_revision = '5cc6620d7da9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('learner_profiles', sa.Column('structured_understanding', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('learner_profiles', 'structured_understanding')

