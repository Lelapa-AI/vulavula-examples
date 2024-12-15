import json
import requests
from requests.exceptions import HTTPError, RequestException
from domain.schema import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseCreateResponse,
    KnowledgeBaseDocumentAddResponse,
    KnowledgeBaseQueryResponse,
    KnowledgeBaseQuery
)


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

    def create_knowledge_base(
            self,
            knowledge_base_create_request: KnowledgeBaseCreateRequest
    ) -> KnowledgeBaseCreateResponse:
        headers = {
            "Content-Type": "application/json",
            "X-CLIENT-TOKEN": self.vulavula_api_key
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/search/knowledgebase",
                data=json.dumps(knowledge_base_create_request.model_dump()),
                headers=headers
            )
            response.raise_for_status()
            knowledge_base_create_response = KnowledgeBaseCreateResponse(**response.json())
            return knowledge_base_create_response
        except (HTTPError, RequestException) as e:
            print(e)

    def add_document_to_knowledgebase(
            self,
            knowledgebase_id: str,
            file_path: str
    ) -> KnowledgeBaseDocumentAddResponse:
        files = {
            "file": open(file_path, "rb")
        }
        headers = {
            "X-CLIENT-TOKEN": self.vulavula_api_key
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/search/knowledgebase/{knowledgebase_id}/document",
                headers=headers,
                files=files
            )
            response.raise_for_status()
            knowledgebase_document_response = KnowledgeBaseDocumentAddResponse(**response.json())
            return knowledgebase_document_response
        except (HTTPError, RequestException) as e:
            print(e)

    def query_knowledgebase(
            self,
            knowledgebase_id: str,
            query: KnowledgeBaseQuery
    ) -> KnowledgeBaseQueryResponse:
        headers = {
            "Content-Type": "application/json",
            "X-CLIENT-TOKEN": self.vulavula_api_key
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/search/knowledgebase/{knowledgebase_id}/query",
                data=json.dumps(query.model_dump()),
                headers=headers
            )
            response.raise_for_status()
            knowledge_base_query_response = KnowledgeBaseQueryResponse(**response.json())
            return knowledge_base_query_response
        except (HTTPError, RequestException) as e:
            print(e)

    def delete_knowledgebase(self, knowledgebase_id: str):
        headers = {
            "Content-Type": "application/json",
            "X-CLIENT-TOKEN": self.vulavula_api_key
        }
        try:
            response = requests.delete(
                f"{self.base_url}/api/v1/search/knowledgebase/{knowledgebase_id}",
                headers=headers
            )
            response.raise_for_status()
        except HTTPError as e:
            print(e)