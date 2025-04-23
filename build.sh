#!/bin/bash

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install

# Build Tailwind CSS for production
npx tailwindcss -i app/static/css/src/main.css -o app/static/css/tailwind.css --minify

# Run database migrations if needed
# Note: Uncomment the line below if you want to run migrations during build
# flask db upgrade 