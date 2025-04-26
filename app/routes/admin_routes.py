from flask import Blueprint, render_template
from app.database.models import Trip, Activity, Recommendation, User
from sqlalchemy import func
from app.database import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
def admin_dashboard():
    """Simple admin dashboard for debugging database entries"""
    # Get all data from the database
    trips = Trip.query.all()
    activities = Activity.query.all()
    recommendations = Recommendation.query.all()
    users = User.query.all()
    
    # Get recommendation counts for each activity
    recommendation_counts = {}
    activity_recommendation_counts = db.session.query(
        Recommendation.activity_id, 
        func.count(Recommendation.id).label('count')
    ).group_by(Recommendation.activity_id).all()
    
    for activity_id, count in activity_recommendation_counts:
        recommendation_counts[activity_id] = count
    
    return render_template(
        'admin/dashboard.html', 
        trips=trips,
        activities=activities,
        recommendations=recommendations,
        users=users,
        recommendation_counts=recommendation_counts
    ) 