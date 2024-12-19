import os
import requests
from pprint import pprint
from settings import get_settings


def read_file_data(path: str) -> bytes:
    if not os.path.exists(path):
        raise FileNotFoundError(f"The file at {path} does not exist.")
    try:
        with open(path, "rb") as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Failed to read file {path}: {e}")


def send_transcription_request(file_data: bytes, api_key: str, url: str, lang_code: str = "sot") -> dict:
    headers = {"X-CLIENT-TOKEN": api_key}
    files = {'upload': ('file_to_transcribe.wav', file_data, 'audio/wav')}
    params = {"lang_code": lang_code}

    try:
        response = requests.post(url, headers=headers, files=files, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Request failed: {e}")

    try:
        return response.json()
    except ValueError as e:
        raise ValueError(f"Failed to parse JSON response: {e}")


def main():
    settings = get_settings()
    api_key = settings.VULAVULA_API_KEY
    wav_file_path = os.path.join(os.path.dirname(__file__), "../../data/transcription/transcription.wav")
    api_url = f"{settings.BASE_URL}/v2alpha/transcribe/fast"

    try:
        file_data = read_file_data(wav_file_path)
    except (FileNotFoundError, IOError) as e:
        print(f"Error: {e}")
        return

    try:
        response_data = send_transcription_request(file_data, api_key, api_url)
        pprint(response_data)
    except (ConnectionError, ValueError) as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
