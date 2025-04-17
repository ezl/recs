#!/usr/bin/env python3
"""
Script to update the database schema for recommendations.
"""
from app import create_app
from app.database import db
from sqlalchemy import text

# Create the Flask application
app = create_app()

def update_schema():
    with app.app_context():
        # Check if recommendations table exists
        engine = db.engine
        inspector = db.inspect(engine)
        
        if 'recommendations' in inspector.get_table_names():
            # Check if website_url column exists
            columns = [c['name'] for c in inspector.get_columns('recommendations')]
            
            if 'website_url' not in columns:
                print("Adding website_url column to recommendations table...")
                with engine.connect() as connection:
                    connection.execute(text("ALTER TABLE recommendations ADD COLUMN website_url VARCHAR(255)"))
                print("Column added successfully!")
            else:
                print("website_url column already exists in recommendations table.")
        else:
            print("recommendations table does not exist.")

if __name__ == "__main__":
    update_schema() 