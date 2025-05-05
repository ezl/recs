import os
import sys
import pytest
import tempfile
from flask import Flask

# Add parent directory to path so that app imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import db as _db

@pytest.fixture
def app():
    """Create a Flask application for testing."""
    # Set up configuration for testing
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
    })
    
    with app.app_context():
        _db.create_all()
        
    yield app
    
    with app.app_context():
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def db(app):
    """Provide the database object for testing."""
    with app.app_context():
        yield _db 