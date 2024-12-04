import json
from typing import List
from collections import Counter
from .schema import IntentExample



def is_intent_example_list_valid(intent_example_list: List[IntentExample]) -> bool:
    intent_counts = Counter(example.intent for example in intent_example_list)
    if len(intent_counts) < 2:
        print("Validation failed: Less than two types of intents exist.")
        return False
    if any(count < 2 for count in intent_counts.values()):
        print("Validation failed: At least one intent has less than two examples.")
        return False
    return True


class IntentExampleParser:
    @staticmethod
    def from_json(file_path) -> List[IntentExample]:
        with open(file_path, 'r') as file:
            data = json.load(file)
        intent_example_list = [IntentExample(**item) for item in data]
        if is_intent_example_list_valid(intent_example_list):
            return intent_example_list
        else:
            raise ValueError("Intent examples do not satisfy minimum requirements")