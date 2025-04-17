#!/usr/bin/env python3
"""
Database Reset Script

This script provides a single command to:
1. Remove all existing database files and migration history
2. Create a fresh database with the current schema
3. Seed the database with initial data

Usage:
    python3 db_reset.py

This eliminates the need for multiple database management scripts.
"""
import os
import shutil
import sys
from pathlib import Path
from app import create_app
from app.database import db
from app.database.models import User, Post, AuthToken, Trip, Recommendation
from flask_migrate import Migrate, init, migrate, upgrade

# Create the Flask application
app = create_app()
migrate_obj = Migrate(app, db)

def reset_database():
    """Complete database reset and initialization"""
    print("\n=== STEP 1: Removing existing database files and migrations ===")
    
    # Get roots and paths
    root_dir = Path(__file__).parent
    migrations_dir = root_dir / 'migrations'
    instance_dir = root_dir / 'instance'
    db_path = app.config.get('SQLALCHEMY_DATABASE_URI').replace('sqlite:///', '')
    
    # Remove migrations directory if it exists
    if migrations_dir.exists():
        print(f"Removing migrations directory: {migrations_dir}")
        shutil.rmtree(migrations_dir)
        print("Migrations directory removed.")
    else:
        print("No migrations directory found.")
    
    # Remove instance directory with database files
    if instance_dir.exists():
        print(f"Removing instance directory: {instance_dir}")
        shutil.rmtree(instance_dir)
        print("Instance directory removed.")
    else:
        print("No instance directory found.")
    
    print("\n=== STEP 2: Creating new database with latest schema ===")
    
    # Create instance directory
    instance_dir.mkdir(exist_ok=True)
    print(f"Created instance directory: {instance_dir}")
    
    with app.app_context():
        # Initialize migration repository
        print("\nInitializing new migration repository...")
        init(directory='migrations')
        print("Migration repository initialized.")
        
        # Create initial migration
        print("\nCreating initial migration...")
        migrate(directory='migrations', message='initial schema')
        print("Initial migration created.")
        
        # Apply migration to create tables
        print("\nApplying migration to create database tables...")
        upgrade(directory='migrations')
        print("Migration applied. Tables created.")
        
        # Verify all tables exist with correct schema
        engine = db.engine
        inspector = db.inspect(engine)
        tables = inspector.get_table_names()
        
        print("\nVerifying database schema...")
        expected_tables = ['users', 'auth_tokens', 'posts', 'trips', 'recommendations']
        
        for table in expected_tables:
            if table in tables:
                print(f"✅ Table '{table}' exists")
                
                # Verify columns in recommendations table
                if table == 'recommendations':
                    columns = [c['name'] for c in inspector.get_columns(table)]
                    if 'website_url' in columns:
                        print(f"  ✅ Column 'website_url' exists in '{table}' table")
                    else:
                        print(f"  ❌ Column 'website_url' missing from '{table}' table")
                        print(f"  Adding 'website_url' column to '{table}' table...")
                        db.session.execute("ALTER TABLE recommendations ADD COLUMN website_url VARCHAR(255)")
                        print(f"  'website_url' column added to '{table}' table")
            else:
                print(f"❌ Table '{table}' is missing")
    
    print("\n=== STEP 3: Seeding database with initial data ===")
    
    with app.app_context():
        # Create admin user
        admin_email = 'admin@example.com'
        admin_user = User.query.filter_by(email=admin_email).first()
        
        if not admin_user:
            admin_user = User(email=admin_email, name='Admin User')
            db.session.add(admin_user)
            db.session.commit()
            print(f"Created admin user: {admin_email}")
        
        # Create anonymous user
        anon_email = 'anonymous@example.com'
        anon_user = User.query.filter_by(email=anon_email).first()
        
        if not anon_user:
            anon_user = User(email=anon_email, name='Anonymous User')
            db.session.add(anon_user)
            db.session.commit()
            print(f"Created anonymous user: {anon_email}")
    
    print("\n=== Database Reset Complete ===")
    print(f"Database created at: {db_path}")
    print("You can now run the application with: python3 run.py")

if __name__ == "__main__":
    # Ask for confirmation
    response = input("This will permanently delete all database files and migrations. Continue? (y/n): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        sys.exit(0)
    
    try:
        reset_database()
    except Exception as e:
        import traceback
        print(f"\nError during database reset: {e}")
        traceback.print_exc()
        print("\nThe reset process failed. Please check the error above.")
        sys.exit(1) 