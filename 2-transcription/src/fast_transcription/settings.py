from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    VULAVULA_API_KEY: str
    BASE_URL: str = 'https://vulavula-services.lelapa.ai/api'


@lru_cache()
def get_settings():
    return Settings()
