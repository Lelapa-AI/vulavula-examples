# Overview
Demonstrates the Vulavula Live API: streaming transcription and (optionally) translation over
a WebSocket, modeled on OpenAI's Realtime API. See the [Live API
docs](https://docs.lelapa.ai/live/realtime) for the full protocol reference.

Two variants are provided:

- [`python/`](python/) — streams a WAV file from disk using a Python WebSocket client.
- [`browser/`](browser/) — captures microphone audio in the browser. Since a real API key
  must never live in browser JS, this variant also includes a tiny local relay server
  (`relay_server.py`) that mints short-lived client secrets on the page's behalf.

## Python example

```commandline
cd python
pdm install -p .
```

Set up `.env` from `.env.example` (your `VULAVULA_API_KEY`, and `AUDIO_FILE_PATH` pointing at
a mono 16-bit PCM WAV file). Leave `TARGET_LANGUAGE` blank for transcription-only, or set it
(e.g. `eng`) to also get translated-transcript deltas.

```commandline
pdm run live
```

## Browser example

```commandline
cd browser
pdm install -p .
```

Set up `.env` from `.env.example` (your `VULAVULA_API_KEY`). Then run the relay server:

```commandline
pdm run relay
```

In a separate terminal, serve the static page (any static file server works, e.g.):

```commandline
python -m http.server 8000
```

Open `http://localhost:8000`, click **Start**, and allow microphone access. Transcript and
translation deltas print live on the page as you speak.
