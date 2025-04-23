#!/bin/bash
set -e  # Exit immediately if any command fails

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Build Tailwind CSS for production
echo "Building Tailwind CSS for production..."
npx tailwindcss -i app/static/css/src/main.css -o app/static/css/tailwind.css --minify

# Database initialization and migration
echo "Setting up the database..."

# Set the Flask app environment variable
export FLASK_APP=run.py

# Print current directory and list files for debugging
echo "Current directory: $(pwd)"
echo "Project files:"
ls -la

# Try to use Flask-Migrate first
echo "Attempting to use Flask-Migrate..."
MIGRATION_SUCCESS=0

# Check if migrations directory exists
if [ ! -d "migrations" ]; then
  echo "Migrations directory not found. Initializing..."
  flask db init
  if [ $? -ne 0 ]; then
    echo "Error: Failed to initialize database migrations"
    MIGRATION_SUCCESS=1
  fi
else
  echo "Migrations directory found at:"
  ls -la migrations/
  
  # Check for version files
  echo "Migration versions:"
  ls -la migrations/versions/ || echo "No versions directory or files found"
fi

# Only try migrations if init was successful
if [ $MIGRATION_SUCCESS -eq 0 ]; then
  # Create a migration if there are model changes
  echo "Creating migration for any model changes..."
  flask db migrate -m "Auto-migration on build $(date +%Y%m%d%H%M%S)"
  
  # Always run upgrades to ensure database is up to date
  echo "Applying migrations to database..."
  flask db upgrade
  if [ $? -ne 0 ]; then
    echo "Warning: Migration application failed"
    MIGRATION_SUCCESS=1
  else
    echo "✅ Database migrations completed successfully!"
  fi
fi

# If migrations failed, try direct table creation
if [ $MIGRATION_SUCCESS -ne 0 ]; then
  echo "Trying direct table creation instead of migrations..."
  python init_db.py
  if [ $? -ne 0 ]; then
    echo "❌ Direct table creation also failed!"
    echo "Please check database connection and permissions."
    exit 1
  else
    echo "✅ Direct table creation successful!"
  fi
fi

echo "✅ Database setup complete!" 