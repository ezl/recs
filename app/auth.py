from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, session
import secrets
from datetime import datetime, timedelta
from app.database import db
from app.database.models import User, AuthToken

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
    
    # In debug mode, just print to console
    if current_app.debug:
        print("\n----- DEBUG: PASSWORDLESS LOGIN -----")
        print(f"Email would be sent to: {email}")
        print(f"Auth link: {auth_link}")
        print("---------------------------------------\n")
    else:
        # TODO: Implement actual email sending here
        # This would use a service like SendGrid, SMTP, etc.
        pass
    
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
        
        # Only include the auth_link in debug mode
        if current_app.debug:
            template_args['auth_link'] = auth_link
            
        return render_template('auth/check_email.html', **template_args)
    
    return render_template('auth/login.html')

@auth.route('/verify/<token>')
def verify_token(token):
    # Get token from database
    db_token = AuthToken.get_valid_token(token)
    
    if not db_token:
        flash('Invalid or expired login link', 'error')
        return redirect(url_for('auth.login'))
    
    # Token is valid - log the user in
    user = db_token.user
    
    # Mark token as used
    db_token.used = True
    
    # Update last login time
    user.last_login_at = datetime.utcnow()
    db.session.commit()
    
    # Store user ID in session
    session['user_id'] = user.id
    session['user_email'] = user.email
    
    flash('You have been logged in successfully', 'success')
    return redirect(url_for('auth.dashboard'))

@auth.route('/dashboard')
def dashboard():
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please log in to access the dashboard', 'error')
        return redirect(url_for('auth.login'))
    
    # Get user from database
    user = User.query.get(session['user_id'])
    if not user:
        # User was deleted or doesn't exist anymore
        session.clear()
        flash('User account not found', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/dashboard.html', user=user)

@auth.route('/logout')
def logout():
    # Clear the session
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('auth.login')) 