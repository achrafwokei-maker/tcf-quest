"""Milestone 4: Belleville missions, mistake notebook, spaced reviews, mastery, minutes."""

import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tcfquest import checking, content, notebook


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


def right_answer(item):
    if isinstance(item, content.MultiItem):
        return item.answers
    if isinstance(item, content.ChoiceItem):
        return item.answer
    if isinstance(item, content.ArrangeItem):
        return item.answers[0]
    if isinstance(item, content.TypeItem):
        return item.answers[0]
    return None


def play(client, set_id, wrong=(), duration_ms=30000):
    """Play a whole set; items in `wrong` get a wrong answer on their first try."""
    s = content.get_set(set_id)
    seen_wrong = set()
    for _ in range(60):
        state = client.get(f"/api/sets/{set_id}").json()["state"]
        if state["status"] == "completed":
            return state
        item = content.item_by_id(s, state["current_item_id"])
        response = right_answer(item)
        if item.id in wrong and item.id not in seen_wrong:
            seen_wrong.add(item.id)
            response = "zzz" if isinstance(item, (content.ChoiceItem, content.TypeItem)) else ["zzz"]
        r = client.post(f"/api/sets/{set_id}/answer",
                        json={"item_id": item.id, "response": response, "duration_ms": duration_ms})
        assert r.status_code == 200, r.text
    raise AssertionError("set never completed")


# ---------- unit: checklist checking, schedule, mastery ----------

def test_check_multi():
    assert checking.check_multi(["a", "b", "d"], ["a", "b", "d"]).verdict == "correct"
    assert checking.check_multi(["a", "b"], ["a", "b", "d"]).verdict == "partial"          # one missing
    assert checking.check_multi(["a", "b", "d", "c"], ["a", "b", "d"]).verdict == "partial"  # one extra
    assert checking.check_multi(["c"], ["a", "b", "d"]).verdict == "incorrect"
    assert checking.check_multi([], ["a", "b"]).verdict == "incorrect"


def test_schedule_moves_1_3_7_14_and_masters(client):
    item = content.item_by_id(content.get_set("premiers-pas-a"), "ppa-habiter")
    c = conn()
    d0 = date(2026, 10, 16)
    assert notebook.record(c, "premiers-pas-a", item, "incorrect", "habitez", d0) == "opened"
    row = c.execute("SELECT * FROM mistake").fetchone()
    assert row["next_review"] == "2026-10-17" and row["status"] == "open"
    # Correct the same day doesn't move it (no cramming)
    assert notebook.record(c, "premiers-pas-a", item, "correct", "habitons", d0) is None
    expected = [(1, 3, "improving"), (4, 7, "improving"), (11, 14, "mastered")]
    day = d0 + timedelta(days=1)
    for offset, interval, status in expected:
        day = d0 + timedelta(days=offset)
        notebook.record(c, "premiers-pas-a", item, "correct", "habitons", day)
        row = c.execute("SELECT * FROM mistake").fetchone()
        assert (row["interval_days"], row["status"]) == (interval, status)
    # Wrong again later re-opens it from the start
    assert notebook.record(c, "premiers-pas-a", item, "incorrect", "habitent", day + timedelta(days=20)) == "reopened"
    row = c.execute("SELECT * FROM mistake").fetchone()
    assert (row["status"], row["interval_days"], row["recurrence"]) == ("open", 1, 2)


def test_mastery_needs_attempts_days_and_an_unhinted_answer(client):
    item = content.item_by_id(content.get_set("premiers-pas-a"), "ppa-habiter")
    c = conn()
    for i in range(6):
        notebook.update_mastery(c, item, "correct", 0.4, hinted=True, today=date(2026, 10, 16))
    row = c.execute("SELECT * FROM mastery WHERE competency = 'gram.present-er'").fetchone()
    assert row["p_known"] >= 0.85 and not notebook.is_mastered(row)        # one day only, all hinted
    notebook.update_mastery(c, item, "correct", 0.4, hinted=False, today=date(2026, 10, 17))
    row = c.execute("SELECT * FROM mastery WHERE competency = 'gram.present-er'").fetchone()
    assert notebook.is_mastered(row)


# ---------- missions ----------

def test_belleville_b1_end_to_end_without_ai(client):
    state = play(client, "belleville-b1", wrong={"bb1-aimerais", "bb1-preparation"})
    s = content.get_set("belleville-b1")
    assert state["summary"]["items"] == len(content.scored(s.items)) == 12
    assert state["summary"]["correct_first_try"] == 10
    seen = [r for r in state["results"] if r["verdict"] == "seen"]
    assert len(seen) == 5                                                    # story, objective, method, language, outro
    c = conn()
    assert c.execute("SELECT COUNT(*) FROM attempt WHERE context_id = 'belleville-b1'").fetchone()[0] == 14  # 12 + 2 retries
    mistakes = {r["item_id"]: r for r in c.execute("SELECT * FROM mistake")}
    assert set(mistakes) == {"bb1-aimerais", "bb1-preparation"}
    assert mistakes["bb1-aimerais"]["correction"] == "aimerais" and mistakes["bb1-aimerais"]["set_id"] == "belleville-b1"
    assert c.execute("SELECT minutes FROM study_day").fetchone()[0] == 7    # 14 answers × 30 s, rounded up

    report = client.get("/api/sets/belleville-b1/report").json()
    assert report["minutes"] == 7 and report["mistakes_in_notebook"] == 2
    assert report["xp"] > 0 and any(comp["id"] == "eo.relance" for comp in report["competencies"])


