#!/usr/bin/env python
"""
Script to fix the missing columns in the activities table.
This script will:
1. Check if the columns exist
2. Add them if they don't exist
3. Create the appropriate indexes
"""

import os
import sys
from flask import Flask
from sqlalchemy import inspect, text
import logging

# Add the current directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import db
from config import Config
import alembic.config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def fix_missing_columns():
    """Add missing columns to activities table if needed"""
    app = create_app()
    
    with app.app_context():
        try:
            # Get column information
            inspector = inspect(db.engine)
            columns = inspector.get_columns('activities')
            column_names = [column['name'] for column in columns]
            
            fixed_something = False
            
            # Check and add google_place_id column
            if 'google_place_id' not in column_names:
                logger.info("Column 'google_place_id' is missing. Adding it now...")
                with db.engine.begin() as conn:
                    conn.execute(text("ALTER TABLE activities ADD COLUMN google_place_id VARCHAR(255)"))
                    logger.info("Column google_place_id added successfully.")
                    
                    # Create the index
                    logger.info("Creating unique index on google_place_id...")
                    conn.execute(text("CREATE UNIQUE INDEX ix_activities_google_place_id ON activities (google_place_id)"))
                    logger.info("Index created successfully.")
                fixed_something = True
            else:
                logger.info("Column 'google_place_id' already exists.")
                
            # Check and add place_data column
            if 'place_data' not in column_names:
                logger.info("Column 'place_data' is missing. Adding it now...")
                with db.engine.begin() as conn:
                    # Add JSON column type - using JSONB for PostgreSQL or TEXT for others
                    # Detect database type
                    db_type = str(db.engine.url.drivername)
                    if 'postgres' in db_type:
                        conn.execute(text("ALTER TABLE activities ADD COLUMN place_data JSONB"))
                    else:
                        conn.execute(text("ALTER TABLE activities ADD COLUMN place_data TEXT"))
                    logger.info("Column place_data added successfully.")
                fixed_something = True
            else:
                logger.info("Column 'place_data' already exists.")
                
            # Check and add is_place_based column
            if 'is_place_based' not in column_names:
                logger.info("Column 'is_place_based' is missing. Adding it now...")
                with db.engine.begin() as conn:
                    conn.execute(text("ALTER TABLE activities ADD COLUMN is_place_based BOOLEAN DEFAULT TRUE"))
                    logger.info("Column is_place_based added successfully.")
                fixed_something = True
            else:
                logger.info("Column 'is_place_based' already exists.")
            
            if fixed_something:
                logger.info("Database columns fix completed successfully!")
            else:
                logger.info("All required columns already exist. No changes needed.")
            return True
            
        except Exception as e:
            logger.error(f"Error fixing database: {str(e)}")
            return False

def run_alembic_migration():
    """Run the Alembic migration as an alternative approach"""
    try:
        logger.info("Running Alembic migration...")
        alembic_args = [
            '--raiseerr',
            'upgrade', 'head',
        ]
        alembic.config.main(argv=alembic_args)
        logger.info("Alembic migration completed successfully!")
        return True
    except Exception as e:
        logger.error(f"Error running Alembic migration: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        # Try the direct fix first
        if fix_missing_columns():
            sys.exit(0)
        
        # If that fails, try the Alembic migration
        if run_alembic_migration():
            sys.exit(0)
        
        # If both approaches fail, exit with error
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1) 