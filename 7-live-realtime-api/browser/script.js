// Vulavula Live API browser example: mic capture -> PCM16 -> WebSocket.
//
// The real VULAVULA_API_KEY never touches this file -- it lives only in relay_server.py.
// This page calls the local relay server to mint a short-lived client secret, then uses it
// on the WebSocket handshake via `Sec-WebSocket-Protocol` (browsers can't set custom headers
// during a WS handshake, so this is the standard workaround -- see the Live API docs page).

const RELAY_URL = "http://localhost:8787";
const REALTIME_WS_PATH = "/v1/realtime";
const INPUT_SAMPLE_RATE = 24000;

const startButton = document.getElementById("startButton");
const stopButton = document.getElementById("stopButton");
const sourceEl = document.getElementById("sourceTranscript");
const translatedEl = document.getElementById("translatedTranscript");

let audioContext;
let mediaStream;
let workletNode;
let ws;

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

async function start() {
  const targetLanguage = document.getElementById("targetLanguage").value.trim();
  sourceEl.textContent = "";
  translatedEl.textContent = "";

  const { value: clientSecret, base_url: baseUrl } = await mintClientSecret(targetLanguage);
  const wsUrl = baseUrl.replace(/^https?:/, baseUrl.startsWith("https") ? "wss:" : "ws:") + REALTIME_WS_PATH;

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
    }
  };

  ws.onopen = async () => {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioContext = new AudioContext({ sampleRate: INPUT_SAMPLE_RATE });

    await audioContext.audioWorklet.addModule(
      URL.createObjectURL(
        new Blob(
          [
            `
            class PCMProcessor extends AudioWorkletProcessor {
              process(inputs) {
                const input = inputs[0][0];
                if (input) this.port.postMessage(input.slice());
                return true;
              }
            }
            registerProcessor("pcm-processor", PCMProcessor);
            `,
          ],
          { type: "application/javascript" },
        ),
      ),
    );

    const source = audioContext.createMediaStreamSource(mediaStream);
    workletNode = new AudioWorkletNode(audioContext, "pcm-processor");
    workletNode.port.onmessage = (event) => {
      const pcm16 = floatTo16BitPCM(event.data);
      ws.send(
        JSON.stringify({
          type: "session.input_audio_buffer.append",
          audio: base64EncodeInt16(pcm16),
        }),
      );
    };
    source.connect(workletNode);
  };

  startButton.disabled = true;
  stopButton.disabled = false;
}

function stop() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "session.close" }));
    ws.close();
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
  }
  if (audioContext) {
    audioContext.close();
  }

  startButton.disabled = false;
  stopButton.disabled = true;
}

startButton.addEventListener("click", () => start().catch((err) => console.error(err)));
stopButton.addEventListener("click", stop);
