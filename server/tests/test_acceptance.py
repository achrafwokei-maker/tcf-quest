"""M13: the 12-step learner journey, end to end, on a fresh database (AI mocked out).

1 discover the format · 2 set a target · 3 diagnostic · 4 roadmap · 5 TCF mission · 6 feedback ·
7 weakness recorded · 8 corrective practice · 9 improve on an unseen task · 10 weekly trial ·
11 diagnostic report · 12 the next plan adapts.
"""

import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tcfquest import content, planner, speaking_ai, weakness, writing_ai


@pytest.fixture()
def client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("TCFQUEST_DB", str(Path(tmp) / "test.db"))
        monkeypatch.setattr(writing_ai, "run", lambda c, sid: "failed")
        monkeypatch.setattr(speaking_ai, "run", lambda c, sid: "failed")
        from tcfquest.main import app

        with TestClient(app) as c:
            yield c


def conn():
    from tcfquest import db
    return db.connect()


def run_exam(client, exam_id, set_id, right_if):
    aid = client.post(f"/api/exams/{exam_id}/start").json()["id"]
    while True:
        s = client.get(f"/api/exams/attempts/{aid}").json()
        if s["status"] == "completed":
            return s
        cur = s["current"]
        if not cur["started"]:
            client.post(f"/api/exams/attempts/{aid}/begin")
            continue
        if "item" in cur:
            it = content.item_by_id(content.get_set(set_id), cur["item"]["id"])
            if it.type == "listen":
                client.post(f"/api/exams/attempts/{aid}/play", json={"item_id": it.id})
            client.post(f"/api/exams/attempts/{aid}/answer",
                        json={"item_id": it.id, "response": it.answer if right_if(it) else "zzz"})
        else:
            client.post(f"/api/exams/attempts/{aid}/finish")


def test_the_twelve_step_learner_journey(client):
    c = conn()
    # 1–2. Discover the format and set a target (onboarding, autosaved per step)
    for step, ans in [("language", {"ui_language": "en"}), ("welcome", {"ui_language": "en"}),
                      ("briefing", {"briefing_done": True}), ("target", {"target_nclc": 9}),
                      ("timing", {"exam_window": "3m"}), ("comfort", {"self_rating": 3}),
                      ("concern", {"concern": "speaking"}), ("daily_time", {"daily_minutes": 20}),
                      ("explorer", {"start_route": "evaluate", "display_name": "Alex"})]:
        assert client.put("/api/onboarding", json={"step": step, "answers": ans}).status_code == 200
    client.post("/api/onboarding/complete")
    profile = client.get("/api/profile").json()["profile"]
    assert profile["exam_briefing_done"] == 1 and profile["target_nclc"] == 9
    assert client.get("/api/campaign").json()["start"]["provisional"] is True

    # 3. Diagnostic across the four skills (adaptive CO/CE + EE + EO)
    diag = run_exam(client, "diagnostic", "diagnostic-1", lambda it: it.level in ("A1", "A2", "B1"))
    assert diag["report"]["kind"] == "diagnostic" and len(diag["report"]["skills"]) == 4
    assert client.get("/api/campaign").json()["start"]["provisional"] is False

    # 4. A personalised roadmap with reasons
    plan = client.get("/api/today").json()["plan"]
    assert plan["steps"] and all(s["reason"] for s in plan["steps"]) and plan["diagnostic"]["status"] == "completed"

    # 5–6. A TCF-specific mission with feedback
    from test_missions_notebook import play
    play(client, "belleville-a2", wrong={"ba2-voudrais"})
    r = c.execute("SELECT verdict FROM attempt WHERE item_id = 'ba2-voudrais' ORDER BY id").fetchall()
    assert [x["verdict"] for x in r][:2] == ["incorrect", "correct"]                 # wrong, then re-queued and fixed

    # 7. The weakness is recorded at concept level
    nb = client.get("/api/notebook").json()
    w = next(x for x in nb["weaknesses"] if x["competency"] == "gram.conditionnel-politesse")
    assert w["state"] in ("detected", "training") and w["examples"]

    # 8. Corrective practice: tomorrow's plan opens with the review
    c.execute("UPDATE mistake SET next_review = ?", (date.today().isoformat(),))
    assert client.get("/api/today").json()["plan"]["steps"][0]["kind"] == "review"

    # 9. Improvement confirmed on an UNSEEN question
    item = content.item_by_id(content.get_set("belleville-a2"), "ba2-voudrais")
    for d in (1, 2):
        weakness.observe(c, "belleville-a2", item, "correct", "", "", False, date.today() + timedelta(days=d))
    w = c.execute("SELECT * FROM weakness WHERE competency = 'gram.conditionnel-politesse'").fetchone()
    assert w["state"] == "retest_due" and w["retest_item"] and "ba2-voudrais" not in w["retest_item"]
    client.post("/api/reviews/start")
    ids = list(client.get("/api/sets/revisions").json()["set"]["items"])
    assert w["retest_item"] in ids
    src, retest = content.resolve_item(None, w["retest_item"])
    state = client.get("/api/sets/revisions").json()["state"]
    while state["status"] != "completed":
        iid = state["current_item_id"]
        _, it = content.resolve_item(None, iid)
        resp = it.answers[0] if isinstance(it, content.TypeItem) else getattr(it, "answer", None)
        state = client.post("/api/sets/revisions/answer", json={"item_id": iid, "response": resp}).json()["state"]
    assert c.execute("SELECT state FROM weakness WHERE competency = 'gram.conditionnel-politesse'").fetchone()[0] == "mastered"

    # 10–11. A weekly timed trial and its report
    before = {x["set"].id: x["score"] for x in planner.candidates(c, date.today(), planner.phase_for(12))}
    trial = run_exam(client, "weekly-1", "trial-1", lambda it: it.tcf_target.section == "CE")
    rep = trial["report"]
    assert rep["kind"] == "weekly" and rep["limits"] and rep["priorities"] and rep["focus"]
    assert rep["focus"][0]["skill"] == "listening"

    # 12. The next plan adapts to the result
    after = {x["set"].id: x for x in planner.candidates(c, date.today(), planner.phase_for(12))}
    changed = [k for k in after if k in before and after[k]["score"] > before[k] and after[k]["factors"]["focus"] > 0]
    assert changed, "no set gained priority from the trial"
