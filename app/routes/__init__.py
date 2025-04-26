from flask import Blueprint
from .trip_routes import trip_bp
from .recommendation_routes import recommendation_bp
from .user_routes import user_bp
from .audio_routes import audio_bp
from .misc_routes import misc_bp
from .testing_routes import testing_bp
from .admin_routes import admin_bp

def init_app(app):
    """Initialize all route blueprints with the app"""
    app.register_blueprint(misc_bp)  # Register main routes with no prefix
    app.register_blueprint(trip_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(audio_bp)
    app.register_blueprint(admin_bp)
    
    # Only register testing routes in development mode
    if app.config.get('FLASK_ENV') != 'production':
        app.register_blueprint(testing_bp) 