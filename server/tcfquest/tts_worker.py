"""Local voice worker: French text-to-speech (Pocket TTS / Piper) and speech-to-text (MLX Whisper).

Runs in its own Python environment (.tools/tts-eval: Pocket TTS + Piper are heavy, so the
main API stays light). Listens on 127.0.0.1 only. Standard library HTTP server, one synthesis
at a time (the engines are not thread-safe and the Mac has one CPU budget anyway).

  GET  /voices   → {"pocket": [...], "piper": [...]}  what can actually be loaded
  POST /synth    {"engine", "voice", "sentences": [...], "speed"} → audio/wav (sentences joined
                 with short natural pauses)
  POST /transcribe  body = WAV bytes → {"text", "confidence", "status", "duration_s", "segments"}

Run: .tools/tts-eval/bin/python -m tcfquest.tts_worker   (from server/)
"""

from __future__ import annotations

import io
import json
import os
import sys
import threading
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PIPER_DIR = ROOT / "models" / "piper"
os.environ.setdefault("HF_HOME", str(ROOT / "models" / "hf-cache"))
PORT = int(os.environ.get("TCFQUEST_TTS_PORT", "8788"))

POCKET_VOICES = ["estelle", "jean", "charles", "marius", "paul", "george"]
PAUSE_S = {".": 0.32, "?": 0.38, "!": 0.34, ",": 0.18}       # silence after a sentence, by its last mark

_lock = threading.Lock()
_stt_lock = threading.Lock()
WHISPER = os.environ.get("TCFQUEST_WHISPER", "mlx-community/whisper-large-v3-turbo")
# Whisper sometimes "hears" subtitle credits in silence or noise: never accept these as speech.
HALLUCINATIONS = ("sous-titr", "amara.org", "merci d'avoir regardé", "abonnez-vous", "sous titres", "radio-canada")
_pocket = None
_pocket_states: dict[str, object] = {}
_piper: dict[str, object] = {}


def _pocket_model():
    global _pocket
    if _pocket is None:
        from pocket_tts import TTSModel
        _pocket = TTSModel.load_model(language="french")
    return _pocket


def _synth_pocket(voice: str, text: str) -> tuple[np.ndarray, int]:
    model = _pocket_model()
    if voice not in _pocket_states:
        _pocket_states[voice] = model.get_state_for_audio_prompt(voice)
    audio = model.generate_audio(_pocket_states[voice], text, max_tokens=max(60, int(len(text) * 1.3) + 25))
    return audio.numpy().astype(np.float32), model.sample_rate


def _synth_piper(voice: str, text: str, speed: float) -> tuple[np.ndarray, int]:
    from piper import PiperVoice, SynthesisConfig
    name, _, speaker = voice.partition(":")
    if name not in _piper:
        _piper[name] = PiperVoice.load(str(PIPER_DIR / f"{name}.onnx"))
    v = _piper[name]
    cfg = SynthesisConfig(speaker_id=v.config.speaker_id_map.get(speaker) if speaker else None,
                          length_scale=1.0 / speed)              # real slower speech, not a stretched recording
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        v.synthesize_wav(text, wf, syn_config=cfg)
    buf.seek(0)
    with wave.open(buf, "rb") as wf:
        rate = wf.getframerate()
        pcm = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
    return pcm.astype(np.float32) / 32768.0, rate


