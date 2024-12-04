from pydantic import BaseModel
from typing import List


class IntentExample(BaseModel):
    """
        Represents a single example of an intent, consisting of the intent's name
        and a textual example describing it.

        Attributes:
            intent (str): The name of the intent (e.g., 'Playing', 'Reading').
            example (str): A text example illustrating the intent.
    """
    intent: str
    example: str


class IntentDetectionRequest(BaseModel):
    """
        Represents a request payload for intent detection, containing input text(s)
        to classify and reference examples for intent definitions.

        Attributes:
            inputs (List[str]): A list of text inputs for which intents need to be detected.
            examples (List[IntentExample]): A list of intent examples for model reference.
    """
    inputs: List[str]
    examples: List[IntentExample]


class IntentDetectionScore(BaseModel):
    """
        Represents the score of a detected intent, indicating the model's confidence level.

        Attributes:
            intent (str): The name of the detected intent.
            score (float): The confidence score for the detected intent, between 0 and 1.
    """
    intent: str
    score: float


class IntentDetectionResponse(BaseModel):
    """
        Represents the response from an intent detection API, including probabilities
        for detected intents.

        Attributes:
            probabilities (List[IntentDetectionScore]): A list of intents and their associated scores.
    """
    probabilities: List[IntentDetectionScore]