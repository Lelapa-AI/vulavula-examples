// Vulavula Live API browser example: realtime transcription + translation.
//
// The real VULAVULA_API_KEY never touches this file -- it lives only in relay_server.py.
// This page calls the local relay server to mint a short-lived client secret, then uses it
// on the WebSocket handshake via `Sec-WebSocket-Protocol` (browsers can't set custom headers
// during a WS handshake, so this is the standard workaround -- see the Live API docs page).
//
// Two input sources:
//   - "sample": replays a bundled isiZulu clip from data/ (served by the relay) and shows
//     its ground-truth transcript/translation for comparison.
//   - "mic":    captures your microphone.

const RELAY_URL = "http://localhost:8787";
const REALTIME_WS_PATH = "/v1/realtime";
const INPUT_SAMPLE_RATE = 24000;

const startButton = document.getElementById("startButton");
const stopButton = document.getElementById("stopButton");
const modeSelect = document.getElementById("mode");
const sampleSelect = document.getElementById("sampleSelect");
const sampleLabel = document.getElementById("sampleLabel");
const sourceEl = document.getElementById("sourceTranscript");
const translatedEl = document.getElementById("translatedTranscript");
const groundTruthPanel = document.getElementById("groundTruthPanel");
const groundTruthEl = document.getElementById("groundTruth");

let samples = [];
let audioContext;
let mediaStream;
let workletNode;
let ws;

// ---- Sample index + ground truth (served from data/ by the relay) ----

function getSelectedSample() {
  return samples.find((s) => s.filename === sampleSelect.value);
}

function renderGroundTruth(sample) {
  if (!sample) return;
  groundTruthEl.textContent =
    `source (isiZulu):\n${sample.transcript}\n\n` +
    `translation (English):\n${sample.translation}`;
  groundTruthPanel.hidden = false;
}

async function loadSamples() {
  const response = await fetch(`${RELAY_URL}/samples`);
  samples = await response.json();
  for (const sample of samples) {
    const option = document.createElement("option");
    option.value = sample.filename;
    option.textContent =
      `${sample.domain} · ${sample.topic} · ${sample.scenario} ` +
      `(${sample.gender}, ${sample.age_range}, ${Math.round(sample.duration)}s)`;
    sampleSelect.appendChild(option);
  }
  onModeChange();
}

function onModeChange() {
  const sampleMode = modeSelect.value === "sample";
  sampleSelect.disabled = !sampleMode;
  sampleLabel.style.opacity = sampleMode ? "1" : "0.5";
  if (sampleMode) {
    renderGroundTruth(getSelectedSample());
  } else {
    groundTruthPanel.hidden = true;
  }
}

// ---- Auth: mint a short-lived client secret via the local relay ----

