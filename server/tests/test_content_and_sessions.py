"""Milestone 1: content format with TCF tags, and exercise sessions (save, requeue, resume)."""

import copy
import json
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from tcfquest import content


# ---------- content format ----------

def test_all_content_files_are_valid_and_tagged():
    sets = content.all_sets()
    assert {"premiers-pas-a", "premiers-pas-b"} <= set(sets)
    for s in sets.values():
        assert s.tcf_target.section in {"CO", "CE", "EO", "EE"}
        for item in s.items:
            assert item.tcf_target.purpose
            if item.type != "card":                      # cards are read, not scored
                assert item.competencies


def _raw_set():
    return json.loads((content.SETS_DIR / "premiers-pas-a.json").read_text())


def test_untagged_item_is_rejected():
    data = _raw_set()
    del data["items"][0]["tcf_target"]
    with pytest.raises(ValidationError):
        content.ExerciseSet.model_validate(data)


def test_task_must_match_section():
    data = _raw_set()
    data["items"][0]["tcf_target"] = {"section": "CO", "task": "EE-T1", "purpose": "mismatched task"}
    with pytest.raises(ValidationError):
        content.ExerciseSet.model_validate(data)


@pytest.mark.parametrize("mutate", [
    lambda d: d["items"][0].__setitem__("answer", "z"),                              # key not an option
    lambda d: d["items"][0]["options"][1].__setitem__("text", "Deux croissants."),    # duplicate option text
    lambda d: d["items"][4].__setitem__("sentence", "No gap here."),                  # type item without ___
    lambda d: d["items"][3]["answers"].append(["Je", "voudrais"]),                     # alternative with other tiles
    lambda d: d["items"][0].__delitem__("audio"),                                      # listen item without audio
])
def test_broken_items_are_rejected(mutate):
    data = copy.deepcopy(_raw_set())
    mutate(data)
    with pytest.raises(ValidationError):
        content.ExerciseSet.model_validate(data)


def test_public_items_never_leak_answer_keys():
    for s in content.all_sets().values():
        for item in s.items:
            pub = json.dumps(content.public_item(item))
            assert '"answer"' not in pub and '"answers"' not in pub and '"explanation"' not in pub


# ---------- sessions ----------

@pytest.fixture()
def client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("TCFQUEST_DB", str(Path(tmp) / "test.db"))
        from tcfquest.main import app

        with TestClient(app) as c:
            yield c


def answer(client, item_id, response, **extra):
    return client.post("/api/sets/premiers-pas-a/answer", json={"item_id": item_id, "response": response, **extra})


def test_full_session_with_requeue_and_resume(client):
    start = client.get("/api/sets/premiers-pas-a").json()
    assert start["state"]["current_item_id"] == "ppa-boulangerie"
    assert start["state"]["total"] == 5

    r = answer(client, "ppa-boulangerie", "a", plays=1).json()
    assert r["verdict"] == "correct" and r["will_retry"] is False
    assert r["transcript"].startswith("Bonjour")

    r = answer(client, "ppa-salle-de-sport", "a").json()                  # wrong
    assert r["verdict"] == "incorrect" and r["will_retry"] is True
    assert r["correct_answer"] == "Non, elle est fermée."
    assert "Tuesday" in r["chosen_explanation"]
    assert r["state"]["total"] == 6                                       # re-queued once at the end

    # Refresh: the server resumes at the next unanswered item.
    resumed = client.get("/api/sets/premiers-pas-a").json()["state"]
    assert resumed["current_item_id"] == "ppa-ouverture-ami"

    # A stale tab re-submitting an answered item gets a 409 with the current state.
    stale = answer(client, "ppa-salle-de-sport", "b")
    assert stale.status_code == 409
    assert stale.json()["detail"]["state"]["current_item_id"] == "ppa-ouverture-ami"

    answer(client, "ppa-ouverture-ami", "a")
    r = answer(client, "ppa-cafe-poli", ["Je", "voudrais", "café,", "un", "s'il", "vous", "plaît."]).json()
    assert r["verdict"] == "partial" and r["will_retry"] is True          # two tiles swapped
    r = answer(client, "ppa-habiter", "habitez").json()
    assert r["verdict"] == "partial"
    # Re-queued items come back once, in order.
    r = answer(client, "ppa-salle-de-sport", "b").json()
    assert r["verdict"] == "correct" and r["will_retry"] is False
    answer(client, "ppa-cafe-poli", ["Je", "voudrais", "un", "café,", "s'il", "vous", "plaît."])
    r = answer(client, "ppa-habiter", "habitez").json()                  # wrong again: not re-queued twice
    assert r["will_retry"] is False
    assert r["state"]["status"] == "completed"
    assert r["state"]["summary"] == {"items": 5, "correct_first_try": 2}


def test_attempts_are_saved_with_evidence_weights(client):
    answer(client, "ppa-boulangerie", "a", plays=2)
    answer(client, "ppa-salle-de-sport", "b", hints_used=1)
    answer(client, "ppa-ouverture-ami", None, skipped=True)

    from tcfquest import db
    rows = db.connect().execute(
        "SELECT item_id, skill, verdict, evidence_weight, flags FROM attempt ORDER BY id").fetchall()
    assert [(r["item_id"], r["skill"], r["verdict"]) for r in rows] == [
        ("ppa-boulangerie", "listening", "correct"),
        ("ppa-salle-de-sport", "reading", "correct"),
        ("ppa-ouverture-ami", "writing", "skipped"),
    ]
    assert [r["evidence_weight"] for r in rows] == [0.32, 0.2, 0.0]     # 0.4×0.8 (2 plays), 0.4×0.5 (hint), skip
    assert json.loads(rows[1]["flags"]) == ["hint"]


def test_listening_with_audio_off_is_not_listening_evidence(client):
    answer(client, "ppa-boulangerie", "a", audio_off=True)
    from tcfquest import db
    row = db.connect().execute("SELECT evidence_weight, flags FROM attempt").fetchone()
    assert row["evidence_weight"] == 0.0 and "audio_off" in row["flags"]


def test_restart_and_unknown_set(client):
    answer(client, "ppa-boulangerie", "a")
    assert client.post("/api/sets/premiers-pas-a/restart").json()["state"]["index"] == 0
    assert client.get("/api/sets/nope").status_code == 404
    assert client.post("/api/sets/premiers-pas-a/hint", params={"item_id": "ppa-habiter"}).json()["hint"].startswith("With")
