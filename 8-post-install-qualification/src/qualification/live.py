import asyncio
import base64
import json
import time
import wave
from dataclasses import dataclass
from typing import Optional

import websockets

REALTIME_WS_PATH = "/v1/realtime"
_SUBPROTOCOL_PREFIX = "vulavula-insecure-api-key."


@dataclass
class LiveCheckResult:
    success: bool
    detail: str
    latency_ms: float = 0.0


@dataclass
class LiveStreamResult:
    success: bool
    detail: str
    transcript_text: str = ""
    first_delta_latency_ms: float = 0.0
    total_duration_ms: float = 0.0
    audio_duration_ms: float = 0.0


def _ws_url(base_url: str) -> str:
    return base_url.replace("https://", "wss://").replace("http://", "ws://") + REALTIME_WS_PATH


def get_wav_sample_rate(wav_path: str) -> int:
    with wave.open(wav_path, "rb") as wav_file:
        return wav_file.getframerate()


def get_wav_duration_ms(wav_path: str) -> float:
    with wave.open(wav_path, "rb") as wav_file:
        return 1000 * wav_file.getnframes() / float(wav_file.getframerate())


def _read_pcm16_chunks(wav_path: str, chunk_ms: int = 100):
    """Yields raw PCM16 audio chunks from a mono WAV file, sized to `chunk_ms`
    milliseconds each - same chunking as the 7-live-realtime-api example.
    """
    with wave.open(wav_path, "rb") as wav_file:
        if wav_file.getsampwidth() != 2 or wav_file.getnchannels() != 1:
            raise ValueError("Expected a mono 16-bit PCM WAV file")

        frames_per_chunk = int(wav_file.getframerate() * chunk_ms / 1000)
        while True:
            frames = wav_file.readframes(frames_per_chunk)
            if not frames:
                break
            yield frames


async def _open_session(base_url: str, client_secret: str, timeout_s: float) -> LiveCheckResult:
    """Opens the /v1/realtime WebSocket (same client-secret subprotocol
    handshake as the 7-live-realtime-api example) and waits for the server's
    `session.created` event, which is the signal the live/streaming path is
    actually up (not just that the socket accepted a TCP connection).
    """
    start = time.perf_counter()
    try:
        async with websockets.connect(
            _ws_url(base_url),
            subprotocols=["realtime", f"{_SUBPROTOCOL_PREFIX}{client_secret}"],
            open_timeout=timeout_s,
        ) as ws:
            message = await asyncio.wait_for(ws.recv(), timeout=timeout_s)
            latency_ms = (time.perf_counter() - start) * 1000
            event = json.loads(message)

            if event.get("type") != "session.created":
                return LiveCheckResult(False, f"unexpected first event: {event.get('type')!r}", latency_ms)

            await ws.send(json.dumps({"type": "session.close"}))
            session_id = (event.get("session") or {}).get("id", "?")
            return LiveCheckResult(True, f"session.created (session_id={session_id})", latency_ms)
    except asyncio.TimeoutError:
        return LiveCheckResult(False, f"timed out waiting for session.created after {timeout_s:.0f}s")
    except Exception as e:
        return LiveCheckResult(False, f"WebSocket connection failed: {e}")


def check_live_endpoint(base_url: str, client_secret: str, timeout_s: float = 10) -> LiveCheckResult:
    return asyncio.run(_open_session(base_url, client_secret, timeout_s))


async def _stream_transcription(base_url: str, client_secret: str, wav_path: str,
                                 timeout_s: float) -> LiveStreamResult:
    """Streams `wav_path` over /v1/realtime as fast as the socket allows (not
    paced to real-time - this is an accuracy check, not a realistic-client
    simulation) and collects `session.input_transcript.delta` events.

    Unlike `check_live_endpoint`, this exercises the actual ASR model behind
    the live endpoint - a session.created event only proves the WebSocket
    handshake works, not that anything downstream is producing transcripts.
    """
    audio_duration_ms = get_wav_duration_ms(wav_path)
    start = time.perf_counter()
    first_delta_at: Optional[float] = None
    transcript_parts = []

    try:
        async with websockets.connect(
            _ws_url(base_url),
            subprotocols=["realtime", f"{_SUBPROTOCOL_PREFIX}{client_secret}"],
            open_timeout=timeout_s,
        ) as ws:
            created = json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout_s))
            if created.get("type") != "session.created":
                return LiveStreamResult(False, f"unexpected first event: {created.get('type')!r}")

            async def send_audio():
                for chunk in _read_pcm16_chunks(wav_path):
                    await ws.send(json.dumps({
                        "type": "session.input_audio_buffer.append",
                        "audio": base64.b64encode(chunk).decode(),
                    }))

            sender = asyncio.create_task(send_audio())
            close_requested = False

            # The protocol has no explicit "flush"/"end of input" event short of
            # session.close, and closing right after the last chunk is sent can
            # truncate the transcript if the server hasn't finished processing
            # already-sent audio yet - especially since we're sending faster
            # than real-time here. Instead: keep reading; once all audio is
            # sent and no further event arrives within `timeout_s` (i.e. things
            # have gone quiet), only then request session.close.
            while True:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=timeout_s)
                except asyncio.TimeoutError:
                    if close_requested:
                        break  # no session.closed came back; use what we have.
                    if not sender.done():
                        raise  # stalled mid-stream - a genuine failure.
                    await ws.send(json.dumps({"type": "session.close"}))
                    close_requested = True
                    continue

                event = json.loads(message)
                event_type = event.get("type")

                if event_type == "session.input_transcript.delta":
                    if first_delta_at is None:
                        first_delta_at = time.perf_counter()
                    transcript_parts.append(event.get("delta", ""))
                elif event_type == "error":
                    sender.cancel()
                    return LiveStreamResult(False, f"server error: {(event.get('error') or {}).get('message')}")
                elif event_type == "session.closed":
                    break

            await sender
    except asyncio.TimeoutError:
        return LiveStreamResult(False, f"timed out waiting for a server event after {timeout_s:.0f}s")
    except Exception as e:
        return LiveStreamResult(False, f"WebSocket streaming failed: {e}")

    total_duration_ms = (time.perf_counter() - start) * 1000
    first_delta_latency_ms = (first_delta_at - start) * 1000 if first_delta_at else total_duration_ms
    transcript_text = "".join(transcript_parts).strip()

    if not transcript_text:
        return LiveStreamResult(False, "no transcript received", "", first_delta_latency_ms,
                                 total_duration_ms, audio_duration_ms)

    return LiveStreamResult(True, "ok", transcript_text, first_delta_latency_ms,
                             total_duration_ms, audio_duration_ms)


def stream_live_transcription(base_url: str, client_secret: str, wav_path: str,
                               timeout_s: float = 30) -> LiveStreamResult:
    return asyncio.run(_stream_transcription(base_url, client_secret, wav_path, timeout_s))
