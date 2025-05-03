from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, session
import secrets
from datetime import datetime, timedelta
import requests
from app.database import db
from app.database.models import User, AuthToken
import logging

# Temporary toggle to enable real email sending in dev mode
FORCE_REAL_EMAILS = False

auth = Blueprint('auth', __name__, url_prefix='/auth')

def generate_auth_token(email):
    """Generate a secure token for passwordless auth and store in database"""
    # Get or create the user
    user, _ = User.get_or_create(email)
    
    # Generate a secure token
    token_string = secrets.token_urlsafe(32)
    
    # Create expiry time (10 minutes from now)
    expiry = datetime.utcnow() + timedelta(minutes=10)
    
    # Create token in database
    token = AuthToken(
        token=token_string,
        user_id=user.id,
        expires_at=expiry
    )
    db.session.add(token)
    db.session.commit()
    
    return token_string, user

def send_auth_email(email, token):
    """Send authentication email with login link"""
    auth_link = url_for('auth.verify_token', token=token, _external=True)
    
    # In debug mode, just print to console (unless FORCE_REAL_EMAILS is True)
    if current_app.debug and not FORCE_REAL_EMAILS:
        print("\n----- DEBUG: PASSWORDLESS LOGIN -----")
        print(f"Email would be sent to: {email}")
        print(f"Auth link: {auth_link}")
        print("---------------------------------------\n")
    else:
        # Use Resend to send actual emails
        try:
            from_email = current_app.config.get('MAIL_FROM_EMAIL')
            from_name = current_app.config.get('MAIL_FROM_NAME')
            api_key = current_app.config.get('RESEND_API_KEY')
            
            if not api_key:
                current_app.logger.error("Resend API key is not configured")
                if current_app.debug:
                    print("\n----- ERROR: RESEND API KEY NOT CONFIGURED -----")
                    print(f"Auth link: {auth_link}")
                    print("-----------------------------------------------\n")
                return auth_link
                
            # Define email content
            subject = "Your Login Link"
            html_content = f"""
            <div>
                <h1>Welcome to Recs!</h1>
                <p>Click the button below to log in:</p>
                <div>
                    <a href="{auth_link}" style="display: inline-block; background-color: #4F46E5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                        Log in to Recs
                    </a>
                </div>
                <p>Or copy and paste this link in your browser:</p>
                <p>{auth_link}</p>
                <p>This link will expire in 10 minutes.</p>
            </div>
            """
            
            # Prepare the payload for Resend API
            payload = {
                "from": f"{from_name} <{from_email}>",
                "to": [email],
                "subject": subject,
                "html": html_content
            }
            
            # Make the API request to Resend
            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                print(f"Authentication email sent to {email}")
                current_app.logger.info(f"Authentication email sent to {email}")
            else:
                error_msg = f"Failed to send email: {response.text}"
                print(f"\n----- ERROR: {error_msg} -----\n")
                current_app.logger.error(error_msg)
                
                # In debug mode, also print the link for convenience
                if current_app.debug:
                    print(f"Auth link: {auth_link}")
                
        except Exception as e:
            error_msg = f"Error sending email: {str(e)}"
            print(f"\n----- ERROR: {error_msg} -----\n")
            current_app.logger.error(error_msg)
            
            # In debug mode, also print the link for convenience
            if current_app.debug:
                print(f"Auth link: {auth_link}")
    
    return auth_link

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Email is required')
            return render_template('auth/login.html')
        
        # Generate token and "send" auth email
        token, user = generate_auth_token(email)
        auth_link = send_auth_email(email, token)
        
        # Redirect to waiting page
        template_args = {'email': email}
        
        # Only include the auth_link in debug mode (and not using real emails)
        if current_app.debug and not FORCE_REAL_EMAILS:
            template_args['auth_link'] = auth_link
            
        return render_template('auth/check_email.html', **template_args)
    
    return render_template('auth/login.html')

@auth.route('/verify/<token>')
def verify_token(token):
    logger = logging.getLogger(__name__)
    
    logger.info(f"=================== VERIFY TOKEN ROUTE CALLED ===================")
    logger.info(f"Token: {token[:10]}...")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Session data before processing: {dict(session)}")
    logger.info(f"Current trip_mode: '{session.get('trip_mode', 'NOT SET')}'")
    
    # Get token from database
    db_token = AuthToken.get_valid_token(token)
    
    if not db_token:
        logger.warning(f"Invalid or expired login token: {token[:10]}...")
        flash('Invalid or expired login link', 'error')
        return redirect(url_for('auth.login'))
    
    # Token is valid - log the user in
    user = db_token.user
    logger.info(f"Valid token for user: {user.id} ({user.email})")
    
    # Mark token as used
    db_token.used = True
    
    # Update last login time
    user.last_login_at = datetime.utcnow()
    db.session.commit()
    
    # Store user ID in session
    session['user_id'] = user.id
    session['user_email'] = user.email
    
    # Make sure we preserve trip_mode if it exists
    trip_mode = session.get('trip_mode')
    if trip_mode:
        logger.info(f"Preserving trip_mode '{trip_mode}' after authentication")
        # Explicitly set it again to ensure it's not lost
        session['trip_mode'] = trip_mode
        session.modified = True
    
    logger.info(f"Session data after authentication: {dict(session)}")
    
    flash('You have been logged in successfully', 'success')
    
    # Check if we have a next URL to redirect to
    next_url = session.pop('auth_next', None)
    logger.info(f"Next URL after authentication: {next_url}")
    logger.info(f"trip_mode after popping auth_next: '{session.get('trip_mode', 'NOT SET')}'")
    
    if next_url:
        logger.info(f"Redirecting to next_url: {next_url}")
        return redirect(next_url)
    
    logger.info(f"No next_url, redirecting to my_trips")
    return redirect(url_for('user.my_trips'))

@auth.route('/logout')
def logout():
    # Clear the session
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('auth.login')) 