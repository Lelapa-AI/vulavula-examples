from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchor the default to the repo-root data/ folder relative to this file, so the example
# works regardless of the working directory it's run from (same convention as
# 3-transcription). Can still be overridden via DATA_DIR in .env.
DEFAULT_DATA_DIR = str(Path(__file__).resolve().parents[4] / "data")


class Settings(BaseSettings):
    """Environment-driven configuration for the Live API example (see `.env.example`)."""

    model_config = SettingsConfigDict(
        env_file=".env",  # Path to the .env file, where environment variables are stored.
        env_file_encoding="utf-8",  # The encoding to use when reading the .env file.
        extra="ignore",  # Ignore any extra fields in the environment variables that aren't part of the Settings class.
    )

    # Your Vulavula API key. (Obtain the key from https://vulavula.lelapa.ai/)
    VULAVULA_API_KEY: str

    # The base URL for the API (no leading slash).
    BASE_URL: str = "https://api.lelapa.ai"

    # Folder containing the sample WAVs and the metadata index CSV (repo-root `data/`).
    # Defaults to the repo-root data/ folder next to this example; override if your
    # samples live elsewhere.
    DATA_DIR: str = DEFAULT_DATA_DIR

    # Which row of the metadata CSV to stream (0-based).
    SAMPLE_INDEX: int = 0

    # Target language code to enable translation (e.g. "eng" for isiZulu -> English).
    # Leave blank ("") for transcription-only.
    TARGET_LANGUAGE: str = "eng"

    # Print the CSV's ground-truth transcript/translation after streaming, with a
    # similarity score against what the Live API produced. Off by default: the score
    # isn't an accuracy benchmark while the models are being tuned.
    SHOW_GROUND_TRUTH: bool = False


# The '@lru_cache()' decorator caches the result of the function, so subsequent calls
# to 'get_settings()' return the same instance, and settings are only loaded from the
# .env file once during the application's runtime.
@lru_cache()
def get_settings():
    """
    Return a cached Settings instance loaded from the `.env` file.
    """
    return Settings()
