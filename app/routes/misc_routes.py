import os
from flask import Blueprint, render_template
from datetime import datetime

misc_bp = Blueprint('main', __name__)

@misc_bp.route('/')
def index():
    return render_template('index.html')

@misc_bp.route('/how-it-works/')
def how_it_works():
    """How it works page explaining the recommendation system"""
    return render_template('how_it_works.html')

@misc_bp.context_processor
def inject_now():
    return {'now': datetime.now()} 