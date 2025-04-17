import os
import json
import requests
import logging

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
            
            data = {
                "model": "gpt-3.5-turbo",  # Fallback to a more reliable model
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that extracts structured recommendations from text."},
                    {"role": "user", "content": prompt}
                ]
            }
            
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
            
            if response.status_code != 200:
                logger.error(f"OpenAI API Error: Status code {response.status_code}, Response: {response.text}")
                raise Exception(f"OpenAI API Error: Status code {response.status_code}, Response: {response.text}")
                
            response.raise_for_status()  # Raise exception for HTTP errors
            result = response.json()
            
            if "error" in result:
                logger.error(f"OpenAI API Error: {result['error']}")
                raise Exception(f"OpenAI API Error: {result.get('error', {}).get('message', 'Unknown error')}")
            
            content = result["choices"][0]["message"]["content"]
            # Extract JSON from the response - might need to handle different response formats
            start_idx = content.find("[")
            end_idx = content.rfind("]") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                extracted_data = json.loads(json_str)
                return extracted_data
            else:
                error_msg = "Failed to extract JSON from OpenAI response"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
        except Exception as e:
            logger.error(f"Error in AI recommendation extraction: {e}")
            raise 