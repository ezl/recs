from flask import Blueprint, render_template, request, redirect, url_for

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        # In a real application, you would validate the email
        # and authenticate the user here
        
        # Just redirect to dashboard for now
        return redirect(url_for('auth.dashboard'))
    
    return render_template('auth/login.html')

@auth.route('/dashboard')
def dashboard():
    return render_template('auth/dashboard.html') 