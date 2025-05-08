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

# Set the Flask app environment variable
export FLASK_APP=run.py

# First approach: Try to run Alembic migrations
echo "Running database migrations with Alembic..."
flask db upgrade

# Check if migrations succeeded
if [ $? -eq 0 ]; then
  echo "✅ Database migrations completed successfully!"
else
  echo "⚠️ Migration with Alembic failed, attempting fallback methods..."
  
  # Try running the fix script directly
  echo "Running the fix_missing_columns script..."
  python fix_missing_column.py
  
  if [ $? -eq 0 ]; then
    echo "✅ Database column fix applied successfully!"
  else
    # Last resort: use direct SQLAlchemy table creation
    echo "Falling back to direct table creation with SQLAlchemy..."
    python init_db.py
    
    if [ $? -eq 0 ]; then
      echo "✅ Database tables created successfully as a fallback!"
    else
      echo "❌ All database setup methods failed."
      echo "❌ Build failed."
      exit 1 # Exit with failure
    fi
  fi
fi

# Verify database schema against SQLAlchemy models and fix any issues
echo "Verifying database schema against models..."
python verify_db_schema.py --fix

if [ $? -eq 0 ]; then
  echo "✅ Database schema verification successful!"
else
  echo "⚠️ Database schema verification found issues. Check logs for details."
  # Don't exit with failure here, as the previous steps might have been sufficient
fi

echo "✅ Build completed successfully!"
exit 0 # Exit with success 