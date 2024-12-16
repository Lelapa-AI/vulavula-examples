from pydantic import BaseModel
from typing import List


class KnowledgebaseCreateRequest(BaseModel):
    """
    Represents a request to create a knowledgebase.

    Attributes:
        knowledgebase_name (str): The name of the knowledgebase to be created.
    """
    knowledgebase_name: str


class KnowledgebaseCreateResponse(BaseModel):
    """
    Represents the response received after creating a knowledgebase.

    Attributes:
        id (str): The unique identifier of the created knowledgebase.
        knowledgebase_name (str): The name of the created knowledgebase.
    """
    id: str
    knowledgebase_name: str


class KnowledgebaseDocumentAddResponse(BaseModel):
    """
    Represents the response received after adding a document to a knowledgebase.

    Attributes:
        id (str): The unique identifier of the added document.
        knowledgebase_id (str): The unique identifier of the knowledgebase the document belongs to.
        filename (str): The name of the uploaded document file.
    """
    id: str
    knowledgebase_id: str
    filename: str


class SearchResult(BaseModel):
    """
    Represents a single search result from querying a knowledgebase.

    Attributes:
        text (str): The text content of the search result.
        score (float): The confidence score of the search result, typically ranging from 0 to 1.
    """
    text: str
    score: float


class KnowledgebaseQueryResponse(BaseModel):
    """
    Represents the response received after querying a knowledgebase.

    Attributes:
        search_results (List[SearchResult]): A list of search results matching the query.
    """
    search_results: List[SearchResult]


class KnowledgebaseQuery(BaseModel):
    """
    Represents a query to be executed on a knowledgebase.

    Attributes:
        query (str): The search query string.
    """
    query: str