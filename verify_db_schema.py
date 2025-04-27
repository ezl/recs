#!/usr/bin/env python
"""
Database Schema Verification Tool

This script verifies the database schema against the expected structure
from the SQLAlchemy models. It can detect and optionally fix missing columns
or tables.

Usage:
  python verify_db_schema.py [--fix]

Options:
  --fix    Attempt to fix any schema issues found (default: report only)
"""

import os
import sys
import argparse
import logging
from flask import Flask
from sqlalchemy import inspect, text
from sqlalchemy.sql import sqltypes

# Add the current directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import db
from config import Config
from app.database.models import Activity, User, Trip, Recommendation, AuthToken, Post, TripSubscription

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('db_verification.log')
    ]
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def get_expected_schema():
    """
    Return a dictionary of expected tables and columns based on SQLAlchemy models
    {
        'table_name': {
            'column_name': {
                'type': SQLAlchemy type object,
                'nullable': bool,
                'default': default value or None
            }
        }
    }
    """
    expected_schema = {}
    
    # Get all SQLAlchemy models
    models = [Activity, User, Trip, Recommendation, AuthToken, Post, TripSubscription]
    
    for model in models:
        table_name = model.__tablename__
        expected_schema[table_name] = {}
        
        for column in model.__table__.columns:
            col_name = column.name
            expected_schema[table_name][col_name] = {
                'type': type(column.type),
                'nullable': column.nullable,
                'default': column.default
            }
    
    return expected_schema

def get_actual_schema(connection):
    """
    Return a dictionary of actual tables and columns in the database
    {
        'table_name': {
            'column_name': {
                'type': SQLAlchemy type object,
                'nullable': bool,
                'default': default value or None
            }
        }
    }
    """
    actual_schema = {}
    
    inspector = inspect(connection)
    table_names = inspector.get_table_names()
    
    for table_name in table_names:
        actual_schema[table_name] = {}
        columns = inspector.get_columns(table_name)
        
        for column in columns:
            col_name = column['name']
            actual_schema[table_name][col_name] = {
                'type': type(column['type']),
                'nullable': column.get('nullable', True),
                'default': column.get('default')
            }
    
    return actual_schema

def compare_schemas(expected, actual):
    """
    Compare expected and actual schemas and return differences
    """
    differences = {
        'missing_tables': [],
        'missing_columns': {}
    }
    
    # Check for missing tables
    for table_name in expected:
        if table_name not in actual:
            differences['missing_tables'].append(table_name)
            continue
        
        # Check for missing columns
        for col_name in expected[table_name]:
            if col_name not in actual[table_name]:
                if table_name not in differences['missing_columns']:
                    differences['missing_columns'][table_name] = []
                differences['missing_columns'][table_name].append(col_name)
    
    return differences

def fix_schema_issues(connection, differences, expected_schema):
    """
    Fix schema issues by adding missing tables and columns
    """
    if not differences['missing_tables'] and not differences['missing_columns']:
        logger.info("No schema issues to fix.")
        return
    
    # Get database dialect
    dialect = connection.dialect.name
    
    # Fix missing tables
    for table_name in differences['missing_tables']:
        logger.warning(f"Missing table {table_name} cannot be automatically created. "
                      "Please use proper migrations or SQLAlchemy to create it.")
    
    # Fix missing columns
    for table_name, columns in differences['missing_columns'].items():
        for col_name in columns:
            col_def = expected_schema[table_name][col_name]
            col_type = col_def['type']
            
            # Map SQLAlchemy types to SQL types for the specific dialect
            sql_type = ""
            
            if col_type == sqltypes.String:
                sql_type = "VARCHAR(255)"
            elif col_type == sqltypes.Integer:
                sql_type = "INTEGER"
            elif col_type == sqltypes.Float:
                sql_type = "FLOAT"
            elif col_type == sqltypes.Boolean:
                sql_type = "BOOLEAN" if dialect != 'sqlite' else "INTEGER"
            elif col_type == sqltypes.DateTime:
                sql_type = "TIMESTAMP" if dialect != 'sqlite' else "DATETIME"
            elif col_type == sqltypes.Text:
                sql_type = "TEXT"
            elif "JSON" in str(col_type):
                sql_type = "JSONB" if dialect == 'postgresql' else "TEXT"
            else:
                sql_type = "TEXT"  # Default fallback
            
            # Set nullability
            null_clause = "NULL" if col_def['nullable'] else "NOT NULL"
            
            # Set default if available
            default_clause = ""
            if col_def['default'] is not None:
                if isinstance(col_def['default'], bool):
                    default_value = "TRUE" if col_def['default'] else "FALSE"
                    default_clause = f"DEFAULT {default_value}"
                else:
                    default_clause = f"DEFAULT {col_def['default']}"
            
            # Build and execute ALTER TABLE statement
            try:
                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {sql_type} {null_clause} {default_clause}"
                connection.execute(text(alter_sql.strip()))
                logger.info(f"Added column {col_name} to table {table_name}")
            except Exception as e:
                logger.error(f"Error adding column {col_name} to table {table_name}: {str(e)}")

def verify_db_schema(fix=False):
    """
    Verify the database schema against the expected structure from SQLAlchemy models
    """
    app = create_app()
    
    with app.app_context():
        try:
            # Get expected schema from SQLAlchemy models
            expected_schema = get_expected_schema()
            
            # Get actual schema from database
            actual_schema = get_actual_schema(db.engine)
            
            # Compare schemas
            differences = compare_schemas(expected_schema, actual_schema)
            
            # Report results
            if not differences['missing_tables'] and not differences['missing_columns']:
                logger.info("Database schema verification passed! All tables and columns exist.")
                return True
            
            # Log missing tables
            for table_name in differences['missing_tables']:
                logger.error(f"Missing table: {table_name}")
            
            # Log missing columns
            for table_name, columns in differences['missing_columns'].items():
                for col_name in columns:
                    logger.error(f"Missing column: {table_name}.{col_name}")
            
            # Fix schema issues if requested
            if fix:
                logger.info("Attempting to fix schema issues...")
                fix_schema_issues(db.engine, differences, expected_schema)
                return verify_db_schema(fix=False)  # Verify again after fixes
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying database schema: {str(e)}")
            return False

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Verify database schema against SQLAlchemy models")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix schema issues")
    args = parser.parse_args()
    
    # Run verification
    success = verify_db_schema(fix=args.fix)
    sys.exit(0 if success else 1) 