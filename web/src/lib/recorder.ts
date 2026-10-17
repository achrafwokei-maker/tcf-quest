// Microphone recording in the browser → 16 kHz mono 16-bit WAV (what local Whisper expects).
// The audio goes only to the local API (127.0.0.1), which keeps it in data/recordings.

export type MicError = "denied" | "no_device" | "unsupported" | "failed";

export interface Recording {
  stop: () => Promise<Blob>;       // resolves with the WAV
  cancel: () => void;
  level: () => number;             // 0..1 input level for the meter
}

export function micSupported(): boolean {
  return typeof navigator !== "undefined" && !!navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== "undefined";
}

export async function startRecording(): Promise<Recording> {
  if (!micSupported()) throw "unsupported" as MicError;
  let stream: MediaStream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, channelCount: 1 } });
  } catch (e) {
    const name = (e as DOMException)?.name;
    throw (name === "NotAllowedError" || name === "SecurityError" ? "denied" : name === "NotFoundError" ? "no_device" : "failed") as MicError;
  }
  const ctx = new AudioContext();
  const analyser = ctx.createAnalyser();
  analyser.fftSize = 512;
  ctx.createMediaStreamSource(stream).connect(analyser);
  const buf = new Uint8Array(analyser.fftSize);
  const recorder = new MediaRecorder(stream);
  const chunks: Blob[] = [];
  recorder.ondataavailable = (e) => e.data.size && chunks.push(e.data);
  recorder.start();

  const release = () => {
    stream.getTracks().forEach((t) => t.stop());
    void ctx.close();
  };

  return {
    level: () => {
      analyser.getByteTimeDomainData(buf);
      let peak = 0;
      for (const v of buf) peak = Math.max(peak, Math.abs(v - 128));
      return Math.min(1, peak / 64);
    },
    cancel: () => {
      recorder.onstop = null;
      if (recorder.state !== "inactive") recorder.stop();
      release();
    },
    stop: () =>
      new Promise<Blob>((resolve, reject) => {
        recorder.onstop = async () => {
          release();
          try {
            resolve(await toWav16k(new Blob(chunks, { type: recorder.mimeType })));
          } catch (e) {
            reject(e);
          }
        };
        recorder.stop();
      }),
  };
}

async function toWav16k(blob: Blob): Promise<Blob> {
  const decodeCtx = new AudioContext();
  const decoded = await decodeCtx.decodeAudioData(await blob.arrayBuffer());
  void decodeCtx.close();
  const frames = Math.ceil(decoded.duration * 16000);
  const offline = new OfflineAudioContext(1, Math.max(1, frames), 16000);
  const src = offline.createBufferSource();
  src.buffer = decoded;
  src.connect(offline.destination);
  src.start();
  const rendered = await offline.startRendering();
  return encodeWav(rendered.getChannelData(0), 16000);
}

export function encodeWav(samples: Float32Array, rate: number): Blob {
  const out = new DataView(new ArrayBuffer(44 + samples.length * 2));
  const str = (o: number, s: string) => [...s].forEach((c, i) => out.setUint8(o + i, c.charCodeAt(0)));
  str(0, "RIFF"); out.setUint32(4, 36 + samples.length * 2, true); str(8, "WAVE");
  str(12, "fmt "); out.setUint32(16, 16, true); out.setUint16(20, 1, true); out.setUint16(22, 1, true);
  out.setUint32(24, rate, true); out.setUint32(28, rate * 2, true); out.setUint16(32, 2, true); out.setUint16(34, 16, true);
  str(36, "data"); out.setUint32(40, samples.length * 2, true);
  samples.forEach((v, i) => out.setInt16(44 + i * 2, Math.max(-1, Math.min(1, v)) * 0x7fff, true));
  return new Blob([out], { type: "audio/wav" });
}

export type SpeechStatus = "ok" | "uncertain" | "no_speech" | "too_short" | "too_quiet" | "engine_off";

export interface Transcript {
  recording_id: number; text: string; confidence: number; status: SpeechStatus; duration_s: number;
}

export async function transcribe(wav: Blob, context = "check", ref?: string): Promise<Transcript> {
  const q = new URLSearchParams({ context, ...(ref ? { ref } : {}) });
  const res = await fetch(`/api/speech/transcribe?${q}`, { method: "POST", headers: { "Content-Type": "audio/wav" }, body: wav });
  if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail ?? res.statusText);
  return res.json();
}

export const STATUS_HELP: Record<SpeechStatus, string> = {
  ok: "",
  uncertain: "The recogniser isn't sure what it heard. Check the words below and correct them if needed. This never counts against you.",
  no_speech: "No speech was detected. Try again closer to the microphone, or type your answer.",
  too_short: "That was very short. Hold the button a little longer, or type your answer.",
  too_quiet: "The recording is almost silent. Check that the right microphone is selected, or type your answer.",
  engine_off: "The local speech recogniser isn't running (restart the app with scripts/dev.sh). Your recording is saved; type your answer for now.",
};
