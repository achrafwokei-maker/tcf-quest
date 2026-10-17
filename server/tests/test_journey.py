"""The adventure: one journey, personal order, side missions, and a single Continue action."""

import json
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tcfquest import content, journey, speaking_ai, writing_ai


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


def onboard(client):
    for step, ans in [("language", {"ui_language": "en"}), ("welcome", {"ui_language": "en"}),
                      ("briefing", {"briefing_done": True}), ("target", {"target_nclc": 9}),
                      ("timing", {"exam_window": "3m"}), ("comfort", {"self_rating": 3}),
                      ("concern", {"concern": "speaking"}), ("daily_time", {"daily_minutes": 20}),
                      ("explorer", {"start_route": "evaluate", "display_name": "A"})]:
        client.put("/api/onboarding", json={"step": step, "answers": ans})
    assert client.post("/api/onboarding/complete").status_code == 200


def finish_diagnostic(client):
    from test_acceptance import run_exam
    run_exam(client, "diagnostic", "diagnostic-1", lambda it: it.level in ("A1", "A2"))


def test_every_node_points_at_real_content():
    from tcfquest import exam, speaking, writing
    for ch in journey.spec()["chapters"]:
        for ref in ch["nodes"] + ([ch["boss"]] if ch.get("boss") else []):
            kind, _, val = ref.partition(":")
            assert {"set": lambda v: all(content.get_set(x) for x in v.split("|")), "ee": writing.get_task, "eo": speaking.get_task,
                    "exam": lambda v: v in exam.exams(), "onboarding": lambda v: True}[kind](val), ref
    assert [c["n"] for c in journey.spec()["chapters"]] == [0, 1, 2, 3, 4, 5]


def test_new_learner_starts_at_the_briefing_then_the_level_check(client):
    c = client.get("/api/journey/continue").json()
    assert c["node"]["ref"] == "onboarding" and c["where"].startswith("Chapter 0")
    onboard(client)
    c = client.get("/api/journey/continue").json()
    assert c["node"]["kind"] == "diagnostic" and c["node"]["action"] == {"type": "start_exam", "exam_id": "diagnostic"}
    j = client.get("/api/journey").json()
    assert j["chapters"][1]["unlocked"] and not j["chapters"][2]["unlocked"]
    assert j["chapters"][1]["boss"]["state"] == "locked"                          # trial waits for progress + level check


def test_continue_resumes_the_exact_mission_in_progress(client):
    onboard(client)
    finish_diagnostic(client)
    s = client.get("/api/sets/acad-eo1").json()
    first = s["state"]["current_item_id"]
    client.post("/api/sets/acad-eo1/answer", json={"item_id": first})        # a card: the module is now started
    c = client.get("/api/journey/continue").json()
    assert c["node"]["ref"] == "set:acad-eo1" and c["node"]["state"] == "in_progress"
    assert c["why"].startswith("Resume") and c["next"]


def test_reviews_are_a_short_detour_then_back_to_the_main_route(client):
    onboard(client)
    finish_diagnostic(client)
    from test_missions_notebook import play
    play(client, "premiers-pas-a", wrong={"ppa-habiter"})
    conn().execute("UPDATE mistake SET next_review = ?", (date.today().isoformat(),))
    c = client.get("/api/journey/continue").json()
    assert c["node"]["kind"] == "review" and "quick detour" in c["where"] and "Then back to" in c["why"]
    assert c["node"]["action"] == {"type": "start_reviews"}


def test_upcoming_order_is_personal_and_easy_nodes_become_optional(client):
    onboard(client)
    c = conn()
    c.execute("UPDATE skill_profile SET cefr_low = 'B2', cefr_high = 'C1' WHERE skill = 'listening'")
    j = journey.build(c)
    ch1 = j["chapters"][1]
    pa = next(x for x in ch1["nodes"] if x["ref"] == "set:premiers-pas-a")
    assert pa["optional"] is True                                                 # A1–A2 listening for a B2 listener
    assert ch1["upcoming"][-1] == "set:premiers-pas-a" or pa["state"] == "done"   # optional nodes go last


def test_chapter_unlocks_after_most_of_the_previous_one(client):
    onboard(client)
    finish_diagnostic(client)
    c = conn()
    j = journey.build(c)
    assert not j["chapters"][2]["unlocked"]
    for ref in journey.spec()["chapters"][1]["nodes"]:
        kind, _, val = ref.partition(":")
        if kind == "set":
            c.execute("INSERT OR REPLACE INTO mission_progress (mission_id, status, step) VALUES (?, 'completed', 1)", (f"set:{val}",))
    j = journey.build(c)
    assert j["chapters"][1]["progress"] >= 0.6 and j["chapters"][2]["unlocked"]
    assert j["chapters"][1]["boss"]["state"] == "available"                       # weekly trial is due (none taken yet)


def test_journey_never_changes_learning_records(client):
    onboard(client)
    c = conn()
    before = [tuple(r) for r in c.execute("SELECT * FROM skill_profile ORDER BY skill")]
    client.get("/api/journey"); client.get("/api/journey/continue")
    assert [tuple(r) for r in c.execute("SELECT * FROM skill_profile ORDER BY skill")] == before
    assert c.execute("SELECT COUNT(*) FROM attempt").fetchone()[0] == 0


def test_every_journey_route_exists_in_the_app(client):
    import re
    paths = re.findall(r'<Route\s+(?:index|path="([^"]*)")', (Path(__file__).resolve().parents[2] / "web/src/main.tsx").read_text())
    patterns = [re.compile("^/" + re.sub(r":[A-Za-z]+", "[^/]+", p) + "$") for p in paths if p and p != "*"]
    onboard(client)
    conn().execute("UPDATE mistake SET next_review = date('now')")
    j = client.get("/api/journey").json()
    routes = [x["route"] for c in j["chapters"] for x in c["nodes"] + ([c["boss"]] if c["boss"] else [])] + [s["route"] for s in j["side_missions"]]
    cont = client.get("/api/journey/continue").json()
    if cont["node"]:
        routes.append(cont["node"]["route"])
    assert routes and all(any(p.match(r) for p in patterns) for r in routes), [r for r in routes if not any(p.match(r) for p in patterns)]
