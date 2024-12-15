from pydantic import BaseModel
from typing import List


class KnowledgeBaseCreateRequest(BaseModel):
    knowledgebase_name: str


class KnowledgeBaseCreateResponse(BaseModel):
    id: str
    knowledgebase_name: str


class KnowledgeBaseDocumentAddResponse(BaseModel):
    id: str
    knowledgebase_id: str
    filename: str


class SearchResult(BaseModel):
    text: str
    score: float


class KnowledgeBaseQueryResponse(BaseModel):
    search_results: List[SearchResult]


class KnowledgeBaseQuery(BaseModel):
    query: str