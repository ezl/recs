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
        
        # If no API key is configured, return mock data for development
        if not api_key:
            logger.warning("No OpenAI API key found. Using mock recommendations.")
            return AIService._get_mock_recommendations()
        
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
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
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that extracts structured recommendations from text."},
                    {"role": "user", "content": prompt}
                ]
            }
            
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
            result = response.json()
            
            if "error" in result:
                logger.error(f"OpenAI API Error: {result['error']}")
                return AIService._get_mock_recommendations()
            
            content = result["choices"][0]["message"]["content"]
            # Extract JSON from the response - might need to handle different response formats
            start_idx = content.find("[")
            end_idx = content.rfind("]") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                extracted_data = json.loads(json_str)
                return extracted_data
            else:
                logger.error("Failed to extract JSON from OpenAI response")
                return AIService._get_mock_recommendations()
                
        except Exception as e:
            logger.error(f"Error in AI recommendation extraction: {e}")
            return AIService._get_mock_recommendations()
    
    @staticmethod
    def _get_mock_recommendations():
        """Return mock recommendation data for development"""
        return [
            {
                "name": "Rooftop Bar with Acropolis View",
                "type": "Bar",
                "website_url": "https://example.com/rooftopbar",
                "description": "Amazing views of the Acropolis at sunset."
            },
            {
                "name": "Local Taverna in Plaka",
                "type": "Restaurant",
                "website_url": "",
                "description": "Authentic Greek food with live music on weekends."
            },
            {
                "name": "Ancient Agora",
                "type": "Historical Site",
                "website_url": "https://example.com/agora",
                "description": "Less crowded than the Acropolis but just as interesting."
            }
        ] 