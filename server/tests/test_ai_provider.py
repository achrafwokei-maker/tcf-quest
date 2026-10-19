"""Online beta AI: Cloudflare Workers AI requests, daily allowance, and tester isolation (Cloudflare mocked)."""

import json
import tempfile
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from tcfquest import ai, testers, writing_ai

from test_writing import TEXT, rubric


class FakeCloudflare:
    def __init__(self, results, status=200):
        self.results, self.status, self.calls = list(results), status, []

    def __call__(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "json": json, "headers": headers})
        result = self.results.pop(0) if len(self.results) > 1 else self.results[0]
        body = {"result": result} if self.status == 200 else {"errors": [{"message": "daily free allocation of 10,000 neurons used"}]}
        return httpx.Response(self.status, json=body, request=httpx.Request("POST", url))


@pytest.fixture()
def workers(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("TCFQUEST_DB", str(Path(tmp) / "test.db"))
        monkeypatch.setenv("TCFQUEST_AI_PROVIDER", "workers")
        monkeypatch.setenv("TCFQUEST_CF_ACCOUNT", "acct")
        monkeypatch.setenv("TCFQUEST_CF_TOKEN", "tok")
        from tcfquest.main import app

        with TestClient(app) as c:
            yield c


def test_chat_calls_workers_ai_and_counts_neurons(workers, monkeypatch):
    fake = FakeCloudflare([{"response": {"reply": "Bonjour !"}, "usage": {"prompt_tokens": 1000, "completion_tokens": 100}}])
    monkeypatch.setattr(ai.httpx, "post", fake)
    out = ai.chat({"messages": [{"role": "user", "content": "x"}], "format": {"type": "object"},
                   "options": {"temperature": 0.6, "seed": 3, "num_predict": 120}}, 30)
    assert json.loads(out) == {"reply": "Bonjour !"}
    call = fake.calls[0]
    assert call["url"].endswith("/accounts/acct/ai/run/" + ai.CF_MODEL)
    assert call["headers"] == {"Authorization": "Bearer tok"}
    assert call["json"]["max_tokens"] == 120 and call["json"]["seed"] == 3
    assert call["json"]["response_format"]["type"] == "json_schema"
    b = ai.budget()
    assert b["limited"] and b["used"] == pytest.approx(4.119 + 3.487, abs=0.1) and not b["resting"]


def test_daily_cap_stops_calls_and_writing_fails_cleanly(workers, monkeypatch):
    monkeypatch.setenv("TCFQUEST_AI_DAILY_CAP", "5")
    ai.record(6)
    fake = FakeCloudflare([{"response": "{}"}])
    monkeypatch.setattr(ai.httpx, "post", fake)
    with pytest.raises(ai.QuotaExceeded):
        ai.chat({"messages": []}, 30)
    assert fake.calls == []                                      # never even asked Cloudflare
    s = workers.post("/api/writing/tasks/ee1-voisin-fete/start", json={"mode": "training"}).json()
    workers.put(f"/api/writing/submissions/{s['id']}", json={"text": TEXT})
    workers.post(f"/api/writing/submissions/{s['id']}/submit")
    sub = workers.get(f"/api/writing/submissions/{s['id']}").json()
    assert sub["feedback_status"] == "failed" and sub["text"] == TEXT
    assert workers.get("/api/ai/budget").json()["resting"] is True


def test_cloudflare_quota_error_is_reported_as_quota(workers, monkeypatch):
    monkeypatch.setattr(ai.httpx, "post", FakeCloudflare([{}], status=429))
    with pytest.raises(ai.QuotaExceeded):
        ai.chat({"messages": []}, 30)


def test_transcribe_returns_the_worker_shape(workers, monkeypatch):
    fake = FakeCloudflare([{"text": " Bonjour, je m'appelle Sam. ", "segments": [
        {"start": 0, "end": 2.1, "text": "Bonjour, je m'appelle Sam.", "avg_logprob": -0.1}]}])
    monkeypatch.setattr(ai.httpx, "post", fake)
    r = ai.transcribe(b"RIFF....", 2.1)
    assert r["text"] == "Bonjour, je m'appelle Sam." and r["status"] == "ok" and 0.85 < r["confidence"] < 0.95
    assert fake.calls[0]["json"]["language"] == "fr" and fake.calls[0]["url"].endswith(ai.CF_STT_MODEL)
    assert ai.budget()["used"] == pytest.approx(46.63 * 2.1 / 60, abs=0.1)


def test_local_mode_has_no_allowance(monkeypatch):
    monkeypatch.delenv("TCFQUEST_AI_PROVIDER", raising=False)
    assert ai.budget() == {"limited": False}


def test_background_feedback_lands_in_the_right_testers_database(monkeypatch):
    """Writing feedback runs after the response; it must still write to the tester who submitted."""
    with tempfile.TemporaryDirectory() as tmp:
        for k, v in {"TCFQUEST_MODE": "beta", "TCFQUEST_TESTERS_DIR": tmp, "TCFQUEST_SECRET": "s" * 40,
                     "TCFQUEST_DB": str(Path(tmp) / "unused.db"), "TCFQUEST_AI_PROVIDER": "workers",
                     "TCFQUEST_CF_ACCOUNT": "a", "TCFQUEST_CF_TOKEN": "t",
                     "TCFQUEST_INVITES": f"amina:{testers.code_hash('code-amina')},jo:{testers.code_hash('code-jo')}"}.items():
            monkeypatch.setenv(k, v)
        testers._ready.clear()
        monkeypatch.setattr(ai.httpx, "post", FakeCloudflare([
            {"response": json.dumps(rubric()), "usage": {"prompt_tokens": 2500, "completion_tokens": 800}},
            {"response": json.dumps({"criteria": rubric()["criteria"]}), "usage": {"prompt_tokens": 2500, "completion_tokens": 300}}]))
        from tcfquest.main import app

        a, j = (TestClient(app, base_url="https://testserver") for _ in range(2))
        a.post("/api/beta/login", json={"code": "code-amina"})
        j.post("/api/beta/login", json={"code": "code-jo"})
        s = a.post("/api/writing/tasks/ee1-voisin-fete/start", json={"mode": "training"}).json()
        a.put(f"/api/writing/submissions/{s['id']}", json={"text": TEXT})
        a.post(f"/api/writing/submissions/{s['id']}/submit")
        assert a.get(f"/api/writing/submissions/{s['id']}").json()["feedback_status"] == "done"
        assert a.get("/api/ai/budget").json()["used"] > 20
        assert j.get("/api/ai/budget").json()["used"] == 0
        assert j.get(f"/api/writing/submissions/{s['id']}").status_code == 404
