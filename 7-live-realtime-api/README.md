# Overview
Demonstrates the Vulavula Live API: streaming transcription and (optionally) translation over
a WebSocket, modeled on OpenAI's Realtime API. See the [Live API
docs](https://docs.lelapa.ai/live/realtime) for the full protocol reference.

> **Note:** unlike the other examples in this repo, `/v1/realtime` isn't routed on the public
> `api.lelapa.ai` product domain yet -- it currently only exists on their-cloud-mvp's own
> staging host (`triton.staging.lelapa.ai`, the default `BASE_URL` below), and isn't deployed
> to prod at all yet. You'll also need an API key with a `REALTIME`-channel subscription
> provisioned for it to pass the usage gate.

Both variants stream the bundled isiZulu sample clips in [`data/`](../data/). The clips and
their ground truth (reference transcript + translation, domain/topic, speaker metadata) are
indexed in
[`data/vulavula-isizulu-samples - 5_sample_metadata.csv`](../data/vulavula-isizulu-samples%20-%205_sample_metadata.csv).
Each demo picks a sample, streams it at realtime pace, and shows the live isiZulu transcript
plus English translation deltas -- then lets you compare with the ground truth, i.e. the
experience a customer gets when integrating Live transcription + translation.

## Python example

```commandline
cd python
pdm install -p .
```

Set up `.env` from `.env.example` (your `VULAVULA_API_KEY`). `SAMPLE_INDEX` picks which
clip to stream (0-4, see the metadata CSV); `TARGET_LANGUAGE` defaults to `eng`
(isiZulu → English) -- leave it blank for transcription-only. With `SHOW_GROUND_TRUTH=true`
(default) the CSV's reference transcript/translation and a similarity score are printed after
streaming.

```commandline
pdm run live
```

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
