"""
Local relay server for the browser Live API example.

The browser page must never hold a real VULAVULA_API_KEY -- anyone with devtools open
could read it straight out of the page. Instead, the browser calls this local server,
which holds the real key and mints a short-lived client secret on the page's behalf
(the same pattern recommended by OpenAI's Realtime API docs: "your backend calls the
real API, your frontend gets a short-lived token").

The relay also serves the bundled sample clips (and their ground truth, read from the
metadata CSV in the repo-root `data/` folder) so the demo page can stream a sample
file instead of the microphone.

Run with: pdm run relay   (see pyproject.toml)
"""

import csv
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

load_dotenv()

VULAVULA_API_KEY = os.environ["VULAVULA_API_KEY"]
BASE_URL = os.environ.get("BASE_URL", "https://api.lelapa.ai")
# Repo-root data/ folder: sample WAVs + metadata index CSV. Anchored to this file so it
# works regardless of the working directory; override with DATA_DIR if needed.
DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parents[2] / "data")))
METADATA_FILENAME = "vulavula-isizulu-samples - 5_sample_metadata.csv"

app = Flask(__name__)
CORS(app)


def load_samples() -> dict:
    """Parse the metadata CSV into {filename: {metadata, ground truth}}."""
    samples = {}
    with (DATA_DIR / METADATA_FILENAME).open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            samples[row["filename"]] = {
                "filename": row["filename"],
                "domain": row["domain"],
                "topic": row["topic"],
                "scenario": row["scenario"],
                "duration": float(row["duration"]),
                "gender": row["gender"],
                "age_range": row["age_range"],
                "transcript": row["transcript"],   # ground-truth source transcript (isiZulu)
                "translation": row["translation"],  # ground-truth translation (English)
            }
    return samples


SAMPLES = load_samples()


@app.get("/samples")
def list_samples():
    """List the bundled samples and their ground truth, for the page's dropdown."""
    return jsonify(list(SAMPLES.values()))


@app.get("/samples/<filename>")
def serve_sample(filename):
    """Serve one sample WAV so the browser can stream it without a microphone."""
    # Membership check against the CSV index blocks path traversal (only exact
    # metadata filenames are ever served).
    wav_path = DATA_DIR / filename
    if filename not in SAMPLES or not wav_path.is_file():
        return jsonify({"error": "unknown sample"}), 404
    return send_file(wav_path, mimetype="audio/wav")


@app.post("/mint-token")
def mint_token():
    """
    Mint a short-lived client secret for the browser to use on the Live API WebSocket.

    Expects an optional JSON body: {"target_language": "eng"}. Omit or leave blank for
    transcription-only. The audio session is minted at 24kHz -- the browser's
    AudioContext sample rate (see INPUT_SAMPLE_RATE in script.js); sample clips and
    mic audio are resampled to it by Web Audio.
    """
    target_language = (request.get_json(silent=True) or {}).get("target_language", "")

    session = {
        "audio": {
            "input": {"format": {"type": "audio/pcm", "rate": 24000}},
        }
    }
    if target_language:
        session["audio"]["output"] = {"language": target_language}

    response = requests.post(
        f"{BASE_URL}/v1/realtime/client_secrets",
        # The Live API's usage gate expects x-api-key, not X-CLIENT-TOKEN -- see vv-auth's
        # /v1/verify-live-usage route.
        headers={"x-api-key": VULAVULA_API_KEY, "Content-Type": "application/json"},
        json={"session": session},
    )
    response.raise_for_status()

    body = response.json()
    return jsonify({"value": body["value"], "base_url": BASE_URL})


if __name__ == "__main__":
    app.run(port=8787)
