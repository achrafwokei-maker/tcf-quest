"""M8: adaptive four-skill diagnostic and its report."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tcfquest import content, exam, speaking_ai, writing_ai


@pytest.fixture()
def client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("TCFQUEST_DB", str(Path(tmp) / "test.db"))
        monkeypatch.setattr(writing_ai, "run", lambda c, sid: "failed")
        monkeypatch.setattr(speaking_ai, "run", lambda c, sid: "failed")
        from tcfquest.main import app

        with TestClient(app) as c:
            yield c


def run_section(client, aid, correct_if):
    """Answer the adaptive section; `correct_if(level)` decides whether to answer right. Returns levels served."""
    levels = []
    while True:
        s = client.get(f"/api/exams/attempts/{aid}").json()
        cur = s.get("current", {})
        if "item" not in cur:
            return levels, s
        item = cur["item"]
        it = content.item_by_id(content.get_set("diagnostic-1"), item["id"])
        levels.append(it.level)
        if item["type"] == "listen":
            client.post(f"/api/exams/attempts/{aid}/play", json={"item_id": item["id"]})
        resp = it.answer if correct_if(it.level) else "zzz"
        assert client.post(f"/api/exams/attempts/{aid}/answer", json={"item_id": item["id"], "response": resp}).status_code == 200


def test_staircase_goes_up_for_a_strong_learner_and_down_for_a_weak_one(client):
    aid = client.post("/api/exams/diagnostic/start").json()["id"]
    client.post(f"/api/exams/attempts/{aid}/begin")
    strong, s = run_section(client, aid, lambda lvl: True)
    assert len(strong) == 8 and strong[0] in ("A2", "B1") and "C1" in strong
    client.post(f"/api/exams/attempts/{aid}/begin")
    weak, s = run_section(client, aid, lambda lvl: False)
    assert len(weak) == 8 and "C1" not in weak and sum(l in ("A1", "A2") for l in weak) >= 5   # pool has 5 A1–A2 items (M11 adds more)
    assert s["sections"][1]["ended"]
    final = exam._load(__import__("tcfquest.db", fromlist=["db"]).connect(), aid)[2][1]["level"]
    assert final == 0                                              # the staircase settled at A1
    assert len(set(strong)) > 1                                   # it really adapts


def test_full_diagnostic_produces_a_report_and_marks_the_campaign_assessed(client):
    client.put("/api/onboarding", json={"step": "concern", "answers": {"self_rating": 3}})
    for step, ans in [("welcome", {"ui_language": "en"}), ("timing", {"exam_window": "6m"}),
                      ("daily_time", {"daily_minutes": 20}), ("explorer", {"start_route": "evaluate"})]:
        client.put("/api/onboarding", json={"step": step, "answers": ans})
    client.post("/api/onboarding/complete")
    assert client.get("/api/campaign").json()["start"]["provisional"] is True
    aid = client.post("/api/exams/diagnostic/start").json()["id"]
    client.post(f"/api/exams/attempts/{aid}/begin")
    run_section(client, aid, lambda lvl: lvl in ("A1", "A2", "B1"))
    client.post(f"/api/exams/attempts/{aid}/begin")
    run_section(client, aid, lambda lvl: lvl in ("A1", "A2"))
    client.post(f"/api/exams/attempts/{aid}/begin")
    s = client.post(f"/api/exams/attempts/{aid}/finish").json()                  # EE: nothing written
    client.post(f"/api/exams/attempts/{aid}/begin")
    s = client.post(f"/api/exams/attempts/{aid}/finish").json()                  # EO
    assert s["status"] == "completed"
    r = s["report"]
    assert r["kind"] == "diagnostic" and r["label"].startswith("Practice estimate")
    listening, reading = r["skills"][0], r["skills"][1]
    assert listening["estimate"]["cefr_low"] and listening["adaptive_final_level"]
    assert any("not an official TCF result" in x for x in r["limits"])
    assert r["priorities"] and r["next"]["steps"]
    assert r["error_categories"]                                                # wrong answers → categories
    assert client.get("/api/campaign").json()["start"]["provisional"] is False
    assert client.post("/api/exams/diagnostic/start").status_code == 409        # once only
    hist = exam.listing(__import__("tcfquest.db", fromlist=["db"]).connect())
    assert hist["diagnostic"]["status"] == "completed" and hist["weekly_due"]   # the diagnostic isn't a weekly trial
