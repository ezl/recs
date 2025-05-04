import os
import json
import base64
import requests
import traceback
from datetime import datetime
from io import BytesIO
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from app.database import db
from app.database.models import Trip
from app.services.ai_service import AIService

audio_bp = Blueprint('audio', __name__)

@audio_bp.route('/api/transcribe/', methods=['POST'])
def transcribe_audio():
    """
    Endpoint to handle audio transcription
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
        
        # Return just the transcription - recommendations will be handled by the same flow as text input
        return jsonify({
            "status": "success",
            "transcription": transcription
        }), 200
    
    except Exception as e:
        import traceback
        print(f"ERROR: Exception in transcribe_audio: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({"error": str(e)}), 500

@audio_bp.route('/trip/<slug>/process-audio', methods=['POST'])
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
        # Get data from either JSON or form data
        data = None
        
        # Check if coming from form data (new approach)
        if 'recommendations_data' in request.form:
            print("Getting recommendations from form data")
            try:
                form_data = request.form.get('recommendations_data', '')
                data = json.loads(form_data)
                print(f"Successfully parsed recommendations from form data, type: {type(data)}")
            except Exception as form_error:
                print(f"Error parsing form data: {str(form_error)}")
                print(f"Raw form data: {request.form.get('recommendations_data', '')[:200]}...")
                return redirect(url_for('recommendation.add_recommendation', slug=slug, error="Invalid audio data"))
        else:
            # Fallback to JSON parsing (original approach)
            try:
                data = request.json
                print(f"Parsed JSON data type: {type(data)}")
            except Exception as json_error:
                print(f"ERROR parsing JSON: {str(json_error)}")
                print(f"Raw request data: {request.get_data().decode('utf-8', errors='replace')[:500]}...")
                return redirect(url_for('recommendation.add_recommendation', slug=slug, error="Invalid JSON data"))
        
        # Log a sample of the data (truncated for logs)
        if data:
            data_sample = str(data)[:500] + "..." if len(str(data)) > 500 else str(data)
            print(f"Received data sample: {data_sample}")
        
        if not data:
            print("ERROR: No data received")
            flash('No recommendation data received', 'error')
            return redirect(url_for('recommendation.add_recommendation', slug=slug))
        
        if not isinstance(data, list):
            print(f"ERROR: Data is not a list, it's a {type(data)}")
            print(f"Data content: {data}")
            
            # Try to handle if data is a string representation of a list
            if isinstance(data, str) and data.startswith('[') and data.endswith(']'):
                try:
                    import json
                    data = json.loads(data)
                    print("Successfully converted string to list")
                except Exception as e:
                    print(f"Failed to convert string to list: {str(e)}")
                    flash('Invalid recommendation data format', 'error')
                    return redirect(url_for('recommendation.add_recommendation', slug=slug))
            else:
                flash('Invalid recommendation data format', 'error')
                return redirect(url_for('recommendation.add_recommendation', slug=slug))
        
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
        
        # Get URL to redirect to
        redirect_url = url_for('audio.confirm_audio_recommendations', slug=slug)
        
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
        
        # Return a redirect response instead of JSON
        print(f"=== REDIRECTING TO: {redirect_url} ===")
        return redirect(redirect_url)
        
    except Exception as e:
        import traceback
        print(f"ERROR in process_audio_recommendation: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        flash('Error processing audio recommendations', 'error')
        return redirect(url_for('recommendation.add_recommendation', slug=slug))

@audio_bp.route('/trip/<slug>/confirm-audio', methods=['GET'])
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
    print(f"Fallback parameter present: {bool(fallback_param)}")
    
    if (not extracted_recommendations or not isinstance(extracted_recommendations, list) or len(extracted_recommendations) == 0) and fallback_param:
        print(f"Using fallback data from query parameter")
        try:
            # Decode the fallback data
            import json
            import base64
            
            # Handle URL-safe decoding
            padded_fb = fallback_param + '=' * (4 - len(fallback_param) % 4)
            
            try:
                decoded_data = base64.urlsafe_b64decode(padded_fb).decode()
                print(f"Decoded fallback data (raw): {decoded_data[:200]}...")
                fallback_data = json.loads(decoded_data)
                print(f"Parsed fallback data: {fallback_data}")
            except Exception as decode_error:
                print(f"Error decoding with padding: {str(decode_error)}")
                # Try without padding as a fallback
                try:
                    decoded_data = base64.urlsafe_b64decode(fallback_param).decode()
                    fallback_data = json.loads(decoded_data)
                    print(f"Decoded without padding: {fallback_data}")
                except Exception as e:
                    print(f"Error decoding without padding: {str(e)}")
                    raise
            
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
        return redirect(url_for('recommendation.add_recommendation', slug=slug))
    
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

@audio_bp.route('/trip/<slug>/audio-error', methods=['GET'])
def audio_error(slug):
    """Handle audio processing errors with flash messages"""
    error_message = request.args.get('message', 'There was an error processing your audio. Please try again or use text input instead.')
    flash(error_message, 'error')
    return '', 204  # Return no content with 204 status code 