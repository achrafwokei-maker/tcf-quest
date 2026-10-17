"""M2: evidence → CEFR range + confidence (deterministic)."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tcfquest import estimates

B1, B2, A2 = 2.0, 3.0, 1.0


def full(d, c, n):
    return [(d, c, 0.4)] * n


def test_no_evidence_means_no_estimate():
    e = estimates.estimate([], 2.0)
    assert e["cefr_low"] is None and estimates.confidence("listening", e) == "none"


def test_strong_runs_move_up_weak_runs_move_down():
    strong = estimates.estimate(full(B1, 1, 12) + full(B2, 1, 8) + full(B2, 0, 2), prior_mean=1.0)
    weak = estimates.estimate(full(A2, 0, 6) + full(A2, 1, 4) + full(B1, 0, 6), prior_mean=1.0)
    assert strong["theta"] > 3.0 and strong["cefr_low"] in ("B2", "C1")
    assert weak["theta"] < 1.5 and weak["cefr_high"] in ("A1", "A2", "B1")


def test_range_narrows_with_more_evidence():
    few = estimates.estimate(full(B1, 1, 2) + full(B1, 0, 1), 2.0)
    many = estimates.estimate((full(B1, 1, 2) + full(B1, 0, 1)) * 10, 2.0)
    assert many["se"] < few["se"]
    assert estimates.confidence("reading", few) == "low"
    assert estimates.confidence("reading", many) == "high"


def test_a_few_lucky_answers_do_not_give_c2():
    e = estimates.estimate(full(B1, 1, 3), prior_mean=1.0)
    assert e["cefr_low"] in ("A2", "B1") and e["theta"] < 3.5


def test_speaking_and_writing_proxies_stay_low_confidence():
    e = estimates.estimate(full(B1, 1, 28) + full(B1, 0, 12), 2.0)
    assert estimates.confidence("speaking", e) == "low" and estimates.confidence("writing", e) == "low"
    assert estimates.confidence("listening", e) == "high"


def test_hinted_evidence_counts_less():
    plain = estimates.estimate(full(B2, 1, 6), 1.0)
    hinted = estimates.estimate([(B2, 1, 0.2)] * 6, 1.0)
    assert hinted["theta"] < plain["theta"] and hinted["equivalents"] == 3.0


@pytest.fixture()
def client(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setenv("TCFQUEST_DB", str(Path(tmp) / "test.db"))
        from tcfquest.main import app

        with TestClient(app) as c:
            yield c


def test_playing_updates_the_profile_and_history_and_disputes_remove_evidence(client):
    from test_missions_notebook import conn, play
    play(client, "premiers-pas-b", wrong={"ppb-message-julie"})
    c = conn()
    listening = c.execute("SELECT * FROM skill_profile WHERE skill = 'listening'").fetchone()
    assert listening["evidence"] == 1 and listening["cefr_low"] and listening["confidence"] == "low"
    assert listening["cefr_low"] != listening["cefr_high"]                      # always a range when weak
    assert c.execute("SELECT COUNT(*) FROM progress_history WHERE source = 'practice'").fetchone()[0] >= 1
    # Re-queued retry is not counted twice
    assert c.execute("SELECT COUNT(*) FROM attempt WHERE skill = 'listening'").fetchone()[0] == 2
    aid = c.execute("SELECT id FROM attempt WHERE item_id = 'ppb-message-julie' AND verdict = 'incorrect'").fetchone()[0]
    client.post(f"/api/attempts/{aid}/flags", json={"kind": "technical"})
    after = c.execute("SELECT * FROM skill_profile WHERE skill = 'listening'").fetchone()
    assert after["evidence"] == 0 and after["cefr_low"] is None and after["confidence"] == "none"
