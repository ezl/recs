from flask import Blueprint, render_template, redirect, url_for, request, flash, session, abort, jsonify
from datetime import datetime
import uuid
import os
from app.database import db
from app.database.models import User, Trip, Recommendation
from app.services.ai_service import AIService

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/create-trip', methods=['POST'])
def create_trip():
    destination = request.form.get('destination')
    traveler_name = request.form.get('name')
    
    if not destination:
        flash('Please enter a destination', 'error')
        return redirect(url_for('main.index'))
    
    if not traveler_name:
        flash('Please enter your name', 'error')
        return redirect(url_for('main.index'))
    
    # Generate a unique share token
    share_token = str(uuid.uuid4())[:8]
    
    # Generate slug
    slug = Trip.generate_slug(destination, traveler_name)
    
    # Check if slug already exists and modify if needed
    base_slug = slug
    counter = 1
    while Trip.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Check if user is logged in
    user_id = session.get('user_id')
    
    # If not logged in, create or get the anonymous user
    if not user_id:
        anon_user = User.query.filter_by(email='anonymous@example.com').first()
        if not anon_user:
            anon_user = User(email='anonymous@example.com', name='Anonymous User')
            db.session.add(anon_user)
            db.session.commit()
        user_id = anon_user.id
    
    # Create trip
    trip = Trip(
        destination=destination,
        traveler_name=traveler_name,
        share_token=share_token,
        slug=slug,
        user_id=user_id
    )
    
    db.session.add(trip)
    db.session.commit()
    
    return redirect(url_for('main.view_trip', slug=trip.slug))

@main.route('/trip/<slug>')
def view_trip(slug):
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    return render_template('trip.html', trip=trip)

@main.route('/trip/<slug>/add', methods=['GET'])
def add_recommendation(slug):
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    return render_template('add_recommendation.html', trip=trip)

@main.route('/trip/<slug>/process', methods=['POST'])
def process_recommendation(slug):
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    
    # Get unstructured recommendations from form
    unstructured_recommendations = request.form.get('unstructured_recommendations', '')
    recommender_name = request.form.get('recommender_name', '')
    
    if not unstructured_recommendations:
        flash('Please provide some recommendations', 'error')
        return redirect(url_for('main.add_recommendation', slug=slug))
    
    try:
        # Call OpenAI API to extract structured recommendations
        extracted_recommendations = AIService.extract_recommendations(unstructured_recommendations, trip.destination)
        
        # Render confirmation template with extracted recommendations
        return render_template(
            'confirm_recommendations.html', 
            trip=trip, 
            extracted_recommendations=extracted_recommendations,
            recommender_name=recommender_name
        )
    except ValueError as e:
        flash(f'API Configuration Error: {str(e)}', 'error')
        return redirect(url_for('main.add_recommendation', slug=slug))
    except Exception as e:
        flash(f'Error processing recommendations: {str(e)}', 'error')
        return redirect(url_for('main.add_recommendation', slug=slug))

@main.route('/trip/<slug>/save', methods=['POST'])
def save_recommendations(slug):
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    
    recommendations = request.form.getlist('recommendations[]')
    descriptions = request.form.getlist('descriptions[]')
    place_types = request.form.getlist('place_types[]')
    website_urls = request.form.getlist('website_urls[]')
    recommender_name = request.form.get('recommender_name')
    
    if not recommendations or len(recommendations) == 0:
        flash('Please add at least one recommendation', 'error')
        return redirect(url_for('main.add_recommendation', slug=slug))
    
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
            
        recommendation = Recommendation(
            name=recommendations[i],
            description=descriptions[i] if i < len(descriptions) and descriptions[i] else None,
            place_type=place_types[i] if i < len(place_types) and place_types[i] else None,
            website_url=website_urls[i] if i < len(website_urls) and website_urls[i] else None,
            author_id=user_id,
            trip_id=trip.id
        )
        
        db.session.add(recommendation)
    
    db.session.commit()
    
    flash('Thank you for your recommendations!', 'success')
    return redirect(url_for('main.view_trip', slug=slug))

# Legacy route to handle old share_token links
@main.route('/recommendations/<token>')
def recommendation_request(token):
    trip = Trip.query.filter_by(share_token=token).first_or_404()
    return redirect(url_for('main.view_trip', slug=trip.slug))

@main.route('/my-trips')
def my_trips():
    # Check if user is logged in
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login', next=url_for('main.my_trips')))
    
    trips = Trip.query.filter_by(user_id=user_id).order_by(Trip.created_at.desc()).all()
    return render_template('my_trips.html', trips=trips)

@main.context_processor
def inject_now():
    return {'now': datetime.now()} 