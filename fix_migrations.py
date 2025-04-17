#!/usr/bin/env python
"""
Script to fix migration history by marking migrations as completed
"""
import os
import sys
from sqlalchemy import create_engine, text
from flask import Flask
from flask_migrate import Migrate, init, stamp
from app.database import db

def fix_migrations():
    print("Starting migration fix...")
    
    # Create a Flask app
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Initialize database but don't create tables
    db.init_app(app)
    
    # Initialize migrations
    migrate = Migrate(app, db)
    
    with app.app_context():
        # Stamp the database with the ID of the most recent migration
        # This tells Alembic that the database is up to date with this migration
        stamp(directory='migrations', revision='2491eb2a7b66')
        print("Database stamped with migration 2491eb2a7b66")
        
        # Now you can create new migrations from this point forward
        print("Migration history fixed. You can now create new migrations with 'flask db migrate'")

if __name__ == "__main__":
    fix_migrations() 