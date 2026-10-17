"""Compare local French TTS voices objectively (run with the .tools/tts-eval Python).

For each candidate voice: synthesise a fixed French corpus (after tcfquest.tts_text normalisation),
time it, transcribe the audio with local Whisper, and compute the character error rate (CER)
against the spoken text. Also flag transcripts where symbols were read aloud.

Objective numbers are a proxy only: the final quality call is a human listening test (1–5).
Usage: .tools/tts-eval/bin/python scripts/tts_eval.py [--only pocket,piper,say]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import unicodedata
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
from tcfquest.tts_text import to_speech  # noqa: E402

OUT = ROOT / "models" / "tts-eval"
PIPER_DIR = ROOT / "models" / "piper"

CORPUS = [
    "Bonjour Monsieur, je vous appelle de la part de Madame Roux.",
    "Pourriez-vous me dire où en est sa livraison ?",
    "Les enfants ont attendu une heure et demie devant l'école.",
    "Notre camion est tombé en panne hier soir sur l'autoroute.",
    "Mon fils peut venir vers 11 h, avec 10 kg de comté.",
    "Pourquoi… ? / Quand… ? / À quelle heure… ?",
    "Ça fait 2,40 €. Vous payez par carte ou en espèces ?",
    "À mon avis, le télétravail a plus d'avantages que d'inconvénients.",
    "Bien que cette réforme soit contestée, elle répond à un besoin réel.",
    "M. Delaunay arrive le 1er décembre, n'est-ce pas ?",
    "Je voudrais un café crème et deux croissants, s'il vous plaît.",
    "Qu'est-ce que vous en pensez, franchement ?",
]

CANDIDATES = [
    # engine, voice id, label, gender
    ("pocket", "estelle", "Pocket · Estelle", "F"),
    ("pocket", "jean", "Pocket · Jean", "M"),
    ("pocket", "charles", "Pocket · Charles", "M"),
    ("pocket", "marius", "Pocket · Marius", "M"),
    ("pocket", "paul", "Pocket · Paul", "M"),
    ("pocket", "george", "Pocket · George", "M"),
    ("piper", "fr_FR-siwis-medium", "Piper · Siwis", "F"),
    ("piper", "fr_FR-upmc-medium:jessica", "Piper · UPMC Jessica", "F"),
    ("piper", "fr_FR-upmc-medium:pierre", "Piper · UPMC Pierre", "M"),
    ("piper", "fr_FR-tom-medium", "Piper · Tom", "M"),
    ("piper", "fr_FR-gilles-low", "Piper · Gilles (low)", "M"),
    ("say", "Thomas", "macOS · Thomas", "M"),
    ("say", "Jacques", "macOS · Jacques", "M"),
    ("say", "Amélie", "macOS · Amélie (fr-CA)", "F"),
    ("say", "Flo (French (France))", "macOS · Flo", "F"),
    ("say", "Eddy (French (France))", "macOS · Eddy (current app voice)", "M"),
]

SYMBOL_WORDS = ["slash", "barre oblique", "point point", "astérisque", "dièse", "underscore"]


def plain(s: str) -> str:
    s = s.lower().replace("’", "'")
    s = re.sub(r"[^\w' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def cer(ref: str, hyp: str) -> float:
    r, h = plain(ref), plain(hyp)
    prev = list(range(len(h) + 1))
    for i, a in enumerate(r, 1):
        cur = [i]
        for j, b in enumerate(h, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a != b)))
        prev = cur
    return prev[-1] / max(1, len(r))


def load_16k(path: Path):
    """Mono float32 at 16 kHz, what Whisper expects (no ffmpeg needed)."""
    from math import gcd
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    audio, sr = sf.read(str(path), dtype="float32", always_2d=True)
    audio = audio.mean(axis=1)
    if sr != 16000:
        g = gcd(sr, 16000)
        audio = resample_poly(audio, 16000 // g, sr // g).astype(np.float32)
    return audio


def duration(path: Path) -> float:
    import soundfile as sf
    info = sf.info(str(path))
    return info.frames / info.samplerate


class Pocket:
    def __init__(self):
        from pocket_tts import TTSModel
        self.model = TTSModel.load_model(language="french")
        self.states = {}

    def say(self, voice: str, text: str, path: Path):
        import scipy.io.wavfile
        if voice not in self.states:
            self.states[voice] = self.model.get_state_for_audio_prompt(voice)
        audio = self.model.generate_audio(self.states[voice], text, max_tokens=max(60, int(len(text) * 1.3) + 25))
        scipy.io.wavfile.write(str(path), self.model.sample_rate, audio.numpy())


class Piper:
    def __init__(self):
        self.voices = {}

    def say(self, voice: str, text: str, path: Path):
        from piper import PiperVoice, SynthesisConfig
        name, _, speaker = voice.partition(":")
        if name not in self.voices:
            self.voices[name] = PiperVoice.load(str(PIPER_DIR / f"{name}.onnx"))
        v = self.voices[name]
        cfg = SynthesisConfig(speaker_id=v.config.speaker_id_map.get(speaker) if speaker else None)
        with wave.open(str(path), "wb") as wf:
            v.synthesize_wav(text, wf, syn_config=cfg)


def say_mac(voice: str, text: str, path: Path):
    aiff = path.with_suffix(".aiff")
    subprocess.run(["say", "-v", voice, "-o", str(aiff), text], check=True)
    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@22050", str(aiff), str(path)], check=True)
    aiff.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="pocket,piper,say")
    ap.add_argument("--whisper", default="mlx-community/whisper-large-v3-turbo")
    args = ap.parse_args()
    engines = set(args.only.split(","))

    import mlx_whisper

    pocket = Pocket() if "pocket" in engines else None
    piper = Piper() if "piper" in engines else None
    results = []
    for engine, voice, label, gender in CANDIDATES:
        if engine not in engines:
            continue
        vdir = OUT / re.sub(r"[^\w-]+", "_", f"{engine}_{voice}")
        vdir.mkdir(parents=True, exist_ok=True)
        rows, ok = [], True
        for i, text in enumerate(CORPUS):
            spoken = to_speech(text)
            path = vdir / f"{i:02d}.wav"
            t0 = time.perf_counter()
            try:
                if engine == "pocket":
                    pocket.say(voice, spoken, path)
                elif engine == "piper":
                    piper.say(voice, spoken, path)
                else:
                    say_mac(voice, spoken, path)
            except Exception as e:  # voice not available for this engine/language
                print(f"  ! {label}: {e}", file=sys.stderr)
                ok = False
                break
            gen = time.perf_counter() - t0
            dur = duration(path)
            hyp = mlx_whisper.transcribe(load_16k(path), path_or_hf_repo=args.whisper, language="fr")["text"].strip()
            rows.append({"text": text, "spoken": spoken, "heard": hyp, "cer": round(cer(spoken, hyp), 3),
                         "gen_s": round(gen, 3), "audio_s": round(dur, 2),
                         "symbols_read": [w for w in SYMBOL_WORDS if w in hyp.lower()]})
        if not ok or not rows:
            results.append({"engine": engine, "voice": voice, "label": label, "gender": gender, "available": False})
            continue
        n = len(rows)
        results.append({
            "engine": engine, "voice": voice, "label": label, "gender": gender, "available": True,
            "mean_cer": round(sum(r["cer"] for r in rows) / n, 3),
            "worst": max(rows, key=lambda r: r["cer"]),
            "rtf": round(sum(r["gen_s"] for r in rows) / sum(r["audio_s"] for r in rows), 3),
            "mean_gen_s": round(sum(r["gen_s"] for r in rows) / n, 2),
            "symbols_read": sum(len(r["symbols_read"]) for r in rows),
            "rows": rows,
        })
        r = results[-1]
        print(f"{label:34s} CER {r['mean_cer']:.3f}  RTF {r['rtf']:.2f}  gen {r['mean_gen_s']:.2f}s  symbols {r['symbols_read']}")
    (OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
