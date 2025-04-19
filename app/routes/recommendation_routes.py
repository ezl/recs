import uuid
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from app.database import db
from app.database.models import User, Trip, Recommendation, Activity, TripSubscription
from app.services.ai_service import AIService

recommendation_bp = Blueprint('recommendation', __name__)

@recommendation_bp.route('/trip/<slug>/add', methods=['GET'])
def add_recommendation(slug):
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    return render_template('add_recommendation.html', trip=trip)

@recommendation_bp.route('/trip/<slug>/process', methods=['POST'])
def process_recommendation(slug):
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    
    # Get unstructured recommendations from form
    unstructured_recommendations = request.form.get('unstructured_recommendations', '')
    recommender_name = request.form.get('recommender_name', '')
    
    if not unstructured_recommendations:
        flash('Please provide some recommendations', 'error')
        return redirect(url_for('recommendation.add_recommendation', slug=slug))
    
    try:
        # Call OpenAI API to extract structured recommendations
        extracted_recommendations = AIService.extract_recommendations(unstructured_recommendations, trip.destination)
        
        # If no recommendations were extracted, still show the confirmation page with the empty state
        if not extracted_recommendations or len(extracted_recommendations) == 0:
            return render_template(
                'confirm_recommendations.html', 
                trip=trip, 
                extracted_recommendations=[],
                recommender_name=recommender_name
            )
        
        # Render confirmation template with extracted recommendations
        return render_template(
            'confirm_recommendations.html', 
            trip=trip, 
            extracted_recommendations=extracted_recommendations,
            recommender_name=recommender_name
        )
    except ValueError as e:
        flash(f'API Configuration Error: {str(e)}', 'error')
        return redirect(url_for('recommendation.add_recommendation', slug=slug))
    except Exception as e:
        flash(f'Error processing recommendations: {str(e)}', 'error')
        return redirect(url_for('recommendation.add_recommendation', slug=slug))

@recommendation_bp.route('/trip/<slug>/save', methods=['POST'])
def save_recommendations(slug):
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    
    recommendations = request.form.getlist('recommendations[]')
    descriptions = request.form.getlist('descriptions[]')
    place_types = request.form.getlist('place_types[]')
    website_urls = request.form.getlist('website_urls[]')
    recommender_name = request.form.get('recommender_name')
    
    if not recommendations or len(recommendations) == 0:
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
        else:
            anon_user = User.query.filter_by(email='anonymous@example.com').first()
            if not anon_user:
                anon_user = User(email='anonymous@example.com', name='Anonymous User')
                db.session.add(anon_user)
                db.session.commit()
            user_id = anon_user.id
    
    # Create recommendations
    for i in range(len(recommendations)):
        if not recommendations[i]:  # Skip empty recommendations
            continue
            
        # First find or create the Activity
        activity = Activity.get_or_create(
            name=recommendations[i],
            category=place_types[i] if i < len(place_types) and place_types[i] else None,
            website_url=website_urls[i] if i < len(website_urls) and website_urls[i] else None
        )
        
        # Then create the Recommendation which links this Activity to the Trip
        recommendation = Recommendation(
            activity_id=activity.id,
            description=descriptions[i] if i < len(descriptions) and descriptions[i] else None,
            author_id=user_id,
            trip_id=trip.id
        )
        
        db.session.add(recommendation)
    
    db.session.commit()
    
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