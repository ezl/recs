#!/bin/bash
# Don't exit immediately, we want to try multiple approaches
set +e

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

# Database initialization - BYPASSING FLASK-MIGRATE ENTIRELY
echo "Setting up the database using direct SQLAlchemy..."

# Set the Flask app environment variable
export FLASK_APP=run.py

# Use SQLAlchemy directly to create tables
echo "Creating tables directly with SQLAlchemy..."
python init_db.py

# Check if direct table creation succeeded
if [ $? -eq 0 ]; then
  echo "✅ Database tables created successfully! Skipping migrations completely."
  echo "✅ Build completed successfully!"
  exit 0 # Exit with success
else
  echo "❌ Failed to create database tables."
  echo "❌ Build failed."
  exit 1 # Exit with failure
fi 