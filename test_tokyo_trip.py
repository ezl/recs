#!/usr/bin/env python3
"""
Script to test our fixes by creating a Tokyo trip with multiple
recommendations from different users for the same places

Usage:
    python test_tokyo_trip.py --use-real-api  # Use real Google Places API
    python test_tokyo_trip.py                 # Use mock data (default)
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
logger = logging.getLogger('test_tokyo_trip')

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

def create_tokyo_trip(use_real_api=False):
    """Create a test Tokyo trip with recommendations"""
    app = create_app()
    
    with app.app_context():
        logger.info("Creating Tokyo trip with recommendations...")
        
        # Create test users
        users = {}
        for name in ['Alpha', 'Bravo', 'Charlie']:
            email = f"{name.lower()}@example.com"
            user = User.query.filter_by(email=email).first()
            
            if not user:
                user = User(email=email, name=name)
                db.session.add(user)
                db.session.commit()
                logger.info(f"Created user: {name}")
            
            users[name] = user
        
        # Create Tokyo trip
        destination = "Tokyo"
        share_token = secrets.token_urlsafe(16)
        slug = "tokyo-apr-2025"  # Use fixed slug for consistency
        
        trip = Trip.query.filter_by(slug=slug).first()
        if not trip:
            trip = Trip(
                destination=destination,
                traveler_name="Test User",
                share_token=share_token,
                slug=slug,
                user_id=users['Alpha'].id,
                destination_display_name="Tokyo, Japan",
                destination_country="Japan"
            )
            
            db.session.add(trip)
            db.session.commit()
            logger.info(f"Created trip to {destination} with slug: {slug}")
        
        # Clear existing recommendations
        Recommendation.query.filter_by(trip_id=trip.id).delete()
        db.session.commit()
        logger.info("Cleared existing recommendations")
        
        # Create recommendations with intentionally similar places
        recommendations = [
            # Same place, different categories, different users
            {"user": "Alpha", "place": "Asakusa", "category": "Historic district", 
             "description": "Explore the traditional charm of Asakusa, featuring ancient temples, street food vendors, and a glimpse of old-school Tokyo vibes."},
            {"user": "Charlie", "place": "Asakusa", "category": "Historic area", 
             "description": "Old-school Tokyo vibes, visit Sensoji Temple and grab some street snacks."},
            
            # Same place, different categories, different users
            {"user": "Alpha", "place": "TeamLab Planets", "category": "Interactive art exhibition", 
             "description": "An immersive experience where visitors can walk through interactive art installations resembling a dream."},
            {"user": "Charlie", "place": "TeamLab Planets", "category": "Art Museum", 
             "description": "Wild immersive art experience, feels like another world."},
            
            # Same place, different formatting, different users
            {"user": "Bravo", "place": "Ramen Street", "category": "Restaurant", 
             "description": "Don't miss Ramen Street at Tokyo Station for a must-try culinary experience in Tokyo."},
            {"user": "Charlie", "place": "Ramen Street (Tokyo Station)", "category": "Food", 
             "description": "A whole underground row of famous ramen shops, easy and delicious."},
            
            # Other recommendations
            {"user": "Alpha", "place": "Shibuya Scramble Crossing", "category": "Famous landmark", 
             "description": "Experience the iconic and bustling Shibuya Scramble Crossing, and explore the charming streets of Shibuya."},
            {"user": "Alpha", "place": "Tsukiji Market", "category": "Market", 
             "description": "Experience the lively atmosphere of Tsukiji Market, known for its fresh seafood and sushi breakfast offerings."},
            {"user": "Bravo", "place": "Nakameguro", "category": "Neighborhood", 
             "description": "Nakameguro offers a peaceful morning by the river with opportunities to enjoy coffee and a leisurely walk."},
            {"user": "Charlie", "place": "Nakameguro", "category": "Neighborhood", 
             "description": "Chill riverside neighborhood, great for coffee shops and boutique shopping."}
        ]
        
        # Add new recommendations
        for rec_data in recommendations:
            # First find or create the Activity
            if use_real_api:
                activity = Activity.get_or_create(
                    name=rec_data["place"],
                    category=rec_data["category"],
                    destination_country="Japan",
                    search_vicinity="Tokyo"
                )
                # Save mock data if it doesn't exist
                if not (MOCK_DATA_DIR / f"{rec_data['place'].lower().replace(' ', '_')}_response.json").exists():
                    save_mock_data(rec_data["place"], activity.place_data)
            else:
                # Use mock data
                mock_data = load_mock_data(rec_data["place"])
                if not mock_data:
                    logger.error(f"Failed to load mock data for {rec_data['place']}")
                    continue
                
                # Check if activity already exists with this place_id
                existing_activity = Activity.query.filter_by(google_place_id=mock_data.get('place_id')).first()
                if existing_activity:
                    activity = existing_activity
                    logger.info(f"Using existing activity: {activity.name} (ID: {activity.id})")
                else:
                    activity = Activity(
                        name=rec_data["place"],
                        category=rec_data["category"],
                        website_url=mock_data.get('website'),
                        address=mock_data.get('formatted_address'),
                        city="Tokyo",
                        country="Japan",
                        latitude=mock_data.get('geometry', {}).get('location', {}).get('lat'),
                        longitude=mock_data.get('geometry', {}).get('location', {}).get('lng'),
                        google_place_id=mock_data.get('place_id'),
                        place_data=mock_data
                    )
                    db.session.add(activity)
                    db.session.commit()
                    logger.info(f"Created new activity: {activity.name} (ID: {activity.id})")
            
            # Create recommendation
            recommendation = Recommendation(
                activity_id=activity.id,
                description=rec_data["description"],
                author_id=users[rec_data["user"]].id,
                trip_id=trip.id
            )
            
            db.session.add(recommendation)
        
        db.session.commit()
        logger.info(f"Added {len(recommendations)} recommendations")
        
        # Verify results
        logger.info("\nTrip Details:")
        logger.info(f"Trip: {trip.destination}")
        logger.info(f"Slug: {trip.slug}")
        logger.info(f"Recommendations count: {len(trip.recommendations)}")
        
        # Check grouping
        logger.info("\nGrouped Recommendations:")
        logger.info("-" * 80)
        
        grouped = trip.get_grouped_recommendations()
        for group in grouped:
            activity = group['activity']
            recommendations = group['recommendations']
            
            logger.info(f"Activity: {activity.name} (ID: {activity.id})")
            logger.info(f"Category: {activity.category}")
            logger.info(f"Recommended by {len(recommendations)} people:")
            
            for rec in recommendations:
                logger.info(f"  - {rec.author.name}: \"{rec.description}\"")
            
            logger.info("-" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create a test Tokyo trip with recommendations')
    parser.add_argument('--use-real-api', action='store_true', help='Use real Google Places API instead of mock data')
    args = parser.parse_args()
    
    create_tokyo_trip(use_real_api=args.use_real_api) 