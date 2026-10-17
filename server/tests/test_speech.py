"""M5: speaking pipeline — local recordings, honest transcription states, typed corrections."""

import io
import tempfile
import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tcfquest import speech, tts


def wav(seconds=1.0, rate=16000) -> bytes:
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(b"\x00\x01" * int(seconds * rate))
    return b.getvalue()


@pytest.fixture()
def client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("TCFQUEST_DB", str(Path(tmp) / "test.db"))
        monkeypatch.setattr(tts, "WORKER_URL", "http://127.0.0.1:9")      # nothing listens there
        from tcfquest.main import app

        with TestClient(app) as c:
            c.tmp = Path(tmp)
            yield c


def test_engine_off_keeps_the_recording_and_says_so(client):
    r = client.post("/api/speech/transcribe?context=check", content=wav(1.5), headers={"Content-Type": "audio/wav"}).json()
    assert r["status"] == "engine_off" and r["text"] == "" and r["duration_s"] == 1.5
    files = list((client.tmp / "recordings").rglob("*.wav"))
    assert len(files) == 1                                                  # saved locally, in data/
    assert client.put(f"/api/speech/recordings/{r['recording_id']}", json={"text": "Bonjour"}).json() == {"ok": True}
    assert client.delete(f"/api/speech/recordings/{r['recording_id']}").json() == {"ok": True}
    assert not list((client.tmp / "recordings").rglob("*.wav"))             # deleting removes the file
    assert client.delete(f"/api/speech/recordings/{r['recording_id']}").status_code == 404


def test_rejects_non_wav_and_huge_uploads(client, monkeypatch):
    assert client.post("/api/speech/transcribe", content=b"not audio").status_code == 422
    monkeypatch.setattr(speech, "MAX_BYTES", 100)
    assert client.post("/api/speech/transcribe", content=wav(1)).status_code == 422


def test_worker_result_is_stored(client, monkeypatch):
    class Resp:
        def raise_for_status(self): pass
        def json(self): return {"text": "Bonjour Madame", "confidence": 0.41, "status": "uncertain", "duration_s": 1.0, "segments": []}

    class FakeClient:
        def __init__(self, *a, **k): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        async def post(self, url, content=None, headers=None):
            assert url.endswith("/transcribe") and content[:4] == b"RIFF"
            return Resp()

    monkeypatch.setattr(speech.httpx, "AsyncClient", FakeClient)
    r = client.post("/api/speech/transcribe?context=eo-task&ref=eo1-a", content=wav(1)).json()
    assert r["status"] == "uncertain" and r["text"] == "Bonjour Madame"
    from tcfquest import db
    row = db.connect().execute("SELECT * FROM speech_recording").fetchone()
    assert (row["context"], row["context_ref"], row["confidence"], row["engine"]) == ("eo-task", "eo1-a", 0.41, speech.ENGINE)


def test_compare_is_order_aware_and_ignores_case_and_punctuation():
    r = speech.compare("Pourriez-vous me dire à quelle heure ?", "pourriez vous me dire quelle heure")
    found = {w["word"]: w["found"] for w in r["words"]}
    assert found["à"] is False and found["quelle"] is True and r["ratio"] == 0.86
    assert speech.compare("Bonjour Madame", "")["ratio"] == 0.0
