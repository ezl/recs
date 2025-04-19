import uuid
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app.database import db
from app.database.models import User, Trip
from app.services.ai_service import AIService

user_bp = Blueprint('user', __name__)

@user_bp.route('/create-trip', methods=['POST'])
def create_trip():
    destination = request.form.get('destination')
    
    if not destination:
        flash('Please enter a destination', 'error')
        return redirect(url_for('main.index'))
    
    # Store destination in session for the next step
    session['temp_destination'] = destination
    
    # Redirect to the user info page
    return redirect(url_for('user.user_info'))

@user_bp.route('/user-info')
def user_info():
    # Check if we have a destination in the session
    destination = session.get('temp_destination')
    if not destination:
        flash('Please start by entering your destination', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('user_info.html', destination=destination)

@user_bp.route('/complete-trip', methods=['POST'])
def complete_trip():
    # Get form data
    destination = request.form.get('destination')
    name = request.form.get('name')
    email = request.form.get('email')
    
    # Validate input
    if not destination:
        flash('Please enter a destination', 'error')
        return redirect(url_for('main.index'))
    
    if not name:
        flash('Please enter your name', 'error')
        return redirect(url_for('user.user_info'))
    
    if not email:
        flash('Please enter your email address', 'error')
        return redirect(url_for('user.user_info'))
    
    # Look up user by email
    user = User.query.filter_by(email=email).first()
    
    # If user exists and has a name that doesn't match, redirect to name resolution
    if user and user.name and user.name != name:
        session['temp_destination'] = destination
        session['temp_email'] = email
        session['temp_name'] = name
        return redirect(url_for('user.name_resolution'))
    
    # If user doesn't exist or name matches, proceed with trip creation
    if not user:
        # Create new user
        user = User(email=email, name=name)
        db.session.add(user)
        db.session.commit()
    elif not user.name:
        # Update name if it was null
        user.name = name
        db.session.commit()
    
    # Generate a unique share token
    share_token = str(uuid.uuid4())[:8]
    
    # Generate slug
    slug = Trip.generate_slug(destination, name)
    
    # Check if slug already exists and modify if needed
    base_slug = slug
    counter = 1
    while Trip.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Get destination information from OpenAI
    try:
        destinations = AIService.get_destination_suggestions(destination)
        main_destination = destinations[0] if destinations else None
    except Exception as e:
        # Log the error but continue with trip creation
        print(f"Error getting destination suggestions: {str(e)}")
        main_destination = None
    
    # Create trip
    trip = Trip(
        destination=destination,
        traveler_name=name,
        share_token=share_token,
        slug=slug,
        user_id=user.id
    )
    
    # Add destination information if available
    if main_destination:
        trip.destination_info = destinations
        trip.destination_display_name = main_destination.get('name')
        trip.destination_country = main_destination.get('country')
    
    db.session.add(trip)
    db.session.commit()
    
    return redirect(url_for('trip.view_trip', slug=trip.slug))

@user_bp.route('/name-resolution')
def name_resolution():
    # Check if we have the necessary information in the session
    destination = session.get('temp_destination')
    email = session.get('temp_email')
    new_name = session.get('temp_name')
    
    if not destination or not email or not new_name:
        flash('Please start by entering your destination', 'error')
        return redirect(url_for('main.index'))
    
    # Get the existing user
    user = User.query.filter_by(email=email).first()
    if not user:
        # If user doesn't exist, just create a new trip
        return redirect(url_for('user.complete_trip'))
    
    previous_name = user.name
    
    return render_template(
        'name_resolution.html',
        destination=destination,
        email=email,
        previous_name=previous_name,
        new_name=new_name
    )

@user_bp.route('/resolve-name', methods=['POST'])
def resolve_name():
    """Handle the name resolution form submission."""
    # Log form data for debugging
    print("Received form data:", request.form.to_dict())
    
    # Get form data
    destination = request.form.get('destination')
    email = request.form.get('email')
    resolved_name = request.form.get('resolved_name')
    
    # If "other" option was selected, use the value from other_name field
    if resolved_name == 'other':
        other_name = request.form.get('other_name')
        if other_name and other_name.strip():
            resolved_name = other_name
    
    # Validate input
    if not destination or not email or not resolved_name:
        print(f"Missing required data: destination={destination}, email={email}, resolved_name={resolved_name}")
        flash('Please provide all required information', 'error')
        return redirect(url_for('user.name_resolution'))
    
    # Get the user
    user = User.query.filter_by(email=email).first()
    if not user:
        # If user doesn't exist (unlikely at this point), create one
        user = User(email=email, name=resolved_name)
        db.session.add(user)
        print(f"Created new user with email={email}, name={resolved_name}")
    else:
        # Update the user's name with the resolved name
        print(f"Updating user name from '{user.name}' to '{resolved_name}'")
        user.name = resolved_name
    
    db.session.commit()
    
    # Generate a unique share token
    share_token = str(uuid.uuid4())[:8]
    
    # Generate slug
    slug = Trip.generate_slug(destination, resolved_name)
    
    # Check if slug already exists and modify if needed
    base_slug = slug
    counter = 1
    while Trip.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Get destination information from OpenAI
    try:
        destinations = AIService.get_destination_suggestions(destination)
        main_destination = destinations[0] if destinations else None
    except Exception as e:
        # Log the error but continue with trip creation
        print(f"Error getting destination suggestions: {str(e)}")
        main_destination = None
    
    # Create trip
    trip = Trip(
        destination=destination,
        traveler_name=resolved_name,
        share_token=share_token,
        slug=slug,
        user_id=user.id
    )
    
    # Add destination information if available
    if main_destination:
        trip.destination_info = destinations
        trip.destination_display_name = main_destination.get('name')
        trip.destination_country = main_destination.get('country')
    
    db.session.add(trip)
    db.session.commit()
    print(f"Created trip with slug={slug}, destination={destination}, user_id={user.id}")
    
    # Clean up session variables
    for key in ['temp_destination', 'temp_email', 'temp_name']:
        if key in session:
            session.pop(key)
    
    print(f"Redirecting to trip page: /trip/{slug}")
    return redirect(url_for('trip.view_trip', slug=trip.slug))

@user_bp.route('/my-trips')
def my_trips():
    # Check if user is logged in
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login', next=url_for('user.my_trips')))
    
    trips = Trip.query.filter_by(user_id=user_id).order_by(Trip.created_at.desc()).all()
    return render_template('my_trips.html', trips=trips) 