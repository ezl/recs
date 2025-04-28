from flask import Flask
import atexit
from datetime import datetime, timedelta
import os
import logging
from logging.handlers import RotatingFileHandler
import sys

def create_app():
    # Setup logging first so we can capture initialization logs
    setup_logging()
    
    app = Flask(__name__)
    
    # Load configuration based on environment
    flask_env = os.environ.get('FLASK_ENV', 'development')
    if flask_env == 'testing':
        app.config.from_object('config.TestConfig')
        print("🧪 Using TestConfig for testing environment")
    elif flask_env == 'production':
        app.config.from_object('config.ProdConfig')
    else:
        app.config.from_object('config.DevConfig')
    
    # Explicitly set FLASK_ENV in app config so it's accessible in templates
    app.config['FLASK_ENV'] = flask_env
    
    # Ensure secret key is set for sessions
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = 'dev-key-please-change-in-production'
    
    # Set longer session lifetime
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
    
    # Initialize database
    from app.database import init_db
    init_db(app)
    
    # Import models to ensure they're registered with SQLAlchemy
    from app.database.models import User, Post, AuthToken, Trip, Recommendation, Activity
    
    # Register CLI commands
    from app.cli import init_app as init_cli
    init_cli(app)
    
    # Register route blueprints
    from app.routes import init_app as init_routes
    init_routes(app)
    
    # Register auth blueprint
    from app.auth import auth
    app.register_blueprint(auth)
    
    # Add context processor for template variables
    from datetime import datetime
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}
    
    # Setup token cleanup on app shutdown
    from app.database import db
    from app.database.models import AuthToken
    
    def cleanup_expired_tokens():
        """Remove expired auth tokens on app shutdown"""
        with app.app_context():
            try:
                tokens = AuthToken.query.filter(AuthToken.expires_at < datetime.now()).all()
                if tokens:
                    for token in tokens:
                        db.session.delete(token)
                    db.session.commit()
                    print(f"Cleaned up {len(tokens)} expired tokens")
            except Exception as e:
                print(f"Error cleaning up tokens: {e}")
    
    atexit.register(cleanup_expired_tokens)
    
    # Log application startup
    app.logger.info("Application started")
    
    return app

def setup_logging():
    """Configure logging for the application"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Set up formatter
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )
    
    # Set up console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Set up file handler for general logs
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=1024 * 1024 * 10,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Set up file handler for Google Places API logs
    places_file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'google_places.log'),
        maxBytes=1024 * 1024 * 5,  # 5 MB
        backupCount=3
    )
    places_file_handler.setFormatter(formatter)
    places_file_handler.setLevel(logging.DEBUG)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Configure specific module loggers
    google_places_logger = logging.getLogger('app.services.google_places_service')
    google_places_logger.setLevel(logging.DEBUG)
    google_places_logger.addHandler(places_file_handler)
    
    activity_model_logger = logging.getLogger('app.database.models')
    activity_model_logger.setLevel(logging.DEBUG)
    activity_model_logger.addHandler(places_file_handler)
    
    rec_routes_logger = logging.getLogger('app.routes.recommendation_routes')
    rec_routes_logger.setLevel(logging.DEBUG)
    
    # Also log SQLAlchemy operations at INFO level in dev environment
    if os.environ.get('FLASK_ENV') != 'production':
        sql_logger = logging.getLogger('sqlalchemy.engine')
        sql_logger.setLevel(logging.WARNING)  # WARNING to reduce noise, INFO for all queries 