import json
from typing import List
from collections import Counter
from .schema import IntentExample


def is_intent_example_list_valid(intent_example_list: List[IntentExample]) -> bool:
    """
        Validates whether the provided list of intent examples satisfies the following conditions:
        - There are at least two distinct types of intents.
        - Each intent type has at least two examples.

        Args:
            intent_example_list (List[IntentExample]): A list of intent examples to validate.

        Returns:
            bool: True if the list satisfies the conditions, False otherwise.

        Prints:
            Validation messages if the list fails to meet the conditions.
    """
    intent_counts = Counter(example.intent for example in intent_example_list)
    if len(intent_counts) < 2:
        print("Validation failed: Less than two types of intents exist.")
        return False
    if any(count < 2 for count in intent_counts.values()):
        print("Validation failed: At least one intent has less than two examples.")
        return False
    return True


class IntentExampleParser:
    """
        A utility class for parsing and validating intent examples from JSON files.
    """
    @staticmethod
    def from_json(file_path) -> List[IntentExample]:
        """
            Parses a JSON file to create a list of IntentExample objects. Validates that the list
            meets the minimum requirements for distinct intents and examples per intent.

            Args:
                file_path (str): The path to the JSON file containing the intent examples.

            Returns:
                List[IntentExample]: A list of IntentExample objects if validation is successful.

            Raises:
                ValueError: If the intent examples do not meet the validation criteria.
        """
        with open(file_path, 'r') as file:
            data = json.load(file)
        intent_example_list = [IntentExample(**item) for item in data]
        if is_intent_example_list_valid(intent_example_list):
            return intent_example_list
        else:
            raise ValueError("Intent examples do not satisfy minimum requirements")