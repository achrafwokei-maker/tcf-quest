"""M1: concept-level weaknesses, unseen retests, item metadata and the reserved assessment pool."""

import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tcfquest import content, weakness

D0 = date(2026, 10, 17)


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


def item(set_id, item_id):
    return content.item_by_id(content.get_set(set_id), item_id)


def row(c, comp):
    return c.execute("SELECT * FROM weakness WHERE competency = ?", (comp,)).fetchone()


def attempt(c, ref):
    """Pretend the learner answered `ref` (so it is no longer 'unseen')."""
    c.execute("INSERT INTO attempt (item_id, content_ver, skill, competency, mode, context, context_id, response, "
              "correct, score, verdict, evidence_weight, flags) VALUES (?, 'x@1', 'speaking', 'c', 'training', "
              "'mission', 'x', '\"a\"', 0, 0, 'incorrect', 0.4, '[]')", (ref,))


COMP = "gram.conditionnel-politesse"
A2 = ("belleville-a2", "ba2-voudrais")      # failed item
B1 = ("belleville-b1", "bb1-aimerais")      # same competency, never seen → the retest


def test_full_loop_detect_train_improve_retest_master(client):
    c, it = conn(), item(*A2)
    attempt(c, A2[1])
    assert weakness.observe(c, A2[0], it, "incorrect", "veux", "voudrais", False, D0) == "detected"
    r = row(c, COMP)
    assert (r["skill"], r["task"], r["category"], r["confidence"]) == ("speaking", "EO-T2", "grammar", "low")
    weakness.mark_practised(c, [COMP], today=D0)
    assert row(c, COMP)["state"] == "training"
    assert weakness.observe(c, A2[0], it, "correct", "voudrais", "voudrais", False, D0 + timedelta(1)) == "improving"
    # A hinted correct answer proves nothing
    assert weakness.observe(c, A2[0], it, "correct", "voudrais", "voudrais", True, D0 + timedelta(2)) is None
    assert weakness.observe(c, A2[0], it, "correct", "voudrais", "voudrais", False, D0 + timedelta(3)) == "retest_due"
    r = row(c, COMP)
    assert r["retest_item"] == "belleville-b1--bb1-aimerais"                  # unseen sibling, not the failed item
    # More practice on the old item can't confirm it; only the unseen one can
    assert weakness.observe(c, A2[0], it, "correct", "voudrais", "voudrais", False, D0 + timedelta(4)) is None
    assert weakness.observe(c, B1[0], item(*B1), "correct", "aimerais", "aimerais", False, D0 + timedelta(4)) == "mastered"
    r = row(c, COMP)
    assert r["mastered_at"] == (D0 + timedelta(4)).isoformat() and '"passed"' in r["interventions"]


def test_mastered_weakness_reopens_and_failed_retests_trigger_rethink(client):
    c, it = conn(), item(*A2)
    attempt(c, A2[1])
    weakness.observe(c, A2[0], it, "incorrect", "veux", "voudrais", False, D0)
    for d in (1, 2):
        weakness.observe(c, A2[0], it, "correct", "", "", False, D0 + timedelta(d))
    assert row(c, COMP)["state"] == "retest_due"
    # Retest failed → back to training, retest cleared
    weakness.observe(c, B1[0], item(*B1), "incorrect", "aime", "aimerais", False, D0 + timedelta(3))
    r = row(c, COMP)
    assert (r["state"], r["retest_item"], r["rethink"], r["frequency"]) == ("training", None, 0, 2)
    assert r["confidence"] == "medium" and r["severity"] > 0.25
    # Once every item practising this concept has been seen, no unseen retest remains
    for _, seen in content.fresh_items(COMP, set()):
        attempt(c, seen.id)
    for d in (4, 5):
        weakness.observe(c, A2[0], it, "correct", "", "", False, D0 + timedelta(d))
    r = row(c, COMP)
    assert r["state"] == "retest_due" and r["retest_item"] is None and r["needs_content"] == 1
    # Wrong again after mastery reopens it
    c.execute("UPDATE weakness SET state = 'mastered' WHERE competency = ?", (COMP,))
    assert weakness.observe(c, A2[0], it, "incorrect", "veux", "voudrais", False, D0 + timedelta(9)) == "training"
    assert row(c, COMP)["reopen_count"] == 1


