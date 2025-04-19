# This file is maintained for backwards compatibility
# Routes have been refactored into the routes/ directory

# Import all blueprints
from flask import Blueprint
from app.routes.misc_routes import misc_bp
from app.routes.trip_routes import trip_bp 
from app.routes.recommendation_routes import recommendation_bp
from app.routes.user_routes import user_bp
from app.routes.audio_routes import audio_bp
from app.routes.testing_routes import testing_bp

# Re-export main blueprint for compatibility with existing imports
main = misc_bp

# Define a list of all routes for compatibility
all_routes = [misc_bp, trip_bp, recommendation_bp, user_bp, audio_bp, testing_bp]

# New code should import directly from the appropriate module 