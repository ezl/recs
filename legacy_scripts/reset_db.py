#!/usr/bin/env python3
"""
Reset the database and migration system for the Flask application.
This script completely resets the database and migration history.
"""
from app import create_app
from app.database import db
from app.database.models import User, Post, AuthToken
from app.cli import seed_db_command
import os
import shutil
import sys
from flask_migrate import Migrate, init, migrate, upgrade, stamp

app = create_app()
migrate_obj = Migrate(app, db)

def reset_database_and_migrations():
    """Reset the entire database and migration system."""
    # Get database path
    db_path = app.config.get('SQLALCHEMY_DATABASE_URI').replace('sqlite:///', '')
    
    # Check if the migrations directory exists
    if os.path.exists('migrations'):
        print("Removing existing migrations directory...")
        shutil.rmtree('migrations')
        print("Migrations directory removed.")
    
    # Remove existing database file if it exists
    if os.path.exists(db_path):
        print(f"Removing existing database at: {db_path}")
        os.remove(db_path)
        print("Database removed.")
    
    # Make sure instance directory exists
    instance_dir = os.path.dirname(db_path)
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        print(f"Created instance directory: {instance_dir}")
    
    with app.app_context():
        # Initialize the migration repository
        print("\nInitializing new migration repository...")
        init(directory='migrations')
        print("Migration repository initialized.")
        
        # Create the initial migration
        print("\nCreating initial migration...")
        migrate(directory='migrations', message='initial schema with auth tokens')
        print("Initial migration created.")
        
        # Apply the migration to create tables
        print("\nApplying migration to create tables...")
        upgrade(directory='migrations')
        print("Migration applied.")
        
        # Seed the database
        print("\nSeeding database with sample data...")
        seed_db_command()
        
        # Display information about the database
        if os.path.exists(db_path):
            print(f"\nDatabase created successfully at: {db_path}")
            print(f"Database size: {os.path.getsize(db_path) / 1024:.2f} KB")
        else:
            print(f"\nWarning: Database file not found at expected location: {db_path}")
        
        print("\nDatabase and migrations have been reset successfully!")
        print("You can now run the application with: python run.py")

if __name__ == '__main__':
    try:
        reset_database_and_migrations()
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        print("The reset process failed. Please check the error above.") 