"""M4: writing studio — word rules, drafts, exam timing, AI feedback safeguards (AI mocked)."""

import json
import tempfile
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from tcfquest import writing, writing_ai

TEXT = ("Bonjour Monsieur Tremblay, je suis votre voisin. Samedi soir je fais une fête pour mon anniversaire. "
        "Elle commence a 19 heures et finit vers minuit. Je suis désolé si il y a du bruit. Les invités est "
        "nombreux mais calmes. Vous êtes invité, venez quand vous voulez ! Il y aura des gâteaux et des boissons "
        "pour tout le monde. Merci pour votre compréhension et à samedi peut-être. Cordialement, Alex")


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


def rubric(task=4, grammar=3, corrections=None):
    crit = {c: {"score": s, "comment": f"Comment on {c}."} for c, s in
            zip(writing_ai.CRITERIA, (task, 4, 4, grammar, 4))}
    return {"criteria": crit, "corrections": corrections if corrections is not None else [
        {"original": "Les invités est", "corrected": "Les invités sont", "explanation": "Plural verb.", "category": "accord", "kind": "error"},
        {"original": "Les invités est", "corrected": "Les invités sont", "explanation": "Duplicate.", "category": "accord", "kind": "error"},
        {"original": "pas dans le texte", "corrected": "x", "explanation": "Invented quote.", "category": "accord", "kind": "error"},
        {"original": "Je suis désolé si", "corrected": "Je suis désolé(e) si", "explanation": "Gender unknown.", "category": "accord", "kind": "error"},
        {"original": "venez quand vous voulez", "corrected": "venez à l'heure qui vous convient", "explanation": "Nicer.", "category": "registre", "kind": "style"},
    ], "strengths": ["Clear purpose."], "priorities": ["Check verb agreement."],
        "revised_version": "Bonjour Monsieur Tremblay, je vous écris pour vous prévenir…", "cefr_estimate": "B1"}


class FakeOllama:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), 0

    def __call__(self, url, json=None, timeout=None):
        self.calls += 1
        reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        if isinstance(reply, Exception):
            raise reply
        content = reply if isinstance(reply, str) else __import__("json").dumps(reply)
        return httpx.Response(200, json={"message": {"content": content}}, request=httpx.Request("POST", url))


# ---------- deterministic rules ----------

def test_tasks_and_word_ranges_come_from_the_verified_exam_file():
    assert writing.word_ranges() == {"EE-T1": {"min": 60, "max": 120}, "EE-T2": {"min": 120, "max": 150},
                                     "EE-T3": {"min": 120, "max": 180}}
    tasks = writing.task_file().tasks
    assert {t.task for t in tasks} == {"EE-T1", "EE-T2", "EE-T3"}
    assert all(len(t.documents) == 2 for t in tasks if t.task == "EE-T3")


def test_word_count_rule():
    assert writing.count_words("Salut Léa, c'est moi ! Aujourd'hui, j'ai 2 chats — et toi ?") == 10
    assert writing.count_words("   ") == 0
    assert writing.range_status("EE-T1", 59)["state"] == "short"
    assert writing.range_status("EE-T1", 60)["ok"] and writing.range_status("EE-T1", 121)["state"] == "long"


def test_draft_autosave_submit_and_lock(client, monkeypatch):
    s = client.post("/api/writing/tasks/ee1-voisin-fete/start", json={"mode": "training"}).json()
    assert s["status"] == "draft" and s["time_limit_s"] is None
    again = client.post("/api/writing/tasks/ee1-voisin-fete/start", json={"mode": "training"}).json()
    assert again["id"] == s["id"]                                               # resumes the draft
    saved = client.put(f"/api/writing/submissions/{s['id']}", json={"text": "Bonjour à tous"}).json()
    assert saved["word_count"] == 3 and saved["range"]["state"] == "short"
    monkeypatch.setattr(writing_ai, "run", lambda c, sid: "failed")            # no AI in this test
    done = client.post(f"/api/writing/submissions/{s['id']}/submit").json()
    assert done["status"] == "submitted" and done["word_range_ok"] == 0
    assert client.put(f"/api/writing/submissions/{s['id']}", json={"text": "x"}).status_code == 409
    assert client.post(f"/api/writing/submissions/{s['id']}/submit").status_code == 409
    assert client.post("/api/writing/tasks/nope/start", json={"mode": "training"}).status_code == 404