def synthesize(engine: str, voice: str, sentences: list[str], speed: float) -> bytes:
    chunks: list[np.ndarray] = []
    rate = 24000
    with _lock:
        for s in sentences:
            if engine == "pocket":
                audio, rate = _synth_pocket(voice, s)
            elif engine == "piper":
                audio, rate = _synth_piper(voice, s, speed)
            else:
                raise ValueError(f"unknown engine {engine}")
            chunks.append(audio)
            chunks.append(np.zeros(int(rate * PAUSE_S.get(s.rstrip()[-1:], 0.3)), dtype=np.float32))
    pcm = np.concatenate(chunks[:-1]) if chunks else np.zeros(1, dtype=np.float32)
    peak = float(np.abs(pcm).max()) or 1.0
    pcm = np.clip(pcm * min(1.0, 0.95 / peak), -1, 1)                 # even loudness, no clipping
    out = io.BytesIO()
    with wave.open(out, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes((pcm * 32767).astype(np.int16).tobytes())
    return out.getvalue()


def _wav_to_16k(data: bytes) -> np.ndarray:
    """Any WAV (int16, float32, mono/stereo, any rate) → mono float32 at 16 kHz."""
    from math import gcd
    import soundfile as sf
    from scipy.signal import resample_poly
    pcm, rate = sf.read(io.BytesIO(data), dtype="float32", always_2d=True)
    pcm = pcm.mean(axis=1)
    if rate != 16000:
        g = gcd(rate, 16000)
        pcm = resample_poly(pcm, 16000 // g, rate // g).astype(np.float32)
    return pcm


def transcribe(data: bytes) -> dict:
    """French transcription with a confidence estimate and honest failure states.

    status: ok | uncertain | no_speech | too_short | too_quiet
    confidence: duration-weighted exp(avg_logprob) of the segments (0–1), lowered by no-speech probability.
    """
    audio = _wav_to_16k(data)
    duration = len(audio) / 16000
    if duration < 0.4:
        return {"text": "", "confidence": 0.0, "status": "too_short", "duration_s": round(duration, 2), "segments": []}
    rms = float(np.sqrt(np.mean(audio ** 2))) if len(audio) else 0.0
    if rms < 0.004:
        return {"text": "", "confidence": 0.0, "status": "too_quiet", "duration_s": round(duration, 2), "segments": []}
    import mlx_whisper
    with _stt_lock:
        out = mlx_whisper.transcribe(audio, path_or_hf_repo=WHISPER, language="fr", temperature=0.0,
                                     condition_on_previous_text=False, no_speech_threshold=0.6,
                                     hallucination_silence_threshold=2.0)
    segs = [s for s in out.get("segments", []) if s.get("text", "").strip()
            and not any(h in s["text"].lower() for h in HALLUCINATIONS)]
    import re
    segs = [s for s in segs if re.search(r"\w", s["text"])]          # "..." or "♪" is not speech
    text = " ".join(s["text"].strip() for s in segs).strip()
    if not text:
        return {"text": "", "confidence": 0.0, "status": "no_speech", "duration_s": round(duration, 2), "segments": []}
    total = sum(max(0.01, s["end"] - s["start"]) for s in segs)
    conf = sum(float(np.exp(s["avg_logprob"])) * (1 - s["no_speech_prob"]) * max(0.01, s["end"] - s["start"])
               for s in segs) / total
    status = "ok" if conf >= 0.6 else "uncertain"
    return {"text": text, "confidence": round(conf, 3), "status": status, "duration_s": round(duration, 2),
            "segments": [{"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"].strip(),
                          "confidence": round(float(np.exp(s["avg_logprob"])), 3)} for s in segs]}


def available() -> dict:
    piper = []
    for onnx in sorted(PIPER_DIR.glob("*.onnx")):
        cfg = json.loads(Path(str(onnx) + ".json").read_text())
        speakers = list(cfg.get("speaker_id_map") or {})
        piper += [f"{onnx.stem}:{s}" for s in speakers] if len(speakers) > 1 and len(speakers) < 10 else [onnx.stem]
    try:
        import pocket_tts  # noqa: F401
        pocket = POCKET_VOICES
    except ImportError:
        pocket = []
    return {"pocket": pocket, "piper": piper}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # quiet
        pass

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/voices":
            return self._send(200, json.dumps(available()).encode(), "application/json")
        self._send(404, b"{}", "application/json")

    def do_POST(self):
        if self.path == "/transcribe":
            try:
                result = transcribe(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            except Exception as e:
                return self._send(500, json.dumps({"error": str(e)}).encode(), "application/json")
            return self._send(200, json.dumps(result, ensure_ascii=False).encode(), "application/json")
        if self.path != "/synth":
            return self._send(404, b"{}", "application/json")
        try:
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            speed = min(1.25, max(0.75, float(req.get("speed", 1.0))))
            wav = synthesize(req["engine"], req["voice"], list(req["sentences"]), speed)
        except Exception as e:  # report, never crash the worker
            return self._send(500, json.dumps({"error": str(e)}).encode(), "application/json")
        self._send(200, wav, "audio/wav")


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"TTS worker on http://127.0.0.1:{PORT}", file=sys.stderr)
    if "--warm" in sys.argv:                                           # load Pocket now, not on first request
        threading.Thread(target=lambda: synthesize("pocket", "estelle", ["Bonjour."], 1.0), daemon=True).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
