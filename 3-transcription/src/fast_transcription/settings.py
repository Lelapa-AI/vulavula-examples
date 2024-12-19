from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

# The 'Settings' class inherits from Pydantic's BaseSettings, which helps manage
# environment variables and configuration settings for the application.
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",  # Path to the .env file, where environment variables are stored.
        env_file_encoding="utf-8",  # The encoding to use when reading the .env file.
        extra="ignore"  # Ignore any extra fields in the environment variables that aren't part of the Settings class.
    )

    # Define the environment variables the application needs. These will be loaded from the `.env` file.
    VULAVULA_API_KEY: str # The API key required for authenticating with the VULAVULA service. (Obtain the key from https://vulavula.lelapa.ai/)
    BASE_URL: str = 'https://vulavula-services.lelapa.ai/api' # The base URL for the API (this has a default value but can be overridden in the .env file) NOTE: No leading slash should be included.


# The '@lru_cache()' decorator caches the result of the function, so subsequent calls to 'get_settings()'
# will return the same instance of the Settings class, improving performance and ensuring
# that the settings are only loaded once during the application's runtime.
@lru_cache()
def get_settings():
    """
    This function returns an instance of the Settings class, which loads environment variables
    and configuration settings required by the application.

    It leverages the @lru_cache decorator to ensure that the settings are cached after the first call.
    This improves performance by preventing re-loading the settings from the .env file repeatedly.
    """
    return Settings() # Create and return an instance of the Settings class, which will read from the .env file.
