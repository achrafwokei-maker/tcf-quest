"""M12: full TCF Canada mock and section mocks — official timings, 3-task writing block, unseen guarantee."""

import json
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tcfquest import exam, planner, speaking_ai, writing_ai


@pytest.fixture()
def client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("TCFQUEST_DB", str(Path(tmp) / "test.db"))
        monkeypatch.setattr(writing_ai, "run", lambda c, sid: "failed")
        monkeypatch.setattr(speaking_ai, "run", lambda c, sid: "failed")
        from tcfquest.main import app

        with TestClient(app) as c:
            yield c


def test_full_mock_matches_the_official_format():
    e = exam.exams()["mock-full-1"]
    cfg = {s["id"]: s for s in json.loads(exam.EXAM_CONFIG.read_text())["sections"]}
    limits = [exam._limit_s(e, s.model_dump()) for s in e.sections]
    assert limits[:3] == [cfg["CO"]["minutes"] * 60, cfg["CE"]["minutes"] * 60, cfg["EE"]["minutes"] * 60]
    assert sum(limits[3:]) == cfg["EO"]["minutes"] * 60
    assert sum(limits) == 167 * 60                                                   # 2 h 47
    assert len(exam.section_items(e, "CO")) == cfg["CO"]["items"] == 39
    assert len(exam.section_items(e, "CE")) == cfg["CE"]["items"] == 39


def test_three_writing_tasks_share_one_countdown(client):
    aid = client.post("/api/exams/mock-ee-1/start").json()["id"]
    s = client.post(f"/api/exams/attempts/{aid}/begin").json()
    ids = s["current"]["writing_submission_ids"]
    assert len(ids) == 3 and [t["task"] for t in s["current"]["writing_tasks"]] == ["EE-T1", "EE-T2", "EE-T3"]
    subs = [client.get(f"/api/writing/submissions/{i}").json() for i in ids]
    assert {x["time_limit_s"] for x in subs} == {3600}
    client.put(f"/api/writing/submissions/{ids[1]}", json={"text": "Récit commencé par la tâche 2."})   # any order
    s = client.post(f"/api/exams/attempts/{aid}/finish").json()
    assert s["status"] == "completed"
    assert all(client.get(f"/api/writing/submissions/{i}").json()["status"] == "submitted" for i in ids)
    assert s["results"]["sections"][0]["writing_submission_ids"] == ids


def test_section_mock_makes_the_full_mock_unavailable(client):
    aid = client.post("/api/exams/mock-co-1/start").json()["id"]
    client.post(f"/api/exams/attempts/{aid}/begin")
    item = client.get(f"/api/exams/attempts/{aid}").json()["current"]["item"]
    client.post(f"/api/exams/attempts/{aid}/play", json={"item_id": item["id"]})
    client.post(f"/api/exams/attempts/{aid}/answer", json={"item_id": item["id"], "response": "a"})
    client.post(f"/api/exams/attempts/{aid}/finish")
    r = client.post("/api/exams/mock-full-1/start")
    assert r.status_code == 409 and "listening" in r.json()["detail"]
    full = next(x for x in client.get("/api/exams").json()["exams"] if x["id"] == "mock-full-1")
    assert full["blocked_by_seen"] == "listening"
    assert client.post("/api/exams/mock-ce-1/start").status_code == 200          # reading questions still unseen


def test_mock_is_recommended_after_two_weekly_trials(client):
    from test_missions_notebook import conn
    c = conn()
    assert planner.plan(c)["mock"]["recommended"] is False
    c.execute("INSERT INTO exam_attempt (exam_id, kind, status, sections, started_at, completed_at, results) "
              "VALUES ('diagnostic', 'diagnostic', 'completed', '[]', '2026-09-30 10:00:00', '2026-09-30 10:30:00', '{\"sections\": []}')")
    for n in (1, 2):
        c.execute("INSERT INTO exam_attempt (exam_id, kind, status, sections, started_at, completed_at, results) "
                  "VALUES (?, 'weekly', 'completed', '[]', '2026-10-01 10:00:00', '2026-10-01 11:00:00', '{\"sections\": []}')", (f"weekly-{n}",))
    m = planner.plan(c)["mock"]
    assert m["recommended"] and m["minutes"] == 167


def test_new_learner_starts_with_the_level_check(client):
    from test_missions_notebook import conn
    c = conn()
    c.execute("INSERT INTO profile (id, display_name, exam_window) VALUES (1, 'A', 'lt1m')")
    p = planner.plan(c)
    assert p["diagnostic"]["status"] == "available"
    assert p["weekly_trial"]["due"] is False and p["mock"]["recommended"] is False
