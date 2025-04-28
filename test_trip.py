#!/usr/bin/env python3
"""
Test script to verify database setup by creating a test trip

Usage:
    python test_trip.py --use-real-api  # Use real Google Places API
    python test_trip.py                 # Use mock data (default)
"""
from app import create_app
from app.database import db
from app.database.models import User, Trip, Recommendation, Activity
import secrets
import logging
import argparse
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_trip')

# Mock data directory
MOCK_DATA_DIR = Path(__file__).parent / 'mock_data'
MOCK_DATA_DIR.mkdir(exist_ok=True)

def save_mock_data(place_name, response_data):
    """Save API response data to mock data file"""
    mock_file = MOCK_DATA_DIR / f"{place_name.lower().replace(' ', '_')}_response.json"
    with open(mock_file, 'w') as f:
        json.dump(response_data, f, indent=2)
    logger.info(f"Saved mock data to {mock_file}")

def load_mock_data(place_name):
    """Load mock data from file"""
    mock_file = MOCK_DATA_DIR / f"{place_name.lower().replace(' ', '_')}_response.json"
    if not mock_file.exists():
        logger.error(f"Mock data file not found: {mock_file}")
        return None
    with open(mock_file, 'r') as f:
        return json.load(f)

def test_create_trip(use_real_api=False):
    """Create a test trip to verify database functionality"""
    app = create_app()
    
    with app.app_context():
        logger.info("Connecting to database...")
        
        # Get or create test user
        test_email = 'test@example.com'
        test_user = User.query.filter_by(email=test_email).first()
        
        if not test_user:
            test_user = User(email=test_email, name='Test User')
            db.session.add(test_user)
            db.session.commit()
            logger.info(f"Created test user: {test_email}")
        
        # Clean up any existing test data
        existing_trips = Trip.query.filter_by(user_id=test_user.id).all()
        for trip in existing_trips:
            # Delete recommendations first
            Recommendation.query.filter_by(trip_id=trip.id).delete()
            db.session.delete(trip)
        db.session.commit()
        logger.info(f"Cleaned up {len(existing_trips)} existing test trips")
        
        # Clean up test activities
        Activity.query.filter_by(name="Eiffel Tower").delete()
        db.session.commit()
        logger.info("Cleaned up existing test activities")
        
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
        logger.info(f"Created test trip to {destination} with slug: {slug}")
        
        # Create a test activity and recommendation
        if use_real_api:
            activity = Activity.get_or_create(
                name="Eiffel Tower",
                category="landmark",
                search_vicinity="Paris",
                destination_country="France"
            )
            # Save mock data if it doesn't exist
            if not (MOCK_DATA_DIR / "eiffel_tower_response.json").exists():
                save_mock_data("Eiffel Tower", activity.place_data)
        else:
            # Use mock data
            mock_data = load_mock_data("Eiffel Tower")
            if not mock_data:
                logger.error("Failed to load mock data for Eiffel Tower")
                return False
                
            activity = Activity(
                name="Eiffel Tower",
                category="landmark",
                website_url=mock_data.get('website'),
                address=mock_data.get('formatted_address'),
                city="Paris",
                country="France",
                latitude=mock_data.get('geometry', {}).get('location', {}).get('lat'),
                longitude=mock_data.get('geometry', {}).get('location', {}).get('lng'),
                google_place_id=mock_data.get('place_id'),
                place_data=mock_data
            )
            db.session.add(activity)
            db.session.commit()
        
        recommendation = Recommendation(
            activity_id=activity.id,
            description="You must visit the Eiffel Tower!",
            author_id=test_user.id,
            trip_id=trip.id
        )
        
        db.session.add(recommendation)
        db.session.commit()
        logger.info(f"Created recommendation for {activity.name}")
        
        # Verify all was created
        logger.info("\nVerification:")
        logger.info(f"- Users: {User.query.count()}")
        logger.info(f"- Trips: {Trip.query.count()}")
        logger.info(f"- Activities: {Activity.query.count()}")
        logger.info(f"- Recommendations: {Recommendation.query.count()}")
        
        logger.info("\nTest successful!")
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test database setup by creating a test trip')
    parser.add_argument('--use-real-api', action='store_true', help='Use real Google Places API instead of mock data')
    args = parser.parse_args()
    
    success = test_create_trip(use_real_api=args.use_real_api)
    exit(0 if success else 1) 