def test_two_failed_retests_set_rethink(client):
    c = conn()
    c.execute("INSERT INTO weakness (competency, skill, task, category, state, frequency, retests, retest_item, "
              "first_seen, last_seen) VALUES (?, 'speaking', 'EO-T2', 'grammar', 'retest_due', 2, "
              "'[{\"item\": \"x\", \"date\": \"2026-10-01\", \"verdict\": \"incorrect\"}]', ?, '2026-10-01', '2026-10-01')",
              (COMP, "belleville-b1--bb1-aimerais"))
    weakness.observe(c, B1[0], item(*B1), "incorrect", "aime", "aimerais", False, D0)
    assert row(c, COMP)["rethink"] == 1


def test_fresh_items_respect_review_status_pool_and_seen(monkeypatch):
    sets = dict(content.all_sets())
    b1 = sets["belleville-b1"]
    reserved = b1.model_copy(update={"items": [i.model_copy(update={"pool": "assessment"}) if i.id == "bb1-aimerais" else i
                                               for i in b1.items]})
    monkeypatch.setitem(sets, "belleville-b1", reserved)
    monkeypatch.setattr(content, "all_sets", lambda: sets)
    ids = [i.id for _, i in content.fresh_items(COMP, set())]
    first = next(i for _, i in content.fresh_items(COMP, set()))
    assert first.competencies[0] == COMP and "ba2-voudrais" in ids and "bb1-aimerais" not in ids   # primary first; reserved excluded
    assert "ba2-voudrais" not in [i.id for _, i in content.fresh_items(COMP, {"ba2-voudrais"})]   # seen excluded
    assert "bb1-aimerais" not in [i.id for i in content.playable(reserved)]               # never played in training
    for sid in list(sets):
        monkeypatch.setitem(sets, sid, sets[sid].model_copy(update={"review_status": "draft"}))
    assert content.fresh_items(COMP, set()) == []                                         # drafts never retest


def test_difficulty_defaults_from_level():
    assert content.difficulty(item(*A2)) == 2 and content.difficulty(item(*B1)) == 3


def test_answers_feed_weaknesses_and_reviews_include_unseen_retest(client):
    from test_missions_notebook import play
    play(client, "belleville-a2", wrong={"ba2-voudrais"})
    c = conn()
    assert row(c, COMP)["state"] == "detected"
    nb = client.get("/api/notebook").json()
    assert [w["competency"] for w in nb["weaknesses"]] == [COMP] and nb["weaknesses"][0]["examples"]
    # Two later days of correct practice → retest scheduled on the unseen B1 item
    for d in (1, 2):
        weakness.observe(c, *A2[:1], item(*A2), "correct", "", "", False, date.today() + timedelta(d))
    c.execute("UPDATE mistake SET next_review = ?", (date.today().isoformat(),))
    r = client.post("/api/reviews/start").json()
    ids = list(client.get("/api/sets/revisions").json()["set"]["items"])
    assert r["items"] == 2 and "belleville-b1--bb1-aimerais" in ids and "belleville-a2--ba2-voudrais" in ids
    res = client.post("/api/sets/revisions/answer", json={"item_id": ids[0], "response": "zzz"})
    assert res.status_code == 200


def test_backfill_rebuilds_from_past_attempts(client):
    from test_missions_notebook import play
    play(client, "belleville-a2", wrong={"ba2-voudrais", "ba2-preparation"})
    c = conn()
    c.execute("DELETE FROM weakness")
    assert weakness.backfill(c) >= 2
    assert {r["competency"] for r in c.execute("SELECT competency FROM weakness")} >= {COMP, "eo.preparation-t2"}
    assert weakness.backfill(c) == 0                                                     # only once
