import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, abort, jsonify
from app.database import db
from app.database.models import User, Trip
from app.services.ai_service import AIService

trip_bp = Blueprint('trip', __name__, url_prefix='/trip')

@trip_bp.route('/<slug>')
def view_trip(slug):
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    config = {'GOOGLE_MAPS_API_KEY': os.environ.get('GOOGLE_MAPS_API_KEY', '')}
    return render_template('trip.html', trip=trip, config=config)

@trip_bp.route('/<slug>/thank-you')
def thank_you_page(slug):
    """
    Thank you page for recommendation submissions
    """
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    return render_template('thank_you.html', trip=trip)

# Legacy route to handle old share_token links
@trip_bp.route('/<token>', endpoint='recommendation_request')
def recommendation_request(token):
    trip = Trip.query.filter_by(share_token=token).first_or_404()
    return redirect(url_for('trip.view_trip', slug=trip.slug)) 