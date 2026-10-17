"""Milestone 2: learner feedback flags, disputes and the review queue."""

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


def answer(client, set_id, item_id, response):
    r = client.post(f"/api/sets/{set_id}/answer", json={"item_id": item_id, "response": response})
    assert r.status_code == 200, r.text
    return r.json()


def weight(attempt_id):
    from tcfquest import db
    return db.connect().execute("SELECT evidence_weight, verdict FROM attempt WHERE id = ?", (attempt_id,)).fetchone()


def flag(client, attempt_id, kind, note=""):
    return client.post(f"/api/attempts/{attempt_id}/flags", json={"kind": kind, "note": note})


def advance_to(client, set_id, item_id):
    """Answer earlier items correctly-ish until item_id is current."""
    for _ in range(10):
        state = client.get(f"/api/sets/{set_id}").json()["state"]
        if state["current_item_id"] == item_id:
            return
        client.post(f"/api/sets/{set_id}/answer", json={"item_id": state["current_item_id"], "response": None, "skipped": True})
    raise AssertionError("item not reached")


def test_noted_flags_do_not_touch_evidence(client):
    a = answer(client, "premiers-pas-a", "ppa-boulangerie", "a")
    before = weight(a["attempt_id"])["evidence_weight"]
    for kind in ("too_easy", "too_hard", "unclear"):
        r = flag(client, a["attempt_id"], kind).json()
        assert r["status"] == "noted" and r["evidence_removed"] is False
    assert weight(a["attempt_id"])["evidence_weight"] == before
    assert flag(client, a["attempt_id"], "too_easy").status_code == 409          # once per kind
    assert flag(client, a["attempt_id"], "nonsense").status_code == 422


def test_only_wrong_answers_can_be_disputed(client):
    a = answer(client, "premiers-pas-a", "ppa-boulangerie", "a")                  # correct
    assert flag(client, a["attempt_id"], "dispute").status_code == 409
    assert flag(client, 9999, "dispute").status_code == 404


def test_accepted_dispute_restores_evidence_and_accepts_the_answer_next_time(client):
    advance_to(client, "premiers-pas-a", "ppa-habiter")
    a = answer(client, "premiers-pas-a", "ppa-habiter", "résidons")                # plausible, not in the key
    assert a["verdict"] == "incorrect"
    original = weight(a["attempt_id"])["evidence_weight"]
    assert original > 0

    r = flag(client, a["attempt_id"], "dispute", "« résider » works here too").json()
    assert r["evidence_removed"] is True
    assert weight(a["attempt_id"])["evidence_weight"] == 0

    queue = client.get("/api/review").json()
    report = next(x for x in queue["reports"] if x["kind"] == "dispute")
    assert report["learner_answer"] == "résidons" and report["expected"] == "habitons"
    assert report["prompt"].startswith("Nous ___")

    assert client.post(f"/api/review/{report['id']}/accept", json={"note": "Valid synonym"}).json()["accepted"] == 1
    row = weight(a["attempt_id"])
    assert row["verdict"] == "correct" and row["evidence_weight"] == original
    assert client.get("/api/review").json()["reports"] == []
    assert client.post(f"/api/review/{report['id']}/accept", json={}).status_code == 409   # already resolved

    # Next time the same answer is correct immediately (case/accents of the stored key normalised).
    client.post("/api/sets/premiers-pas-a/restart")
    advance_to(client, "premiers-pas-a", "ppa-habiter")
    again = answer(client, "premiers-pas-a", "ppa-habiter", "Résidons")
    assert again["verdict"] == "correct" and "Accepted" in again["note"]


def test_rejected_dispute_needs_a_reason_and_restores_evidence(client):
    a = answer(client, "premiers-pas-a", "ppa-boulangerie", "c")                  # wrong
    original = weight(a["attempt_id"])["evidence_weight"]
    flag(client, a["attempt_id"], "dispute")
    fid = client.get("/api/review").json()["reports"][0]["id"]
    assert client.post(f"/api/review/{fid}/reject", json={"note": ""}).status_code == 422
    assert client.post(f"/api/review/{fid}/reject", json={"note": "The audio says « deux croissants »."}).status_code == 200
    row = weight(a["attempt_id"])
    assert row["verdict"] == "incorrect" and row["evidence_weight"] == original


def test_technical_report_removes_evidence_permanently(client):
    a = answer(client, "premiers-pas-a", "ppa-boulangerie", "a")
    flag(client, a["attempt_id"], "technical", "Audio cut off")
    fid = client.get("/api/review").json()["reports"][0]["id"]
    assert client.post(f"/api/review/{fid}/accept", json={}).status_code == 409    # not a dispute
    assert client.post(f"/api/review/{fid}/close", json={"note": "Known browser issue"}).status_code == 200
    assert weight(a["attempt_id"])["evidence_weight"] == 0


def test_items_to_fix_after_repeated_unclear_reports(client):
    for _ in range(2):
        client.post("/api/sets/premiers-pas-a/restart")
        a = answer(client, "premiers-pas-a", "ppa-boulangerie", "a")
        flag(client, a["attempt_id"], "unclear")
    fix = client.get("/api/review").json()["items_to_fix"]
    assert fix and fix[0]["item_id"] == "ppa-boulangerie"


def test_why_only_after_answering(client):
    assert client.get("/api/sets/premiers-pas-a/why/ppa-boulangerie").status_code == 404
    answer(client, "premiers-pas-a", "ppa-boulangerie", "b")
    why = client.get("/api/sets/premiers-pas-a/why/ppa-boulangerie").json()
    assert why["correct_answer"] == "Deux croissants."
    assert len(why["options"]) == 4 and sum(o["correct"] for o in why["options"]) == 1
    assert why["transcript"].startswith("Bonjour")