async function mintClientSecret(targetLanguage) {
  const response = await fetch(`${RELAY_URL}/mint-token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_language: targetLanguage }),
  });
  if (!response.ok) {
    throw new Error(`Failed to mint client secret: ${response.status}`);
  }
  return response.json();
}

// ---- PCM16 conversion ----

function floatTo16BitPCM(float32Array) {
  const pcm16 = new Int16Array(float32Array.length);
  for (let i = 0; i < float32Array.length; i++) {
    const sample = Math.max(-1, Math.min(1, float32Array[i]));
    pcm16[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
  }
  return pcm16;
}

function base64EncodeInt16(int16Array) {
  const bytes = new Uint8Array(int16Array.buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

// ---- Audio plumbing ----

const PCM_PROCESSOR_SOURCE = `
  class PCMProcessor extends AudioWorkletProcessor {
    process(inputs) {
      const input = inputs[0][0];
      if (input) this.port.postMessage(input.slice());
      return true;
    }
  }
  registerProcessor("pcm-processor", PCMProcessor);
`;

async function addPCMWorklet() {
  await audioContext.audioWorklet.addModule(
    URL.createObjectURL(new Blob([PCM_PROCESSOR_SOURCE], { type: "application/javascript" })),
  );
  workletNode = new AudioWorkletNode(audioContext, "pcm-processor");
  workletNode.port.onmessage = (event) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const pcm16 = floatTo16BitPCM(event.data);
    ws.send(
      JSON.stringify({
        type: "session.input_audio_buffer.append",
        audio: base64EncodeInt16(pcm16),
      }),
    );
  };
  // A dangling AudioWorkletNode is never processed (Chrome pulls only nodes on a path
  // to the destination). Keep it in the rendering graph through a zero-gain node, so
  // process() runs and frames are posted to the WebSocket -- without audible output.
  const silent = audioContext.createGain();
  silent.gain.value = 0;
  workletNode.connect(silent);
  silent.connect(audioContext.destination);
}

async function ensureAudioContext() {
  audioContext = new AudioContext({ sampleRate: INPUT_SAMPLE_RATE });
  await addPCMWorklet();
}

async function startMicCapture() {
  mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  await ensureAudioContext();
  const source = audioContext.createMediaStreamSource(mediaStream);
  source.connect(workletNode);
}

async function startSamplePlayback() {
  // Fetch the selected clip from the relay, decode it (16kHz WAV), and replay it at the
  // context's 24kHz rate through the same worklet -- Web Audio resamples automatically.
  const sample = getSelectedSample();
  renderGroundTruth(sample);
  const response = await fetch(`${RELAY_URL}/samples/${encodeURIComponent(sample.filename)}`);
  const wavBytes = await response.arrayBuffer();

  await ensureAudioContext();
  const buffer = await audioContext.decodeAudioData(wavBytes);

  const source = audioContext.createBufferSource();
  source.buffer = buffer;
  source.connect(workletNode);
  source.connect(audioContext.destination); // hear the clip while it streams
  source.onended = () => stop(); // clip finished -> close the session
  source.start();
}

// ---- Session lifecycle ----

async function start() {
  const targetLanguage = document.getElementById("targetLanguage").value.trim();
  sourceEl.textContent = "";
  translatedEl.textContent = "";
  groundTruthPanel.hidden = true;

  const { value: clientSecret, base_url: baseUrl } = await mintClientSecret(targetLanguage);
  const wsUrl = baseUrl.replace(/^http/, "ws") + REALTIME_WS_PATH;

  // Browsers can't send custom headers on a WS handshake, so the client secret is passed via
  // the Sec-WebSocket-Protocol subprotocol list instead.
  ws = new WebSocket(wsUrl, ["realtime", `vulavula-insecure-api-key.${clientSecret}`]);

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === "session.input_transcript.delta") {
      sourceEl.textContent += message.delta;
    } else if (message.type === "session.output_transcript.delta") {
      translatedEl.textContent += message.delta;
    } else if (message.type === "error") {
      console.error("Live API error:", message.error);
    } else if (message.type === "session.closed") {
      console.log("Session closed");
    }
  };

  ws.onerror = (event) => console.error("WebSocket error:", event);
  ws.onclose = () => stop(); // clean up mic/audio-context/buttons on drop or failed handshake

  ws.onopen = async () => {
    if (modeSelect.value === "sample") {
      await startSamplePlayback();
    } else {
      await startMicCapture();
    }
  };

  startButton.disabled = true;
  stopButton.disabled = false;
}

function stop() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "session.close" }));
    // Give the server a moment to flush trailing transcript deltas before dropping
    // the socket (session.closed comes back before we tear down).
    const socket = ws;
    setTimeout(() => {
      if (socket && socket.readyState === WebSocket.OPEN) socket.close();
    }, 1500);
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
  }
  if (audioContext && audioContext.state !== "closed") {
    audioContext.close();
  }

  startButton.disabled = false;
  stopButton.disabled = true;
}

// ---- Wiring ----

modeSelect.addEventListener("change", onModeChange);
sampleSelect.addEventListener("change", () => onModeChange());
startButton.addEventListener("click", () => start().catch((err) => console.error(err)));
stopButton.addEventListener("click", stop);
loadSamples();
