#!/usr/bin/env python3
"""
Test script to verify Google Places API integration

This script creates an activity for a well-known place (Eiffel Tower in Paris)
and verifies that Google Places data is properly populated in the activity record.
"""
import os
import logging
import sys
import json
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.database import db
from app.database.models import Activity, User, Trip
from app.services.google_places_service import GooglePlacesService
from pprint import pprint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('test_google_places')

def test_google_places_integration():
    """Test Google Places API integration with Activity model"""
    
    # Create and configure the Flask app
    app = create_app()
    
    with app.app_context():
        logger.info("=" * 80)
        logger.info("TESTING GOOGLE PLACES API INTEGRATION")
        logger.info("=" * 80)
        
        # Check if Google Maps API key is set
        api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        if not api_key:
            logger.error("GOOGLE_MAPS_API_KEY environment variable is not set!")
            logger.error("Please set this variable before running the test.")
            return False
        
        logger.info(f"Using Google Maps API key: {api_key[:5]}...{api_key[-4:]}")
        
        # Clean up any existing test data
        Activity.query.filter(Activity.name == "Eiffel Tower").delete()
        Trip.query.filter(Trip.destination == "Paris").delete()
        User.query.filter(User.email == "test@example.com").delete()
        db.session.commit()
        
        # Create test user
        user = User(
            email="test@example.com",
            name="Test User",
            password="test_hash"
        )
        db.session.add(user)
        db.session.commit()
        
        # Create test trip
        trip = Trip(
            destination="Paris",
            destination_country="France",
            share_token="test_token_123",
            slug="paris-test-trip",
            user_id=user.id
        )
        db.session.add(trip)
        db.session.commit()
        
        # Initialize Google Places service
        places_service = GooglePlacesService()
        
        # Test place search
        logger.info("Calling GooglePlacesService.find_place()...")
        search_result = places_service.find_place(
            "Eiffel Tower",
            search_vicinity="Paris",
            destination_country="France"
        )
        
        logger.info("\n=== Full Google Places API Response ===")
        logger.info(json.dumps(search_result, indent=2))
        logger.info("\n=== End of Response ===\n")
        
        if not search_result:
            logger.error("❌ Failed to find Eiffel Tower")
            return False
        
        logger.info("✅ Found Eiffel Tower!")
        logger.info(f"Place ID: {search_result.get('place_id')}")
        logger.info(f"Address: {search_result.get('formatted_address')}")
        logger.info(f"Types: {search_result.get('types')}")
        
        # Create activity with the place data
        activity = Activity(
            name="Eiffel Tower",
            category="attraction",
            website_url=search_result.get('website'),
            address=search_result.get('formatted_address'),
            city="Paris",
            country="France",
            latitude=search_result.get('geometry', {}).get('location', {}).get('lat'),
            longitude=search_result.get('geometry', {}).get('location', {}).get('lng'),
            google_place_id=search_result.get('place_id'),
            place_data=search_result
        )
        db.session.add(activity)
        db.session.commit()
        
        logger.info("\n✅ Activity created with Google Places data")
        logger.info(f"Activity ID: {activity.id}")
        logger.info(f"Google Place ID: {activity.google_place_id}")
        
        # Clean up
        db.session.delete(activity)
        db.session.delete(trip)
        db.session.delete(user)
        db.session.commit()
        
        logger.info("\n✅ Test completed successfully")
        return True

if __name__ == "__main__":
    success = test_google_places_integration()
    exit(0 if success else 1) 