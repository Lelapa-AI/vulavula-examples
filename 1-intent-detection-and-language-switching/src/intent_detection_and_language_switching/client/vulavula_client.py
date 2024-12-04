import json
import requests
from typing import List
from requests.exceptions import HTTPError, RequestException
from domain.schema import IntentDetectionRequest, IntentDetectionResponse


class VulavulaClient:
    def __init__(self, vulavula_api_key: str):
        self.vulavula_api_key = vulavula_api_key
        self.base_url = "https://vulavula-services.lelapa.ai"

    def send_intent_detection_request(
            self,
            intent_detection_request: IntentDetectionRequest
    ) -> List[IntentDetectionResponse]:
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