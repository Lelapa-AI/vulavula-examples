"""
Vulavula Live API example -- realtime transcription + translation.

Streams one of the bundled isiZulu sample WAVs from the repo-root `data/` folder
(selected with `SAMPLE_INDEX`, indexed in `data/vulavula-isizulu-samples -
5_sample_metadata.csv`) over the Live API WebSocket at realtime pace. Transcript
deltas print as they arrive; with `SHOW_GROUND_TRUTH` the CSV's expected
transcript/translation is printed afterwards so you can compare live output with
ground truth.

See the [Live API docs](https://docs.lelapa.ai/live/realtime) for the full protocol
reference.
"""

import asyncio
import base64
import difflib
import json
import os
import sys
import wave

import requests
import websockets

from samples import load_samples
from settings import get_settings

CLIENT_SECRET_PATH = "/v1/realtime/client_secrets"
REALTIME_WS_PATH = "/v1/realtime"
CHUNK_MS = 100  # stream in 100ms PCM chunks, paced at realtime speed


def mint_client_secret(base_url: str, api_key: str, target_language: str, input_sample_rate: int) -> str:
    """
    Call the Live API's REST endpoint to mint a short-lived client secret. This step must
    happen server-side with your real API key -- only the returned short-lived value should
    ever reach a client (browser, mobile app, etc).

    Args:
        base_url (str): The Vulavula API base URL.
        api_key (str): Your real Vulavula API key.
        target_language (str): Target language code to enable translation, or "" for
            transcription-only.
        input_sample_rate (int): Sample rate of the audio you'll stream -- must match the
            actual WAV file's frame rate, since the server resamples based on this value.

    Returns:
        str: A short-lived client secret to use for the WebSocket handshake.

    Raises:
        ConnectionError: If the request to mint a client secret fails.
    """
    session = {
        "audio": {
            "input": {"format": {"type": "audio/pcm", "rate": input_sample_rate}},
        }
    }
    if target_language:
        session["audio"]["output"] = {"language": target_language}

    try:
        response = requests.post(
            f"{base_url}{CLIENT_SECRET_PATH}",
            # The Live API's usage gate expects x-api-key, not X-CLIENT-TOKEN (which the
            # other, sync-transcription examples use) -- see vv-auth's
            # /v1/verify-live-usage route.
            headers={"x-api-key": api_key, "Content-Type": "application/json"},
            json={"session": session},
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Failed to mint client secret: {e}")

    return response.json()["value"]


def read_pcm16_chunks(wav_path: str, chunk_ms: int = CHUNK_MS):
    """
    Yield raw PCM16 audio chunks from a mono WAV file, sized to `chunk_ms` milliseconds each.

    Args:
        wav_path (str): Path to a mono 16-bit PCM WAV file.
        chunk_ms (int): Chunk duration in milliseconds.

    Yields:
        bytes: Raw PCM16 audio frames for one chunk.

    Raises:
        ValueError: If the WAV file isn't mono 16-bit PCM.
    """
    with wave.open(os.fspath(wav_path), "rb") as wav_file:
        if wav_file.getsampwidth() != 2 or wav_file.getnchannels() != 1:
            raise ValueError("Expected a mono 16-bit PCM WAV file")

        frames_per_chunk = int(wav_file.getframerate() * chunk_ms / 1000)
        while True:
            frames = wav_file.readframes(frames_per_chunk)
            if not frames:
                break
            yield frames


def get_wav_sample_rate(wav_path: str) -> int:
    with wave.open(os.fspath(wav_path), "rb") as wav_file:
        return wav_file.getframerate()


def _emit_delta(label: str, delta: str, current_label: str, parts: list) -> str:
    """
    Print a transcript delta, starting a new labeled line when the stream switches
    between source and translated output. Also accumulates the delta in `parts`.
    """
    parts.append(delta)
    if label != current_label:
        print(f"\n{label}: ", end="", flush=True)
    print(delta, end="", flush=True)
    return label


async def consume_events(ws, source_parts: list, translated_parts: list) -> None:
    """
    Read server events until the session closes: print transcript/translation deltas
    as they arrive and accumulate them for the ground-truth comparison.
    """
    current_label = None
    async for message in ws:
        event = json.loads(message)
        event_type = event.get("type")

        if event_type == "session.input_transcript.delta":
            current_label = _emit_delta("source", event["delta"], current_label, source_parts)
        elif event_type == "session.output_transcript.delta":
            current_label = _emit_delta("translated", event["delta"], current_label, translated_parts)
        elif event_type == "error":
            print(f"\n[error] {event['error']['message']}", file=sys.stderr)
            return  # session failed -- lets stream_audio stop sending early
        elif event_type == "session.closed":
            print("\n[session closed]")
            return


async def stream_audio(ws_url: str, client_secret: str, sample) -> tuple:
    """
    Open the Live API WebSocket, stream a sample WAV as PCM16 chunks at realtime pace,
    and return the accumulated (source, translated) transcripts.
    """
    async with websockets.connect(
        ws_url,
        subprotocols=["realtime", f"vulavula-insecure-api-key.{client_secret}"],
    ) as ws:
        source_parts, translated_parts = [], []
        receiver = asyncio.create_task(consume_events(ws, source_parts, translated_parts))

        for chunk in read_pcm16_chunks(sample.path):
            if receiver.done():
                break  # session ended early (server error / socket closed)
            await ws.send(json.dumps({
                "type": "session.input_audio_buffer.append",
                "audio": base64.b64encode(chunk).decode(),
            }))
            await asyncio.sleep(CHUNK_MS / 1000)  # pace at realtime speed

        await ws.send(json.dumps({"type": "session.close"}))
        await receiver
        return "".join(source_parts), "".join(translated_parts)


def print_ground_truth(sample, live_source: str, live_translated: str) -> None:
    """
    Print the sample's ground-truth transcript/translation from the metadata CSV and a
    similarity score against what the Live API actually produced.
    """
    print("\n── Ground truth (data/ metadata CSV) ─────────────")
    print(f"source:     {sample.transcript}")
    print(f"translated: {sample.translation}")

    if not live_source.strip():
        print("\n(no live transcript captured -- check VULAVULA_API_KEY and BASE_URL)")
        return

    source_sim = difflib.SequenceMatcher(None, live_source, sample.transcript).ratio()
    print(f"\nsimilarity vs live output: source {source_sim:.1%}")
    if live_translated.strip():
        trans_sim = difflib.SequenceMatcher(None, live_translated, sample.translation).ratio()
        print(f"                           translation {trans_sim:.1%}")


def main():
    """
    Pick a sample from the data/ index, mint a client secret, stream the WAV over the
    Live API WebSocket at realtime pace, then (optionally) compare with ground truth.
    """
    settings = get_settings()

    samples = load_samples(settings.DATA_DIR)
    if not samples:
        sys.exit(f"No samples found in {settings.DATA_DIR!r} -- check DATA_DIR.")
    if not 0 <= settings.SAMPLE_INDEX < len(samples):
        sys.exit(f"SAMPLE_INDEX {settings.SAMPLE_INDEX} out of range (0-{len(samples) - 1}).")
    sample = samples[settings.SAMPLE_INDEX]

    print("Vulavula Live API -- realtime transcription + translation")
    print(f"▶ Sample {settings.SAMPLE_INDEX + 1}/{len(samples)} -- {sample.domain} · {sample.topic} · {sample.scenario}")
    print(f"  file:    {sample.filename}")
    print(f"  speaker: {sample.gender}, {sample.age_range} · {sample.duration:.1f}s")
    print(f"  target:  {settings.TARGET_LANGUAGE or '(transcription-only)'}")

    input_sample_rate = get_wav_sample_rate(sample.path)
    client_secret = mint_client_secret(
        settings.BASE_URL, settings.VULAVULA_API_KEY, settings.TARGET_LANGUAGE, input_sample_rate
    )
    ws_url = settings.BASE_URL.replace("https://", "wss://").replace("http://", "ws://") + REALTIME_WS_PATH

    print("\nStreaming at realtime pace -- deltas appear as the server sends them.\n")
    live_source, live_translated = asyncio.run(stream_audio(ws_url, client_secret, sample))

    if settings.SHOW_GROUND_TRUTH:
        print_ground_truth(sample, live_source, live_translated)


if __name__ == "__main__":
    main()
