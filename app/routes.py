import os
import uuid
import json
from datetime import datetime
from io import BytesIO
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, abort, jsonify, current_app
from app.database import db
from app.database.models import User, Trip, Recommendation, Activity, TripSubscription
from app.services.ai_service import AIService

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/create-trip', methods=['POST'])
def create_trip():
    destination = request.form.get('destination')
    
    if not destination:
        flash('Please enter a destination', 'error')
        return redirect(url_for('main.index'))
    
    # Store destination in session for the next step
    session['temp_destination'] = destination
    
    # Redirect to the user info page
    return redirect(url_for('main.user_info'))

@main.route('/user-info')
def user_info():
    # Check if we have a destination in the session
    destination = session.get('temp_destination')
    if not destination:
        flash('Please start by entering your destination', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('user_info.html', destination=destination)

@main.route('/complete-trip', methods=['POST'])
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
        return redirect(url_for('main.user_info'))
    
    if not email:
        flash('Please enter your email address', 'error')
        return redirect(url_for('main.user_info'))
    
    # Look up user by email
    user = User.query.filter_by(email=email).first()
    
    # If user exists and has a name that doesn't match, redirect to name resolution
    if user and user.name and user.name != name:
        session['temp_destination'] = destination
        session['temp_email'] = email
        session['temp_name'] = name
        return redirect(url_for('main.name_resolution'))
    
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
    
    return redirect(url_for('main.view_trip', slug=trip.slug))

@main.route('/name-resolution')
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
        return redirect(url_for('main.complete_trip'))
    
    previous_name = user.name
    
    return render_template(
        'name_resolution.html',
        destination=destination,
        email=email,
        previous_name=previous_name,
        new_name=new_name
    )

@main.route('/resolve-name', methods=['POST'])
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
        return redirect(url_for('main.name_resolution'))
    
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
    return redirect(url_for('main.view_trip', slug=trip.slug))

@main.route('/trip/<slug>')
def view_trip(slug):
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    config = {'GOOGLE_MAPS_API_KEY': os.environ.get('GOOGLE_MAPS_API_KEY', '')}
    return render_template('trip.html', trip=trip, config=config)

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
    
    if not recommender_name:
        flash('Please provide your name', 'error')
        return redirect(url_for('main.process_recommendation', slug=slug))
    
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
    return redirect(url_for('main.thank_you_page', slug=trip.slug))

@main.route('/trip/<slug>/thank-you')
def thank_you_page(slug):
    """
    Thank you page for recommendation submissions
    """
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    return render_template('thank_you.html', trip=trip)

@main.route('/trip/<slug>/save-email', methods=['POST'])
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
        return redirect(url_for('main.thank_you_page', slug=slug))
    
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

@main.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Endpoint to handle audio transcription and process it into recommendations
    """
    print("=== TRANSCRIBE API CALLED ===")
    
    if 'audio' not in request.files:
        print("ERROR: No audio file provided in request")
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['audio']
    destination = request.form.get('destination', '')
    
    print(f"Received audio file: {audio_file.filename}, content type: {audio_file.content_type}, size: {request.content_length} bytes")
    print(f"Destination: {destination}")
    
    if not destination:
        print("ERROR: No destination provided")
        return jsonify({"error": "No destination provided"}), 400
    
    if audio_file.filename == '':
        print("ERROR: No selected file (empty filename)")
        return jsonify({"error": "No selected file"}), 400
    
    try:
        # Read audio data directly
        audio_data = audio_file.read()
        print(f"Read {len(audio_data)} bytes from audio file")
        
        if len(audio_data) == 0:
            print("ERROR: Audio data is empty (0 bytes)")
            return jsonify({"error": "Audio file is empty"}), 400
        
        # Get API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: OpenAI API key not configured")
            return jsonify({"error": "API key not configured"}), 500
        
        print(f"Using OpenAI API key starting with: {api_key[:8]}...")
        
        # Use OpenAI Whisper API for transcription
        import requests
        from io import BytesIO
        
        # Create in-memory file-like object
        audio_file_object = BytesIO(audio_data)
        audio_file_object.name = audio_file.filename  # Set name for content type detection
        
        print("Sending request to OpenAI Whisper API (directly from memory)...")
        
        # Send the request with the in-memory file
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (audio_file.filename, audio_file_object, audio_file.content_type)},
            data={"model": "whisper-1"}
        )
        
        print(f"OpenAI API response status code: {response.status_code}")
        if response.status_code != 200:
            print(f"ERROR: OpenAI API returned non-200 status: {response.status_code}")
            print(f"Response content: {response.text}")
            return jsonify({"error": f"OpenAI API error: {response.text}"}), 500
        
        response_data = response.json()
        print(f"OpenAI API response data: {response_data}")
        
        transcription = response_data.get("text", "")
        
        if not transcription:
            print("ERROR: No transcription text in response")
            return jsonify({"error": "Failed to transcribe audio"}), 500
        
        print(f"Successfully transcribed text: '{transcription[:100]}...' (truncated)")
        print(f"Full transcription: {transcription}")
        
        # Process the transcription to extract recommendations
        print("Extracting recommendations from transcription...")
        try:
            extracted_recommendations = AIService.extract_recommendations(transcription, destination)
            print(f"Extracted {len(extracted_recommendations)} recommendations")
            
            # Log the actual recommendations for debugging
            print(f"Recommendation details: {json.dumps(extracted_recommendations, indent=2)}")
            
            if not extracted_recommendations or len(extracted_recommendations) == 0:
                print("WARNING: No recommendations were extracted from the transcription")
                return jsonify({
                    "status": "success",
                    "recommendations": [],
                    "transcription": transcription
                }), 200
            
            response = jsonify({
                "status": "success",
                "recommendations": extracted_recommendations,
                "transcription": transcription
            })
            print("response:")
            print(response)
            
            return response, 200
            
        except Exception as extract_error:
            print(f"ERROR during recommendation extraction: {str(extract_error)}")
            import traceback
            print(f"Extraction error traceback: {traceback.format_exc()}")
            
            # Return the transcription even if recommendation extraction failed
            return jsonify({
                "status": "partial_success",
                "error": f"Transcription succeeded but recommendation extraction failed: {str(extract_error)}",
                "transcription": transcription,
                "recommendations": []
            }), 200
    
    except Exception as e:
        import traceback
        print(f"ERROR: Exception in transcribe_audio: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({"error": str(e)}), 500

@main.route('/trip/<slug>/process-audio', methods=['POST'])
def process_audio_recommendation(slug):
    """
    Endpoint to process pre-extracted recommendations from audio
    """
    # Generate request ID for tracking this request
    request_id = f"req-{datetime.now().strftime('%H%M%S%f')}"
    print(f"=== PROCESS AUDIO API CALLED [{request_id}] for trip {slug} ===")
    
    # Log session information
    session_id = id(session)
    print(f"Session object ID: {session_id}")
    print(f"Session dictionary: {dict(session)}")
    
    # Log request details
    print(f"Request cookies: {request.cookies}")
    print(f"User agent: {request.headers.get('User-Agent')}")
    print(f"Content-Type: {request.headers.get('Content-Type')}")
    print(f"Request method: {request.method}")
    print(f"Request body type: {type(request.get_data())}")
    print(f"Request body size: {len(request.get_data())} bytes")
    
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    
    try:
        # Get the pre-extracted recommendations from the request body
        data = request.json
        print(f"Parsed JSON data type: {type(data)}")
        
        if not data:
            print("ERROR: No data in request.json")
            print(f"Raw request data: {request.get_data()[:200]}...")
            return jsonify({"error": "No data received in request"}), 400
        
        if not isinstance(data, list):
            print(f"ERROR: Data is not a list, it's a {type(data)}")
            print(f"Data content: {data}")
            return jsonify({"error": "Invalid recommendations data format - expected list"}), 400
        
        # Log the data for debugging
        print(f"Storing {len(data)} recommendations in session: {data}")
        
        # Debug the current session state
        print(f"Session before: {dict(session)}")
        
        # Store in session for the confirmation page
        session['extracted_recommendations'] = data
        
        # Add diagnostic test value
        session['test_value'] = f'test-{request_id}'
        session['timestamp'] = datetime.now().isoformat()
        
        # Make sure session is modified
        session.modified = True
        
        # Check if the data was actually stored
        print(f"Session after: {dict(session)}")
        print(f"Verification - extracted_recommendations in session: {'extracted_recommendations' in session}")
        print(f"Verification - test_value in session: {session.get('test_value')}")
        
        # Prepare a fallback - encode the first recommendation in query params (simplified)
        fallback_data = None
        if data and len(data) > 0:
            # Create a simplified version with just the first recommendation
            first_rec = data[0]
            fallback_data = {
                'name': first_rec.get('name', ''),
                'type': first_rec.get('type', ''),
                'desc': first_rec.get('description', '')[:200],  # Truncate long descriptions
                'request_id': request_id  # Add request ID for tracking
            }
        
        # Return URL to redirect to
        redirect_url = url_for('main.confirm_audio_recommendations', slug=slug)
        
        # Add fallback query param with encoded data
        if fallback_data:
            import json
            import base64
            encoded_data = base64.urlsafe_b64encode(json.dumps(fallback_data).encode()).decode()
            redirect_url = f"{redirect_url}?fb={encoded_data}"
        
        print(f"Redirect URL: {redirect_url}")
        
        # Force session save
        from flask import get_flashed_messages
        get_flashed_messages()  # This forces a session save
        
        # Log response details
        from flask import make_response
        response = jsonify({
            "status": "success",
            "redirect_url": redirect_url,
            "request_id": request_id
        })
        
        # Add diagnostic information to response
        response.headers['X-Request-ID'] = request_id
        print(f"Response headers: {response.headers}")
        
        return response, 200
        
    except Exception as e:
        import traceback
        print(f"ERROR in process_audio_recommendation: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        print(f"Request headers: {dict(request.headers)}")
        
        return jsonify({"error": str(e)}), 500

@main.route('/trip/<slug>/confirm-audio', methods=['GET'])
def confirm_audio_recommendations(slug):
    """
    Show confirmation page for audio recommendations
    """
    # Generate request ID for tracking
    request_id = f"conf-{datetime.now().strftime('%H%M%S%f')}"
    print(f"=== CONFIRM AUDIO RECOMMENDATIONS CALLED [{request_id}] for trip {slug} ===")
    
    # Log session information
    session_id = id(session)
    print(f"Session object ID: {session_id}")
    print(f"Session dictionary: {dict(session)}")
    
    # Check test value from previous request
    test_value = session.get('test_value', 'NOT FOUND')
    timestamp = session.get('timestamp', 'NO TIMESTAMP')
    print(f"Test value in session: {test_value}")
    print(f"Timestamp from previous request: {timestamp}")
    
    if timestamp != 'NO TIMESTAMP':
        try:
            prev_time = datetime.fromisoformat(timestamp)
            time_diff = datetime.now() - prev_time
            print(f"Time difference between requests: {time_diff.total_seconds()} seconds")
        except Exception as e:
            print(f"Error calculating time difference: {e}")
    
    # Log request details
    print(f"Request cookies: {request.cookies}")
    print(f"User agent: {request.headers.get('User-Agent')}")
    print(f"Request args: {dict(request.args)}")
    
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    print(f"Trip found: {trip.id} - {trip.destination}")
    
    # Get recommendations from session
    extracted_recommendations = session.get('extracted_recommendations', [])
    
    # Log for debugging
    print(f"Retrieved from session: {type(extracted_recommendations)}")
    print(f"Recommendations count: {len(extracted_recommendations) if extracted_recommendations else 0}")
    if extracted_recommendations and len(extracted_recommendations) > 0:
        print(f"First recommendation: {extracted_recommendations[0]}")
    
    # Check if we need to use fallback data from query parameter
    fallback_param = request.args.get('fb')
    if (not extracted_recommendations or not isinstance(extracted_recommendations, list) or len(extracted_recommendations) == 0) and fallback_param:
        print(f"Using fallback data from query parameter")
        try:
            # Decode the fallback data
            import json
            import base64
            fallback_data = json.loads(base64.urlsafe_b64decode(fallback_param).decode())
            print(f"Decoded fallback data: {fallback_data}")
            
            # Check if request_id is in fallback data for correlation
            fallback_req_id = fallback_data.get('request_id', 'NO_ID')
            print(f"Fallback request ID: {fallback_req_id}")
            
            # Create a recommendation from fallback data
            extracted_recommendations = [{
                'name': fallback_data.get('name', 'Recommendation from recording'),
                'type': fallback_data.get('type', ''),
                'website_url': '',
                'description': fallback_data.get('desc', '')
            }]
            print(f"Created recommendation from fallback: {extracted_recommendations[0]}")
        except Exception as e:
            import traceback
            print(f"Error decoding fallback data: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            print(f"Raw fallback parameter: {fallback_param}")
    
    # Check if it's still empty after fallback attempt
    if not extracted_recommendations or not isinstance(extracted_recommendations, list) or len(extracted_recommendations) == 0:
        print("No recommendations found in session or fallback!")
        flash('No recommendations found. Please try again.', 'error')
        return redirect(url_for('main.add_recommendation', slug=slug))
    
    print(f"About to render template with {len(extracted_recommendations)} recommendations")
    
    # Clear from session to avoid persistence issues
    session.pop('extracted_recommendations', None)
    
    # Keep test values for debugging
    # session.pop('test_value', None)
    # session.pop('timestamp', None)
    
    # Render the same template as text recommendations
    return render_template(
        'confirm_recommendations.html', 
        trip=trip, 
        extracted_recommendations=extracted_recommendations,
        recommender_name=''
    )

@main.route('/trip/<slug>/audio-error', methods=['GET'])
def audio_error(slug):
    """Handle audio processing errors with flash messages"""
    error_message = request.args.get('message', 'There was an error processing your audio. Please try again or use text input instead.')
    flash(error_message, 'error')
    return '', 204  # Return no content with 204 status code

@main.route('/how-it-works')
def how_it_works():
    """How it works page explaining the recommendation system"""
    return render_template('how_it_works.html')

@main.route('/test-session')
def test_session():
    """
    Test route for verifying session functionality
    """
    # Create a unique test value
    test_id = f"sess-test-{datetime.now().strftime('%H%M%S%f')}"
    
    # Store in session
    old_value = session.get('session_test', 'No previous value')
    session['session_test'] = test_id
    
    # Make sure session is modified
    session.modified = True
    
    # Log session details
    print(f"=== TEST SESSION ROUTE CALLED ===")
    print(f"Session ID: {id(session)}")
    print(f"Setting session_test to: {test_id}")
    print(f"Previous value was: {old_value}")
    print(f"Current session: {dict(session)}")
    
    # Force session save
    from flask import get_flashed_messages
    get_flashed_messages()
    
    # Render a page with links to verify
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Session Test</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .box {{ border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 5px; }}
            .success {{ color: green; }}
            .error {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>Session Test</h1>
        
        <div class="box">
            <h2>Current Session Data</h2>
            <p><strong>Test ID:</strong> {test_id}</p>
            <p><strong>Previous value:</strong> {old_value}</p>
            <p><strong>Session object ID:</strong> {id(session)}</p>
        </div>
        
        <div class="box">
            <h2>Test Session Persistence</h2>
            <p>Click the links below to test if session data persists:</p>
            
            <ul>
                <li><a href="/verify-session">Verify Session (Same tab)</a></li>
                <li><a href="/verify-session" target="_blank">Verify Session (New tab)</a></li>
                <li><a href="javascript:fetch('/verify-session-ajax').then(r=>r.json()).then(data=>alert('Session test: ' + (data.success ? 'SUCCESS' : 'FAILED') + '\\n\\nStored: {test_id}\\nRetrieved: ' + data.value))">Verify Session (AJAX)</a></li>
            </ul>
        </div>
        
        <div class="box">
            <h2>Test Redirect with Session</h2>
            <p>Test if session persists across redirects:</p>
            
            <ul>
                <li><a href="/test-session-redirect">Test Redirect (Same tab)</a></li>
                <li><a href="/test-session-redirect" target="_blank">Test Redirect (New tab)</a></li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    return html

@main.route('/verify-session')
def verify_session():
    """Verify the session value from test-session route"""
    session_test = session.get('session_test', 'NOT FOUND')
    
    print(f"=== VERIFY SESSION ROUTE CALLED ===")
    print(f"Session ID: {id(session)}")
    print(f"Retrieved session_test: {session_test}")
    print(f"Current session: {dict(session)}")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Session Verification</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .box {{ border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 5px; }}
            .success {{ color: green; font-weight: bold; }}
            .error {{ color: red; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Session Verification</h1>
        
        <div class="box">
            <h2>Session Test Results</h2>
            <p><strong>Session Test Value:</strong> <span class="{'' if session_test != 'NOT FOUND' else 'error'}">{session_test}</span></p>
            <p><strong>Session ID:</strong> {id(session)}</p>
            <p class="{'' if session_test != 'NOT FOUND' else 'error'}">
                {'' if session_test != 'NOT FOUND' else '⚠️ SESSION TEST FAILED - Value not found!'}
            </p>
            <p class="{'' if session_test == 'NOT FOUND' else 'success'}">
                {'' if session_test == 'NOT FOUND' else '✅ SESSION TEST PASSED - Value found!'}
            </p>
        </div>
        
        <div class="box">
            <p><a href="/test-session">← Back to Test Session</a></p>
        </div>
    </body>
    </html>
    """
    
    return html

@main.route('/verify-session-ajax')
def verify_session_ajax():
    """Verify the session value via AJAX"""
    session_test = session.get('session_test', 'NOT FOUND')
    
    print(f"=== VERIFY SESSION AJAX ROUTE CALLED ===")
    print(f"Session ID: {id(session)}")
    print(f"Retrieved session_test: {session_test}")
    print(f"Current session: {dict(session)}")
    
    return jsonify({
        'success': session_test != 'NOT FOUND',
        'value': session_test
    })

@main.route('/test-session-redirect')
def test_session_redirect():
    """Set a session value and redirect to test persistence through redirects"""
    # Create a unique test value
    test_id = f"redirect-test-{datetime.now().strftime('%H%M%S%f')}"
    
    # Store in session
    session['redirect_test'] = test_id
    session.modified = True
    
    print(f"=== TEST SESSION REDIRECT ROUTE CALLED ===")
    print(f"Session ID: {id(session)}")
    print(f"Setting redirect_test to: {test_id}")
    print(f"Current session: {dict(session)}")
    
    # Force session save
    from flask import get_flashed_messages
    get_flashed_messages()
    
    # Redirect to verification page
    return redirect(url_for('main.verify_session_redirect'))

@main.route('/verify-session-redirect')
def verify_session_redirect():
    """Verify the session after redirect"""
    redirect_test = session.get('redirect_test', 'NOT FOUND')
    
    print(f"=== VERIFY SESSION REDIRECT ROUTE CALLED ===")
    print(f"Session ID: {id(session)}")
    print(f"Retrieved redirect_test: {redirect_test}")
    print(f"Current session: {dict(session)}")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Redirect Session Test</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .box {{ border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 5px; }}
            .success {{ color: green; font-weight: bold; }}
            .error {{ color: red; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Redirect Session Test</h1>
        
        <div class="box">
            <h2>Session After Redirect</h2>
            <p><strong>Redirect Test Value:</strong> <span class="{'' if redirect_test != 'NOT FOUND' else 'error'}">{redirect_test}</span></p>
            <p><strong>Session ID:</strong> {id(session)}</p>
            <p class="{'' if redirect_test != 'NOT FOUND' else 'error'}">
                {'' if redirect_test != 'NOT FOUND' else '⚠️ REDIRECT TEST FAILED - Value not found after redirect!'}
            </p>
            <p class="{'' if redirect_test == 'NOT FOUND' else 'success'}">
                {'' if redirect_test == 'NOT FOUND' else '✅ REDIRECT TEST PASSED - Value persisted through redirect!'}
            </p>
        </div>
        
        <div class="box">
            <p><a href="/test-session">← Back to Test Session</a></p>
        </div>
    </body>
    </html>
    """
    
    return html

@main.route('/test-fallback/<slug>')
def test_fallback(slug):
    """
    Test route that creates a direct link to the confirmation page with a fallback parameter
    """
    trip = Trip.query.filter_by(slug=slug).first_or_404()
    
    # Create a test recommendation
    fallback_data = {
        'name': 'Test Recommendation (Direct Fallback)',
        'type': 'Test',
        'desc': 'This is a test recommendation created directly with the fallback mechanism to verify it works correctly.',
        'request_id': f"direct-test-{datetime.now().strftime('%H%M%S%f')}"
    }
    
    # Encode as fallback parameter
    import json
    import base64
    encoded_data = base64.urlsafe_b64encode(json.dumps(fallback_data).encode()).decode()
    
    # Create the redirect URL
    redirect_url = url_for('main.confirm_audio_recommendations', slug=slug, fb=encoded_data)
    
    # Log what we're doing
    print(f"=== TEST FALLBACK ROUTE CALLED for trip {slug} ===")
    print(f"Created fallback data: {fallback_data}")
    print(f"Encoded as: {encoded_data[:30]}...")
    print(f"Redirect URL: {redirect_url}")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Fallback Mechanism</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .box {{ border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 5px; }}
            pre {{ background: #f5f5f5; padding: 10px; overflow: auto; }}
        </style>
    </head>
    <body>
        <h1>Test Fallback Mechanism</h1>
        
        <div class="box">
            <h2>Test Information</h2>
            <p><strong>Trip:</strong> {trip.destination} for {trip.traveler_name}</p>
            <p><strong>Trip Slug:</strong> {slug}</p>
            <p><strong>Test ID:</strong> {fallback_data['request_id']}</p>
        </div>
        
        <div class="box">
            <h2>Fallback Data</h2>
            <pre>{json.dumps(fallback_data, indent=2)}</pre>
        </div>
        
        <div class="box">
            <h2>Test the Fallback</h2>
            <p>Click the links below to test if the fallback mechanism works:</p>
            
            <ul>
                <li><a href="{redirect_url}">Test Fallback (Same tab)</a></li>
                <li><a href="{redirect_url}" target="_blank">Test Fallback (New tab)</a></li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    return html 