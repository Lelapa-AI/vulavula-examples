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
import json
import os
import re
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
            # The Live API authenticates via the x-api-key header (not the
            # X-CLIENT-TOKEN header used by the sync-transcription examples).
            headers={"x-api-key": api_key, "Content-Type": "application/json"},
            json={"session": session},
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Failed to mint client secret: {e}")

    return response.json()["value"]


def open_pcm16_wav(wav_path: str):
    """
    Open a WAV file, raising ValueError if it isn't mono 16-bit PCM. Use as a context
    manager (`with open_pcm16_wav(...) as wav_file`) -- the single validation point for
    both the sample-rate lookup and the chunk reader.
    """
    wav_file = wave.open(os.fspath(wav_path), "rb")
    if wav_file.getsampwidth() != 2 or wav_file.getnchannels() != 1:
        wav_file.close()
        raise ValueError("Expected a mono 16-bit PCM WAV file")
    return wav_file


def read_pcm16_chunks(wav_path: str, chunk_ms: int = CHUNK_MS):
    """
    Yield raw PCM16 audio chunks from a mono WAV file, sized to `chunk_ms` milliseconds each.

    Args:
        wav_path (str): Path to a mono 16-bit PCM WAV file.
        chunk_ms (int): Chunk duration in milliseconds.

    Yields:
        bytes: Raw PCM16 audio frames for one chunk.
    """
    with open_pcm16_wav(wav_path) as wav_file:
        frames_per_chunk = int(wav_file.getframerate() * chunk_ms / 1000)
        while True:
            frames = wav_file.readframes(frames_per_chunk)
            if not frames:
                break
            yield frames


def get_wav_sample_rate(wav_path: str) -> int:
    with open_pcm16_wav(wav_path) as wav_file:
        return wav_file.getframerate()


def _emit_delta(label: str, delta: str, current_label: str) -> str:
    """
    Print a transcript delta, starting a new labeled line when the stream switches
    between source and translated output.
    """
    if label != current_label:
        print(f"\n{label}: ", end="", flush=True)
    print(delta, end="", flush=True)
    return label


async def consume_events(ws) -> None:
    """
    Read server events until the session closes, printing transcript/translation
    deltas as they arrive.
    """
    current_label = None
    async for message in ws:
        event = json.loads(message)
        event_type = event.get("type")

        if event_type == "session.input_transcript.delta":
            current_label = _emit_delta("source", event["delta"], current_label)
        elif event_type == "session.output_transcript.delta":
            current_label = _emit_delta("translated", event["delta"], current_label)
        elif event_type == "error":
            print(f"\n[error] {event['error']['message']}", file=sys.stderr)
            return  # session failed -- lets stream_audio stop sending early
        elif event_type == "session.closed":
            print("\n[session closed]")
            return


async def stream_audio(ws_url: str, client_secret: str, sample) -> None:
    """
    Open the Live API WebSocket and stream a sample WAV as PCM16 chunks at realtime
    pace, printing transcript/translation deltas as they arrive.
    """
    async with websockets.connect(
        ws_url,
        subprotocols=["realtime", f"vulavula-insecure-api-key.{client_secret}"],
    ) as ws:
        receiver = asyncio.create_task(consume_events(ws))

        try:
            for chunk in read_pcm16_chunks(sample.path):
                if receiver.done():
                    break  # session ended early (server error / socket closed)
                await ws.send(json.dumps({
                    "type": "session.input_audio_buffer.append",
                    "audio": base64.b64encode(chunk).decode(),
                }))
                await asyncio.sleep(CHUNK_MS / 1000)  # pace at realtime speed
            await ws.send(json.dumps({"type": "session.close"}))
        except websockets.ConnectionClosed:
            pass  # server closed the socket mid-stream

        try:
            await receiver
        except websockets.ConnectionClosed:
            pass  # connection dropped before the session ended cleanly


def print_ground_truth(sample) -> None:
    """
    Print the sample's reference transcript/translation from the metadata CSV so the
    live output can be compared side by side. Reference text only -- no scoring.
    """
    print("\n── Ground truth (data/ metadata CSV) ─────────────")
    print(f"source:     {sample.transcript}")
    print(f"translated: {sample.translation}")


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
    ws_url = re.sub(r"^http", "ws", settings.BASE_URL) + REALTIME_WS_PATH

    print("\nStreaming at realtime pace -- deltas appear as the server sends them.\n")
    asyncio.run(stream_audio(ws_url, client_secret, sample))

    if settings.SHOW_GROUND_TRUTH:
        print_ground_truth(sample)


if __name__ == "__main__":
    main()
