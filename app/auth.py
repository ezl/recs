from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, session
import secrets
import time
from datetime import datetime, timedelta

auth = Blueprint('auth', __name__, url_prefix='/auth')

# Store for auth tokens: {token: {'email': email, 'expires': timestamp}}
auth_tokens = {}

def generate_auth_token(email):
    """Generate a secure token for passwordless auth"""
    token = secrets.token_urlsafe(32)
    # Token expires in 10 minutes
    expiry = datetime.now() + timedelta(minutes=10)
    
    # Store token with email and expiry
    auth_tokens[token] = {
        'email': email,
        'expires': expiry
    }
    
    return token

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

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Email is required')
            return render_template('auth/login.html')
        
        # Generate token and "send" auth email
        token = generate_auth_token(email)
        send_auth_email(email, token)
        
        # Redirect to waiting page
        return render_template('auth/check_email.html', email=email)
    
    return render_template('auth/login.html')

@auth.route('/verify/<token>')
def verify_token(token):
    # Check if token exists and is valid
    if token not in auth_tokens:
        flash('Invalid or expired login link')
        return redirect(url_for('auth.login'))
    
    # Check if token is expired
    token_data = auth_tokens[token]
    if datetime.now() > token_data['expires']:
        # Remove expired token
        auth_tokens.pop(token)
        flash('Login link has expired')
        return redirect(url_for('auth.login'))
    
    # Token is valid - log the user in
    email = token_data['email']
    
    # Remove used token
    auth_tokens.pop(token)
    
    # For now, just store email in session
    session['user_email'] = email
    flash('You have been logged in successfully', 'success')
    
    # Redirect to dashboard
    return redirect(url_for('auth.dashboard'))

@auth.route('/dashboard')
def dashboard():
    # Check if user is logged in
    if 'user_email' not in session:
        flash('Please log in to access the dashboard', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/dashboard.html', user_email=session['user_email'])

@auth.route('/logout')
def logout():
    # Clear the session
    session.pop('user_email', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('auth.login')) 