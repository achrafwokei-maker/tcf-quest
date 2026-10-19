"""Pre-record every content line with the natural voices, as small MP3 files for the online beta.

Run on the Mac with the voice worker started (scripts/dev.sh), from the project root:
    server/.venv/bin/python scripts/prerender_audio.py
Writes content/audio/tts/<key>.mp3 (the same keys the API uses) and removes files no longer used.
Only the default voices at normal speed are recorded; other choices fall back to live voices.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

import httpx  # noqa: E402

from tcfquest import tts  # noqa: E402

OUT = tts.PRERECORDED_DIR
ENCODER = ROOT / ".tools" / "tts-eval" / "bin" / "python"   # has soundfile + libsndfile with MP3


def lines() -> set[tuple[str, str | None]]:
    found: set[tuple[str, str | None]] = set()

    def walk(o):
        if isinstance(o, dict):
            a = o.get("audio")
            if isinstance(a, dict) and a.get("text"):
                found.add((a["text"], a.get("speaker")))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for f in (ROOT / "content").rglob("*.json"):
        walk(json.loads(f.read_text()))
    for card in json.loads((ROOT / "content" / "vocab" / "vocab.json").read_text())["cards"]:
        found.add((card["fr"], "Céleste"))                       # VocabPage speaks the card as Céleste
    return found


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    wanted: dict[str, tuple[str, str]] = {}
    for text, speaker in lines():
        voice = tts.DEFAULTS[tts.CHARACTERS.get(speaker or "", "narrator")]
        key, speed = tts.audio_key(voice, text, tts.DEFAULTS["speed"])
        wanted[key] = (voice, text)
    todo = {k: v for k, v in wanted.items() if not (OUT / f"{k}.mp3").exists()}
    print(f"{len(wanted)} lines, {len(todo)} to record")
    with tempfile.TemporaryDirectory() as tmp:
        for i, (key, (voice, text)) in enumerate(sorted(todo.items()), 1):
            v = tts.VOICES[voice]
            _, speed = tts.audio_key(voice, text, tts.DEFAULTS["speed"])
            r = httpx.post(f"{tts.WORKER_URL}/synth", timeout=300, json={
                "engine": v["engine"], "voice": v["voice"], "sentences": tts.sentences(text), "speed": speed})
            r.raise_for_status()
            (Path(tmp) / f"{key}.wav").write_bytes(r.content)
            print(f"  {i}/{len(todo)} {voice}: {text[:50]}")
        if todo:
            subprocess.run([str(ENCODER), "-I", "-c", (
                "import sys, pathlib, soundfile as sf\n"
                "src, dst = map(pathlib.Path, sys.argv[1:])\n"
                "for f in src.glob('*.wav'):\n"
                "    data, rate = sf.read(f)\n"
                "    sf.write(dst / (f.stem + '.mp3'), data, rate, format='MP3', subtype='MPEG_LAYER_III',\n"
                "             compression_level=0.6)\n"), tmp, str(OUT)], check=True)
    stale = [f for f in OUT.glob("*.mp3") if f.stem not in wanted]
    for f in stale:
        f.unlink()
    size = sum(f.stat().st_size for f in OUT.glob("*.mp3"))
    print(f"done: {len(wanted)} files, {size / 1e6:.1f} MB, {len(stale)} stale removed")


if __name__ == "__main__":
    main()
