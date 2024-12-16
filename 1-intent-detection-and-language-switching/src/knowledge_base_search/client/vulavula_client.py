import json
import requests
from requests.exceptions import HTTPError, RequestException
from domain.schema.knowledgebase import (
    KnowledgebaseCreateRequest,
    KnowledgebaseCreateResponse,
    KnowledgebaseDocumentAddResponse,
    KnowledgebaseQueryResponse,
    KnowledgebaseQuery
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
            knowledgebase_create_request: KnowledgebaseCreateRequest
    ) -> KnowledgebaseCreateResponse:
        """
        Creates a new knowledgebase.

        Args:
            knowledgebase_create_request (KnowledgebaseCreateRequest): The request object containing
                details about the knowledgebase to be created.

        Returns:
            KnowledgebaseCreateResponse: The response object containing details of the created knowledgebase.

        Raises:
            HTTPError: If the HTTP request returns an error status.
            RequestException: For any other issues during the HTTP request.
        """
        headers = {
            "Content-Type": "application/json",
            "X-CLIENT-TOKEN": self.vulavula_api_key
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/search/knowledgebase",
                data=json.dumps(knowledgebase_create_request.model_dump()),
                headers=headers
            )
            response.raise_for_status()
            knowledge_base_create_response = KnowledgebaseCreateResponse(**response.json())
            return knowledge_base_create_response
        except (HTTPError, RequestException) as e:
            print(e)

    def add_document_to_knowledgebase(
            self,
            knowledgebase_id: str,
            file_path: str
    ) -> KnowledgebaseDocumentAddResponse:
        """
        Adds a document to an existing knowledgebase.

        Args:
            knowledgebase_id (str): The unique identifier of the knowledgebase.
            file_path (str): The file path to the document to be uploaded.

        Returns:
            KnowledgebaseDocumentAddResponse: The response object containing details of the added document.

        Raises:
            HTTPError: If the HTTP request returns an error status.
            RequestException: For any other issues during the HTTP request.
        """
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
            knowledgebase_document_response = KnowledgebaseDocumentAddResponse(**response.json())
            return knowledgebase_document_response
        except (HTTPError, RequestException) as e:
            print(e)

    def query_knowledgebase(
            self,
            knowledgebase_id: str,
            query: KnowledgebaseQuery
    ) -> KnowledgebaseQueryResponse:
        """
        Queries an existing knowledgebase for specific information.

        Args:
            knowledgebase_id (str): The unique identifier of the knowledgebase to query.
            query (KnowledgebaseQuery): The query object containing the search criteria.

        Returns:
            KnowledgebaseQueryResponse: The response object containing the search results.

        Raises:
            HTTPError: If the HTTP request returns an error status.
            RequestException: For any other issues during the HTTP request.
        """
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
            knowledge_base_query_response = KnowledgebaseQueryResponse(**response.json())
            return knowledge_base_query_response
        except (HTTPError, RequestException) as e:
            print(e)

    def delete_knowledgebase(self, knowledgebase_id: str):
        """
        Deletes an existing knowledgebase.

        Args:
           knowledgebase_id (str): The unique identifier of the knowledgebase to be deleted.

        Raises:
           HTTPError: If the HTTP request returns an error status.
           RequestException: For any other issues during the HTTP request.
        """
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