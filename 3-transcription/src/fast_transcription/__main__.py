import os
import requests
from pprint import pprint
from settings import get_settings


def read_file_data(path: str) -> bytes:
    """
    Read binary data from a file and return it.

    Args:
        path (str): The path to the file to read.

    Returns:
        bytes: The binary content of the file.

    Raises:
        FileNotFoundError: If the file does not exist at the given path.
        IOError: If an error occurs while reading the file.
    """
    # Check if the file exists at the given path
    if not os.path.isfile(path):
        raise FileNotFoundError(f"The file at '{path}' does not exist.")

    try:
        # Open the file in binary read mode and return the content
        with open(path, "rb") as file:
            return file.read()
    except Exception as e:
        # If there is an error reading the file, raise an IOError with the error message
        raise IOError(f"Failed to read file '{path}': {e}")


def send_transcription_request(file_data: bytes, api_key: str, url: str, lang_code: str = "sot") -> dict:
    """
    A helper method that send a transcription request to the API and return the response as a dictionary.

    Args:
        file_data (bytes): The binary data of the audio file to transcribe.
        api_key (str): The API key for authentication.
        url (str): The API endpoint to send the request to.
        lang_code (str, optional): The language code for transcription.

    Returns:
        dict: The API response containing the transcription data.

    Raises:
        ConnectionError: If there is an issue with the API request.
        ValueError: If the response cannot be parsed as JSON.
    """
    headers = {"X-CLIENT-TOKEN": api_key}  # Set the authentication header with the API key
    files = {'upload': ('file_to_transcribe.wav', file_data, 'audio/wav')}  # Prepare the audio file for upload
    params = {"lang_code": lang_code}  # Set the language code for transcription (optional)

    try:
        # Send a POST request to the API with the file data, headers, and parameters
        response = requests.post(url, headers=headers, files=files, params=params)
        response.raise_for_status()  # Raise an error if the response status is not 2xx
    except requests.exceptions.RequestException as e:
        # If there is a network or request issue, raise a ConnectionError
        raise ConnectionError(f"Request failed: {e}")

    try:
        # Attempt to parse the JSON response
        return response.json()
    except ValueError as e:
        # If the response cannot be parsed as JSON, raise a ValueError
        raise ValueError(f"Failed to parse JSON response: {e}")


def main():
    """
    Main function to handle file reading, sending a transcription request, and displaying the response.

    This function will:
        1. Read the audio file from disk.
        2. Send the audio data to the API for transcription.
        3. Print the response from the API.
    """
    settings = get_settings() # Get an instance of the Settings class to access configuration
    api_key = settings.VULAVULA_API_KEY # Get the API key from the settings
    # Define the path to the WAV file for transcription (obtained from the data folder on the root of transcription example) (add one if missing)
    wav_file_path = os.path.join(os.path.dirname(__file__), "../../data/transcription/transcription.wav")
    # Construct the API URL using the base URL and endpoint for transcription (can adjust from v1 to v2alpha when needed)
    api_url = f"{settings.BASE_URL}/v2alpha/transcribe/fast"

    try:
        # Attempt to read the file data from the given file path
        file_data = read_file_data(wav_file_path)
    except (FileNotFoundError, IOError) as e:
        # Handle file-related errors (e.g., file not found, failed to read)
        print(f"Error: {e}")
        return # Exit the program if the file cannot be read

    try:
        # Attempt to send the transcription request and get the response
        response_data = send_transcription_request(file_data, api_key, api_url)
        pprint(response_data) # Pretty-print the response data for inspection
    except (ConnectionError, ValueError) as e:
        # Handle errors related to the API request or response parsing
        print(f"Error: {e}")

# Run the main function if this script is executed directly
if __name__ == "__main__":
    main()