def test_exam_mode_timer_locks_late_saves(client):
    s = client.post("/api/writing/tasks/ee3-teletravail/start", json={"mode": "exam"}).json()
    assert s["time_limit_s"] == 25 * 60 and 0 < s["remaining_s"] <= 25 * 60
    conn().execute("UPDATE writing_submission SET started_at = datetime('now', '-26 minutes') WHERE id = ?", (s["id"],))
    r = client.put(f"/api/writing/submissions/{s['id']}", json={"text": "trop tard"})
    assert r.status_code == 409 and "Time is up" in r.json()["detail"]
    sub = writing.submit(conn(), s["id"])
    assert sub["timed_out"] == 1


# ---------- AI safeguards ----------

def test_clean_keeps_quoted_unique_short_corrections_and_adds_rules():
    r = writing_ai.Rubric.model_validate(rubric())
    out = writing_ai.clean(r, TEXT)
    pairs = [(c.original, c.source) for c in out.corrections]
    assert ("si il", "rule") in pairs and ("a 19 heures", "rule") in pairs
    assert pairs.count(("Les invités est", "ai")) == 1                          # duplicate removed
    assert not any(o == "pas dans le texte" for o, _ in pairs)                  # invented quote removed
    assert not any("désolé" in o for o, _ in pairs)                             # gender-only "(e)" dropped


def test_combine_flags_low_agreement():
    a = writing_ai.Rubric.model_validate(rubric(task=5))
    b = writing_ai.Scores.model_validate({"criteria": rubric(task=2)["criteria"]})
    fb = writing_ai.combine(a, b)
    assert fb["agreement"] == "low" and fb["criteria"]["task"] == {**fb["criteria"]["task"], "low": 2, "high": 5}
    assert "Unofficial" in fb["label"]


def test_feedback_feeds_only_errors_into_weaknesses_and_estimate(client, monkeypatch):
    fake = FakeOllama([rubric(), {"criteria": rubric()["criteria"]}])
    monkeypatch.setattr(writing_ai.httpx, "post", fake)
    c = conn()
    s = writing.start(c, "ee1-voisin-fete", "training")
    writing.save(c, s["id"], TEXT)
    writing.submit(c, s["id"])
    assert writing_ai.run(c, s["id"]) == "done" and fake.calls == 2
    sub = writing.submission(c, s["id"])
    assert sub["feedback"]["agreement"] == "high" and sub["prompt_version"] == writing_ai.PROMPT_VERSION
    comps = {r["competency"] for r in c.execute("SELECT competency FROM weakness")}
    assert comps == {"gram.accord", "orth.orthographe", "orth.accents"}         # style suggestion ignored
    a = c.execute("SELECT * FROM attempt WHERE context_id = 'writing'").fetchone()
    assert a["evidence_weight"] == 0.2 and "ai_scored" in a["flags"] and a["skill"] == "writing"
    w = c.execute("SELECT * FROM skill_profile WHERE skill = 'writing'").fetchone()
    assert w["evidence"] == 1 and w["confidence"] == "low"


def test_invalid_output_is_retried_then_fails_cleanly(client, monkeypatch):
    c = conn()
    s = writing.start(c, "ee2-premier-jour", "training")
    writing.save(c, s["id"], TEXT)
    writing.submit(c, s["id"])
    monkeypatch.setattr(writing_ai.httpx, "post", FakeOllama(["not json"]))
    assert writing_ai.run(c, s["id"]) == "failed"
    monkeypatch.setattr(writing_ai.httpx, "post", FakeOllama([httpx.ConnectError("Ollama off")]))
    assert writing_ai.run(c, s["id"]) == "failed"
    assert writing.submission(c, s["id"])["text"] == TEXT                       # nothing lost
    assert c.execute("SELECT COUNT(*) FROM weakness").fetchone()[0] == 0


def test_retry_endpoint_reschedules_failed_feedback(client, monkeypatch):
    c = conn()
    s = writing.start(c, "ee2-premier-jour", "training")
    writing.save(c, s["id"], TEXT)
    writing.submit(c, s["id"])
    c.execute("UPDATE writing_submission SET feedback_status = 'failed' WHERE id = ?", (s["id"],))
    fake = FakeOllama([rubric(), {"criteria": rubric()["criteria"]}])
    monkeypatch.setattr(writing_ai.httpx, "post", fake)
    client.post(f"/api/writing/submissions/{s['id']}/feedback")
    assert writing.submission(c, s["id"])["feedback_status"] == "done"
