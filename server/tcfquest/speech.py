"""Speaking pipeline: save the learner's recording locally, transcribe it with local Whisper
(voice worker), and report honest states.

The recogniser's confidence describes how sure the *machine* is about the words. It is never a
pronunciation score: a low value can come from the microphone, noise, an accent the model
handles badly, or the learner. Uncertain results are shown with a way to correct or type the
answer, and they never count against the learner.
"""

from __future__ import annotations

import io
import json
import sqlite3
import uuid
import wave
from datetime import date

import httpx

from . import db, tts

MAX_BYTES = 10 * 1024 * 1024        # ~5 minutes of 16 kHz mono WAV
ENGINE = "mlx-whisper large-v3-turbo"


class BadAudio(ValueError):
    pass


def recordings_dir():
    d = db.db_path().parent / "recordings" / date.today().strftime("%Y-%m")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _check_wav(data: bytes) -> float:
    if len(data) > MAX_BYTES:
        raise BadAudio("Recording too long (5 minutes maximum).")
    try:
        with wave.open(io.BytesIO(data), "rb") as wf:
            return wf.getnframes() / wf.getframerate()
    except (wave.Error, EOFError, ZeroDivisionError):
        raise BadAudio("Not a WAV recording.")


async def transcribe(conn: sqlite3.Connection, data: bytes, context: str = "check", ref: str | None = None) -> dict:
    duration = _check_wav(data)
    path = recordings_dir() / f"{uuid.uuid4().hex}.wav"
    path.write_bytes(data)
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{tts.WORKER_URL}/transcribe", content=data,
                                  headers={"Content-Type": "audio/wav"})
        r.raise_for_status()
        result = r.json()
    except (httpx.HTTPError, ValueError):
        result = {"text": "", "confidence": 0.0, "status": "engine_off", "duration_s": round(duration, 2), "segments": []}
    cur = conn.execute(
        """INSERT INTO speech_recording (path, context, context_ref, duration_s, transcript, confidence, status, engine)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (str(path.relative_to(db.db_path().parent)), context, ref, result["duration_s"], result["text"],
         result["confidence"], result["status"], None if result["status"] == "engine_off" else ENGINE))
    conn.commit()
    return {"recording_id": cur.lastrowid, **result}


def correct(conn: sqlite3.Connection, rid: int, typed: str) -> bool:
    cur = conn.execute("UPDATE speech_recording SET typed_text = ? WHERE id = ?", (typed.strip(), rid))
    return cur.rowcount == 1


def delete(conn: sqlite3.Connection, rid: int) -> bool:
    row = conn.execute("SELECT path FROM speech_recording WHERE id = ?", (rid,)).fetchone()
    if row is None:
        return False
    (db.db_path().parent / row["path"]).unlink(missing_ok=True)
    conn.execute("DELETE FROM speech_recording WHERE id = ?", (rid,))
    return True


def words(s: str) -> list[str]:
    import re
    import unicodedata
    s = unicodedata.normalize("NFC", s.lower()).replace("’", "'")
    return re.findall(r"[\w']+", s)


def compare(target: str, heard: str) -> dict:
    """Which words of a model sentence the recogniser found (order-aware LCS). Content check only."""
    t, h = words(target), words(heard)
    dp = [[0] * (len(h) + 1) for _ in range(len(t) + 1)]
    for i in range(len(t) - 1, -1, -1):
        for j in range(len(h) - 1, -1, -1):
            dp[i][j] = dp[i + 1][j + 1] + 1 if t[i] == h[j] else max(dp[i + 1][j], dp[i][j + 1])
    found, i, j = [], 0, 0
    while i < len(t) and j < len(h):
        if t[i] == h[j]:
            found.append(i); i += 1; j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            i += 1
        else:
            j += 1
    return {"words": [{"word": w, "found": k in found} for k, w in enumerate(t)],
            "ratio": round(len(found) / max(1, len(t)), 2)}
