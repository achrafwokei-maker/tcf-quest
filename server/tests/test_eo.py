"""M6: speaking tasks with the AI examiner — timings, turns, fallbacks, ASR-safe feedback (AI mocked)."""

import json
import tempfile
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from tcfquest import speaking, speaking_ai


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


class Fake:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []

    def __call__(self, url, json=None, timeout=None):
        self.calls.append(json)
        r = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        if isinstance(r, Exception):
            raise r
        return httpx.Response(200, json={"message": {"content": __import__("json").dumps(r)}}, request=httpx.Request("POST", url))


def test_timings_come_from_the_verified_exam_file():
    assert speaking.timings() == {"EO-T1": (0, 120), "EO-T2": (120, 210), "EO-T3": (0, 270)}
    assert {t.task for t in speaking.task_file().tasks} == {"EO-T1", "EO-T2", "EO-T3"}


def test_t2_hidden_facts_never_reach_the_learner(client):
    t = client.get("/api/eo/tasks/eo2-club-sport").json()["task"]
    assert "facts" not in t and t["prep_s"] == 120 and t["targets"]
    assert "travaux" not in json.dumps(client.get("/api/eo").json())


def test_t2_prep_then_conversation_with_examiner(client, monkeypatch):
    fake = Fake([{"reply": "L'abonnement coûte **45 dollars** par mois. C'est un bon prix. Autre chose ?"}])
    monkeypatch.setattr(speaking.httpx, "post", fake)
    s = client.post("/api/eo/tasks/eo2-club-sport/start", json={"mode": "training"}).json()
    assert s["status"] == "prep" and s["turns"] == [] and 0 < s["remaining_s"] <= 120
    s = client.post(f"/api/eo/sessions/{s['id']}/begin").json()
    assert s["status"] == "active" and s["turns"][0]["text"].startswith("Club Énergie Plus")
    s = client.post(f"/api/eo/sessions/{s['id']}/turn", json={"text": "Combien coûte l'abonnement ?", "source": "typed"}).json()
    assert s["turns"][-1]["text"] == "L'abonnement coûte 45 dollars par mois. C'est un bon prix."   # Markdown stripped, 2 sentences
    system = fake.calls[0]["messages"][0]["content"]
    assert "travaux" in system and "IMPORTANT" in system                                      # facts + surprise given to the examiner


def test_examiner_falls_back_when_the_ai_is_off(client, monkeypatch):
    monkeypatch.setattr(speaking.httpx, "post", Fake([httpx.ConnectError("off")]))
    s = client.post("/api/eo/tasks/eo1-presentation/start", json={"mode": "exam"}).json()
    assert s["status"] == "active" and s["turns"][0]["text"].startswith("Bonjour")
    s = client.post(f"/api/eo/sessions/{s['id']}/turn", json={"text": "Je m'appelle Alex.", "source": "speech",
                                                               "confidence": 0.9, "asr_status": "ok"}).json()
    assert s["turns"][-1]["text"] == speaking.get_task("eo1-presentation").questions[0] and s["ai_fallbacks"] == 1


def test_time_limit_ends_the_task(client, monkeypatch):
    monkeypatch.setattr(speaking.httpx, "post", Fake([{"reply": "D'accord."}]))
    s = client.post("/api/eo/tasks/eo3-teletravail/start", json={"mode": "exam"}).json()
    conn().execute("UPDATE eo_session SET talk_started_at = datetime('now', '-5 minutes') WHERE id = ?", (s["id"],))
    r = client.post(f"/api/eo/sessions/{s['id']}/turn", json={"text": "Je pense que oui.", "source": "typed"})
    assert r.status_code == 409 and "Time is up" in r.json()["detail"]
    assert client.get(f"/api/eo/sessions/{s['id']}").json()["status"] == "ended"


RUBRIC = {"criteria": {c: {"score": 3, "comment": f"About {c}."} for c in speaking_ai.CRITERIA},
          "corrections": [
              {"original": "Est-ce que les cours de yoga est compris dans le prix ?", "corrected": "Est-ce que les cours de yoga sont compris dans le prix ?",
               "explanation": "Plural subject.", "category": "accord", "kind": "error"},
              {"original": "le piscine fermé", "corrected": "la piscine est fermée", "explanation": "From an uncertain turn.", "category": "accord", "kind": "error"}],
          "strengths": ["Polite opening."], "priorities": ["Agreement."], "better_answer": "Est-ce que les cours de yoga sont compris ?",
          "targets_obtained": [0, 4, 99], "cefr_estimate": "B1"}


def test_feedback_ignores_uncertain_turns_and_narrows_corrections(client, monkeypatch):
    c = conn()
    s = speaking.start(c, "eo2-club-sport", "training")
    speaking.begin(c, s["id"])
    monkeypatch.setattr(speaking.httpx, "post", Fake([{"reply": "Oui."}]))
    speaking.turn(c, s["id"], "Est-ce que les cours de yoga est compris dans le prix ?", "speech", 0.9, "ok")
    speaking.turn(c, s["id"], "Bon le piscine fermé alors je peux faire un essai ?", "speech", 0.4, "uncertain")
    speaking.end(c, s["id"])
    fake = Fake([RUBRIC, {"criteria": RUBRIC["criteria"]}])
    monkeypatch.setattr(speaking_ai.httpx, "post", fake)
    assert speaking_ai.run(c, s["id"]) == "done"
    assert "[transcription incertaine]" in fake.calls[0]["messages"][1]["content"]
    fb = speaking.public(c, s["id"])["feedback"]
    assert [(x["original"], x["corrected"]) for x in fb["corrections"]] == [("yoga est compris", "yoga sont compris")]
    assert [t["obtained"] for t in fb["targets"]] == [True, False, False, False, True]
    assert fb["stats"]["uncertain_turns"] == 1 and "pronunciation" in fb["label"]
    assert {r["competency"] for r in c.execute("SELECT competency FROM weakness")} == {"gram.accord"}
    a = c.execute("SELECT * FROM attempt WHERE context_id = 'speaking'").fetchone()
    assert a["evidence_weight"] == 0.2 and a["skill"] == "speaking"


def test_mostly_uncertain_sessions_weigh_half(client, monkeypatch):
    c = conn()
    s = speaking.start(c, "eo3-teletravail", "training")
    monkeypatch.setattr(speaking.httpx, "post", Fake([{"reply": "Pourquoi ?"}]))
    speaking.turn(c, s["id"], "je pense que le télétravail bien", "speech", 0.3, "uncertain")
    speaking.end(c, s["id"])
    monkeypatch.setattr(speaking_ai.httpx, "post", Fake([RUBRIC, {"criteria": RUBRIC["criteria"]}]))
    speaking_ai.run(c, s["id"])
    a = c.execute("SELECT * FROM attempt WHERE context_id = 'speaking'").fetchone()
    assert a["evidence_weight"] == 0.1 and "asr_uncertain" in a["flags"]


def test_no_answer_means_no_feedback(client):
    s = client.post("/api/eo/tasks/eo1-presentation/start", json={"mode": "training"}).json()
    assert client.post(f"/api/eo/sessions/{s['id']}/end").json()["feedback_status"] == "none"