def test_speaking_choices_are_weak_proxy_evidence(client):
    play(client, "belleville-a2")
    c = conn()
    eo = c.execute("SELECT evidence_weight, flags FROM attempt WHERE item_id = 'ba2-appel-1'").fetchone()
    co = c.execute("SELECT evidence_weight FROM attempt WHERE item_id = 'ba2-compte-rendu'").fetchone()
    assert eo["evidence_weight"] == 0.1 and "proxy" in eo["flags"]          # 0.4 × 0.25
    assert co["evidence_weight"] == 0.4


def test_answer_payload_carries_the_character_reply(client):
    for item_id in ("ba2-scene", "ba2-objectif"):
        assert client.post("/api/sets/belleville-a2/answer", json={"item_id": item_id}).json()["verdict"] == "seen"
    r = client.post("/api/sets/belleville-a2/answer", json={"item_id": "ba2-ecoute-roux", "response": "a"}).json()
    assert r["reply"] is None
    s = content.get_set("belleville-a2")
    for item_id in ("ba2-methode", "ba2-preparation", "ba2-langue", "ba2-ouverture", "ba2-voudrais", "ba2-avant-midi"):
        client.post("/api/sets/belleville-a2/answer", json={"item_id": item_id, "response": right_answer(content.item_by_id(s, item_id))})
    r = client.post("/api/sets/belleville-a2/answer", json={"item_id": "ba2-appel-1", "response": "b"}).json()
    assert r["reply"]["speaker"] == "M. Delaunay"


def test_today_picks_the_version_and_counts_reviews(client):
    t = client.get("/api/today").json()
    assert t["mission"]["set_id"] == "belleville-a2" and t["reviews_due"] == 0   # no profile → beginner version
    client.put("/api/onboarding", json={"step": "concern", "answers": {"self_rating": 4}})
    for step, ans in [("welcome", {"ui_language": "en"}), ("timing", {"exam_window": "6m"}),
                      ("daily_time", {"daily_minutes": 20}), ("explorer", {"start_route": "train"})]:
        client.put("/api/onboarding", json={"step": step, "answers": ans})
    client.post("/api/onboarding/complete")
    t = client.get("/api/today").json()
    assert t["mission"]["set_id"] == "belleville-b1" and t["mission"]["status"] == "not_started"
    assert "task 2" in t["mission"]["reason"]


# ---------- notebook and reviews ----------

def make_due():
    c = conn()
    c.execute("UPDATE mistake SET next_review = ?", (date.today().isoformat(),))


def test_review_session_from_due_mistakes(client):
    assert client.post("/api/reviews/start").status_code == 404                # nothing yet
    play(client, "premiers-pas-a", wrong={"ppa-habiter", "ppa-salle-de-sport"})
    nb = client.get("/api/notebook").json()
    assert len(nb["open"]) == 2 and nb["due_today"] == 0                       # due tomorrow
    make_due()
    assert client.get("/api/today").json()["reviews_due"] == 2

    r = client.post("/api/reviews/start").json()
    assert r == {"set_id": "revisions", "items": 2}
    payload = client.get("/api/sets/revisions").json()
    ids = list(payload["set"]["items"])
    assert all("--" in i for i in ids)
    for item_id in ids:
        _, original = content.resolve_item(None, item_id)
        res = client.post("/api/sets/revisions/answer", json={"item_id": item_id, "response": right_answer(original)}).json()
        assert res["verdict"] == "correct" and res["notebook"] == "progress"
    nb = client.get("/api/notebook").json()
    assert {m["status"] for m in nb["open"]} == {"improving"} and nb["due_today"] == 0
    # Why? works on review copies too
    assert client.get(f"/api/sets/revisions/why/{ids[0]}").status_code == 200


def test_mark_understood(client):
    play(client, "premiers-pas-a", wrong={"ppa-habiter"})
    mid = client.get("/api/notebook").json()["open"][0]["id"]
    nb = client.post(f"/api/notebook/{mid}/understood").json()
    assert nb["open"][0]["status"] == "improving" and nb["open"][0]["interval_days"] == 3
    assert client.post("/api/notebook/999/understood").status_code == 404


def test_disputes_update_the_notebook(client):
    play(client, "premiers-pas-a", wrong={"ppa-habiter", "ppa-boulangerie"})
    c = conn()
    attempts = {r["item_id"]: r["id"] for r in c.execute(
        "SELECT id, item_id FROM attempt WHERE verdict = 'incorrect'")}
    client.post(f"/api/attempts/{attempts['ppa-habiter']}/flags", json={"kind": "dispute"})
    client.post(f"/api/attempts/{attempts['ppa-boulangerie']}/flags", json={"kind": "dispute"})
    reports = {r["item_id"]: r["id"] for r in client.get("/api/review").json()["reports"]}
    client.post(f"/api/review/{reports['ppa-habiter']}/accept", json={})
    client.post(f"/api/review/{reports['ppa-boulangerie']}/reject", json={"note": "The audio says « deux croissants »."})
    nb = {m["item_id"]: m for m in client.get("/api/notebook").json()["open"]}
    assert "ppa-habiter" not in nb                                              # the learner was right
    assert nb["ppa-boulangerie"]["review_note"].startswith("The audio")


def test_requeued_items_come_back_before_the_closing_card(client):
    state = play(client, "belleville-a2", wrong={"ba2-voudrais"})
    order = [r["item_id"] for r in state["results"]]
    assert order[-1] == "ba2-fin"                                           # outro stays last
    assert order.index("ba2-voudrais", order.index("ba2-voudrais") + 1) < order.index("ba2-fin")
