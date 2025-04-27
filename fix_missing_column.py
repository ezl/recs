#!/usr/bin/env python
"""
Script to fix the missing google_place_id column in the activities table.
This script will:
1. Check if the column exists
2. Add it if it doesn't exist
3. Create the appropriate index
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

def fix_missing_column():
    """Add the missing google_place_id column to activities table if needed"""
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Check if column exists
            inspector = inspect(db.engine)
            columns = inspector.get_columns('activities')
            column_exists = any(column['name'] == 'google_place_id' for column in columns)
            
            if column_exists:
                logger.info("Column 'google_place_id' already exists in activities table. No fix needed.")
                return True
            
            # 2. Add the column if it doesn't exist
            logger.info("Column 'google_place_id' is missing. Adding it now...")
            with db.engine.begin() as conn:
                conn.execute(text("ALTER TABLE activities ADD COLUMN google_place_id VARCHAR(255)"))
                logger.info("Column added successfully.")
                
                # 3. Create the index
                logger.info("Creating unique index on google_place_id...")
                conn.execute(text("CREATE UNIQUE INDEX ix_activities_google_place_id ON activities (google_place_id)"))
                logger.info("Index created successfully.")
                
            logger.info("Database fix completed successfully!")
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
        if fix_missing_column():
            sys.exit(0)
        
        # If that fails, try the Alembic migration
        if run_alembic_migration():
            sys.exit(0)
        
        # If both approaches fail, exit with error
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1) 