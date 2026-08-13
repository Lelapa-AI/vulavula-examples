# Browser example -- realtime transcription + translation in the page

The demo page streams audio to the Vulavula Live API over a WebSocket and shows
transcript/translation deltas live. Two input sources:

- **Sample clip** (default): replays one of the bundled isiZulu WAVs from
  [`data/`](../../data/) (served by the relay server) and shows the clip's
  ground-truth transcript/translation -- read from
  [`data/vulavula-isizulu-samples - 5_sample_metadata.csv`](../../data/vulavula-isizulu-samples%20-%205_sample_metadata.csv)
  -- so you can compare live output with the reference.
- **Microphone**: captures your mic and streams it.

## Setup

```commandline
pdm install -p .
```

Copy `.env.example` to `.env` and fill in `VULAVULA_API_KEY`.

## Run

In one terminal, start the relay server (holds your real key, mints short-lived
client secrets, serves the sample clips + ground truth):

```commandline
pdm run relay
```

In another terminal, serve the static page (any static file server works):

```commandline
python -m http.server 8000
```

Open `http://localhost:8000`, pick a sample (or switch to Microphone), then click
**Start**. Transcript and translation deltas print live as the audio plays/speaks.
