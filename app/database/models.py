from datetime import datetime
from app.database import db
import re
from slugify import slugify

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=True)
    password = db.Column(db.String(128), nullable=True)  # Make password nullable since we're using passwordless auth
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)
    
    posts = db.relationship('Post', backref='author', lazy=True)
    auth_tokens = db.relationship('AuthToken', backref='user', lazy=True, cascade='all, delete-orphan')
    trips = db.relationship('Trip', backref='user', lazy=True)
    recommendations = db.relationship('Recommendation', backref='author', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    @classmethod
    def get_or_create(cls, email):
        """Get an existing user or create a new one if not exists"""
        user = cls.query.filter_by(email=email).first()
        if not user:
            user = cls(email=email)
            db.session.add(user)
            db.session.commit()
        return user

class AuthToken(db.Model):
    __tablename__ = 'auth_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<AuthToken {self.token[:8]}...>'
    
    @property
    def is_expired(self):
        """Check if the token has expired"""
        return datetime.utcnow() > self.expires_at
    
    @classmethod
    def get_valid_token(cls, token_string):
        """Get a valid token by string"""
        token = cls.query.filter_by(token=token_string, used=False).first()
        if token and not token.is_expired:
            return token
        return None

class Post(db.Model):
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=True)
    published = db.Column(db.Boolean, default=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Post {self.title}>'

class Trip(db.Model):
    __tablename__ = 'trips'
    
    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.String(255), nullable=False)
    traveler_name = db.Column(db.String(100), nullable=True)
    share_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    recommendations = db.relationship('Recommendation', backref='trip', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Trip {self.destination}>'
    
    @staticmethod
    def generate_slug(destination, traveler_name, created_at=None):
        """Generate a URL-friendly slug for the trip"""
        if not created_at:
            created_at = datetime.utcnow()
            
        # Get month and year
        month = created_at.strftime('%b').lower()
        year = created_at.strftime('%Y')
        
        # Create base slug
        base_slug = f"{destination.lower()}-{month}-{year}"
        
        # Slugify to handle special characters and spaces
        return slugify(base_slug)

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)  # Changed to nullable=True
    place_type = db.Column(db.String(50), nullable=True)
    website_url = db.Column(db.String(255), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Recommendation {self.name}>' 