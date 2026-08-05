import os
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List

from client import VulavulaClient
from live import check_live_endpoint, get_wav_sample_rate, stream_live_transcription
from report import CheckResult, Status
from settings import Settings
from wer import word_error_rate

# Known-good (source, source_lang, target_lang, expected_translation) tuples used to
# qualify translation accuracy without requiring the customer to supply their own
# reference data. Expected translations don't need to match verbatim - they're
# compared with a similarity ratio against MIN_TRANSLATION_SIMILARITY.
TRANSLATION_FIXTURES = [
    ("Lo musho ubhalwe ngesiZulu.", "zul_Latn", "eng_Latn", "This sentence is written in isiZulu."),
    ("Sannie is 'n plaas in die Karoo.", "afr_Latn", "eng_Latn", "Sannie is a farm in the Karoo."),
    ("Ke rata ho bala dibuka.", "sot_Latn", "eng_Latn", "I like to read books."),
]


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _status_detail(response) -> str:
    """Human-readable failure detail for a response, covering both HTTP error
    statuses and requests never reaching the server at all (DNS/connection/timeout).

    Deployment error responses are FastAPI HTTPExceptions, so the useful detail
    (e.g. "Invalid sample rate: 8000 Hz") lives at body["detail"]["error"] /
    body["detail"]["message"] - surface that instead of just the status code.
    """
    if response.status_code is None:
        return f"request failed: {getattr(response, 'error', 'unknown error')}"

    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = None

    if isinstance(detail, dict):
        reason = detail.get("error") or detail.get("message")
        if reason:
            return f"got HTTP {response.status_code}: {reason}"
    elif detail:
        return f"got HTTP {response.status_code}: {detail}"

    return f"got HTTP {response.status_code}"


def _transcription_text(body: dict) -> str:
    """Extracts transcription_text from the transcribe endpoint's
    ApiResponseDto envelope: {"success": bool, "data": {"transcription_text": ...}, ...}.
    """
    if not body.get("success"):
        raise ValueError(body.get("message") or body.get("error") or "transcription request did not succeed")
    return (body.get("data") or {}).get("transcription_text", "")


def run_sanity_checks(client: VulavulaClient, settings: Settings) -> List[CheckResult]:
    results = []

    health = client.health()
    if health.response.status_code == 200:
        results.append(CheckResult("Sanity", "Health endpoint reachable", Status.PASS,
                                    f"{health.response.status_code} in {health.latency_ms:.0f}ms"))
    else:
        results.append(CheckResult("Sanity", "Health endpoint reachable", Status.FAIL,
                                    _status_detail(health.response)))

    source, source_lang, target_lang, _ = TRANSLATION_FIXTURES[0]
    translation = client.translate(source, source_lang, target_lang)
    if translation.response.status_code == 200:
        body = translation.response.json()
        if body.get("translated_text"):
            results.append(CheckResult("Sanity", "Translate endpoint returns a valid response", Status.PASS,
                                        f"{translation.response.status_code} in {translation.latency_ms:.0f}ms"))
        else:
            results.append(CheckResult("Sanity", "Translate endpoint returns a valid response", Status.FAIL,
                                        "200 OK but response had no 'translated_text' field"))
    else:
        results.append(CheckResult("Sanity", "Translate endpoint returns a valid response", Status.FAIL,
                                    _status_detail(translation.response)))

    secret = client.mint_realtime_client_secret()
    if secret.response.status_code == 200:
        client_secret = secret.response.json().get("value")
        live = check_live_endpoint(client.base_url, client_secret, settings.LIVE_ENDPOINT_TIMEOUT_S)
        status = Status.PASS if live.success else Status.FAIL
        detail = f"{live.detail} in {live.latency_ms:.0f}ms" if live.success else live.detail
        results.append(CheckResult("Sanity", "Live (realtime) endpoint reachable", status, detail))
    else:
        results.append(CheckResult("Sanity", "Live (realtime) endpoint reachable", Status.FAIL,
                                    f"failed to mint client secret: {_status_detail(secret.response)}"))

    return results


