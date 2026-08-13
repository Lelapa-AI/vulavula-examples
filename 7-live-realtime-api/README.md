# Overview
Demonstrates the Vulavula Live API: streaming transcription and (optionally) translation over
a WebSocket, modeled on OpenAI's Realtime API. See the [Live API
docs](https://docs.lelapa.ai/live/realtime) for the full protocol reference.

> **Note:** you'll need an API key with Live API access.

Both variants stream the bundled isiZulu sample clips in [`data/`](../data/). The clips and
their ground truth (reference transcript + translation, domain/topic, speaker metadata) are
indexed in
[`data/vulavula-isizulu-samples - 5_sample_metadata.csv`](../data/vulavula-isizulu-samples%20-%205_sample_metadata.csv).
Each demo picks a sample, streams it at realtime pace, and shows the live isiZulu transcript
plus English translation deltas -- then lets you compare with the ground truth, i.e. the
experience a customer gets when integrating Live transcription + translation. The Python
example can also stream your own WAV (`AUDIO_FILE_PATH`) so you can verify the API against
your own audio.

## Python example

```commandline
cd python
pdm install -p .
```

Set up `.env` from `.env.example` (your `VULAVULA_API_KEY`). To verify with your own audio,
set `AUDIO_FILE_PATH` to a mono 16-bit PCM WAV (16 or 24 kHz) -- otherwise `SAMPLE_INDEX`
picks one of the bundled clips (0-4, see the metadata CSV). `TARGET_LANGUAGE` defaults to
`eng` (isiZulu → English) -- leave it blank for transcription-only. `SOURCE_LANGUAGE` lets
you override the assumed isiZulu source. Set `SHOW_GROUND_TRUTH=true` to also print a
bundled clip's reference transcript/translation for side-by-side comparison (off by default).

```commandline
pdm run live
```

You'll see `source:` (isiZulu) and `translated:` (English) deltas stream in as the audio
plays, ending with `[session closed]`.

## Browser example

```commandline
cd browser
pdm install -p .
```

Set up `.env` from `.env.example` (your `VULAVULA_API_KEY`). Then run the relay server, which
mints short-lived client secrets and also serves the sample clips + ground truth to the page:

```commandline
pdm run relay
```

In a separate terminal, serve the static page (any static file server works, e.g.):

```commandline
python -m http.server 8000
```

Open `http://localhost:8000`. The page defaults to **Sample clip** mode: pick one of the
bundled clips from `data/`, and the transcript/translation deltas print live next to the
clip's ground truth. Switch to **Microphone** mode to stream your own voice instead.
