import json
import base64
from datetime import datetime
from flask import Blueprint, jsonify, render_template, redirect, url_for, request, session, get_flashed_messages
from app.database.models import Trip

testing_bp = Blueprint('testing', __name__)

@testing_bp.route('/test-session')
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

@testing_bp.route('/verify-session')
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

@testing_bp.route('/verify-session-ajax')
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

@testing_bp.route('/test-session-redirect')
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
    get_flashed_messages()
    
    # Redirect to verification page
    return redirect(url_for('testing.verify_session_redirect'))

@testing_bp.route('/verify-session-redirect')
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

@testing_bp.route('/test-fallback/<slug>')
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
    encoded_data = base64.urlsafe_b64encode(json.dumps(fallback_data).encode()).decode()
    
    # Create the redirect URL
    redirect_url = url_for('audio.confirm_audio_recommendations', slug=slug, fb=encoded_data)
    
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