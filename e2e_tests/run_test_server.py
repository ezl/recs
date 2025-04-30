"""
This is the main test server for the end-to-end test suite.
The e2e tests are located in /e2e_tests and use Playwright.
To run the tests:
1. Start this server: python run_test_server.py
2. In another terminal: cd e2e_tests && npm run test
"""

import os
import sys
import shutil
from pathlib import Path
import sqlite3
import time

# Add parent directory to path so we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import db
import subprocess
from flask_migrate import Migrate, upgrade, init

def reset_test_db():
    """Reset the test database to ensure clean state for tests"""
    print("Setting up test environment...")
    
    # Set environment variable to use TestConfig
    os.environ['FLASK_ENV'] = 'testing'
    
    # Get the test database path from config
    base_dir = Path(__file__).parent.parent
    instance_dir = base_dir / 'instance'
    test_db_path = instance_dir / 'test.db'
    
    # Ensure we have complete cleanup - try multiple removal strategies
    # 1. First try to drop all tables to ensure clean state if file exists
    if test_db_path.exists():
        print(f"Existing test database found: {test_db_path}")
        try:
            print("Attempting to drop all tables first...")
            # Connect directly to the SQLite database and drop all tables
            conn = sqlite3.connect(str(test_db_path))
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()
            
            # Drop each table
            for table in tables:
                print(f"  - Dropping table: {table[0]}")
                cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
            
            conn.commit()
            conn.close()
            print("All tables dropped successfully.")
        except Exception as e:
            print(f"Error dropping tables: {e}")
    
    # 2. Remove the file completely
    try:
        if test_db_path.exists():
            print(f"Removing test database file: {test_db_path}")
            os.remove(test_db_path)
            # Small delay to ensure file is fully released by OS
            time.sleep(0.5)
    except Exception as e:
        print(f"Error removing database file: {e}")
        # If we can't remove it, try to truncate it
        try:
            with open(test_db_path, 'wb') as f:
                f.truncate(0)
            print("Database file truncated.")
        except Exception as e2:
            print(f"Error truncating database file: {e2}")
    
    # Ensure instance directory exists
    instance_dir.mkdir(exist_ok=True)
    
    # Create the test app to initialize the database
    app = create_app()
    
    with app.app_context():
        print("Creating test database tables...")
        
        # Create all tables directly without migrations first
        db.create_all()
        print("Base tables created with SQLAlchemy.")
        
        # Set up migrations
        migrate = Migrate(app, db)
        
        # Initialize migrations if they don't exist
        migrations_dir = base_dir / 'migrations'
        if not migrations_dir.exists():
            print("Initializing migrations...")
            init()
        
        # Run migrations
        print("Running database migrations...")
        try:
            upgrade()
            print("✅ Migrations completed successfully")
        except Exception as e:
            print(f"❌ Warning: Migration issue: {e}")
            print("Continuing with base schema as tables are already created")
        
        # Ensure changes are committed
        db.session.commit()
    
    print("✅ Test database has been reset and initialized")
    return app

def build_tailwind():
    """Build the Tailwind CSS file"""
    print("Building Tailwind CSS...")
    root_dir = Path(__file__).parent.parent
    tailwind_path = root_dir / 'node_modules' / '.bin' / 'tailwindcss'
    
    if not os.path.exists(tailwind_path):
        print("❌ Tailwind CSS executable not found at", tailwind_path)
        print("Installing tailwindcss package...")
        subprocess.run(["npm", "install", "tailwindcss@3", "--save-dev"], check=True, cwd=root_dir)
    
    try:
        # Use the direct path to the executable
        result = subprocess.run(
            [
                str(tailwind_path), 
                "-i", "app/static/css/src/main.css", 
                "-o", "app/static/css/tailwind.css"
            ],
            capture_output=True,
            text=True,
            check=True,
            cwd=root_dir
        )
        print("✅ Tailwind CSS built successfully")
    except subprocess.CalledProcessError as e:
        print("❌ Tailwind CSS build failed:")
        print(e.stderr)

if __name__ == '__main__':
    # Reset the database
    app = reset_test_db()
    
    # Build Tailwind CSS
    build_tailwind()
    
    # Run the app
    print("Starting test server...")
    app.run(debug=True, port=5001) 