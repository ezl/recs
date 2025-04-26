#!/usr/bin/env python3
"""
Script to test our fixes by creating a Tokyo trip with multiple
recommendations from different users for the same places
"""
from app import create_app
from app.database import db
from app.database.models import User, Trip, Recommendation, Activity
import secrets
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def create_tokyo_trip():
    """Create a test Tokyo trip with recommendations"""
    app = create_app()
    
    with app.app_context():
        print("Creating Tokyo trip with recommendations...")
        
        # Create test users
        users = {}
        for name in ['Alpha', 'Bravo', 'Charlie']:
            email = f"{name.lower()}@example.com"
            user = User.query.filter_by(email=email).first()
            
            if not user:
                user = User(email=email, name=name)
                db.session.add(user)
                db.session.commit()
                print(f"Created user: {name}")
            
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
            print(f"Created trip to {destination} with slug: {slug}")
        
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
        
        # Clear existing recommendations
        Recommendation.query.filter_by(trip_id=trip.id).delete()
        db.session.commit()
        print("Cleared existing recommendations")
        
        # Add new recommendations
        for rec_data in recommendations:
            # First find or create the Activity
            activity = Activity.get_or_create(
                name=rec_data["place"],
                category=rec_data["category"],
                destination_country="Japan",
                search_vicinity="Tokyo"
            )
            
            # Create recommendation
            recommendation = Recommendation(
                activity_id=activity.id,
                description=rec_data["description"],
                author_id=users[rec_data["user"]].id,
                trip_id=trip.id
            )
            
            db.session.add(recommendation)
        
        db.session.commit()
        print(f"Added {len(recommendations)} recommendations")
        
        # Verify results
        print("\nTripRecent:")
        print(f"Trip: {trip.destination}")
        print(f"Slug: {trip.slug}")
        print(f"Recommendations count: {len(trip.recommendations)}")
        
        # Check grouping
        print("\nGrouped Recommendations:")
        print("-" * 80)
        
        grouped = trip.get_grouped_recommendations()
        for group in grouped:
            activity = group['activity']
            recommendations = group['recommendations']
            
            print(f"Activity: {activity.name} (ID: {activity.id})")
            print(f"Category: {activity.category}")
            print(f"Recommended by {len(recommendations)} people:")
            
            for rec in recommendations:
                print(f"  - {rec.author.name}: \"{rec.description}\"")
            
            print("-" * 80)

if __name__ == "__main__":
    create_tokyo_trip() 