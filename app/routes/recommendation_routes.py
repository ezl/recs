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
    
    # Get unstructured recommendations from the form
    unstructured_text = request.form.get('unstructured_recommendations', '').strip()
    
    if not unstructured_text:
        flash('Please add at least one recommendation', 'error')
        return redirect(url_for('recommendation.add_recommendation', slug=slug))
    
    try:
        # Use AI service to extract structured recommendations
        recommendations = AIService.extract_recommendations(unstructured_text, trip.destination)
        
        # If no recommendations were extracted, redirect back
        if not recommendations:
            flash('We couldn\'t identify any recommendations in your text. Please try again.', 'error')
            return redirect(url_for('recommendation.add_recommendation', slug=slug))
            
        return render_template(
            'confirm_recommendations.html',
            trip=trip,
            extracted_recommendations=recommendations,
            recommender_name=request.form.get('recommender_name', '').strip(),
            trip_mode=session.get('trip_mode', 'request_mode')
        )
    except Exception as e:
        logger.error(f"Error processing recommendations: {str(e)}")
        flash('There was an error processing your recommendations. Please try again.', 'error')
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
    
    # Check if user is logged in and get trip_mode
    user_id = session.get('user_id')
    trip_mode = session.get('trip_mode', 'request_mode')
    
    # In create_mode, if no recommender_name but user is logged in, we can use the user's name
    if trip_mode == 'create_mode' and user_id and not recommender_name:
        user = User.query.get(user_id)
        if user and user.name:
            recommender_name = user.name
            logger.info(f"Using authenticated user's name '{recommender_name}' for create_mode")
    
    # For request_mode, we still require a recommender name
    if not recommender_name:
        flash('Please provide your name', 'error')
        return redirect(url_for('recommendation.process_recommendation', slug=slug))
    
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
    
    # Different redirect based on trip mode
    if trip_mode == 'create_mode':
        # For guide creators, redirect directly to trip view with success message
        flash(f'Awesome! We saved those recommendations to your guide for {trip.destination}.', 'success')
        return redirect(url_for('trip.view_trip', slug=trip.slug))
    else:
        # For regular recommenders, redirect to thank you page
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