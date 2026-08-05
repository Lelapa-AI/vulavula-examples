import time
from dataclasses import dataclass
from typing import Optional

import requests


class _FailedResponse:
    """A requests.Response-like stand-in used when a request couldn't be sent
    at all (e.g. DNS failure, connection refused, timeout), so callers can
    treat network errors the same way as HTTP error responses.
    """

    def __init__(self, error: Exception):
        self.status_code = None
        self.error = error

    def json(self):
        raise ValueError(f"no response received: {self.error}")


@dataclass
class TimedResponse:
    """An API response paired with how long the request took to complete."""

    response: requests.Response
    latency_ms: float


class VulavulaClient:
    """A thin client for the handful of endpoints exposed by a self-hosted
    Vulavula ("Your Cloud" / their-cloud-mvp) deployment, used to qualify it.

    Unlike the hosted vulavula-services.lelapa.ai API (which authenticates via
    an X-CLIENT-TOKEN header), self-hosted deployments authenticate with
    optional HTTP Basic auth (ENABLE_BASIC_AUTH) and have no `/api` path
    prefix - routes are mounted directly as `/health` and `/v1/...`.
    """

    def __init__(self, base_url: str, username: Optional[str] = None,
                 password: Optional[str] = None, timeout_s: float = 30):
        self.base_url = base_url.rstrip("/")
        self.auth = (username, password) if username and password else None
        self.timeout_s = timeout_s

    def _timed(self, request_fn) -> TimedResponse:
        start = time.perf_counter()
        try:
            response = request_fn()
        except requests.exceptions.RequestException as e:
            response = _FailedResponse(e)
        latency_ms = (time.perf_counter() - start) * 1000
        return TimedResponse(response=response, latency_ms=latency_ms)

    def health(self) -> TimedResponse:
        # Unauthenticated by design - deployment liveness should be checkable
        # regardless of API credentials.
        return self._timed(
            lambda: requests.get(f"{self.base_url}/health", timeout=self.timeout_s)
        )

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> TimedResponse:
        payload = {"text": text, "src_lang": src_lang, "tgt_lang": tgt_lang}
        return self._timed(
            lambda: requests.post(
                f"{self.base_url}/v1/translate",
                json=payload,
                auth=self.auth,
                timeout=self.timeout_s,
            )
        )

    def mint_realtime_client_secret(self, sample_rate: Optional[int] = None) -> TimedResponse:
        """Mints a short-lived client secret for the /v1/realtime WebSocket
        handshake. All request fields have server-side defaults, so an empty
        body is sufficient just to validate the deployment can mint one - pass
        `sample_rate` when the secret will be used to stream a real audio
        file, so the session's declared input rate matches the file's actual
        rate (the server resamples based on this value).
        """
        payload = {}
        if sample_rate is not None:
            payload = {"session": {"audio": {"input": {"format": {"type": "audio/pcm", "rate": sample_rate}}}}}

        return self._timed(
            lambda: requests.post(
                f"{self.base_url}/v1/realtime/client_secrets",
                json=payload,
                auth=self.auth,
                timeout=self.timeout_s,
            )
        )

    def transcribe(self, file_data: bytes, lang_code: str) -> TimedResponse:
        files = {"file": ("sample.wav", file_data, "audio/wav")}
        params = {
            "lang_code": lang_code,
            "enable_translation": False,
            "enable_diarisation": False,
            "enable_dry_run": False,
        }
        return self._timed(
            lambda: requests.post(
                f"{self.base_url}/v1/transcribe",
                auth=self.auth,
                files=files,
                params=params,
                timeout=self.timeout_s,
            )
        )
