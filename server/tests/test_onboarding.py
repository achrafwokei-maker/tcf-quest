"""Milestone 3: conversational onboarding (autosave, resume, completion) and the personal campaign."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tcfquest import onboarding


@pytest.fixture()
def client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("TCFQUEST_DB", str(Path(tmp) / "test.db"))
        from tcfquest.main import app

        with TestClient(app) as c:
            yield c


def save(client, step, **answers):
    r = client.put("/api/onboarding", json={"step": step, "answers": answers})
    assert r.status_code == 200, r.text
    return r.json()


FULL = [
    ("welcome", {"ui_language": "en"}),
    ("target", {"knows_exam": True}),
    ("timing", {"target_choice": "nclc9"}),
    ("comfort", {"exam_window": "3m"}),
    ("concern", {"self_rating": 3}),
    ("daily_time", {"concern": "speaking"}),
    ("preference", {"daily_minutes": 20}),
    ("challenge", {"preference": "conversation"}),
    ("route", {}),
    ("explorer", {"start_route": "train"}),
    ("campaign", {"display_name": "Alex"}),
]


def test_starts_empty_and_resumes_exactly(client):
    s = client.get("/api/onboarding").json()
    assert s == {"step": "language", "answers": {}, "completed": False, "challenge_set": "defi-a"}
    save(client, "welcome", ui_language="fr")
    save(client, "target", knows_exam=False, briefing_done=True, quiz={"q1": "EO", "q2": "2h47"})
    # "Refresh": everything comes back, including the step
    s = client.get("/api/onboarding").json()
    assert s["step"] == "target"
    assert s["answers"]["ui_language"] == "fr" and s["answers"]["quiz"]["q2"] == "2h47"


def test_invalid_answers_and_steps_are_rejected(client):
    assert client.put("/api/onboarding", json={"step": "comfort", "answers": {"self_rating": 9}}).status_code == 422
    assert client.put("/api/onboarding", json={"step": "nowhere", "answers": {}}).status_code == 422
    assert client.put("/api/onboarding", json={"step": "timing", "answers": {"daily_minutes": 17}}).status_code == 422
    assert client.get("/api/onboarding").json()["answers"] == {}       # nothing invalid was saved


def test_challenge_band_follows_self_rating(client):
    assert save(client, "concern", self_rating=2)["challenge_set"] == "defi-a"
    assert save(client, "concern", self_rating=3)["challenge_set"] == "defi-b"


def test_cannot_complete_with_missing_answers(client):
    save(client, "welcome", ui_language="en")
    r = client.post("/api/onboarding/complete")
    assert r.status_code == 409 and "exam_window" in r.json()["detail"]


def test_full_run_creates_profile_and_campaign(client):
    for step, answers in FULL:
        save(client, step, **answers)
    # One challenge answer wrong (reading), one right (listening)
    client.post("/api/sets/defi-b/answer", json={"item_id": "db-cabinet-medical", "response": "c"})
    client.post("/api/sets/defi-b/answer", json={"item_id": "db-centre-ville", "response": "a"})

    c = client.post("/api/onboarding/complete").json()
    assert c["name"] == "Alex"
    assert c["objective"] == {"nclc": 9, "nclc_by_skill": None, "cefr_goal": "C1"}
    assert c["start"]["provisional"] is True
    assert (c["start"]["cefr_low"], c["start"]["cefr_high"]) == ("A2", "B1")
    assert c["rhythm"]["plan_mode"] == "sprint" and c["rhythm"]["weekly_hours"] == 1.7
    assert [p["skill"] for p in c["priorities"]] == ["speaking", "reading", "writing"]
    assert c["priorities"][0]["reason"].startswith("You told me")
    assert c["challenge"] == {"set_id": "defi-b", "answered": 2, "correct": 1}

    profile = client.get("/api/profile").json()["profile"]
    assert profile["onboarded_at"] and profile["display_name"] == "Alex"
    assert client.get("/api/onboarding").json()["completed"] is True
    assert client.get("/api/campaign").json()["route"] == "train"


def test_onboarding_weight_is_weak_evidence(client):
    client.post("/api/sets/defi-a/answer", json={"item_id": "da-pharmacie", "response": "b"})
    from tcfquest import db
    assert db.connect().execute("SELECT evidence_weight FROM attempt").fetchone()[0] == 0.1


def test_per_skill_targets_and_unnamed_explorer(client):
    for step, answers in FULL[:-1]:
        save(client, step, **answers)
    save(client, "timing", target_choice="nclc_specific",
         target_by_skill={"listening": 9, "reading": 9, "speaking": 8, "writing": 7})
    c = client.post("/api/onboarding/complete").json()
    assert c["objective"]["nclc"] == 7                                  # lowest skill target is the binding one
    assert c["objective"]["nclc_by_skill"]["writing"] == 7
    assert c["name"] == "Explorer"


def test_restart_keeps_existing_profile_and_prefills(client):
    client.put("/api/profile", json={"display_name": "Alex", "daily_minutes": 30, "target_nclc": 9})
    s = client.post("/api/onboarding/restart").json()
    assert s["step"] == "language" and s["completed"] is False
    assert s["answers"]["display_name"] == "Alex" and s["answers"]["daily_minutes"] == 30
    assert client.get("/api/profile").json()["profile"]["display_name"] == "Alex"   # untouched


@pytest.mark.parametrize("rating,set_id,verdicts,expected", [
    (1, "defi-a", [], ("A1", "A2")),                                    # always a range
    (2, "defi-a", ["correct"] * 4, ("A1", "B1")),                        # strong on the easy set → upper bound up
    (3, "defi-b", ["incorrect"] * 4, ("A1", "B1")),                      # weak on the harder set → lower bound down
    (4, "defi-b", ["correct", "skipped"], ("B1", "B2")),
])
def test_provisional_band(rating, set_id, verdicts, expected):
    results = [{"item_id": str(i), "verdict": v, "section": "CO"} for i, v in enumerate(verdicts)]
    assert onboarding.provisional_band(rating, set_id, results) == expected
