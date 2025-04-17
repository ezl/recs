#!/usr/bin/env python3
"""
Clean Slate Script
Completely removes all migrations and the database.
Use this to start completely fresh without any migration history.
"""
import os
import shutil
from pathlib import Path

def clean_slate():
    """Remove all migrations and database files"""
    # Project root directory
    root_dir = Path(__file__).parent
    
    # Migrations directory
    migrations_dir = root_dir / 'migrations'
    if migrations_dir.exists():
        print(f"Removing migrations directory: {migrations_dir}")
        shutil.rmtree(migrations_dir)
        print("Migrations directory removed.")
    else:
        print("No migrations directory found.")
    
    # Instance directory with database
    instance_dir = root_dir / 'instance'
    if instance_dir.exists():
        # Remove database files
        for db_file in instance_dir.glob('*.db'):
            print(f"Removing database file: {db_file}")
            os.remove(db_file)
            print(f"Database file {db_file.name} removed.")
        
        # Check if instance dir is empty
        if not any(instance_dir.iterdir()):
            print("Instance directory is empty, removing it.")
            instance_dir.rmdir()
        else:
            print("Instance directory not empty, keeping it.")
    else:
        print("No instance directory found.")
    
    print("\nAll migrations and database files have been removed.")
    print("You can now create a fresh database with your existing schema.")

if __name__ == "__main__":
    response = input("This will permanently delete all migrations and database files. Continue? (y/n): ")
    if response.lower() == 'y':
        clean_slate()
    else:
        print("Operation cancelled.") 