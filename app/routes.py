from flask import Blueprint, render_template
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.context_processor
def inject_now():
    return {'now': datetime.now()} 