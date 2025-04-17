"""Add Activity model and refactor Recommendation

Revision ID: activity_model_001
Revises: 55c6454a07d2
Create Date: 2024-11-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'activity_model_001'
down_revision = '55c6454a07d2'  # Adjust this to your last migration
branch_labels = None
depends_on = None


def upgrade():
    # Create activities table
    op.create_table('activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('website_url', sa.String(length=255), nullable=True),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('is_place_based', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create a temporary recommendations table
    op.create_table('temp_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('activity_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('trip_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['activity_id'], ['activities.id'], ),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 1. Copy existing data: For each recommendation, create an activity
    #    and link it to the recommendation
    connection = op.get_bind()
    recommendations = connection.execute(
        sa.text("SELECT id, name, place_type, website_url, description, author_id, trip_id, created_at, updated_at FROM recommendations")
    ).fetchall()
    
    for rec in recommendations:
        # 1. Insert into activities
        result = connection.execute(
            sa.text("""
                INSERT INTO activities (name, category, website_url, created_at, updated_at) 
                VALUES (:name, :category, :website_url, :created_at, :updated_at)
                RETURNING id
            """),
            {
                'name': rec.name,
                'category': rec.place_type,
                'website_url': rec.website_url,
                'created_at': rec.created_at,
                'updated_at': rec.updated_at
            }
        )
        activity_id = result.fetchone()[0]
        
        # 2. Insert into temp_recommendations
        connection.execute(
            sa.text("""
                INSERT INTO temp_recommendations (activity_id, description, author_id, trip_id, created_at, updated_at)
                VALUES (:activity_id, :description, :author_id, :trip_id, :created_at, :updated_at)
            """),
            {
                'activity_id': activity_id,
                'description': rec.description,
                'author_id': rec.author_id,
                'trip_id': rec.trip_id,
                'created_at': rec.created_at,
                'updated_at': rec.updated_at
            }
        )
    
    # 3. Drop old recommendations table
    op.drop_table('recommendations')
    
    # 4. Rename temp_recommendations to recommendations
    op.rename_table('temp_recommendations', 'recommendations')


def downgrade():
    # Create temporary recommendations table with old structure
    op.create_table('temp_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('place_type', sa.String(length=50), nullable=True),
        sa.Column('website_url', sa.String(length=255), nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('trip_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Migrate data back
    connection = op.get_bind()
    
    # Get all recommendations with their linked activities
    new_recommendations = connection.execute(
        sa.text("""
            SELECT r.id, r.description, r.author_id, r.trip_id, r.created_at, r.updated_at,
                   a.name, a.category as place_type, a.website_url
            FROM recommendations r
            JOIN activities a ON r.activity_id = a.id
        """)
    ).fetchall()
    
    for rec in new_recommendations:
        # Insert into old-style recommendations
        connection.execute(
            sa.text("""
                INSERT INTO temp_recommendations (name, description, place_type, website_url, author_id, trip_id, created_at, updated_at)
                VALUES (:name, :description, :place_type, :website_url, :author_id, :trip_id, :created_at, :updated_at)
            """),
            {
                'name': rec.name,
                'description': rec.description,
                'place_type': rec.place_type,
                'website_url': rec.website_url,
                'author_id': rec.author_id,
                'trip_id': rec.trip_id,
                'created_at': rec.created_at,
                'updated_at': rec.updated_at
            }
        )
    
    # Drop new tables
    op.drop_table('recommendations')
    op.rename_table('temp_recommendations', 'recommendations')
    op.drop_table('activities') 