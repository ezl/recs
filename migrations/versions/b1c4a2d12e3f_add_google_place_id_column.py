"""add google_place_id column

Revision ID: b1c4a2d12e3f
Revises: a5b7ff6ab760
Create Date: 2025-04-27 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'b1c4a2d12e3f'
down_revision = 'a5b7ff6ab760'
branch_labels = None
depends_on = None


def upgrade():
    # First check if column exists to avoid errors
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns('activities')
    column_names = [column['name'] for column in columns]
    
    if 'google_place_id' not in column_names:
        # Add the google_place_id column
        op.add_column('activities', sa.Column('google_place_id', sa.String(length=255), nullable=True))
        op.create_index(op.f('ix_activities_google_place_id'), 'activities', ['google_place_id'], unique=True)


def downgrade():
    # Since this is a recovery migration, downgrade should be a no-op to avoid data loss
    pass 