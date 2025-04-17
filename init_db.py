#!/usr/bin/env python3
"""
Initialize the database for the Flask application.
This script creates all tables and seeds the database with initial data.
"""
from app import create_app
from app.database import db
from app.cli import seed_db_command
import os
import shutil

# Create the application
app = create_app()

with app.app_context():
    # Get database path
    db_path = app.config.get('SQLALCHEMY_DATABASE_URI').replace('sqlite:///', '')
    
    # Remove existing database file if it exists
    if os.path.exists(db_path):
        print(f"Removing existing database at: {db_path}")
        os.remove(db_path)
    
    print("Creating database tables...")
    db.create_all()
    print("Database tables created.")
    
    # Run the seed-db command directly
    print("\nSeeding database with initial data...")
    seed_db_command()
    
    # Print the database location
    if os.path.exists(db_path):
        print(f"\nDatabase created successfully at: {db_path}")
        print(f"Database size: {os.path.getsize(db_path) / 1024:.2f} KB")
    else:
        print(f"\nWarning: Database file not found at expected location: {db_path}")
        
    print("\nDatabase initialization complete!")
    print("You can now run the application with: python run.py") 