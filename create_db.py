#!/usr/bin/env python3
"""
Create Database Script
Creates a fresh database using the existing schema without migrations.
Run this after clean_slate.py to set up a new database.
"""
from app import create_app
from app.database import db
from app.database.models import User, Post, AuthToken
from app.cli import seed_db_command
import os
from pathlib import Path

app = create_app()

def create_fresh_database():
    """Create a fresh database using the existing schema"""
    # Get database path
    db_path = app.config.get('SQLALCHEMY_DATABASE_URI').replace('sqlite:///', '')
    db_path_obj = Path(db_path)
    
    # Make sure instance directory exists
    instance_dir = db_path_obj.parent
    if not instance_dir.exists():
        print(f"Creating instance directory: {instance_dir}")
        os.makedirs(instance_dir)
    
    # Check if database already exists
    if db_path_obj.exists():
        print(f"Warning: Database already exists at: {db_path}")
        response = input("Do you want to overwrite it? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled.")
            return
        os.remove(db_path)
        print(f"Existing database removed.")
    
    with app.app_context():
        # Create all tables directly from models
        print("\nCreating database tables...")
        db.create_all()
        print("Database tables created.")
        
        # Seed the database with sample data
        print("\nSeeding database with sample data...")
        seed_db_command()
        
        # Display information about the database
        if db_path_obj.exists():
            print(f"\nDatabase created successfully at: {db_path}")
            print(f"Database size: {db_path_obj.stat().st_size / 1024:.2f} KB")
        else:
            print(f"\nWarning: Database file not found at expected location: {db_path}")
        
        print("\nDatabase has been created successfully without using migrations!")
        print("You can now run the application with: python run.py")

if __name__ == "__main__":
    create_fresh_database() 