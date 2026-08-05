from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


# The 'Settings' class inherits from Pydantic's BaseSettings, which helps manage
# environment variables and configuration settings for the application.
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Base URL of the self-hosted ("Your Cloud") deployment being qualified.
    # Self-hosted deployments have no `/api` path prefix (unlike the hosted
    # vulavula-services.lelapa.ai API) - routes are mounted at `/health`, `/v1/...`.
    BASE_URL: str = "http://localhost:9000"

    # Self-hosted deployments authenticate via optional HTTP Basic auth (the
    # ENABLE_BASIC_AUTH / CLIENT_USERNAME / CLIENT_PASSWORD settings on the
    # deployment itself), not the hosted API's X-CLIENT-TOKEN header. Leave
    # unset if the deployment has basic auth disabled.
    BASIC_AUTH_USERNAME: Optional[str] = None
    BASIC_AUTH_PASSWORD: Optional[str] = None

    # Performance thresholds. Tune these to the expected envelope for the
    # hardware/deployment being qualified.
    MAX_HEALTH_LATENCY_MS: float = 1000
    MAX_TRANSLATE_LATENCY_MS: float = 3000
    MAX_TRANSCRIBE_LATENCY_MS: float = 15000
    PERFORMANCE_SAMPLES: int = 5

    # How long to wait for a single /v1/realtime WebSocket event (session.created,
    # or a transcript delta while streaming) before treating the live/streaming
    # endpoint as unreachable/stalled.
    LIVE_ENDPOINT_TIMEOUT_S: float = 10
    # Maximum time from the first audio chunk sent to the first transcript delta
    # received while streaming AUDIO_FILE_PATH over /v1/realtime.
    MAX_LIVE_FIRST_DELTA_LATENCY_MS: float = 5000
    # Maximum ratio of (total time to fully process the streamed audio) to
    # (the audio's own duration) - i.e. how far behind real-time the live
    # endpoint is allowed to lag. 1.0 would mean it keeps up exactly; some
    # slack is expected since audio is sent paced at real-time speed already.
    MAX_LIVE_REALTIME_FACTOR: float = 1.5

    # Accuracy thresholds.
    MIN_TRANSLATION_SIMILARITY: float = 0.6
    MAX_TRANSCRIPTION_WER: float = 0.3

    # Optional transcription accuracy check inputs. When unset, that check is skipped.
    AUDIO_FILE_PATH: Optional[str] = None
    AUDIO_REFERENCE_TEXT: Optional[str] = None
    AUDIO_LANG_CODE: str = "zul"


@lru_cache()
def get_settings() -> Settings:
    """Returns a cached Settings instance loaded from the environment / .env file."""
    return Settings()
