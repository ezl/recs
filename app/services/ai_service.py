import os
import json
import requests
import logging
import traceback
import re

logger = logging.getLogger(__name__)

class AIService:
    """Service for interacting with AI APIs for recommendation extraction"""
    
    @staticmethod
    def extract_recommendations(text, destination):
        """
        Extract structured recommendations from unstructured text using OpenAI API
        
        Args:
            text (str): The unstructured recommendation text
            destination (str): The destination city/location for context
            
        Returns:
            list: List of recommendation dictionaries with keys: name, type, website_url, description
        """
        logger.info(f"Extracting recommendations for destination: {destination}")
        logger.info(f"Input text length: {len(text)} characters")
        logger.info(f"Text sample: '{text[:100]}...' (truncated)")
        
        api_key = os.environ.get("OPENAI_API_KEY")
        organization_id = os.environ.get("ORGANIZATION_ID")
        
        # Check if API key is configured
        if not api_key:
            error_msg = "No OpenAI API key found. Please set the OPENAI_API_KEY environment variable."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Log first 8 chars of key to help with debugging
        logger.info(f"Using API key starting with: {api_key[:8]}...")
        
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Add organization ID to headers if available
            if organization_id:
                headers["OpenAI-Organization"] = organization_id
                logger.info(f"Using organization ID: {organization_id}")
            
            prompt = f"""
            Extract specific recommendations for places to visit in {destination} from the following text.
            For each recommendation, provide:
            1. The name of the place or activity
            2. The type of place (restaurant, museum, park, etc.)
            3. Any website URL mentioned (or leave blank)
            4. A brief description based on what was mentioned

            Text: {text}
            
            Output the information as a JSON array of objects with keys: name, type, website_url, description
            """
            
            logger.info("Preparing request to OpenAI API")
            data = {
                "model": "gpt-3.5-turbo",  # Fallback to a more reliable model
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that extracts structured recommendations from text."},
                    {"role": "user", "content": prompt}
                ]
            }
            
            logger.info(f"Sending request to OpenAI API using model: {data['model']}")
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
            
            logger.info(f"Received response from OpenAI API: status={response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"OpenAI API Error: Status code {response.status_code}, Response: {response.text}")
                raise Exception(f"OpenAI API Error: Status code {response.status_code}, Response: {response.text}")
                
            response.raise_for_status()  # Raise exception for HTTP errors
            result = response.json()
            
            if "error" in result:
                logger.error(f"OpenAI API Error: {result['error']}")
                raise Exception(f"OpenAI API Error: {result.get('error', {}).get('message', 'Unknown error')}")
            
            content = result["choices"][0]["message"]["content"]
            logger.info(f"OpenAI response content: '{content[:100]}...' (truncated)")
            
            # Extract JSON from the response - might need to handle different response formats
            start_idx = content.find("[")
            end_idx = content.rfind("]") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                logger.info(f"Found JSON string from position {start_idx} to {end_idx}")
                
                try:
                    extracted_data = json.loads(json_str)
                    logger.info(f"Successfully parsed JSON data: {len(extracted_data)} recommendations extracted")
                    
                    # Log a summary of the extracted recommendations
                    for i, rec in enumerate(extracted_data):
                        logger.info(f"Recommendation {i+1}: {rec.get('name', 'Unnamed')} ({rec.get('type', 'No type')})")
                    
                    return extracted_data
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error: {e}")
                    logger.error(f"Problem JSON string: {json_str}")
                    
                    # Try fallback parsing - attempt to extract any JSON objects even if not an array
                    logger.info("Attempting fallback JSON parsing...")
                    try:
                        # If we can't parse as an array, try to find individual JSON objects
                        # Look for { } patterns and try to parse each
                        pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                        matches = re.finditer(pattern, content)
                        
                        extracted_objects = []
                        for match in matches:
                            try:
                                obj = json.loads(match.group(0))
                                if isinstance(obj, dict) and 'name' in obj:
                                    extracted_objects.append(obj)
                            except:
                                continue
                        
                        if extracted_objects:
                            logger.info(f"Fallback parsing found {len(extracted_objects)} recommendations")
                            return extracted_objects
                    except Exception as fallback_error:
                        logger.error(f"Fallback parsing also failed: {fallback_error}")
                    
                    # If fallback failed too, create a single recommendation with the full text
                    logger.info("Creating fallback recommendation with the full raw text")
                    fallback = [{
                        "name": f"Recommendations for {destination}",
                        "type": "",
                        "website_url": "",
                        "description": text
                    }]
                    return fallback
            else:
                error_msg = "Failed to extract JSON from OpenAI response"
                logger.error(error_msg)
                logger.error(f"Response did not contain valid JSON array: {content}")
                
                # Create a fallback recommendation instead of raising an error
                logger.info("Creating fallback recommendation with the full raw response")
                fallback = [{
                    "name": f"Recommendations for {destination}",
                    "type": "",
                    "website_url": "",
                    "description": content if content else text
                }]
                return fallback
                
        except Exception as e:
            logger.error(f"Error in AI recommendation extraction: {e}")
            logger.error(traceback.format_exc())
            raise
            
    @staticmethod
    def get_destination_suggestions(destination_query):
        """
        Get top 3 destination suggestions based on the user's input using OpenAI API
        
        Args:
            destination_query (str): The user-entered destination query
            
        Returns:
            list: List of destination dictionaries with keys: name, country, description, population, known_for, map_description
        """
        logger.info(f"Getting destination suggestions for query: {destination_query}")
        
        api_key = os.environ.get("OPENAI_API_KEY")
        organization_id = os.environ.get("ORGANIZATION_ID")
        
        # Check if API key is configured
        if not api_key:
            error_msg = "No OpenAI API key found. Please set the OPENAI_API_KEY environment variable."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Log first 8 chars of key to help with debugging
        logger.info(f"Using API key starting with: {api_key[:8]}...")
        
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Add organization ID to headers if available
            if organization_id:
                headers["OpenAI-Organization"] = organization_id
                logger.info(f"Using organization ID: {organization_id}")
            
            prompt = f"""
            Based on the destination query "{destination_query}", provide the top 3 most likely real-world places that someone may be planning to visit.
            
            For each destination, provide the following information:
            1. The full name of the place with proper capitalization and spelling
            2. The country it's in
            3. A brief description (2-3 sentences max)
            4. The approximate population
            5. What the place is known for (short list of key attractions/features)
            6. A brief map description (where it's located geographically)
            
            Ensure each destination is specific enough to be identifiable on a map. For example, if someone types "Paris", assume "Paris, France".
            
            Output the information as a JSON array of objects with keys: name, country, description, population, known_for (array), map_description
            """
            
            logger.info("Preparing request to OpenAI API for destination suggestions")
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are a helpful travel assistant that provides accurate destination information."},
                    {"role": "user", "content": prompt}
                ]
            }
            
            logger.info(f"Sending request to OpenAI API using model: {data['model']}")
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
            
            logger.info(f"Received response from OpenAI API: status={response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"OpenAI API Error: Status code {response.status_code}, Response: {response.text}")
                raise Exception(f"OpenAI API Error: Status code {response.status_code}, Response: {response.text}")
                
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                logger.error(f"OpenAI API Error: {result['error']}")
                raise Exception(f"OpenAI API Error: {result.get('error', {}).get('message', 'Unknown error')}")
            
            content = result["choices"][0]["message"]["content"]
            logger.info(f"OpenAI response content: '{content[:100]}...' (truncated)")
            
            # Extract JSON from the response
            start_idx = content.find("[")
            end_idx = content.rfind("]") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                logger.info(f"Found JSON string from position {start_idx} to {end_idx}")
                
                try:
                    destinations = json.loads(json_str)
                    logger.info(f"Successfully parsed JSON data: {len(destinations)} destinations extracted")
                    
                    # Log a summary of the destinations
                    for i, dest in enumerate(destinations):
                        logger.info(f"Destination {i+1}: {dest.get('name', 'Unnamed')} ({dest.get('country', 'No country')})")
                    
                    return destinations
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error: {e}")
                    logger.error(f"Problem JSON string: {json_str}")
                    
                    # Create a fallback destination if parsing fails
                    logger.info(f"Creating fallback destination with the query: {destination_query}")
                    fallback = [{
                        "name": destination_query,
                        "country": "",
                        "description": "We couldn't find specific information about this destination.",
                        "population": "Unknown",
                        "known_for": ["Travel destination"],
                        "map_description": ""
                    }]
                    return fallback
            else:
                error_msg = "Failed to extract JSON from OpenAI response"
                logger.error(error_msg)
                logger.error(f"Response did not contain valid JSON array: {content}")
                
                # Create a fallback destination
                logger.info(f"Creating fallback destination with the query: {destination_query}")
                fallback = [{
                    "name": destination_query,
                    "country": "",
                    "description": "We couldn't find specific information about this destination.",
                    "population": "Unknown",
                    "known_for": ["Travel destination"],
                    "map_description": ""
                }]
                return fallback
                
        except Exception as e:
            logger.error(f"Error in destination suggestions: {e}")
            logger.error(traceback.format_exc())
            raise 