def run_accuracy_checks(client: VulavulaClient, settings: Settings) -> List[CheckResult]:
    results = []

    for source, source_lang, target_lang, expected in TRANSLATION_FIXTURES:
        timed = client.translate(source, source_lang, target_lang)
        if timed.response.status_code != 200:
            results.append(CheckResult("Accuracy", f"Translate '{source[:30]}...'", Status.FAIL,
                                        _status_detail(timed.response)))
            continue

        actual = timed.response.json().get("translated_text", "")
        ratio = _similarity(actual, expected)
        status = Status.PASS if ratio >= settings.MIN_TRANSLATION_SIMILARITY else Status.FAIL
        results.append(CheckResult(
            "Accuracy", f"Translate '{source[:30]}...'", status,
            f"similarity={ratio:.2f} (min {settings.MIN_TRANSLATION_SIMILARITY}) -> got '{actual}'",
        ))

    if settings.AUDIO_FILE_PATH and settings.AUDIO_REFERENCE_TEXT:
        if not os.path.isfile(settings.AUDIO_FILE_PATH):
            results.append(CheckResult("Accuracy", "Transcription WER", Status.FAIL,
                                        f"AUDIO_FILE_PATH not found: {settings.AUDIO_FILE_PATH}"))
        else:
            with open(settings.AUDIO_FILE_PATH, "rb") as f:
                file_data = f.read()
            timed = client.transcribe(file_data, settings.AUDIO_LANG_CODE)
            if timed.response.status_code != 200:
                results.append(CheckResult("Accuracy", "Transcription WER", Status.FAIL,
                                            _status_detail(timed.response)))
            else:
                try:
                    hypothesis = _transcription_text(timed.response.json())
                except ValueError as e:
                    results.append(CheckResult("Accuracy", "Transcription WER", Status.FAIL, str(e)))
                else:
                    wer = word_error_rate(settings.AUDIO_REFERENCE_TEXT, hypothesis)
                    status = Status.PASS if wer <= settings.MAX_TRANSCRIPTION_WER else Status.FAIL
                    results.append(CheckResult(
                        "Accuracy", "Transcription WER", status,
                        f"WER={wer:.2f} (max {settings.MAX_TRANSCRIPTION_WER}) -> got '{hypothesis}'",
                    ))
    else:
        results.append(CheckResult("Accuracy", "Transcription WER", Status.SKIP,
                                    "AUDIO_FILE_PATH / AUDIO_REFERENCE_TEXT not set"))

    return results


