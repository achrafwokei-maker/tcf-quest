"""Voice API: settings, per-character voices, fallback when the TTS worker is off, cache."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tcfquest import tts


@pytest.fixture()
def client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("TCFQUEST_DB", str(Path(tmp) / "test.db"))
        monkeypatch.setattr(tts, "WORKER_URL", "http://127.0.0.1:9")       # nothing listens there
        from tcfquest.main import app

        with TestClient(app) as c:
            yield c


def test_voices_and_default_settings(client):
    r = client.get("/api/voices").json()
    assert r["worker_running"] is False
    assert {v["gender"] for v in r["voices"]} == {"female", "male"}
    assert r["settings"]["speed"] == 1.0 and r["settings"]["slow_speed"] == 0.85
    assert r["characters"]["M. Delaunay"] == "male" and r["characters"]["Madame Roux"] == "female"


def test_settings_are_saved_and_validated(client):
    s = client.put("/api/voices/settings", json={"male": "pocket:george", "speed": 1.1, "slow_mode": True}).json()
    assert (s["male"], s["speed"], s["slow_mode"]) == ("pocket:george", 1.1, True)
    s = client.put("/api/voices/settings", json={"rating": ["pocket:george", 4]}).json()
    s = client.put("/api/voices/settings", json={"rating": ["pocket:estelle", 5]}).json()
    assert s["ratings"] == {"pocket:george": 4, "pocket:estelle": 5} and s["male"] == "pocket:george"
    assert client.get("/api/voices").json()["settings"]["speed"] == 1.1
    assert client.put("/api/voices/settings", json={"female": "nope"}).status_code == 422
    assert client.put("/api/voices/settings", json={"speed": 2}).status_code == 422
    assert client.put("/api/voices/settings", json={"rating": ["pocket:george", 9]}).status_code == 422


def test_each_character_keeps_its_voice(client):
    from tcfquest import db
    conn = db.connect()
    assert tts.voice_for(conn, "M. Delaunay", None) == tts.DEFAULTS["male"]
    assert tts.voice_for(conn, "Madame Roux", None) == tts.DEFAULTS["female"]
    assert tts.voice_for(conn, "Narratrice", None) == tts.DEFAULTS["narrator"]
    assert tts.voice_for(conn, "Madame Roux", "pocket:paul") == "pocket:paul"          # explicit preview wins
    client.put("/api/voices/settings", json={"male": "pocket:paul"})
    assert tts.voice_for(conn, "M. Delaunay", None) == "pocket:paul"


def test_no_worker_means_503_and_spoken_text_fallback(client):
    r = client.post("/api/tts", json={"text": "Bonjour", "speaker": "Madame Roux"})
    assert r.status_code == 503
    t = client.post("/api/tts/text", json={"text": "**M. Roux** : 2,40 € / kg… ?"}).json()
    assert t["spoken"] == "Monsieur Roux : deux euros quarante par kilo ?"


def test_audio_is_cached(client, monkeypatch):
    calls = []

    class FakeResponse:
        content = b"RIFF-fake-wav"
        def raise_for_status(self):
            pass

    class FakeClient:
        def __init__(self, *a, **k):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *a):
            pass
        async def post(self, url, json):
            calls.append(json)
            return FakeResponse()

    monkeypatch.setattr(tts.httpx, "AsyncClient", FakeClient)
    for _ in range(2):
        r = client.post("/api/tts", json={"text": "Bonjour Madame. Ça va ?", "voice": "piper:fr_FR-tom-medium", "speed": 0.85})
        assert r.status_code == 200 and r.content == b"RIFF-fake-wav"
        assert r.headers["x-speed-applied"] == "1"
    assert len(calls) == 1 and calls[0]["sentences"] == ["Bonjour Madame.", "Ça va ?"] and calls[0]["speed"] == 0.85
    r = client.post("/api/tts", json={"text": "Bonjour Madame. Ça va ?", "voice": "pocket:estelle", "speed": 0.85})
    assert r.headers["x-speed-applied"] == "0" and calls[-1]["speed"] == 1.0    # Pocket: the player slows it
