import os
from flask import Blueprint, request, jsonify
from app.database import db
from app.database.models import Destination
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