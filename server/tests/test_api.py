import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("TCFQUEST_DB", str(Path(tmp) / "test.db"))
        from tcfquest.main import app

        with TestClient(app) as c:
            yield c


def test_health_reports_schema(client):
    body = client.get("/api/health").json()
    assert body["ok"] is True
    from tcfquest import db
    assert body["schema_version"] == db.migrations()[-1][0]
    assert "running" in body["ai"]


def test_profile_starts_empty_then_persists(client):
    assert client.get("/api/profile").json() == {"profile": None}
    r = client.put(
        "/api/profile",
        json={
            "display_name": "Alex",
            "target_cefr": "C1",
            "target_nclc": 9,
            "daily_minutes": 30,
            "hardest_skills": ["speaking", "listening", "speaking"],
        },
    )
    assert r.status_code == 200
    profile = client.get("/api/profile").json()["profile"]
    assert profile["display_name"] == "Alex"
    assert profile["hardest_skills"] == ["listening", "speaking"]  # de-duplicated, sorted
    assert profile["onboarded_at"] is not None


def test_profile_rejects_bad_input(client):
    r = client.put("/api/profile", json={"display_name": "", "target_nclc": 42})
    assert r.status_code == 422


def test_summary_requires_profile_then_works(client):
    assert client.get("/api/summary").status_code == 404
    client.put("/api/profile", json={"display_name": "B"})
    s = client.get("/api/summary").json()
    assert s["xp"] == 0 and s["streak"] == 0
    assert {k["skill"] for k in s["skills"]} == {"listening", "reading", "speaking", "writing"}
    assert s["diagnostic_done"] is False


def test_migrations_are_idempotent(tmp_path):
    from tcfquest import db

    conn = db.connect(tmp_path / "m.db")
    latest = db.migrations()[-1][0]
    assert db.migrate(conn) == latest
    assert db.migrate(conn) == latest


AVATAR = {
    "gender": "man", "hair": "short", "hair_colour": "black", "skin_tone": 4,
    "facial_hair": "beard", "glasses": False, "vibe": "street", "description": "Calm, curious, loves football.",
}


def test_avatar_create_and_read(client):
    body = client.get("/api/avatar").json()
    assert body["avatar"] is None
    assert body["reached_level"] == "A1"
    assert [s["unlocked"] for s in body["skins"]] == [True, False, False, False, False, False]

    saved = client.put("/api/avatar", json=AVATAR).json()["avatar"]
    assert saved["gender"] == "man" and saved["glasses"] is False
    assert saved["equipped_skin"] == "a1"


def test_avatar_rejects_bad_input(client):
    assert client.put("/api/avatar", json={**AVATAR, "skin_tone": 9}).status_code == 422
    assert client.put("/api/avatar", json={**AVATAR, "description": "x" * 601}).status_code == 422


def test_skins_unlock_by_weakest_skill_not_xp(client):
    from tcfquest import db

    client.put("/api/profile", json={"display_name": "B"})
    client.put("/api/avatar", json=AVATAR)
    # Locked while there is no evidence
    assert client.put("/api/avatar/skin", json={"skin": "b1"}).status_code == 403

    conn = db.connect()
    conn.execute("INSERT INTO xp_event (amount, reason) VALUES (100000, 'grind')")  # XP never unlocks skins
    assert client.put("/api/avatar/skin", json={"skin": "a2"}).status_code == 403

    # Weakest skill at B1 → A1, A2, B1 unlocked; B2 still locked
    for skill, low in [("listening", "B2"), ("reading", "C1"), ("speaking", "B1"), ("writing", "B2")]:
        conn.execute("UPDATE skill_profile SET cefr_low = ?, evidence = 20, confidence = 'medium' WHERE skill = ?", (low, skill))
    conn.close()
    body = client.get("/api/avatar").json()
    assert body["reached_level"] == "B1"
    assert [s["unlocked"] for s in body["skins"]] == [True, True, True, False, False, False]
    assert client.put("/api/avatar/skin", json={"skin": "b1"}).json()["avatar"]["equipped_skin"] == "b1"
    assert client.put("/api/avatar/skin", json={"skin": "b2"}).status_code == 403
    assert client.put("/api/avatar/skin", json={"skin": "zz"}).status_code == 404


def test_pasted_settings_are_cleaned():
    from tcfquest.db import clean_setting
    for messy in ("  eyJabc.def-ghi  ", "= eyJabc.def-ghi", '"eyJabc.def-ghi"', "eyJabc.def-ghi\nTCFQUEST_SECRET = x",
                  "        = eyJabc.def-ghi"):
        assert clean_setting(messy) == "eyJabc.def-ghi"
    assert clean_setting("libsql://tcfq-{tester}-org.aws-us-east-1.turso.io ") == "libsql://tcfq-{tester}-org.aws-us-east-1.turso.io"


def test_unexpected_errors_answer_in_json_without_secrets(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    from tcfquest import db, main
    monkeypatch.setenv("TCFQUEST_DB", str(tmp_path / "t.db"))
    monkeypatch.setenv("TCFQUEST_LIBSQL_TOKEN", "secret-token-123456")
    def boom(*a, **k):
        raise ValueError("sync error with secret-token-123456 inside")
    monkeypatch.setattr(db, "connect", boom)
    r = TestClient(main.app, raise_server_exceptions=False).get("/api/profile")
    assert r.status_code == 500 and "ValueError" in r.json()["detail"] and "secret-token" not in r.text
