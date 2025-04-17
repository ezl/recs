import os
from pathlib import Path

basedir = Path(__file__).parent

class Config:
    """Base config."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_please_change')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///' + str(basedir / 'dev.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevConfig(Config):
    """Development config."""
    DEBUG = True
    TESTING = False

class TestConfig(Config):
    """Testing config."""
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(basedir / 'test.db')

class ProdConfig(Config):
    """Production config."""
    DEBUG = False
    TESTING = False 