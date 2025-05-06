import os
from flask import Blueprint, request, jsonify, render_template, send_from_directory
from app.database import db
from app.database.models import Destination
from app.services.google_places_service import GooglePlacesService
from app.services.openstreetmap_service import OpenStreetMapService
import logging

# Set up logger
logger = logging.getLogger(__name__)

# Create blueprint
destination_bp = Blueprint('destination', __name__)

@destination_bp.route('/api/destinations/database/', methods=['GET'])
def search_destinations_database():
    """
    API endpoint to search destinations from the database
    Returns destinations matching the query from our database
    """
    logger.info("=== DATABASE DESTINATION SEARCH API CALLED ===")
    
    # Get query parameter
    query = request.args.get('query', '')
    
    if not query or len(query) < 2:
        logger.info(f"Search rejected - query too short: '{query}'")
        return jsonify({
            "status": "error",
            "message": "Query must be at least 2 characters",
            "results": []
        }), 400
    
    logger.info(f"Searching for destinations matching: '{query}'")
    
    # Perform case-insensitive search on name, display_name, and country
    destinations = Destination.query.filter(
        db.or_(
            Destination.name.ilike(f"%{query}%"),
            Destination.display_name.ilike(f"%{query}%"),
            Destination.country.ilike(f"%{query}%")
        )
    ).limit(10).all()
    
    logger.info(f"Found {len(destinations)} matching destinations")
    
    # Format the results
    results = []
    for dest in destinations:
        results.append({
            "id": dest.id,
            "name": dest.name,
            "display_name": dest.display_name,
            "country": dest.country,
            "type": dest.type,
            "latitude": dest.latitude,
            "longitude": dest.longitude,
            "source": "database"
        })
    
    return jsonify({
        "status": "success",
        "results": results
    }), 200

@destination_bp.route('/api/destinations/google-places/', methods=['GET'])
def search_destinations_google_places():
    """
    API endpoint to search destinations using Google Places API
    Returns destinations matching the query from Google Places
    """
    logger.info("=== GOOGLE PLACES DESTINATION SEARCH API CALLED ===")
    
    # Get query parameter
    query = request.args.get('query', '')
    
    if not query or len(query) < 2:
        logger.info(f"Search rejected - query too short: '{query}'")
        return jsonify({
            "status": "error",
            "message": "Query must be at least 2 characters",
            "results": []
        }), 400
    
    logger.info(f"Searching Google Places API for destinations matching: '{query}'")
    
    # Check if we're in test mode
    use_mock = request.args.get('mock', 'false').lower() == 'true'
    
    if use_mock:
        logger.info("Using mock Google Places API response for testing")
        # Return a mock response for testing
        results = [
            {
                "id": None,
                "name": f"Mock {query} City",
                "display_name": f"Mock {query} City, Mock Country",
                "country": "Mock Country",
                "type": "city",
                "latitude": 12.345,
                "longitude": 67.890,
                "google_place_id": "mock_place_id_123",
                "source": "google_places"
            }
        ]
    else:
        # Use the actual Google Places API
        results = GooglePlacesService.search_destinations(query)
    
    logger.info(f"Returning {len(results)} Google Places API results")
    
    return jsonify({
        "status": "success",
        "results": results
    }), 200

@destination_bp.route('/api/destinations/openstreetmap/', methods=['GET'])
def search_destinations_openstreetmap():
    """
    API endpoint to search destinations using OpenStreetMap Nominatim API
    Returns destinations matching the query from OpenStreetMap
    """
    logger.info("=== OPENSTREETMAP DESTINATION SEARCH API CALLED ===")
    
    # Get query parameter
    query = request.args.get('query', '')
    
    if not query or len(query) < 2:
        logger.info(f"Search rejected - query too short: '{query}'")
        return jsonify({
            "status": "error",
            "message": "Query must be at least 2 characters",
            "results": []
        }), 400
    
    logger.info(f"Searching OpenStreetMap API for destinations matching: '{query}'")
    
    # Check if we're in test mode
    use_mock = request.args.get('mock', 'false').lower() == 'true'
    
    if use_mock:
        logger.info("Using mock OpenStreetMap API response for testing")
        # Return a mock response for testing
        results = [
            {
                "id": None,
                "name": f"Mock OSM {query}",
                "display_name": f"Mock OSM {query}, Mock OSM Country",
                "country": "Mock OSM Country",
                "type": "city",
                "latitude": 34.567,
                "longitude": 89.012,
                "osm_id": "12345678",
                "source": "openstreetmap"
            }
        ]
    else:
        # Use the actual OpenStreetMap API
        results = OpenStreetMapService.search_destinations(query)
    
    logger.info(f"Returning {len(results)} OpenStreetMap API results")
    
    return jsonify({
        "status": "success",
        "results": results
    }), 200

@destination_bp.route('/destination-search-test')
def destination_search_test():
    """
    Route to serve the destination search test page
    """
    return send_from_directory('static/js', 'destination-search-test.html')

@destination_bp.route('/destination-search-demo')
def destination_search_demo():
    """
    Route to serve the comprehensive destination search demo page with documentation
    """
    return send_from_directory('static/js', 'destination-search-demo.html') 