"""
Google Places Service

Provides integration with Google Places API for looking up place information.
This service is used by the Activity model to standardize place data.
"""
import os
import logging
import requests
import json
from urllib.parse import urlencode
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

class GooglePlacesService:
    """Service for interacting with Google Places API"""
    
    @classmethod
    def find_place(cls, name, category=None, **kwargs):
        """
        Find a place using Google Places API
        
        Args:
            name (str): Name of the place to search for
            category (str, optional): Type of place (e.g. restaurant, museum)
            **kwargs: Additional search context parameters like search_vicinity, destination_country
            
        Returns:
            dict: Place data if found, None otherwise
        """
        # Get API key from environment
        api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        if not api_key:
            logger.warning("GOOGLE_MAPS_API_KEY not set in environment variables")
            # Print all environment variables for debugging (without showing their values)
            logger.debug(f"Available environment variables: {', '.join(os.environ.keys())}")
            return None
            
        logger.info(f"Searching Google Places API for: {name}")
        if category:
            logger.info(f"Category: {category}")
        if kwargs.get('search_vicinity'):
            logger.info(f"Search vicinity: {kwargs.get('search_vicinity')}")
        if kwargs.get('destination_country'):
            logger.info(f"Destination country: {kwargs.get('destination_country')}")
        
        try:
            # First try the Find Place API for exact matches
            place_id = cls._find_place_id(name, api_key, **kwargs)
            
            # If we found a place_id, get the details
            if place_id:
                logger.info(f"Found place_id for {name}: {place_id}")
                return cls._get_place_details(place_id, api_key)
                
            # If no exact match, try a broader search with the Places Text Search API
            search_query = name
            
            # Add category to search if provided
            if category:
                search_query = f"{name} {category}"
                
            # Add vicinity/location context if available
            search_vicinity = kwargs.get('search_vicinity')
            destination_country = kwargs.get('destination_country')
            
            if search_vicinity:
                search_query = f"{search_query} {search_vicinity}"
            elif destination_country:
                search_query = f"{search_query} {destination_country}"
            
            logger.info(f"No exact match found, trying text search with: {search_query}")    
            return cls._text_search_place(search_query, api_key)
                
        except Exception as e:
            logger.error(f"Error in Google Places API: {str(e)}")
            return None
    
    @classmethod
    def _find_place_id(cls, name, api_key, **kwargs):
        """Find a place ID using the Find Place API"""
        base_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        
        params = {
            'input': name,
            'inputtype': 'textquery',
            'fields': 'place_id',
            'key': api_key
        }
        
        # Add location bias if we have vicinity information
        search_vicinity = kwargs.get('search_vicinity')
        if search_vicinity:
            params['locationbias'] = f'name:{search_vicinity}'
            
        # Or use country if we have it
        elif kwargs.get('destination_country'):
            params['locationbias'] = f'name:{kwargs.get("destination_country")}'
            
        url = f"{base_url}?{urlencode(params)}"
        logger.info(f"Making FindPlace API request for: {name}")
        
        response = requests.get(url)
        data = response.json()
        
        # Log the response status
        logger.info(f"FindPlace API response status: {data.get('status')}")
        
        if data.get('status') == 'OK' and data.get('candidates'):
            return data['candidates'][0].get('place_id')
        else:
            # Log more details if not successful
            if data.get('status') != 'OK':
                logger.warning(f"FindPlace API returned non-OK status: {data.get('status')}")
                if data.get('error_message'):
                    logger.warning(f"Error message: {data.get('error_message')}")
            elif not data.get('candidates'):
                logger.info(f"FindPlace API returned no candidates for: {name}")
            
        return None
    
    @classmethod
    def _get_place_details(cls, place_id, api_key):
        """Get detailed information about a place using the Place Details API"""
        base_url = "https://maps.googleapis.com/maps/api/place/details/json"
        
        params = {
            'place_id': place_id,
            'fields': 'name,place_id,formatted_address,geometry,website,address_components,type',
            'key': api_key
        }
        
        url = f"{base_url}?{urlencode(params)}"
        logger.info(f"Making PlaceDetails API request for place_id: {place_id}")
        
        response = requests.get(url)
        data = response.json()
        
        # Log the response status
        logger.info(f"PlaceDetails API response status: {data.get('status')}")
        
        if data.get('status') == 'OK':
            logger.info(f"Successfully retrieved details for place: {data.get('result', {}).get('name')}")
            return data.get('result')
        else:
            if data.get('error_message'):
                logger.warning(f"PlaceDetails API error: {data.get('error_message')}")
            
        return None
    
    @classmethod
    def _text_search_place(cls, query, api_key):
        """Search for a place using the Places Text Search API"""
        base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        
        params = {
            'query': query,
            'key': api_key
        }
        
        url = f"{base_url}?{urlencode(params)}"
        logger.info(f"Making TextSearch API request for query: {query}")
        
        response = requests.get(url)
        data = response.json()
        
        # Log the response status
        logger.info(f"TextSearch API response status: {data.get('status')}")
        
        if data.get('status') == 'OK' and data.get('results'):
            logger.info(f"TextSearch API found {len(data.get('results'))} results")
            place_id = data['results'][0].get('place_id')
            if place_id:
                logger.info(f"Using first result with place_id: {place_id}")
                return cls._get_place_details(place_id, api_key)
        else:
            if data.get('status') != 'OK':
                logger.warning(f"TextSearch API returned non-OK status: {data.get('status')}")
                if data.get('error_message'):
                    logger.warning(f"Error message: {data.get('error_message')}")
            elif not data.get('results'):
                logger.info(f"TextSearch API returned no results for query: {query}")
                
        return None 