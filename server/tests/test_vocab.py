"""Vocabulary cards: valid deck, spaced repetition, daily caps, and no effect on skill evidence."""

import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tcfquest import vocab

D0 = date(2026, 11, 2)


@pytest.fixture()
def client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("TCFQUEST_DB", str(Path(tmp) / "test.db"))
        from tcfquest.main import app

        with TestClient(app) as c:
            yield c


def conn():
    from tcfquest import db
    return db.connect()


def test_deck_is_complete_and_tagged():
    d = vocab.deck()
    assert len(d.cards) >= 72 and len(d.functions) == 9
    for f in d.functions:
        assert sum(c.function == f.id for c in d.cards) >= 8
    assert all(c.tcf_target.purpose for c in d.cards)
    assert {c.level for c in d.cards} >= {"A2", "B1", "B2"}


def test_schedule_steps_and_lapses(client):
    c = conn()
    cid = "demander-01"
    r = vocab.grade(c, cid, "good", D0)                           # first meeting: learn now, review tomorrow
    assert (r["box"], r["due"]) == (0, (D0 + timedelta(1)).isoformat())
    r = vocab.grade(c, cid, "good", D0 + timedelta(1))
    assert (r["box"], r["due"]) == (1, (D0 + timedelta(3)).isoformat())           # +2 days
    r = vocab.grade(c, cid, "easy", D0 + timedelta(3))
    assert r["box"] == 3 and r["due"] == (D0 + timedelta(3 + 8)).isoformat()      # skips a step, +8 days
    r = vocab.grade(c, cid, "hard", D0 + timedelta(11))
    assert r["box"] == 3 and r["due"] == (D0 + timedelta(11 + 4)).isoformat()     # same step, shorter
    r = vocab.grade(c, cid, "again", D0 + timedelta(15))
    assert r["box"] == 0 and r["due"] == (D0 + timedelta(16)).isoformat()
    assert c.execute("SELECT lapses FROM vocab_progress WHERE card_id = ?", (cid,)).fetchone()[0] == 1
    for k in range(6):
        r = vocab.grade(c, cid, "easy", D0 + timedelta(20 + k))
    assert r["mastered"] and vocab.overview(c, D0 + timedelta(400))["due"] == 0   # mastered cards stop coming back


def test_session_caps_new_cards_and_orders_reviews_first(client):
    c = conn()
    s = vocab.session(c, D0)
    assert len(s) == vocab.DAILY_NEW and all(x["new"] for x in s)
    for x in s:
        vocab.grade(c, x["id"], "good", D0)
    assert vocab.session(c, D0) == []                                             # nothing left today
    s2 = vocab.session(c, D0 + timedelta(1))
    assert [x["new"] for x in s2] == [False] * 8 + [True] * 8                    # reviews first, then 8 new
    assert len(vocab.session(c, D0 + timedelta(1))) == 16


def test_weak_task_functions_come_first_for_new_cards(client):
    c = conn()
    c.execute("INSERT INTO weakness (competency, skill, task, category, state, frequency, severity, first_seen, last_seen) "
              "VALUES ('x.y', 'writing', 'EE-T3', 'grammar', 'training', 2, 0.5, '2026-10-01', '2026-10-01')")
    first = vocab.session(c, D0)[0]
    assert first["function"] in ("nuancer", "cause", "formel", "raconter")      # writing (EE) functions lead


def test_api_flow_and_records_stay_separate(client):
    before = [tuple(r) for r in conn().execute("SELECT * FROM skill_profile ORDER BY skill")]
    o = client.get("/api/vocab").json()
    assert o["total"] == 72 and o["new_today"] == 8 and len(o["functions"]) == 9
    s = client.get("/api/vocab/session").json()
    assert len(s["cards"]) == 8 and {"fr", "en", "example", "function_label", "new"} <= set(s["cards"][0])
    r = client.post(f"/api/vocab/{s['cards'][0]['id']}/grade", json={"grade": "good"}).json()
    assert r["box"] == 0
    assert client.post("/api/vocab/nope-01/grade", json={"grade": "good"}).status_code == 404
    assert client.post(f"/api/vocab/{s['cards'][0]['id']}/grade", json={"grade": "meh"}).status_code == 422
    assert client.get("/api/vocab").json()["learned"] == 1
    c = conn()
    assert [tuple(r) for r in c.execute("SELECT * FROM skill_profile ORDER BY skill")] == before
    assert c.execute("SELECT COUNT(*) FROM attempt").fetchone()[0] == 0 and c.execute("SELECT COUNT(*) FROM weakness").fetchone()[0] == 0
