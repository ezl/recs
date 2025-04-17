from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('config.Config')
    
    # Initialize database
    from app.database import init_db
    init_db(app)
    
    # Import models to ensure they're registered with SQLAlchemy
    from app.database.models import User, Post
    
    # Register CLI commands
    from app.cli import init_app as init_cli
    init_cli(app)
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    return app 