@dataclass
class _LatencySample:
    latencies_ms: List[float]

    @property
    def p50(self) -> float:
        ordered = sorted(self.latencies_ms)
        return ordered[len(ordered) // 2]

    @property
    def max(self) -> float:
        return max(self.latencies_ms)


def run_performance_checks(client: VulavulaClient, settings: Settings) -> List[CheckResult]:
    results = []
    samples = max(1, settings.PERFORMANCE_SAMPLES)

    health_latencies = []
    for _ in range(samples):
        timed = client.health()
        if timed.response.status_code == 200:
            health_latencies.append(timed.latency_ms)
    if health_latencies:
        sample = _LatencySample(health_latencies)
        status = Status.PASS if sample.max <= settings.MAX_HEALTH_LATENCY_MS else Status.FAIL
        results.append(CheckResult(
            "Performance", "Health endpoint latency", status,
            f"p50={sample.p50:.0f}ms max={sample.max:.0f}ms (max allowed {settings.MAX_HEALTH_LATENCY_MS:.0f}ms, n={len(health_latencies)})",
        ))
    else:
        results.append(CheckResult("Performance", "Health endpoint latency", Status.FAIL,
                                    "no successful health responses to measure"))

    source, source_lang, target_lang, _ = TRANSLATION_FIXTURES[0]
    translate_latencies = []
    for _ in range(samples):
        timed = client.translate(source, source_lang, target_lang)
        if timed.response.status_code == 200:
            translate_latencies.append(timed.latency_ms)
    if translate_latencies:
        sample = _LatencySample(translate_latencies)
        status = Status.PASS if sample.max <= settings.MAX_TRANSLATE_LATENCY_MS else Status.FAIL
        results.append(CheckResult(
            "Performance", "Translate endpoint latency", status,
            f"p50={sample.p50:.0f}ms max={sample.max:.0f}ms (max allowed {settings.MAX_TRANSLATE_LATENCY_MS:.0f}ms, n={len(translate_latencies)})",
        ))
    else:
        results.append(CheckResult("Performance", "Translate endpoint latency", Status.FAIL,
                                    "no successful translate responses to measure"))

    if settings.AUDIO_FILE_PATH and os.path.isfile(settings.AUDIO_FILE_PATH):
        with open(settings.AUDIO_FILE_PATH, "rb") as f:
            file_data = f.read()
        timed = client.transcribe(file_data, settings.AUDIO_LANG_CODE)
        if timed.response.status_code == 200:
            status = Status.PASS if timed.latency_ms <= settings.MAX_TRANSCRIBE_LATENCY_MS else Status.FAIL
            results.append(CheckResult(
                "Performance", "Transcribe endpoint latency", status,
                f"{timed.latency_ms:.0f}ms (max allowed {settings.MAX_TRANSCRIBE_LATENCY_MS:.0f}ms)",
            ))
        else:
            results.append(CheckResult("Performance", "Transcribe endpoint latency", Status.FAIL,
                                        _status_detail(timed.response)))
    else:
        results.append(CheckResult("Performance", "Transcribe endpoint latency", Status.SKIP,
                                    "AUDIO_FILE_PATH not set"))

    return results


def run_live_streaming_checks(client: VulavulaClient, settings: Settings) -> List[CheckResult]:
    """Streams AUDIO_FILE_PATH over /v1/realtime once and derives both an
    accuracy (WER) and a performance (latency/throughput) result from it -
    minting a client secret and getting session.created only proves the
    WebSocket handshake works, not that the ASR model behind it is running.

    Streaming is paced at real-time speed (like the 7-live-realtime-api
    example), so this is run once and shared across categories rather than
    once per category.
    """
    accuracy_name = "Live transcription WER"
    latency_name = "Live streaming first-delta latency"
    throughput_name = "Live streaming realtime factor"

    if not (settings.AUDIO_FILE_PATH and settings.AUDIO_REFERENCE_TEXT):
        return [
            CheckResult("Accuracy", accuracy_name, Status.SKIP,
                        "AUDIO_FILE_PATH / AUDIO_REFERENCE_TEXT not set"),
            CheckResult("Performance", latency_name, Status.SKIP, "AUDIO_FILE_PATH not set"),
            CheckResult("Performance", throughput_name, Status.SKIP, "AUDIO_FILE_PATH not set"),
        ]

    if not os.path.isfile(settings.AUDIO_FILE_PATH):
        detail = f"AUDIO_FILE_PATH not found: {settings.AUDIO_FILE_PATH}"
        return [
            CheckResult("Accuracy", accuracy_name, Status.FAIL, detail),
            CheckResult("Performance", latency_name, Status.FAIL, detail),
            CheckResult("Performance", throughput_name, Status.FAIL, detail),
        ]

    sample_rate = get_wav_sample_rate(settings.AUDIO_FILE_PATH)
    secret = client.mint_realtime_client_secret(sample_rate=sample_rate)
    if secret.response.status_code != 200:
        detail = f"failed to mint client secret: {_status_detail(secret.response)}"
        return [
            CheckResult("Accuracy", accuracy_name, Status.FAIL, detail),
            CheckResult("Performance", latency_name, Status.FAIL, detail),
            CheckResult("Performance", throughput_name, Status.FAIL, detail),
        ]

    client_secret = secret.response.json().get("value")
    stream = stream_live_transcription(
        client.base_url, client_secret, settings.AUDIO_FILE_PATH, settings.LIVE_ENDPOINT_TIMEOUT_S,
    )
    if not stream.success:
        return [
            CheckResult("Accuracy", accuracy_name, Status.FAIL, stream.detail),
            CheckResult("Performance", latency_name, Status.FAIL, stream.detail),
            CheckResult("Performance", throughput_name, Status.FAIL, stream.detail),
        ]

    wer = word_error_rate(settings.AUDIO_REFERENCE_TEXT, stream.transcript_text)
    accuracy_status = Status.PASS if wer <= settings.MAX_TRANSCRIPTION_WER else Status.FAIL

    latency_status = Status.PASS if stream.first_delta_latency_ms <= settings.MAX_LIVE_FIRST_DELTA_LATENCY_MS else Status.FAIL

    realtime_factor = stream.total_duration_ms / stream.audio_duration_ms if stream.audio_duration_ms else float("inf")
    throughput_status = Status.PASS if realtime_factor <= settings.MAX_LIVE_REALTIME_FACTOR else Status.FAIL

    return [
        CheckResult(
            "Accuracy", accuracy_name, accuracy_status,
            f"WER={wer:.2f} (max {settings.MAX_TRANSCRIPTION_WER}) -> got '{stream.transcript_text}'",
        ),
        CheckResult(
            "Performance", latency_name, latency_status,
            f"{stream.first_delta_latency_ms:.0f}ms (max allowed {settings.MAX_LIVE_FIRST_DELTA_LATENCY_MS:.0f}ms)",
        ),
        CheckResult(
            "Performance", throughput_name, throughput_status,
            f"{realtime_factor:.2f}x (max allowed {settings.MAX_LIVE_REALTIME_FACTOR:.2f}x; "
            f"audio={stream.audio_duration_ms:.0f}ms, processing={stream.total_duration_ms:.0f}ms)",
        ),
    ]
