# Python example — realtime transcription + translation

A minimal reference for the Vulavula Live API: streams a WAV over a WebSocket at realtime
pace and prints `source:` / `translated:` deltas as the server produces them.

Use it to verify your integration:

- **Bundled sample** (default) — stream one of the isiZulu clips indexed in
  [`data/vulavula-isizulu-samples - 5_sample_metadata.csv`](../../data/vulavula-isizulu-samples%20-%205_sample_metadata.csv).
- **Your own audio** — set `AUDIO_FILE_PATH` to a mono 16-bit PCM WAV (16 or 24 kHz).

## Setup

```commandline
pdm install -p .
```

Copy `.env.example` to `.env` and fill in `VULAVULA_API_KEY`.

## Run

```commandline
pdm run live
```

Configuration (all optional, in `.env`):

| Variable | Default | Purpose |
| --- | --- | --- |
| `SAMPLE_INDEX` | `0` | Which bundled clip to stream (0-4) |
| `AUDIO_FILE_PATH` | *(unset)* | Stream your own WAV instead of a bundled clip |
| `SOURCE_LANGUAGE` | *(API default: isiZulu)* | e.g. `zul`, `sot`, `eng` |
| `TARGET_LANGUAGE` | `eng` | Translation target; blank = transcription-only |
| `SHOW_GROUND_TRUTH` | `false` | Also print a bundled clip's reference text (no scoring) |

Success looks like live `source:` (isiZulu) and `translated:` (English) deltas streaming in,
ending with `[session closed]`.
