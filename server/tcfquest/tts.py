"""Natural French voices: voice catalogue, per-character voices, saved preferences, audio cache.

The heavy engines run in the separate TTS worker (tts_worker.py, 127.0.0.1:8788). This module
normalises text (tts_text), asks the worker for audio, caches the WAV in data/tts-cache, and
falls back cleanly when the worker is not running (the browser voice then reads the same
normalised spoken text, so symbols are never read aloud).
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path

import httpx

from . import db
from .tts_text import sentences, to_speech

WORKER_URL = os.environ.get("TCFQUEST_TTS_URL", "http://127.0.0.1:8788")

# Finalists from the objective test (docs/VOICE_EVALUATION.md). Every one is free and local.
# "cer": character error rate of Whisper transcribing the voice (lower = clearer).
# "native": the reference speaker is a native French speaker (no accent carried across languages).
VOICES: dict[str, dict] = {
    "pocket:estelle": {"engine": "pocket", "voice": "estelle", "label": "Estelle", "gender": "female", "native": True,
                       "licence": "CC-BY 4.0 model · Kyutai voice", "cer": 0.039, "speed": "playback"},
    "piper:fr_FR-siwis-medium": {"engine": "piper", "voice": "fr_FR-siwis-medium", "label": "Siwis", "gender": "female",
                                 "native": True, "licence": "CC-BY 4.0", "cer": 0.010, "speed": "native"},
    "piper:fr_FR-upmc-medium:jessica": {"engine": "piper", "voice": "fr_FR-upmc-medium:jessica", "label": "Jessica",
                                        "gender": "female", "native": True, "licence": "CC-BY-SA 4.0", "cer": 0.033,
                                        "speed": "native"},
    "pocket:george": {"engine": "pocket", "voice": "george", "label": "George", "gender": "male", "native": False,
                      "licence": "CC-BY 4.0 (VCTK)", "cer": 0.001, "speed": "playback"},
    "pocket:paul": {"engine": "pocket", "voice": "paul", "label": "Paul", "gender": "male", "native": False,
                    "licence": "CC-BY 4.0 (VCTK)", "cer": 0.005, "speed": "playback"},
    "pocket:jean": {"engine": "pocket", "voice": "jean", "label": "Jean", "gender": "male", "native": False,
                    "licence": "CC-BY-NC 4.0 (EARS), personal use only", "cer": 0.010, "speed": "playback"},
    "pocket:charles": {"engine": "pocket", "voice": "charles", "label": "Charles", "gender": "male", "native": False,
                       "licence": "CC-BY 4.0 (VCTK)", "cer": 0.022, "speed": "playback"},
    "pocket:marius": {"engine": "pocket", "voice": "marius", "label": "Marius", "gender": "male", "native": False,
                      "licence": "Kyutai voice donation", "cer": 0.050, "speed": "playback"},
    "piper:fr_FR-tom-medium": {"engine": "piper", "voice": "fr_FR-tom-medium", "label": "Tom", "gender": "male",
                               "native": True, "licence": "AGPL-3.0 voice", "cer": 0.011, "speed": "native"},
    "piper:fr_FR-upmc-medium:pierre": {"engine": "piper", "voice": "fr_FR-upmc-medium:pierre", "label": "Pierre",
                                       "gender": "male", "native": True, "licence": "CC-BY-SA 4.0", "cer": 0.023,
                                       "speed": "native"},
}

# Which voice slot each character uses, so a character always sounds the same.
CHARACTERS = {
    "Madame Roux": "female", "Céleste": "female",
    "M. Delaunay": "male",
    "Narratrice": "narrator",
    "Examinatrice": "narrator", "Examinateur": "male",
}

DEFAULTS = {
    "female": "pocket:estelle",
    "male": "piper:fr_FR-tom-medium",
    "narrator": "piper:fr_FR-siwis-medium",
    "speed": 1.0,          # normal training speed, 0.8–1.2
    "slow_speed": 0.85,    # listening-practice mode
    "slow_mode": False,
    "ratings": {},         # voice id → 1..5, from the learner's listening test
}


def cache_dir() -> Path:
    d = db.db_path().parent / "tts-cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_settings(conn: sqlite3.Connection) -> dict:
    row = conn.execute("SELECT value FROM settings WHERE key = 'voice'").fetchone()
    saved = json.loads(row["value"]) if row else {}
    out = {**DEFAULTS, **saved}
    for slot in ("female", "male", "narrator"):
        if out[slot] not in VOICES:
            out[slot] = DEFAULTS[slot]
    return out


def save_settings(conn: sqlite3.Connection, changes: dict) -> dict:
    current = get_settings(conn)
    current.update(changes)
    conn.execute("INSERT INTO settings (key, value) VALUES ('voice', ?) "
                 "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (json.dumps(current),))
    conn.commit()
    return current


def voice_for(conn: sqlite3.Connection, speaker: str | None, voice: str | None) -> str:
    if voice in VOICES:
        return voice
    s = get_settings(conn)
    return s[CHARACTERS.get(speaker or "", "narrator")]


async def worker_voices() -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            return (await client.get(f"{WORKER_URL}/voices")).json()
    except (httpx.HTTPError, ValueError):
        return None


async def synthesize(voice_id: str, text: str, speed: float) -> tuple[bytes, bool]:
    """WAV bytes for `text`, and whether the speed was applied natively (Piper) or must be
    applied by the player (Pocket: pitch-preserving playback rate)."""
    v = VOICES[voice_id]
    native = v["speed"] == "native"
    engine_speed = round(speed, 2) if native else 1.0
    parts = sentences(text)
    key = hashlib.sha256(json.dumps([voice_id, engine_speed, parts]).encode()).hexdigest()[:32]
    path = cache_dir() / f"{key}.wav"
    if path.exists():
        return path.read_bytes(), native
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{WORKER_URL}/synth", json={"engine": v["engine"], "voice": v["voice"],
                                                            "sentences": parts, "speed": engine_speed})
    r.raise_for_status()
    path.write_bytes(r.content)
    return r.content, native


def spoken_text(text: str) -> str:
    return to_speech(text)
