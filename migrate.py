#!/usr/bin/env python3
"""
Migration script for the Flask application.
This script sets up and runs database migrations using Flask-Migrate.
"""
from app import create_app
from app.database import db, migrate
from flask_migrate import init, migrate as migrate_cmd, upgrade, current
import os
import sys
import importlib
from datetime import datetime

# Add the current directory to the path so we can import modules from the app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.models import User, Post, AuthToken, Trip, Recommendation, Activity, TripSubscription

app = create_app()

def init_migrations():
    """Initialize migration repository if it doesn't exist."""
    with app.app_context():
        if not os.path.exists('migrations'):
            print("Initializing migrations directory...")
            init(directory='migrations')
            print("Migrations directory created.")
        else:
            print("Migrations directory already exists.")

def create_migration(message=None):
    """Create a new migration."""
    with app.app_context():
        msg = f"--message '{message}'" if message else ""
        print(f"Creating new migration{' with message: ' + message if message else ''}...")
        migrate_cmd(directory='migrations', message=message)
        print("Migration created.")

def apply_migrations():
    """Apply all migrations."""
    with app.app_context():
        print("Applying migrations...")
        upgrade(directory='migrations')
        print("Migrations applied.")
        
        # Print current revision
        rev = current(directory='migrations')
        print(f"Current database revision: {rev}")

def run_migrations():
    with app.app_context():
        # Check if tables exist
        engine = db.engine
        inspector = db.inspect(engine)
        tables = inspector.get_table_names()
        
        # Create or update tables
        if not tables:
            print("No tables found. Creating all tables...")
            db.create_all()
            print("Tables created successfully!")
        else:
            print("Tables exist. Running migrations...")
            
            # Check if the users table exists
            if 'users' not in tables:
                print("Creating users table...")
                User.__table__.create(engine)
            
            # Check if the posts table exists
            if 'posts' not in tables:
                print("Creating posts table...")
                Post.__table__.create(engine)
            
            # Check if the auth_tokens table exists
            if 'auth_tokens' not in tables:
                print("Creating auth_tokens table...")
                AuthToken.__table__.create(engine)
                
            # Check if the trips table exists
            if 'trips' not in tables:
                print("Creating trips table...")
                Trip.__table__.create(engine)
                
            # Check if the recommendations table exists
            if 'recommendations' not in tables:
                print("Creating recommendations table...")
                Recommendation.__table__.create(engine)
                
            # Check if the activities table exists
            if 'activities' not in tables:
                print("Creating activities table...")
                Activity.__table__.create(engine)
                
            # Check if the trip_subscriptions table exists
            if 'trip_subscriptions' not in tables:
                print("Creating trip_subscriptions table...")
                TripSubscription.__table__.create(engine)
            
            # Add additional migrations here when needed
            
            print("Migrations completed successfully!")
        
        # Print all tables
        print("\nCurrent database tables:")
        tables = inspector.get_table_names()
        for table in tables:
            print(f"- {table}")
            
            # Print columns for debugging
            columns = inspector.get_columns(table)
            for column in columns:
                print(f"  - {column['name']} ({column['type']})")
            
            print("")

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python migrate.py [init|create|upgrade]")
        print("  init: Initialize the migration repository")
        print("  create [message]: Create a new migration (optional message)")
        print("  upgrade: Apply all migrations")
        return
    
    command = sys.argv[1]
    
    if command == 'init':
        init_migrations()
    elif command == 'create':
        message = sys.argv[2] if len(sys.argv) > 2 else None
        create_migration(message)
    elif command == 'upgrade':
        apply_migrations()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python migrate.py [init|create|upgrade]")
        
if __name__ == '__main__':
    print(f"Starting migrations at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    run_migrations()
    print(f"Completed migrations at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 