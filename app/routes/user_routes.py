import uuid
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app.database import db
from app.database.models import User, Trip
from app.services.ai_service import AIService
from datetime import datetime
from flask import current_app

user_bp = Blueprint('user', __name__)

@user_bp.route('/create-trip', methods=['POST'])
def create_trip():
    destination = request.form.get('destination')
    
    # Log for debugging
    print(f"create_trip received destination='{destination}'")
    
    if not destination:
        flash('Please enter a destination', 'error')
        return redirect(url_for('main.index'))
    
    # Store destination in session for the next step
    # Do not clear all session data as it might affect other functionality
    session['temp_destination'] = destination
    session.modified = True  # Ensure session is saved
    
    print(f"create_trip set session temp_destination='{session.get('temp_destination')}'")
    
    # Redirect to the user info page
    return redirect(url_for('user.user_info'))

@user_bp.route('/user-info')
def user_info():
    # Check if we have a destination in the session
    destination = session.get('temp_destination')
    
    # Debug log for session state
    print(f"user_info: session contains temp_destination='{destination}'")
    
    if not destination:
        flash('Please start by entering your destination', 'error')
        return redirect(url_for('main.index'))
    
    # Ensure the destination stays in the session by refreshing it
    # This prevents session expiration issues
    session['temp_destination'] = destination
    
    return render_template('user_info.html', destination=destination)

@user_bp.route('/complete-trip', methods=['POST'])
def complete_trip():
    # Get form data
    destination = request.form.get('destination')
    name = request.form.get('name')
    email = request.form.get('email')
    
    # Log the request for debugging
    print(f"complete_trip received: destination='{destination}', name='{name}', email='{email}'")
    print(f"session contains: temp_destination='{session.get('temp_destination')}'")
    
    # If destination is missing from form, try to get it from session
    if not destination:
        destination = session.get('temp_destination')
        print(f"Falling back to session destination: '{destination}'")
    
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
    
    # SCENARIO A: If user doesn't exist, create and auto-authenticate
    if not user:
        # Create new user
        user = User(email=email, name=name)
        db.session.add(user)
        db.session.commit()
        
        # Automatically authenticate the new user
        session['user_id'] = user.id
        session['user_email'] = user.email
        
        # Update last login time
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        
        print(f"New user created and auto-authenticated: {user.id}")
        
    # SCENARIO B: If user exists and name matches, redirect to auth with auto-triggered email
    elif user.name and user.name == name:
        print(f"Existing user with matching name: {user.id}")
        
        # Generate a trip before redirecting to auth
        trip = create_trip_for_user(user, destination, name)
        
        # Generate auth token and send email
        from app.auth import generate_auth_token, send_auth_email
        token_string, user = generate_auth_token(email)
        send_auth_email(email, token_string)
        
        # Redirect to check email page with next parameter for redirect after auth
        template_args = {
            'email': email, 
            'message': 'For security, we need to verify it\'s you since this email is already registered.'
        }
        
        # Store the next URL in the session
        session['auth_next'] = url_for('trip.view_trip', slug=trip.slug)
        
        # Only include the auth_link in debug mode (and not using real emails)
        if current_app.debug and not current_app.config.get('FORCE_REAL_EMAILS', False):
            auth_link = url_for('auth.verify_token', token=token_string, _external=True)
            template_args['auth_link'] = auth_link
            
        return render_template('auth/check_email.html', **template_args)
    
    # Update name if it was null (should be rare but handled for completeness)
    elif not user.name:
        user.name = name
        db.session.commit()
        
        # Automatically authenticate the user
        session['user_id'] = user.id
        session['user_email'] = user.email
        
        # Update last login time
        user.last_login_at = datetime.utcnow()
        db.session.commit()
    
    # Create trip
    trip = create_trip_for_user(user, destination, name)
    
    # Clean up session data that's no longer needed
    for key in ['temp_destination', 'temp_email', 'temp_name']:
        if key in session:
            session.pop(key)
    
    return redirect(url_for('trip.view_trip', slug=trip.slug))

def create_trip_for_user(user, destination, traveler_name):
    """Helper function to create a trip for a user"""
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
        traveler_name=traveler_name,
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
    
    return trip

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
        
        # Automatically authenticate the new user (SCENARIO A)
        session['user_id'] = user.id
        session['user_email'] = user.email
        
        # Update last login time
        user.last_login_at = datetime.utcnow()
        db.session.commit()
    else:
        # Update the user's name with the resolved name
        print(f"Updating user name from '{user.name}' to '{resolved_name}'")
        user.name = resolved_name
        db.session.commit()
        
        # SCENARIO C: After name resolution, redirect to auth with auto-triggered email
        print(f"Redirecting to auth after name resolution for user: {user.id}")
        
        # Generate a trip before redirecting to auth
        trip = create_trip_for_user(user, destination, resolved_name)
        
        # Generate auth token and send email
        from app.auth import generate_auth_token, send_auth_email
        token_string, user = generate_auth_token(email)
        send_auth_email(email, token_string)
        
        # Redirect to check email page
        template_args = {
            'email': email,
            'message': 'Thanks for confirming your name. For security, we need to verify your identity since this email is already registered.'
        }
        
        # Store the next URL in the session
        session['auth_next'] = url_for('trip.view_trip', slug=trip.slug)
        
        # Only include the auth_link in debug mode (and not using real emails)
        if current_app.debug and not current_app.config.get('FORCE_REAL_EMAILS', False):
            auth_link = url_for('auth.verify_token', token=token_string, _external=True)
            template_args['auth_link'] = auth_link
            
        # Clean up session data
        for key in ['temp_destination', 'temp_email', 'temp_name']:
            if key in session:
                session.pop(key)
                
        return render_template('auth/check_email.html', **template_args)
    
    # Create trip - only reached if we created a new user
    trip = create_trip_for_user(user, destination, resolved_name)
    
    # Clean up session variables
    for key in ['temp_destination', 'temp_email', 'temp_name']:
        if key in session:
            session.pop(key)
    
    print(f"Created trip with slug={trip.slug}, destination={destination}, user_id={user.id}")
    
    return redirect(url_for('trip.view_trip', slug=trip.slug))

@user_bp.route('/my-trips')
def my_trips():
    # Check if user is logged in
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login', next=url_for('user.my_trips')))
    
    trips = Trip.query.filter_by(user_id=user_id).order_by(Trip.created_at.desc()).all()
    return render_template('my_trips.html', trips=trips) 