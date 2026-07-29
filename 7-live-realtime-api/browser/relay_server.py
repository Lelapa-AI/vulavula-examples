"""
Tiny local relay server for the browser Live API example.

The browser page must never hold a real VULAVULA_API_KEY -- anyone with devtools open could
read it straight out of the page. Instead, the browser calls this local server, which holds
the real key and mints a short-lived client secret on the page's behalf (the same pattern
recommended by OpenAI's Realtime API docs: "your backend calls the real API, your frontend
gets a short-lived token").

Run with: pdm run relay   (see pyproject.toml)
"""

import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()

VULAVULA_API_KEY = os.environ["VULAVULA_API_KEY"]
BASE_URL = os.environ.get("BASE_URL", "https://vulavula-services.lelapa.ai/api")

app = Flask(__name__)
CORS(app)


@app.post("/mint-token")
def mint_token():
    """
    Mint a short-lived client secret for the browser to use on the Live API WebSocket.

    Expects an optional JSON body: {"target_language": "eng_Latn"}. Omit or leave blank for
    transcription-only.
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
        headers={"X-CLIENT-TOKEN": VULAVULA_API_KEY, "Content-Type": "application/json"},
        json={"session": session},
    )
    response.raise_for_status()

    body = response.json()
    return jsonify({"value": body["value"], "base_url": BASE_URL})


if __name__ == "__main__":
    app.run(port=8787)
