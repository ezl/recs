import uuid
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from app.database import db
from app.database.models import User, Trip, Recommendation, Activity, TripSubscription
from app.services.ai_service import AIService
import logging

logger = logging.getLogger(__name__)

recommendation_bp = Blueprint('recommendation', __name__)

@recommendation_bp.route('/trip/<slug>/add', methods=['GET'])
def add_recommendation(slug):
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    return render_template('add_recommendation.html', trip=trip)

@recommendation_bp.route('/trip/<slug>/process', methods=['POST'])
def process_recommendation(slug):
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    
    # Collect recommendations from the form
    try:
        recommendations = []
        for i in range(10):  # Support up to 10 recommendations
            name = request.form.get(f'recommendation_{i}')
            if name and name.strip():  # Only include non-empty recommendations
                place_type = request.form.get(f'place_type_{i}', '')
                website = request.form.get(f'website_url_{i}', '')
                description = request.form.get(f'description_{i}', '')
                
                recommendations.append({
                    'name': name.strip(),
                    'type': place_type.strip() if place_type else '',
                    'website_url': website.strip() if website else '',
                    'description': description.strip() if description else ''
                })
        
        recommender_name = request.form.get('recommender_name', '').strip()
        
        # If no recommendations, redirect back
        if not recommendations:
            flash('Please add at least one recommendation', 'error')
            return redirect(url_for('recommendation.add_recommendation', slug=slug))
            
        return render_template(
            'process_recommendation.html',
            trip=trip,
            recommendations=recommendations,
            recommender_name=recommender_name
        )
    except Exception as e:
        logger.error(f"Error processing recommendations for trip {slug}: {str(e)}")
        flash(f'Error processing recommendations: {str(e)}', 'error')
        return redirect(url_for('recommendation.add_recommendation', slug=slug))

@recommendation_bp.route('/trip/<slug>/save', methods=['POST'])
def save_recommendations(slug):
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    logger.info(f"Saving recommendations for trip {slug} to {trip.destination}")
    
    recommendations = request.form.getlist('recommendations[]')
    descriptions = request.form.getlist('descriptions[]')
    place_types = request.form.getlist('place_types[]')
    website_urls = request.form.getlist('website_urls[]')
    recommender_name = request.form.get('recommender_name')
    
    logger.info(f"Received {len(recommendations)} recommendations for trip {slug}")
    
    # Filter out completely empty recommendations
    # Valid if: name is filled (description is optional)
    valid_indices = []
    for i, rec in enumerate(recommendations):
        if rec.strip():  # If recommendation name is not empty (description can be empty)
            valid_indices.append(i)
    
    logger.info(f"Found {len(valid_indices)} valid recommendations after filtering")
    
    # If no valid recommendations after filtering, redirect
    if not valid_indices:
        flash('Please add at least one recommendation', 'error')
        return redirect(url_for('recommendation.add_recommendation', slug=slug))
    
    if not recommender_name:
        flash('Please provide your name', 'error')
        return redirect(url_for('recommendation.process_recommendation', slug=slug))
    
    # Check if user is logged in
    user_id = session.get('user_id')
    
    # If not logged in, use the anonymous user or create temporary user
    if not user_id:
        # If the recommender provided a name, create a temporary user with that name
        if recommender_name:
            temp_email = f"temp_{uuid.uuid4().hex[:8]}@example.com"
            temp_user = User(email=temp_email, name=recommender_name)
            db.session.add(temp_user)
            db.session.commit()
            user_id = temp_user.id
            logger.info(f"Created temporary user '{recommender_name}' with ID {user_id}")
        else:
            anon_user = User.query.filter_by(email='anonymous@example.com').first()
            if not anon_user:
                anon_user = User(email='anonymous@example.com', name='Anonymous User')
                db.session.add(anon_user)
                db.session.commit()
                logger.info("Created anonymous user")
            user_id = anon_user.id
            logger.info(f"Using anonymous user with ID {user_id}")
    
    # Get destination context for better Google Places API matching
    destination_context = {}
    if trip.destination_display_name:
        destination_context['search_vicinity'] = trip.destination_display_name
    if trip.destination_country:
        destination_context['destination_country'] = trip.destination_country
    
    logger.info(f"Using destination context: {destination_context}")
    
    # Create recommendations - only for valid indices
    created_recommendations = []
    for i in valid_indices:
        rec_name = recommendations[i]
        logger.info(f"Processing recommendation: {rec_name}")
        
        # First find or create the Activity
        activity = Activity.get_or_create(
            name=rec_name,
            category=place_types[i] if i < len(place_types) and place_types[i] else None,
            website_url=website_urls[i] if i < len(website_urls) and website_urls[i] else None,
            **destination_context  # Pass destination context to improve Google Places matching
        )
        
        logger.info(f"Activity for '{rec_name}': ID={activity.id}, place_id={activity.google_place_id or 'None'}")
        
        # Then create the Recommendation which links this Activity to the Trip
        recommendation = Recommendation(
            activity_id=activity.id,
            description=descriptions[i] if i < len(descriptions) and descriptions[i] else None,
            author_id=user_id,
            trip_id=trip.id
        )
        
        db.session.add(recommendation)
        created_recommendations.append(recommendation)
    
    db.session.commit()
    logger.info(f"Saved {len(created_recommendations)} recommendations for trip {slug}")
    
    # Redirect to thank you page
    return redirect(url_for('trip.thank_you_page', slug=trip.slug))

@recommendation_bp.route('/trip/<slug>/save-email', methods=['POST'])
def save_recommender_email(slug):
    """
    Save email address of recommender who wants to be notified
    """
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    email = request.form.get('email')
    
    if not email:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": False, "error": "Please provide an email address"}), 400
        flash('Please provide an email address', 'error')
        return redirect(url_for('trip.thank_you_page', slug=slug))
    
    # Get or create user with this email
    user, _ = User.get_or_create(email)
    
    # Check if this user is already subscribed to this trip
    existing = TripSubscription.query.filter_by(trip_id=trip.id, user_id=user.id).first()
    if not existing:
        # Create new subscription
        subscription = TripSubscription(
            trip_id=trip.id,
            user_id=user.id
        )
        db.session.add(subscription)
        db.session.commit()
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            "success": True,
            "message": "Thank you! We'll notify you when all recommendations are in."
        })
    
    # For regular form submissions
    flash('Thank you! We\'ll notify you when all recommendations are in.', 'success')
    return redirect(url_for('trip.view_trip', slug=slug)) 