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
    trip_subscriptions = db.relationship('TripSubscription', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    @classmethod
    def get_or_create(cls, email, name=None):
        """
        Get an existing user or create a new one if not exists.
        If name is provided and user exists without a name, update the name.
        
        Args:
            email: User's email address
            name: Optional name to set or update
            
        Returns:
            User object and a boolean indicating if the user was created
        """
        user = cls.query.filter_by(email=email).first()
        created = False
        
        if not user:
            # Create new user
            user = cls(email=email, name=name)
            db.session.add(user)
            db.session.commit()
            created = True
        elif name and not user.name:
            # Update name if it was null
            user.name = name
            db.session.commit()
        
        return user, created

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
    
    # New fields for destination information
    destination_info = db.Column(db.JSON, nullable=True)
    destination_display_name = db.Column(db.String(255), nullable=True)
    destination_country = db.Column(db.String(100), nullable=True)
    
    recommendations = db.relationship('Recommendation', backref='trip', lazy=True, cascade='all, delete-orphan')
    subscriptions = db.relationship('TripSubscription', backref='trip', lazy=True, cascade='all, delete-orphan')
    
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
        
    def get_grouped_recommendations(self):
        """
        Group recommendations by activity to show a single card for activities 
        recommended by multiple people.
        
        Returns:
            List of dictionaries with the following structure:
            {
                'activity': Activity object,
                'recommendations': List of recommendation objects for this activity
            }
        """
        grouped = {}
        
        for rec in self.recommendations:
            activity_id = rec.activity_id
            if activity_id not in grouped:
                grouped[activity_id] = {
                    'activity': rec.activity,
                    'recommendations': []
                }
            grouped[activity_id]['recommendations'].append(rec)
            
        # Convert dictionary to list for easier use in templates
        return list(grouped.values())
        
    @property
    def unique_activity_count(self):
        """Returns the count of unique activities recommended for this trip"""
        # Use a set comprehension to get unique activity IDs
        unique_activity_ids = {rec.activity_id for rec in self.recommendations}
        return len(unique_activity_ids)

class Activity(db.Model):
    """
    An activity represents a place or experience that can be recommended.
    It is separated from recommendations to allow multiple users to recommend
    the same activity without duplicating the activity information.
    """
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=True)  # restaurant, museum, hiking, tour, etc.
    website_url = db.Column(db.String(255), nullable=True)
    
    # Location details (optional - for place-based activities)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    # Google Places data
    google_place_id = db.Column(db.String(255), nullable=True, unique=True, index=True)
    place_data = db.Column(db.JSON, nullable=True)  # Store additional Google Place data
    
    is_place_based = db.Column(db.Boolean, default=True)  # Whether it's tied to a physical location
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Activity can be recommended multiple times
    recommendations = db.relationship('Recommendation', backref='activity', lazy=True)
    
    def __repr__(self):
        return f'<Activity {self.name}>'
    
    @classmethod
    def get_or_create(cls, name, category=None, website_url=None, **kwargs):
        """
        Find an existing activity by name (and optionally category) or create a new one.
        This helps prevent duplicate activities when multiple users recommend the same place.
        
        First attempts to match with Google Places API to get standardized place data.
        If Google Place ID is found, uses that for exact matching.
        
        Returns:
            Activity: The existing or newly created activity
        """
        from app.services.google_places_service import GooglePlacesService
        
        # First check if we have a Google Place ID in the kwargs and try to find by that
        google_place_id = kwargs.pop('google_place_id', None)
        if google_place_id:
            activity = cls.query.filter_by(google_place_id=google_place_id).first()
            if activity:
                return activity
        
        # Try to match the place name with Google Places API
        place_data = None
        try:
            # Extract search context parameters
            search_context = {
                'search_vicinity': kwargs.pop('search_vicinity', None),
                'destination_country': kwargs.pop('destination_country', None)
            }
            
            # Filter out None values
            search_context = {k: v for k, v in search_context.items() if v is not None}
            
            place_data = GooglePlacesService.find_place(name, category, **search_context)
            if place_data and place_data.get('place_id'):
                # Check if we already have this place ID in our database
                google_place_id = place_data.get('place_id')
                activity = cls.query.filter_by(google_place_id=google_place_id).first()
                if activity:
                    return activity
        except Exception as e:
            import logging
            logging.error(f"Error matching with Google Places API: {str(e)}")
        
        # If no Google Places match, fallback to our usual name matching
        if not google_place_id:
            activity = cls.query.filter(db.func.lower(cls.name) == db.func.lower(name)).first()
            
            # Remove category filtering - match only by name
            # No longer check category match
        
        # If no activity found, create a new one
        if not activity:
            # Prepare data for the new activity
            activity_data = {
                'name': name,
                'category': category,
                'website_url': website_url,
                **kwargs
            }
            
            # Add Google Places data if available
            if place_data and google_place_id:
                activity_data.update({
                    'google_place_id': google_place_id,
                    'place_data': place_data,
                    'address': place_data.get('formatted_address'),
                    'latitude': place_data.get('geometry', {}).get('location', {}).get('lat'),
                    'longitude': place_data.get('geometry', {}).get('location', {}).get('lng'),
                    'website_url': place_data.get('website') or website_url,
                })
                
                # Try to determine city and country from address components
                if place_data.get('address_components'):
                    for component in place_data.get('address_components', []):
                        if 'locality' in component.get('types', []):
                            activity_data['city'] = component.get('long_name')
                        elif 'country' in component.get('types', []):
                            activity_data['country'] = component.get('long_name')
            
            activity = cls(**activity_data)
            db.session.add(activity)
            db.session.commit()
            
        return activity

class Recommendation(db.Model):
    """
    A recommendation is a user's endorsement of an activity for a specific trip.
    It contains the user's personal comments about the activity.
    """
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    description = db.Column(db.Text, nullable=True)  # Personal notes/comments about the activity
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Recommendation for {self.activity.name if self.activity else "Unknown"}>'

class TripSubscription(db.Model):
    """
    Tracks user subscriptions to trip notifications.
    When a user wants to be notified about updates to a trip,
    such as when all recommendations are submitted.
    """
    __tablename__ = 'trip_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notified = db.Column(db.Boolean, default=False)  # Track if we've sent a notification
    
    # Add a unique constraint to prevent duplicate subscriptions
    __table_args__ = (db.UniqueConstraint('user_id', 'trip_id', name='uix_user_trip_subscription'),)
    
    def __repr__(self):
        return f'<TripSubscription User {self.user_id} for Trip {self.trip_id}>' 