import os
from pathlib import Path

basedir = Path(__file__).parent
instance_dir = basedir / 'instance'

# Create instance directory if it doesn't exist
if not instance_dir.exists():
    instance_dir.mkdir()

class Config:
    """Base config."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_please_change')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///' + str(instance_dir / 'sqlite3.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration
    MAIL_FROM_EMAIL = os.environ.get('MAIL_FROM_EMAIL', 'noreply@example.com')
    MAIL_FROM_NAME = os.environ.get('MAIL_FROM_NAME', 'Recs App')
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
    
    # URL configuration
    PREFERRED_URL_SCHEME = 'http'

class DevConfig(Config):
    """Development config."""
    DEBUG = True
    TESTING = False
    # Use sqlite3.db in development too
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(instance_dir / 'sqlite3.db')

class TestConfig(Config):
    """Testing config."""
    DEBUG = False
    TESTING = True
    # Use a separate database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(instance_dir / 'test.db')

class ProdConfig(Config):
    """Production config."""
    DEBUG = False
    TESTING = False
    # Static file configuration for production
    PREFERRED_URL_SCHEME = 'https' 