"""M3: planner v1 — adapts to results, fits the time available, no backlog after a break."""

import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tcfquest import planner, weakness


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


def sets_in(plan):
    return [s["set_id"] for s in plan["steps"] if s["kind"] != "review"]


@pytest.mark.parametrize("minutes", [10, 20, 40])
def test_plan_fits_the_time_available(client, minutes):
    p = client.get(f"/api/today?minutes={minutes}").json()["plan"]
    assert p["minutes_available"] == minutes and p["steps"]
    assert p["minutes_planned"] <= minutes
    assert all(s["reason"].startswith("Trains") or s["kind"] == "review" for s in p["steps"])
    assert all(s["improves"] for s in p["steps"])


def test_bad_minutes_rejected(client):
    assert client.get("/api/today?minutes=2").status_code == 422


def test_weak_session_pushes_sets_with_unseen_items_on_that_weakness(client):
    from test_missions_notebook import play
    before = planner.plan(conn(), 40)
    play(client, "belleville-a2", wrong={"ba2-voudrais", "ba2-appel-2", "ba2-avant-midi"})
    after = planner.plan(conn(), 40)
    assert "belleville-a2" not in sets_in(after)                         # finished today and nothing unseen
    b1 = next(s for s in after["steps"] if s.get("set_id") == "belleville-b1")
    assert b1["factors"]["weakness"] > 0 and "weak points" in b1["reason"]
    assert any(c.startswith("gram.conditionnel") or c.startswith("eo.") for c in b1["improves"])
    assert sets_in(before) != sets_in(after)


def test_strong_session_moves_to_harder_level(client):
    from test_missions_notebook import play
    c = conn()
    low = {x["set"].id: x["factors"]["fit"] for x in planner.candidates(c, date.today(), planner.phase_for(None))}
    play(client, "premiers-pas-b")                                        # all correct, B1–B2 items
    play(client, "defi-b")
    c.execute("UPDATE skill_profile SET cefr_low = 'B1', cefr_high = 'B2'")  # stronger estimates
    high = {x["set"].id: x["factors"]["fit"] for x in planner.candidates(c, date.today(), planner.phase_for(None))}
    assert high["belleville-b1"] > low["belleville-b1"] and high["belleville-a2"] < low["belleville-a2"]


def test_reviews_come_first_and_include_retests(client):
    from test_missions_notebook import play
    play(client, "belleville-a2", wrong={"ba2-voudrais"})
    c = conn()
    for d in (1, 2):
        weakness.observe(c, "belleville-a2", __import__("tcfquest").content.item_by_id(
            __import__("tcfquest").content.get_set("belleville-a2"), "ba2-voudrais"), "correct", "", "", False,
            date.today() + timedelta(d))
    c.execute("UPDATE mistake SET next_review = ?", (date.today().isoformat(),))
    p = planner.plan(c, 20)
    assert p["steps"][0]["kind"] == "review" and p["steps"][0]["retests"] == 1
    assert "confirm" in p["steps"][0]["reason"]


def test_after_a_break_reviews_are_capped_and_nothing_piles_up(client):
    c = conn()
    today = date(2026, 11, 1)
    c.execute("INSERT INTO study_day (day, minutes) VALUES ('2026-10-20', 20)")
    for i in range(12):
        c.execute("INSERT INTO mistake (skill, category, item_id, set_id, context, learner_answer, correction, "
                  "explanation, next_review) VALUES ('reading', 'c', ?, 'x', 'q', 'a', 'b', 'e', '2026-10-21')", (f"i{i}",))
    p = planner.plan(c, 30, today)
    assert p["welcome_back"] and p["days_away"] == 12
    assert p["steps"][0]["kind"] == "review" and p["steps"][0]["count"] == 5


def test_phase_follows_the_exam_date():
    assert planner.phase_for(None)["focus"] == "foundations"
    assert planner.phase_for(10)["focus"] in ("foundations", "technique")
    assert planner.phase_for(2)["focus"] == "timed"


def test_rethink_weakness_prefers_a_lesson(client):
    c = conn()
    c.execute("INSERT INTO weakness (competency, skill, task, category, state, frequency, severity, rethink, first_seen, last_seen) "
              "VALUES ('gram.accord', 'writing', 'EE', 'grammar', 'training', 3, 0.7, 1, '2026-10-01', '2026-10-10')")
    ranked = planner.candidates(c, date.today(), planner.phase_for(None))
    top = next(x for x in ranked if x["set"].id == "outil-accord")
    assert top["factors"]["lesson"] >= 3 and "differently" in planner._reason(top)
    assert ranked.index(top) < 3


def test_technique_cause_points_to_the_academy(client):
    c = conn()
    c.execute("INSERT INTO weakness (competency, skill, task, category, cause, state, frequency, severity, first_seen, last_seen) "
              "VALUES ('ce.inference', 'reading', 'CE', 'comprehension', 'technique', 'training', 2, 0.4, '2026-10-01', '2026-10-10')")
    ranked = {x["set"].id: x for x in planner.candidates(c, date.today(), planner.phase_for(None))}
    assert ranked["acad-ce"]["factors"]["lesson"] >= 2
