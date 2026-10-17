"""M9: post-exam intelligence — timing, root causes, retests, and next week's plan adapts."""

import tempfile
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tcfquest import analysis, content, planner, speaking_ai, writing_ai


def q(level, comp, correct, answered=True):
    return {"item_id": f"{comp}-{level}", "level": level, "competency": comp, "correct": correct, "answered": answered}


def test_timing_rules():
    res = {"sections": [
        {"section": "CO", "skill": "listening", "timed_out": True, "time_used_s": 480, "limit_s": 480, "total": 8, "correct": 3, "unanswered": 3, "review": []},
        {"section": "CE", "skill": "reading", "timed_out": False, "time_used_s": 200, "limit_s": 720, "total": 8, "correct": 3, "unanswered": 0, "review": []},
    ]}
    t = {x["section"]: x["problem"] for x in analysis.timing(res)}
    assert t == {"CO": "out_of_time", "CE": "rushed"}


def test_root_causes_need_evidence():
    review = [q("A2", "ce.information-cle", True), q("B1", "ce.document-pratique", True),
              q("B1", "ce.inference", False),          # technique: factual B1 was right
              q("A2", "ce.message", False),            # french: within estimated level
              q("C1", "ce.nuance", False),             # above level, no factual C1 right: no diagnosis
              q("B2", "ce.document-pratique", False, answered=False)]
    res = {"sections": [{"section": "CE", "skill": "reading", "timed_out": False, "unanswered": 1, "review": review}]}
    est = {"reading": {"cefr_low": "A2", "cefr_high": "B1"}}
    causes = {c["competency"]: c["cause"] for c in analysis.root_causes(res, est, ["gram.accord"])}
    assert causes == {"ce.inference": "technique", "ce.message": "french", "gram.accord": "french"}


@pytest.fixture()
def client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("TCFQUEST_DB", str(Path(tmp) / "test.db"))
        monkeypatch.setattr(writing_ai, "run", lambda c, sid: "failed")
        monkeypatch.setattr(speaking_ai, "run", lambda c, sid: "failed")
        from tcfquest.main import app

        with TestClient(app) as c:
            yield c


def take_trial(client, exam_id, set_id, right_if):
    aid = client.post(f"/api/exams/{exam_id}/start").json()["id"]
    for _ in range(2):
        client.post(f"/api/exams/attempts/{aid}/begin")
        while True:
            cur = client.get(f"/api/exams/attempts/{aid}").json().get("current", {})
            if "item" not in cur:
                break
            it = content.item_by_id(content.get_set(set_id), cur["item"]["id"])
            if it.type == "listen":
                client.post(f"/api/exams/attempts/{aid}/play", json={"item_id": it.id})
            client.post(f"/api/exams/attempts/{aid}/answer", json={"item_id": it.id, "response": it.answer if right_if(it) else "zzz"})
    for _ in range(2):
        client.post(f"/api/exams/attempts/{aid}/begin")
        s = client.post(f"/api/exams/attempts/{aid}/finish").json()
    return s


def test_weak_listening_trial_changes_next_weeks_plan(client):
    from test_missions_notebook import conn
    c = conn()
    before = {x["set"].id: x["score"] for x in planner.candidates(c, date.today(), planner.phase_for(None))}
    s = take_trial(client, "weekly-1", "trial-1", lambda it: it.tcf_target.section == "CE")   # listening all wrong
    r = s["report"]
    assert r["focus"] and r["focus"][0]["skill"] == "listening" and "0 %" in r["focus"][0]["reason"]
    assert r["retests"] and r["root_causes"] is not None and r["timing"]
    fx = analysis.active_focus(c)
    assert fx[0]["skill"] == "listening"
    after = {x["set"].id: x for x in planner.candidates(c, date.today(), planner.phase_for(None))}
    # Sets whose main section is listening (premiers-pas-a/b) gain the focus bonus
    pa = after["premiers-pas-a"]
    assert pa["factors"]["focus"] > 0 and pa["score"] > before["premiers-pas-a"]
    assert "last assessment" in planner._reason(pa)
    # All listening wrong and nothing right to compare with: no cause can be claimed for listening
    assert not [x for x in r["root_causes"] if x["skill"] == "listening"]
    assert c.execute("SELECT COUNT(*) FROM weakness WHERE skill = 'listening' AND cause != 'unknown'").fetchone()[0] == 0


def test_focus_expires_after_a_week(client):
    from test_missions_notebook import conn
    take_trial(client, "weekly-2", "trial-2", lambda it: False)
    c = conn()
    assert analysis.active_focus(c)
    assert analysis.active_focus(c, date(2099, 1, 1)) == []
