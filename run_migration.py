#!/usr/bin/env python
"""
Standalone script to run the Activity model migration.
Run this script from the command line with: python run_migration.py
"""
import os
import sys
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from datetime import datetime

def run_migration():
    print("Starting Activity model migration...")
    
    # Get the database URL from environment or default to SQLite
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///sqlite3.db')
    
    try:
        # Create engine and connection
        engine = create_engine(db_url)
        connection = engine.connect()
        
        # Start a transaction
        trans = connection.begin()
        
        print("Creating activities table...")
        # Create activities table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                category VARCHAR(50),
                website_url VARCHAR(255),
                address VARCHAR(255),
                city VARCHAR(100),
                country VARCHAR(100),
                latitude FLOAT,
                longitude FLOAT,
                is_place_based BOOLEAN DEFAULT 1,
                created_at DATETIME,
                updated_at DATETIME
            )
        """))
        
        print("Creating temporary recommendations table...")
        # Create a temporary recommendations table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS temp_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER NOT NULL,
                description TEXT,
                author_id INTEGER NOT NULL,
                trip_id INTEGER NOT NULL,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY (activity_id) REFERENCES activities (id),
                FOREIGN KEY (author_id) REFERENCES users (id),
                FOREIGN KEY (trip_id) REFERENCES trips (id)
            )
        """))
        
        print("Copying data from recommendations to activities and temp_recommendations...")
        # Get all recommendations
        result = connection.execute(text(
            "SELECT id, name, place_type, website_url, description, author_id, trip_id, created_at, updated_at FROM recommendations"
        ))
        recommendations = result.fetchall()
        
        migration_count = 0
        for rec in recommendations:
            # Insert into activities
            activity_result = connection.execute(
                text("""
                    INSERT INTO activities (name, category, website_url, created_at, updated_at) 
                    VALUES (:name, :category, :website_url, :created_at, :updated_at)
                    RETURNING id
                """),
                {
                    'name': rec.name,
                    'category': rec.place_type,
                    'website_url': rec.website_url,
                    'created_at': rec.created_at or datetime.utcnow(),
                    'updated_at': rec.updated_at or datetime.utcnow()
                }
            )
            
            activity_id = activity_result.fetchone()[0]
            
            # Insert into temp_recommendations
            connection.execute(
                text("""
                    INSERT INTO temp_recommendations (activity_id, description, author_id, trip_id, created_at, updated_at)
                    VALUES (:activity_id, :description, :author_id, :trip_id, :created_at, :updated_at)
                """),
                {
                    'activity_id': activity_id,
                    'description': rec.description,
                    'author_id': rec.author_id,
                    'trip_id': rec.trip_id,
                    'created_at': rec.created_at or datetime.utcnow(),
                    'updated_at': rec.updated_at or datetime.utcnow()
                }
            )
            migration_count += 1
        
        print(f"Successfully migrated {migration_count} recommendations to the new model.")
        
        print("Dropping old recommendations table...")
        # Drop the old recommendations table
        connection.execute(text("DROP TABLE IF EXISTS recommendations"))
        
        print("Renaming temp_recommendations to recommendations...")
        # Rename temp_recommendations to recommendations
        connection.execute(text("ALTER TABLE temp_recommendations RENAME TO recommendations"))
        
        # Commit the transaction
        trans.commit()
        
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        if 'trans' in locals():
            trans.rollback()
        print(f"Error during migration: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1) 