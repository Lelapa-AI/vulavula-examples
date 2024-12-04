from pydantic import BaseModel


class Example(BaseModel):
    intent: str
    example: str


class IntentDetectionRequest(BaseModel):
    inputs: list[str]
    examples: list[Example]


class IntentDetectionScore(BaseModel):
    intent: str
    score: float


class IntentDetectionResponse(BaseModel):
    probabilities: list[IntentDetectionScore]