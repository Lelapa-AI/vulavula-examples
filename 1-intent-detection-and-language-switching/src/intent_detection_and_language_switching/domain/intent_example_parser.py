import json
from typing import List
from .schema import IntentExample


class IntentExampleParser:
    @staticmethod
    def from_json(file_path) -> List[IntentExample]:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return [IntentExample(**item) for item in data]
