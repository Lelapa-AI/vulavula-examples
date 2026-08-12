# Python example -- stream a sample from `data/`

Streams one of the bundled isiZulu sample WAVs (indexed in
[`data/vulavula-isizulu-samples - 5_sample_metadata.csv`](../../data/vulavula-isizulu-samples%20-%205_sample_metadata.csv))
over the Vulavula Live API WebSocket at realtime pace. Transcript deltas print as
they arrive; with `SHOW_GROUND_TRUTH=true` the CSV's reference transcript and
translation are printed afterwards, with a similarity score, so you can see exactly
the experience a customer gets: live isiZulu transcription + English translation.

## Setup

```commandline
pdm install -p .
```

Copy `.env.example` to `.env` and fill in `VULAVULA_API_KEY`. Optionally change
`SAMPLE_INDEX` (0-4) to stream a different clip, and set/clear `TARGET_LANGUAGE`
(leave blank for transcription-only). `DATA_DIR` defaults to the repo-root `data/`
folder; override it only if your samples live elsewhere.

## Run

```commandline
pdm run live
```
