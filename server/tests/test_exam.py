"""M7: strict exam engine — reserved items, one play, forward-only, timers, no keys before the end."""

import json
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tcfquest import content, exam, speaking_ai, writing_ai


@pytest.fixture()
def client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("TCFQUEST_DB", str(Path(tmp) / "test.db"))
        monkeypatch.setattr(writing_ai, "run", lambda c, sid: "failed")     # no AI in these tests
        monkeypatch.setattr(speaking_ai, "run", lambda c, sid: "failed")
        from tcfquest.main import app

        with TestClient(app) as c:
            yield c


def conn():
    from tcfquest import db
    return db.connect()


def answer_section(client, aid, wrong=()):
    while True:
        s = client.get(f"/api/exams/attempts/{aid}").json()
        cur = s.get("current", {})
        if s["status"] == "completed" or cur.get("section") not in ("CO", "CE") or "item" not in cur:
            return s
        item = cur["item"]
        if item["type"] == "listen" and not cur["played"]:
            assert client.post(f"/api/exams/attempts/{aid}/play", json={"item_id": item["id"]}).status_code == 200
        it = content.item_by_id(content.get_set("trial-1"), item["id"])
        resp = "zzz" if item["id"] in wrong else it.answer
        r = client.post(f"/api/exams/attempts/{aid}/answer", json={"item_id": item["id"], "response": resp})
        assert r.status_code == 200, r.text


def test_reserved_sets_are_hidden_from_training(client):
    assert all(s["context"] != "exam" for s in client.get("/api/sets").json()["sets"])
    assert client.get("/api/sets/trial-1").status_code == 404
    assert "ee1-trial-1" not in json.dumps(client.get("/api/writing").json())
    assert "eo3-trial-1" not in json.dumps(client.get("/api/eo").json())
    assert client.post("/api/writing/tasks/ee1-trial-1/start", json={"mode": "exam"}).status_code == 404


def test_listing_and_weekly_due(client):
    l = client.get("/api/exams").json()
    assert l["weekly_due"] and l["next_weekly"] == "weekly-1"
    w1 = next(x for x in l["exams"] if x["id"] == "weekly-1")
    assert [s["limit_s"] for s in w1["sections"]] == [480, 720, 900, 270]


def test_full_weekly_trial_flow(client):
    s = client.post("/api/exams/weekly-1/start").json()
    aid = s["id"]
    assert s["current"]["section"] == "CO" and not s["current"]["started"] and "item" not in s["current"]
    s = client.post(f"/api/exams/attempts/{aid}/begin").json()
    item = s["current"]["item"]
    assert "audio" not in item and "answer" not in json.dumps(item)                    # no keys, no transcript
    # Must listen before answering; one play only
    assert client.post(f"/api/exams/attempts/{aid}/answer", json={"item_id": item["id"], "response": "a"}).status_code == 409
    played = client.post(f"/api/exams/attempts/{aid}/play", json={"item_id": item["id"]}).json()
    assert played["text"]
    assert client.post(f"/api/exams/attempts/{aid}/play", json={"item_id": item["id"]}).status_code == 409
    s = answer_section(client, aid, wrong={"t1-co-gare", "t1-co-debat-transport"})
    assert s["current"]["section"] == "CE" and "results" not in s
    client.post(f"/api/exams/attempts/{aid}/begin")
    s = answer_section(client, aid, wrong={"t1-ce-tribune-teletravail"})
    assert s["current"]["section"] == "EE"
    s = client.post(f"/api/exams/attempts/{aid}/begin").json()
    sid = s["current"]["writing_submission_id"]
    sub = client.put(f"/api/writing/submissions/{sid}", json={"text": "Bonjour à tous, je dois changer la date du repas."}).json()
    assert sub["mode"] == "exam" and sub["time_limit_s"] == 900
    s = client.post(f"/api/exams/attempts/{aid}/finish").json()
    assert s["current"]["section"] == "EO"
    s = client.post(f"/api/exams/attempts/{aid}/begin").json()
    eo = s["current"]["eo_session_id"]
    assert client.get(f"/api/eo/sessions/{eo}").json()["mode"] == "exam"
    s = client.post(f"/api/exams/attempts/{aid}/finish").json()
    assert s["status"] == "completed"
    co, ce, ee, eo_r = s["results"]["sections"]
    assert (co["correct"], co["total"], ce["correct"], ce["total"]) == (6, 8, 7, 8)
    assert ee["writing_submission_id"] == sid and eo_r["eo_session_id"] == eo
    assert co["review"][0]["transcript"] and co["review"][0]["answer"] == "a"           # keys revealed at the end
    c = conn()
    assert c.execute("SELECT COUNT(*) FROM attempt WHERE context = 'exam'").fetchone()[0] == 16
    assert c.execute("SELECT evidence_weight FROM attempt WHERE context = 'exam'").fetchone()[0] == exam.EXAM_WEIGHT
    assert c.execute("SELECT COUNT(*) FROM weakness").fetchone()[0] >= 2
    assert c.execute("SELECT COUNT(*) FROM progress_history WHERE source = 'weekly'").fetchone()[0] >= 1
    assert c.execute("SELECT COUNT(*) FROM mistake").fetchone()[0] == 0                  # reserved items stay out of reviews
    # Taken once only; next weekly not due for 7 days
    assert client.post("/api/exams/weekly-1/start").status_code == 409
    l = client.get("/api/exams").json()
    assert not l["weekly_due"] and l["next_weekly"] == "weekly-2"


def test_section_timeout_closes_it_and_unanswered_count(client):
    aid = client.post("/api/exams/weekly-1/start").json()["id"]
    client.post(f"/api/exams/attempts/{aid}/begin")
    c = conn()
    row = c.execute("SELECT sections FROM exam_attempt WHERE id = ?", (aid,)).fetchone()
    secs = json.loads(row["sections"])
    secs[0]["started_at"] = "2020-01-01 00:00:00"
    c.execute("UPDATE exam_attempt SET sections = ? WHERE id = ?", (json.dumps(secs), aid))
    s = client.get(f"/api/exams/attempts/{aid}").json()
    assert s["current"]["section"] == "CE" and s["sections"][0]["timed_out"]
    r = client.post(f"/api/exams/attempts/{aid}/answer", json={"item_id": "t1-co-gare", "response": "a"})
    assert r.status_code == 409


def test_resume_returns_the_same_attempt(client):
    a = client.post("/api/exams/weekly-2/start").json()["id"]
    assert client.post("/api/exams/weekly-2/start").json()["id"] == a
