import os
import sys
import shutil
from pathlib import Path

# Add parent directory to path so we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import db
import subprocess

def reset_test_db():
    """Reset the test database to ensure clean state for tests"""
    print("Setting up test environment...")
    
    # Set environment variable to use TestConfig
    os.environ['FLASK_ENV'] = 'testing'
    
    # Get the test database path from config
    base_dir = Path(__file__).parent.parent
    instance_dir = base_dir / 'instance'
    test_db_path = instance_dir / 'test.db'
    
    # Remove test database if it exists
    if test_db_path.exists():
        print(f"Removing existing test database: {test_db_path}")
        os.remove(test_db_path)
    
    # Create the test app to initialize the database
    app = create_app()
    
    with app.app_context():
        print("Creating test database tables...")
        db.create_all()
        
        # Commit the changes
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