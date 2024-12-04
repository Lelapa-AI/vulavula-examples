import json
import requests
from typing import List
from requests.exceptions import HTTPError, RequestException
from domain.schema import IntentDetectionRequest, IntentDetectionResponse


class VulavulaClient:
    """
        A client for interacting with the Vulavula intent detection API.

        Attributes:
            vulavula_api_key (str): The API key for authenticating requests to the Vulavula service.
            base_url (str): The base URL for the Vulavula API.
    """
    def __init__(self, vulavula_api_key: str):
        """
            Initializes the VulavulaClient with the provided API key.

            Args:
                vulavula_api_key (str): The API key for accessing the Vulavula API.
        """
        self.vulavula_api_key = vulavula_api_key
        self.base_url = "https://vulavula-services.lelapa.ai"

    def send_intent_detection_request(
            self,
            intent_detection_request: IntentDetectionRequest
    ) -> List[IntentDetectionResponse]:
        """
            Sends an intent detection request to the Vulavula API and returns the response.

            Args:
                intent_detection_request (IntentDetectionRequest):
                    The request payload containing the text data for intent detection.

            Returns:
                List[IntentDetectionResponse]:
                    A list of responses with detected intents and associated metadata.

            Raises:
                HTTPError: If the response status code is 4xx or 5xx.
                RequestException: For issues like network errors or invalid requests.
        """
        headers = {
            "Content-Type": "application/json",
            "X-CLIENT-TOKEN": self.vulavula_api_key
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/classify",
                data=json.dumps(intent_detection_request.model_dump()),
                headers=headers
            )
            response.raise_for_status()
            intent_detection_response = [IntentDetectionResponse(**item) for item in response.json()]
            return intent_detection_response
        except (HTTPError, RequestException) as e:
            print(e)