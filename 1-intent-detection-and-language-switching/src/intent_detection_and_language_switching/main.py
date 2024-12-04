import os
from client.vulavula_client import VulavulaClient
from domain.intent_example_parser import IntentExampleParser
from domain.schema.intent_detection import IntentDetectionRequest


if __name__ == "__main__":
    # Path to the JSON file containing intent examples
    intent_example_file_path = "data/intent_examples.json"

    # Parse the intent examples from the JSON file
    intent_examples = IntentExampleParser.from_json(intent_example_file_path)

    # Example input text for which intents need to be detected
    example_input_text = [
        "The sun is out, the birds are singing. Let me go for a swim.",
        "When I have time, I like to read."
    ]

    # Create an intent detection request payload
    intent_detection_request = IntentDetectionRequest(
        inputs=example_input_text,
        examples=intent_examples
    )

    # Initialize the Vulavula client with the API key from the environment variable
    vulavula_client = VulavulaClient(vulavula_api_key=os.getenv("VULAVULA_API_KEY"))

    # Send the request to the Vulavula API and get the detection results
    intent_detection_results = vulavula_client.send_intent_detection_request(intent_detection_request)

    # Print the results in a human-readable format
    print("Intent detection results...\n")
    for i, intent_detection_result in enumerate(intent_detection_results):
        print(f"Intent detection for the input statement: '{example_input_text[i]}'")
        for probability in intent_detection_result.probabilities:
            print(f"Intent: {probability.intent}\t\tScore: {probability.score}")
        print()