#!/bin/bash
set -e  # Exit immediately on error

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

# Set the Flask app environment variable
export FLASK_APP=run.py

# Run Alembic migrations (fail fast if this fails)
echo "Running database migrations with Alembic..."
flask db upgrade

echo "✅ Database migrations completed successfully!"

# (Optional) Log Alembic version
echo "Current Alembic version:"
flask db current

echo "✅ Build completed successfully!"
exit 0 