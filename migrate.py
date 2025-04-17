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
    main() 