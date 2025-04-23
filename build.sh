#!/bin/bash

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install

# Build Tailwind CSS for production
npx tailwindcss -i app/static/css/src/main.css -o app/static/css/tailwind.css --minify

# Database initialization and migration
echo "Checking database status and running migrations..."

# Initialize the database if it hasn't been initialized
if [ ! -d "migrations" ]; then
  echo "Initializing database migrations..."
  flask db init
fi

# Create a migration if there are model changes
echo "Creating migration for any model changes..."
flask db migrate -m "Auto-migration on build $(date +%Y%m%d%H%M%S)"

# Always run upgrades to ensure database is up to date
echo "Applying any pending migrations..."
flask db upgrade

echo "Database setup complete!" 