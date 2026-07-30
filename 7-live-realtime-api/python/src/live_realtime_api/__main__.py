import asyncio
import base64
import json
import wave

import requests
import websockets

from settings import get_settings

CLIENT_SECRET_PATH = "/v1/realtime/client_secrets"
REALTIME_WS_PATH = "/v1/realtime"


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
            headers={"X-CLIENT-TOKEN": api_key, "Content-Type": "application/json"},
            json={"session": session},
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Failed to mint client secret: {e}")

    return response.json()["value"]


def read_pcm16_chunks(wav_path: str, chunk_ms: int = 100):
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
    with wave.open(wav_path, "rb") as wav_file:
        if wav_file.getsampwidth() != 2 or wav_file.getnchannels() != 1:
            raise ValueError("Expected a mono 16-bit PCM WAV file")

        frames_per_chunk = int(wav_file.getframerate() * chunk_ms / 1000)
        while True:
            frames = wav_file.readframes(frames_per_chunk)
            if not frames:
                break
            yield frames


def get_wav_sample_rate(wav_path: str) -> int:
    with wave.open(wav_path, "rb") as wav_file:
        return wav_file.getframerate()


async def print_server_events(ws) -> None:
    """
    Read and print server events (transcript/translation deltas, errors) until the session
    closes.
    """
    async for message in ws:
        event = json.loads(message)
        event_type = event.get("type")

        if event_type == "session.input_transcript.delta":
            print(f"[source] {event['delta']}", end="", flush=True)
        elif event_type == "session.output_transcript.delta":
            print(f"[translated] {event['delta']}", end="", flush=True)
        elif event_type == "error":
            print(f"\n[error] {event['error']['message']}")
        elif event_type == "session.closed":
            print("\n[session closed]")
            return


async def stream_audio(ws_url: str, client_secret: str, wav_path: str) -> None:
    """
    Open the Live API WebSocket, stream a WAV file as PCM16 chunks, and print incoming
    transcript/translation events as they arrive.
    """
    async with websockets.connect(
        ws_url,
        subprotocols=["realtime", f"vulavula-insecure-api-key.{client_secret}"],
    ) as ws:
        receiver = asyncio.create_task(print_server_events(ws))

        for chunk in read_pcm16_chunks(wav_path):
            await ws.send(json.dumps({
                "type": "session.input_audio_buffer.append",
                "audio": base64.b64encode(chunk).decode(),
            }))
            await asyncio.sleep(0.1)

        await ws.send(json.dumps({"type": "session.close"}))
        await receiver


def main():
    """
    Mint a client secret, stream the configured WAV file over the Live API WebSocket, and
    print transcript (and, if TARGET_LANGUAGE is set, translation) deltas as they arrive.
    """
    settings = get_settings()

    input_sample_rate = get_wav_sample_rate(settings.AUDIO_FILE_PATH)
    client_secret = mint_client_secret(
        settings.BASE_URL, settings.VULAVULA_API_KEY, settings.TARGET_LANGUAGE, input_sample_rate
    )
    ws_url = settings.BASE_URL.replace("https://", "wss://").replace("http://", "ws://") + REALTIME_WS_PATH

    asyncio.run(stream_audio(ws_url, client_secret, settings.AUDIO_FILE_PATH))


if __name__ == "__main__":
    main()
