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

# First, try direct table creation to ensure tables exist
echo "Creating tables directly with SQLAlchemy..."
python init_db.py
DB_CREATED=$?

if [ $DB_CREATED -ne 0 ]; then
  echo "❌ Direct table creation failed!"
  exit 1
fi

# Now handle migrations - this is for tracking future changes
echo "Setting up migration tracking..."

# Check if migrations directory exists
if [ ! -d "migrations" ]; then
  echo "Migrations directory not found. Initializing..."
  flask db init
  if [ $? -ne 0 ]; then
    echo "⚠️ Failed to initialize migrations, but tables are created"
    echo "✅ Database setup complete (without migrations)!"
    exit 0
  fi
fi

# Try to stamp the database with the current migration head
# This marks all existing migrations as applied without making changes
echo "Stamping database with current migration head..."
flask db stamp head
if [ $? -ne 0 ]; then
  echo "⚠️ Failed to stamp database, but tables are created"
  echo "✅ Database setup complete (without migrations)!"
  exit 0
fi

# Create a new migration to capture any recent model changes
echo "Creating migration for any model changes..."
flask db migrate -m "Auto-migration on build $(date +%Y%m%d%H%M%S)"
if [ $? -ne 0 ]; then
  echo "⚠️ Migration creation failed, but tables are created"
  echo "✅ Database setup complete (without migrations)!"
  exit 0
fi

# Apply any new migrations (should be minimal since we just created tables)
echo "Applying migrations to database..."
flask db upgrade
if [ $? -ne 0 ]; then
  echo "⚠️ Migration application failed, but tables are created"
  echo "✅ Database setup complete (without migrations)!"
  exit 0
fi

echo "✅ Database setup complete with migrations!" 