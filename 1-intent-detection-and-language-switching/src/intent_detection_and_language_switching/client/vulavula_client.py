"""
Vulavula API Client for Intent Detection
Improved by bytte AI
"""
import json
import logging
from typing import List, Optional
from requests.exceptions import HTTPError, RequestException, Timeout
import requests

from domain.schema import IntentDetectionRequest, IntentDetectionResponse

# Configure logging - improved by bytte AI
logger = logging.getLogger(__name__)


class VulavulaClient:
    """
    A client for interacting with the Vulavula intent detection API.
    
    Attributes:
        vulavula_api_key (str): The API key for authenticating requests to the Vulavula service.
        base_url (str): The base URL for the Vulavula API.
        timeout (int): Request timeout in seconds.
    """
    
    # Class constant for base URL - improved by bytte AI
    DEFAULT_BASE_URL = "https://vulavula-services.lelapa.ai"
    DEFAULT_TIMEOUT = 30  # seconds - improved by bytte AI
    
    def __init__(
        self, 
        vulavula_api_key: str,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT
    ):
        """
        Initializes the VulavulaClient with the provided API key.
        
        Args:
            vulavula_api_key (str): The API key for accessing the Vulavula API.
            base_url (Optional[str]): Custom base URL (defaults to production URL).
            timeout (int): Request timeout in seconds.
            
        Raises:
            ValueError: If API key is empty or None.
        """
        # Input validation - improved by bytte AI
        if not vulavula_api_key:
            raise ValueError("API key cannot be empty")
        
        self.vulavula_api_key = vulavula_api_key
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.timeout = timeout
        
        # Pre-build headers - improved by bytte AI
        self._headers = {
            "Content-Type": "application/json",
            "X-CLIENT-TOKEN": self.vulavula_api_key
        }
    
    def send_intent_detection_request(
        self,
        intent_detection_request: IntentDetectionRequest
    ) -> Optional[List[IntentDetectionResponse]]:
        """
        Sends an intent detection request to the Vulavula API and returns the response.
        
        Args:
            intent_detection_request (IntentDetectionRequest):
                The request payload containing the text data for intent detection.
        
        Returns:
            Optional[List[IntentDetectionResponse]]:
                A list of responses with detected intents and associated metadata,
                or None if the request fails.
        
        Raises:
            HTTPError: If the response status code is 4xx or 5xx.
            RequestException: For issues like network errors or invalid requests.
            Timeout: If the request exceeds the timeout period.
        """
        endpoint = f"{self.base_url}/api/v1/classify"
        
        try:
            # Convert request to JSON - improved by bytte AI
            payload = intent_detection_request.model_dump()
            
            logger.info(f"Sending intent detection request to {endpoint}")
            
            response = requests.post(
                endpoint,
                data=json.dumps(payload),
                headers=self._headers,
                timeout=self.timeout  # Added timeout - improved by bytte AI
            )
            
            response.raise_for_status()
            
            # Parse and validate response - improved by bytte AI
            response_data = response.json()
            intent_detection_response = [
                IntentDetectionResponse(**item) for item in response_data
            ]
            
            logger.info(f"Successfully received {len(intent_detection_response)} intent detection results")
            return intent_detection_response
            
        except Timeout as e:
            logger.error(f"Request timeout after {self.timeout}s: {e}")
            raise
            
        except HTTPError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
            
        except RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise
            
        except (KeyError, TypeError, ValueError) as e:
            # Catch response parsing errors - improved by bytte AI
            logger.error(f"Failed to parse response: {str(e)}")
            raise ValueError(f"Invalid response format from API: {str(e)}")
