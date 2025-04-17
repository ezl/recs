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
    
    # Register auth blueprint
    from app.auth import auth
    app.register_blueprint(auth)
    
    # Add context processor for template variables
    from datetime import datetime
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}
    
    return app 