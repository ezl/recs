"""Add destination model

Revision ID: 825af8bdc5e9
Revises: c3e5a6f14e9d
Create Date: 2025-05-04 20:48:02.836841

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '825af8bdc5e9'
down_revision = 'c3e5a6f14e9d'
branch_labels = None
depends_on = None


def upgrade():
    # Create destinations table
    op.create_table('destinations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('population', sa.Integer(), nullable=True),
        sa.Column('travel_popularity', sa.Float(), nullable=True),
        sa.Column('google_place_id', sa.String(length=255), nullable=True),
        sa.Column('place_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on google_place_id
    with op.batch_alter_table('destinations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_destinations_google_place_id'), ['google_place_id'], unique=True)

    # Add destination_id to trips table
    with op.batch_alter_table('trips', schema=None) as batch_op:
        batch_op.add_column(sa.Column('destination_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_trips_destination_id_destinations', 'destinations', ['destination_id'], ['id'])


def downgrade():
    # Remove destination_id from trips
    with op.batch_alter_table('trips', schema=None) as batch_op:
        batch_op.drop_constraint('fk_trips_destination_id_destinations', type_='foreignkey')
        batch_op.drop_column('destination_id')

    # Drop destinations table and index
    with op.batch_alter_table('destinations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_destinations_google_place_id'))
    op.drop_table('destinations')
