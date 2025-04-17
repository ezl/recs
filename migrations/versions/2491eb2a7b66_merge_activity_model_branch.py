"""Merge activity_model branch

Revision ID: 2491eb2a7b66
Revises: 55a862f9d16a, activity_model_001
Create Date: 2025-04-16 23:43:19.458400

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2491eb2a7b66'
down_revision = ('55a862f9d16a', 'activity_model_001')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
