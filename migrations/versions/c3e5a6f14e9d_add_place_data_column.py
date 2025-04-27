"""add place_data column

Revision ID: c3e5a6f14e9d
Revises: b1c4a2d12e3f
Create Date: 2025-04-28 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'c3e5a6f14e9d'
down_revision = 'b1c4a2d12e3f'
branch_labels = None
depends_on = None


def upgrade():
    # First check if columns exist to avoid errors
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = inspector.get_columns('activities')
    column_names = [column['name'] for column in columns]
    
    # Check the database engine type to use appropriate JSON type
    dialect = conn.dialect.name
    
    # Add place_data column if missing
    if 'place_data' not in column_names:
        if dialect == 'postgresql':
            op.add_column('activities', sa.Column('place_data', postgresql.JSONB, nullable=True))
        else:
            op.add_column('activities', sa.Column('place_data', sa.JSON, nullable=True))
    
    # Add is_place_based column if missing
    if 'is_place_based' not in column_names:
        op.add_column('activities', sa.Column('is_place_based', sa.Boolean, server_default='true', nullable=True))


def downgrade():
    # Since this is a recovery migration, downgrade should be a no-op to avoid data loss
    pass 