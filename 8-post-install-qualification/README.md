# Post-Install Qualification

A qualification script for a self-hosted ("Your Cloud") Vulavula deployment. Run it
against any deployment's base URL to get a pass/fail signal that the install is
successful and nominal, covering three categories:

1. **Sanity** - is the deployment reachable and responding correctly at all
   (health endpoint, a minimal authenticated translate call, and a live check
   that the `/v1/realtime` streaming WebSocket endpoint opens a session).
2. **Accuracy** - do translation (and, optionally, transcription and live
   streaming transcription) results fall within an expected quality range,
   using known-good reference cases.
3. **Performance** - do request latencies fall within an expected range for
   the health, translate, and (optionally) transcribe and live streaming
   endpoints.

Note the live endpoint's sanity check only proves the WebSocket handshake and
session setup work - minting a client secret and getting `session.created`
back doesn't touch the ASR model at all. The optional accuracy/performance
checks below actually stream audio through it and verify a real transcript
comes back, which is what catches e.g. the model backend being unreachable
while the WebSocket layer itself is still healthy.

The script exits with code `0` when every check passes ("QUALIFIED") and `1`
otherwise, so it can be dropped into a post-deployment CI/CD step as well as run
manually.

## Setup

Requires Python 3.10-3.12 (WER scoring uses [werpy](https://pypi.org/project/werpy/),
the same library used elsewhere in the Vulavula stack, whose numpy dependency
doesn't yet ship 3.13 wheels).

### Install dependencies
```commandline
pdm install -p .
```

### Setup .env
Take a look at `.env.example`. Create a `.env` file with the same variables.

At minimum you need:
- `BASE_URL` - the base URL of the self-hosted deployment being qualified (e.g.
  `http://localhost:9000` or `https://vulavula.your-domain.internal`). Note
  self-hosted deployments have no `/api` path prefix, unlike the hosted
  vulavula-services.lelapa.ai API.

If the deployment has `ENABLE_BASIC_AUTH` turned on, also set:
- `BASIC_AUTH_USERNAME` / `BASIC_AUTH_PASSWORD` - matching the deployment's
  `CLIENT_USERNAME` / `CLIENT_PASSWORD` configuration. Leave unset for a
  deployment with basic auth disabled (the default).

Everything else in `.env.example` is an optional threshold with a sensible
default - tune them to the expected envelope for your deployment's hardware:

- `MAX_HEALTH_LATENCY_MS`, `MAX_TRANSLATE_LATENCY_MS`, `MAX_TRANSCRIBE_LATENCY_MS` -
  maximum acceptable latency (ms) per endpoint.
- `PERFORMANCE_SAMPLES` - how many requests to sample per endpoint when
  measuring performance.
- `MIN_TRANSLATION_SIMILARITY` - minimum similarity ratio (0-1) a translation
  must reach against its expected reference translation.
- `MAX_TRANSCRIPTION_WER` - maximum Word Error Rate (0-1) allowed for the
  optional transcription accuracy check.
- `LIVE_ENDPOINT_TIMEOUT_S` - how long to wait for a single `/v1/realtime`
  WebSocket event (`session.created`, or a transcript delta while streaming)
  before treating the live endpoint as unreachable/stalled.
- `MAX_LIVE_FIRST_DELTA_LATENCY_MS` - maximum time from the first audio chunk
  sent to the first transcript delta received while streaming
  `AUDIO_FILE_PATH` over `/v1/realtime`.
- `MAX_LIVE_REALTIME_FACTOR` - maximum ratio of (total time to fully process
  the streamed audio) to (the audio's own duration) - how far behind
  real-time the live endpoint is allowed to lag.

### Optional: qualify transcription (sync and live) accuracy/performance too
The script ships with built-in translation reference cases, so translation
accuracy/performance is always checked. Transcription doesn't ship with a
bundled audio sample (avoiding shipping proprietary/licensed audio in a public
repo), so if you also want to qualify sync (`/v1/transcribe`) and live
(`/v1/realtime`) transcription, set:

- `AUDIO_FILE_PATH` - path to a `.wav` file with known-good speech. **Must be
  16kHz mono** - the deployment's `/v1/transcribe` endpoint rejects any other
  sample rate with a 400 (`Invalid sample rate: N Hz`), and the live endpoint
  needs mono 16-bit PCM to stream.
- `AUDIO_REFERENCE_TEXT` - the ground-truth transcript for that file.
- `AUDIO_LANG_CODE` - the language code of the audio (default `zul`).

If these are unset, the transcription checks (both sync and live) are
reported as `SKIP`. Note the live streaming checks send the audio at
real-time speed (matching how a real client would), so they take about as
long as the audio itself - use a short sample (a few seconds) if you just
want a quick check.

## Running

```commandline
pdm run qualify
```

You can also run it directly:
```commandline
pdm run python src/qualification/__main__.py
```

or simply
```commandline
python src/qualification/__main__.py
```

### Example output
```
Qualifying Vulavula deployment at http://localhost:9000

Sanity
------
  [PASS] Health endpoint reachable                    200 in 42ms
  [PASS] Translate endpoint returns a valid response   200 in 310ms
  [PASS] Live (realtime) endpoint reachable            session.created (session_id=sess_2cadbeb5919149e0) in 383ms

Accuracy
--------
  [PASS] Translate 'Lo musho ubhalwe ngesiZulu....'    similarity=0.94 (min 0.6) -> got 'This sentence is written in isiZulu.'
  [PASS] Translate 'Sannie is 'n plaas in die Ka...'    similarity=0.91 (min 0.6) -> got 'Sannie is a farm in the Karoo.'
  [PASS] Translate 'Ke rata ho bala dibuka....'         similarity=1.00 (min 0.6) -> got 'I like to read books.'
  [SKIP] Transcription WER                              AUDIO_FILE_PATH / AUDIO_REFERENCE_TEXT not set
  [SKIP] Live transcription WER                          AUDIO_FILE_PATH / AUDIO_REFERENCE_TEXT not set

Performance
-----------
  [PASS] Health endpoint latency                        p50=39ms max=51ms (max allowed 1000ms, n=5)
  [PASS] Translate endpoint latency                     p50=298ms max=340ms (max allowed 3000ms, n=5)
  [SKIP] Transcribe endpoint latency                     AUDIO_FILE_PATH not set
  [SKIP] Live streaming first-delta latency              AUDIO_FILE_PATH not set
  [SKIP] Live streaming realtime factor                  AUDIO_FILE_PATH not set

Summary: 5 passed, 0 failed, 4 skipped
Overall: QUALIFIED
```

If any check fails, that section reports `FAIL` with the measured value vs.
the configured threshold, and the process exits with a non-zero status.
