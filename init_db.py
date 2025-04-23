"""
Database initialization script to directly create tables without using migrations.
Run this script directly if migrations are failing.
"""
import os
import sys
from app import create_app
from app.database import db
from app.database.models import User, Trip, Recommendation, Activity, AuthToken, Post

# Create Flask app with the database connection
app = create_app()

def init_db():
    """Create all tables directly using SQLAlchemy"""
    with app.app_context():
        print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print("Creating all tables...")
        
        try:
            # Create all tables
            db.create_all()
            print("✅ Tables created successfully!")
            
            # Check if users table was created
            engine = db.engine
            inspector = db.inspect(engine)
            tables = inspector.get_table_names()
            print(f"Tables in database: {tables}")
            
            if 'users' in tables:
                print("✅ 'users' table exists!")
            else:
                print("❌ 'users' table was not created!")
                
            return True
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            return False

if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1) 