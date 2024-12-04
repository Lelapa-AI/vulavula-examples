from pydantic import BaseModel
from typing import List


class IntentExample(BaseModel):
    intent: str
    example: str


class IntentDetectionRequest(BaseModel):
    inputs: List[str]
    examples: List[IntentExample]


class IntentDetectionScore(BaseModel):
    intent: str
    score: float


class IntentDetectionResponse(BaseModel):
    probabilities: List[IntentDetectionScore]