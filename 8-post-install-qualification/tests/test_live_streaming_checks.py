import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "qualification"))

import checks  # noqa: E402
from report import Status  # noqa: E402
from settings import Settings  # noqa: E402


def _settings(**overrides):
    defaults = dict(
        AUDIO_FILE_PATH="/tmp/does-not-matter.wav",
        AUDIO_REFERENCE_TEXT="the quick brown fox",
        MAX_TRANSCRIPTION_WER=0.3,
        MAX_LIVE_FIRST_DELTA_LATENCY_MS=5000,
        MAX_LIVE_REALTIME_FACTOR=1.5,
    )
    defaults.update(overrides)
    return Settings(**defaults)


def _client_with_secret(monkeypatch, secret_status=200):
    client = SimpleNamespace(base_url="http://localhost:9000")
    response = SimpleNamespace(status_code=secret_status, json=lambda: {"value": "sekrit"})
    client.mint_realtime_client_secret = lambda sample_rate=None: SimpleNamespace(response=response, latency_ms=1)
    return client


def test_all_checks_pass_when_stream_is_fast_and_accurate(monkeypatch):
    monkeypatch.setattr(checks, "get_wav_sample_rate", lambda path: 16000)
    monkeypatch.setattr(checks, "stream_live_transcription", lambda *a, **k: SimpleNamespace(
        success=True, detail="ok", transcript_text="the quick brown fox",
        first_delta_latency_ms=200, total_duration_ms=1000, audio_duration_ms=1000,
    ))
    monkeypatch.setattr(os.path, "isfile", lambda path: True)

    client = _client_with_secret(monkeypatch)
    results = checks.run_live_streaming_checks(client, _settings())

    assert {r.name: r.status for r in results} == {
        "Live transcription WER": Status.PASS,
        "Live streaming first-delta latency": Status.PASS,
        "Live streaming realtime factor": Status.PASS,
    }


def test_fails_on_high_wer_slow_first_delta_and_slow_throughput(monkeypatch):
    monkeypatch.setattr(checks, "get_wav_sample_rate", lambda path: 16000)
    monkeypatch.setattr(checks, "stream_live_transcription", lambda *a, **k: SimpleNamespace(
        success=True, detail="ok", transcript_text="completely wrong output here",
        first_delta_latency_ms=9000, total_duration_ms=5000, audio_duration_ms=1000,
    ))
    monkeypatch.setattr(os.path, "isfile", lambda path: True)

    client = _client_with_secret(monkeypatch)
    results = checks.run_live_streaming_checks(client, _settings())

    assert {r.name: r.status for r in results} == {
        "Live transcription WER": Status.FAIL,
        "Live streaming first-delta latency": Status.FAIL,
        "Live streaming realtime factor": Status.FAIL,
    }


def test_stream_failure_fails_all_three_checks(monkeypatch):
    """A model outage (e.g. the ASR backend unreachable) must surface as a
    FAIL across all three derived checks, not a silent PASS - this is the
    gap a session.created-only check has: minting a token and opening the
    socket doesn't touch the model at all.
    """
    monkeypatch.setattr(checks, "get_wav_sample_rate", lambda path: 16000)
    monkeypatch.setattr(checks, "stream_live_transcription", lambda *a, **k: SimpleNamespace(
        success=False, detail="timed out waiting for a server event after 10s",
        transcript_text="", first_delta_latency_ms=0, total_duration_ms=0, audio_duration_ms=0,
    ))
    monkeypatch.setattr(os.path, "isfile", lambda path: True)

    client = _client_with_secret(monkeypatch)
    results = checks.run_live_streaming_checks(client, _settings())

    assert all(r.status == Status.FAIL for r in results)
    assert all("timed out" in r.detail for r in results)


def test_skips_when_audio_not_configured(monkeypatch):
    client = _client_with_secret(monkeypatch)
    results = checks.run_live_streaming_checks(client, _settings(AUDIO_FILE_PATH=None))

    assert all(r.status == Status.SKIP for r in results)
