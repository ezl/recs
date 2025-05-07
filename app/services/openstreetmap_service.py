"""
OpenStreetMap Service

Provides integration with OpenStreetMap's Nominatim API for geocoding and place search.
This service is used to find destination information as an alternative data source.
"""
import os
import logging
import requests
import time
from urllib.parse import urlencode

# Configure logger
logger = logging.getLogger(__name__)

class OpenStreetMapService:
    """Service for interacting with OpenStreetMap Nominatim API"""
    
    # Base URL for Nominatim API
    NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org/search"
    
    # User agent required by Nominatim's usage policy
    USER_AGENT = "RecApp/1.0 (https://recommendations.app)"
    
    # Rate limiting - Nominatim requires max 1 request per second
    last_request_time = 0
    
    @classmethod
    def search_destinations(cls, query):
        """
        Search for destinations using OpenStreetMap Nominatim API
        
        Args:
            query (str): The search query for destinations
            
        Returns:
            list: List of destination dictionaries with standardized format
        """
        logger.info(f"Searching destinations using OpenStreetMap for: {query}")
        
        try:
            # Respect rate limiting (1 request per second)
            cls._respect_rate_limit()
            
            # Set up parameters for the Nominatim API
            params = {
                'q': query,
                'format': 'json',
                'addressdetails': 1,
                'limit': 10,
                # Focus on places, not streets or buildings
                'featuretype': 'city,state,country',
                'accept-language': 'en'
            }
            
            url = f"{cls.NOMINATIM_BASE_URL}?{urlencode(params)}"
            logger.info(f"Making Nominatim API request for: {query}")
            
            # Add user agent to comply with Nominatim usage policy
            headers = {'User-Agent': cls.USER_AGENT}
            
            response = requests.get(url, headers=headers)
            cls.last_request_time = time.time()
            
            if response.status_code != 200:
                logger.warning(f"Nominatim API returned non-200 status: {response.status_code}")
                return []
            
            data = response.json()
            logger.info(f"Found {len(data)} results from Nominatim API")
            
            # Format results to match our standard destination format
            results = []
            for place in data:
                destination = cls._format_place_as_destination(place)
                if destination:
                    results.append(destination)
            
            logger.info(f"Returning {len(results)} formatted destination results")
            return results
            
        except Exception as e:
            logger.error(f"Error in OpenStreetMap API search: {str(e)}")
            return []
    
    @classmethod
    def _format_place_as_destination(cls, place):
        """
        Format OpenStreetMap result as a destination
        
        Args:
            place (dict): Place from OpenStreetMap API
            
        Returns:
            dict: Formatted destination dictionary
        """
        if not place:
            return None
        
        # Extract relevant data
        osm_id = place.get('osm_id')
        name = place.get('display_name', '').split(',')[0]  # Get the first part of display_name
        display_name = place.get('display_name', '')
        address = place.get('address', {})
        country = address.get('country')
        # Extract country_code from place (if present)
        country_code = place.get('country_code') or address.get('country_code')
        if country_code:
            country_code = country_code.upper()
        else:
            country_code = None
        place_type = cls._determine_place_type(place)
        lat = place.get('lat')
        lon = place.get('lon')
        if lat and lon:
            try:
                latitude = float(lat)
                longitude = float(lon)
            except (ValueError, TypeError):
                latitude = None
                longitude = None
        else:
            latitude = None
            longitude = None
        return {
            'id': None,
            'name': name,
            'display_name': display_name,
            'country': country,
            'country_code': country_code,
            'type': place_type,
            'latitude': latitude,
            'longitude': longitude,
            'osm_id': osm_id,
            'source': 'openstreetmap'
        }
    
    @classmethod
    def _determine_place_type(cls, place):
        """
        Determine the type of place based on OSM type and class
        
        Args:
            place (dict): Place from OpenStreetMap API
            
        Returns:
            str: Type of place (city, region, country, etc.)
        """
        osm_type = place.get('osm_type')
        osm_class = place.get('class')
        osm_type_value = place.get('type')
        
        # Extract from address components
        address = place.get('address', {})
        
        if address.get('country') and not address.get('state') and not address.get('city'):
            return 'country'
        
        if address.get('state') and not address.get('city'):
            return 'region'
        
        if address.get('city') or osm_type_value == 'city':
            return 'city'
        
        # Fallback based on OSM classification
        if osm_class == 'place':
            if osm_type_value in ['city', 'town', 'village']:
                return 'city'
            elif osm_type_value in ['state', 'region', 'province']:
                return 'region'
        
        if osm_class == 'boundary' and osm_type_value == 'administrative':
            return 'region'
        
        # Default
        return 'place'
    
    @classmethod
    def _respect_rate_limit(cls):
        """
        Ensure we respect Nominatim's rate limit policy (1 request per second)
        """
        current_time = time.time()
        time_since_last_request = current_time - cls.last_request_time
        
        # If less than 1 second has passed since the last request, wait
        if time_since_last_request < 1.0:
            sleep_time = 1.0 - time_since_last_request
            logger.debug(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time) 