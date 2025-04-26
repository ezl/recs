from flask import Blueprint, render_template
from app.database.models import Trip, Activity, Recommendation, User

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
def admin_dashboard():
    """Simple admin dashboard for debugging database entries"""
    # Get all data from the database
    trips = Trip.query.all()
    activities = Activity.query.all()
    recommendations = Recommendation.query.all()
    users = User.query.all()
    
    return render_template(
        'admin/dashboard.html', 
        trips=trips,
        activities=activities,
        recommendations=recommendations,
        users=users
    ) 