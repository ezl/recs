#!/usr/bin/env python3
"""
Test script to verify database setup by creating a test trip
"""
from app import create_app
from app.database import db
from app.database.models import User, Trip, Recommendation, Activity
import secrets

def test_create_trip():
    """Create a test trip to verify database functionality"""
    app = create_app()
    
    with app.app_context():
        print("Connecting to database...")
        
        # Get or create test user
        test_email = 'test@example.com'
        test_user = User.query.filter_by(email=test_email).first()
        
        if not test_user:
            test_user = User(email=test_email, name='Test User')
            db.session.add(test_user)
            db.session.commit()
            print(f"Created test user: {test_email}")
        
        # Create a test trip
        destination = "Paris"
        share_token = secrets.token_urlsafe(16)
        slug = Trip.generate_slug(destination, "Test User")
        
        trip = Trip(
            destination=destination,
            traveler_name="Test User",
            share_token=share_token,
            slug=slug,
            user_id=test_user.id,
            destination_display_name="Paris, France",
            destination_country="France"
        )
        
        db.session.add(trip)
        db.session.commit()
        print(f"Created test trip to {destination} with slug: {slug}")
        
        # Create a test activity and recommendation
        activity = Activity.get_or_create(
            name="Eiffel Tower",
            category="landmark",
            search_vicinity="Paris",
            destination_country="France"
        )
        
        recommendation = Recommendation(
            activity_id=activity.id,
            description="You must visit the Eiffel Tower!",
            author_id=test_user.id,
            trip_id=trip.id
        )
        
        db.session.add(recommendation)
        db.session.commit()
        print(f"Created recommendation for {activity.name}")
        
        # Verify all was created
        print("\nVerification:")
        print(f"- Users: {User.query.count()}")
        print(f"- Trips: {Trip.query.count()}")
        print(f"- Activities: {Activity.query.count()}")
        print(f"- Recommendations: {Recommendation.query.count()}")
        
        print("\nTest successful!")

if __name__ == "__main__":
    test_create_trip() 