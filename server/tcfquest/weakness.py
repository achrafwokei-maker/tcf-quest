"""Concept-level weaknesses: the loop Detect → Train → Improve → Retest → Mastered (and reopen).

Deterministic rules, no AI:
- detected    first wrong/partial answer on a competency (its primary competency).
- training    seen in corrective practice (a review session) or wrong again.
- improving   an unhinted correct answer on a later day than the last error (same-day retries don't count).
- retest_due  unhinted correct answers on 2 different days → an UNSEEN item on the same competency
              is chosen for the retest (transfer, not memory). No unseen item → needs_content.
- mastered    the unseen retest item answered correctly without hints.
- A wrong answer on a mastered weakness reopens it; a failed retest goes back to training, and two
  failed retests set `rethink` (the planner must switch approach, e.g. a lesson instead of drills).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date

from . import content

STATES = ("detected", "training", "improving", "retest_due", "mastered")
CATEGORY = {"gram": "grammar", "orth": "spelling", "vocab": "vocabulary", "co": "comprehension", "ce": "comprehension",
            "eo": "expression", "ee": "expression"}
SKILL_OF_SECTION = {"CO": "listening", "CE": "reading", "EO": "speaking", "EE": "writing"}


def category_of(competency: str) -> str:
    return CATEGORY.get(competency.split(".", 1)[0], "other")


def _j(row, key) -> list:
    return json.loads(row[key]) if row else []


def _severity(frequency: int, distinct_items: int, reopen: int) -> float:
    return round(min(1.0, 0.25 + 0.15 * (frequency - 1) + 0.15 * (distinct_items > 1) + 0.1 * reopen), 2)


def _confidence(frequency: int, distinct_items: int) -> str:
    if frequency >= 3 and distinct_items >= 2:
        return "high"
    return "medium" if frequency >= 2 else "low"


def attempted_items(conn: sqlite3.Connection) -> set[str]:
    """Original ids of every item the learner has ever answered (review copies included)."""
    out = set()
    for (iid,) in conn.execute("SELECT DISTINCT item_id FROM attempt"):
        out.add(iid.split("--", 1)[1] if "--" in iid else iid)
    return out


def _pick_retest(conn: sqlite3.Connection, competency: str, item) -> str | None:
    fresh = content.fresh_items(competency, attempted_items(conn), item.tcf_target.section, content.difficulty(item))
    return f"{fresh[0][0]}--{fresh[0][1].id}" if fresh else None


def observe(conn: sqlite3.Connection, set_id: str, item, verdict: str, answer: str, correction: str,
            hinted: bool, today: date | None = None) -> str | None:
    """Update the weakness for this item's primary competency. Returns the new state if it changed."""
    if verdict not in ("correct", "partial", "incorrect"):
        return None
    today_s = (today or date.today()).isoformat()
    comp = item.competencies[0]
    ref = f"{set_id}--{item.id}"
    row = conn.execute("SELECT * FROM weakness WHERE competency = ?", (comp,)).fetchone()
    is_retest = row is not None and row["retest_item"] == ref

    if verdict in ("incorrect", "partial"):
        examples = (_j(row, "examples") + [{"item": ref, "answer": answer, "correction": correction, "date": today_s}])[-5:]
        failed = sorted(set(_j(row, "items_failed")) | {ref})
        if row is None:
            conn.execute(
                """INSERT INTO weakness (competency, skill, task, category, state, frequency, severity, confidence,
                                         examples, items_failed, first_seen, last_seen)
                   VALUES (?, ?, ?, ?, 'detected', 1, ?, 'low', ?, ?, ?, ?)""",
                (comp, SKILL_OF_SECTION[item.tcf_target.section], item.tcf_target.task or item.tcf_target.section,
                 category_of(comp), _severity(1, 1, 0), json.dumps(examples, ensure_ascii=False),
                 json.dumps(failed), today_s, today_s))
            return "detected"
        freq = row["frequency"] + 1
        reopen = row["reopen_count"] + (1 if row["state"] == "mastered" else 0)
        interventions, retests, rethink = _j(row, "interventions"), _j(row, "retests"), row["rethink"]
        if is_retest:
            retests.append({"item": ref, "date": today_s, "verdict": verdict})
            interventions.append({"kind": "retest", "date": today_s, "item": ref, "outcome": "failed"})
            rethink = 1 if sum(r["verdict"] != "correct" for r in retests) >= 2 else rethink
        new_state = "training" if row["state"] != "detected" or freq > 1 else "detected"
        conn.execute(
            """UPDATE weakness SET state = ?, frequency = ?, correct_days = '[]', severity = ?, confidence = ?,
                 examples = ?, items_failed = ?, interventions = ?, retests = ?, rethink = ?, reopen_count = ?,
                 retest_item = NULL, needs_content = 0, mastered_at = NULL, last_seen = ? WHERE competency = ?""",
            (new_state, freq, _severity(freq, len(failed), reopen), _confidence(freq, len(failed)),
             json.dumps(examples, ensure_ascii=False), json.dumps(failed), json.dumps(interventions),
             json.dumps(retests), rethink, reopen, today_s, comp))
        return new_state if new_state != row["state"] else None

    # correct answer
    if row is None or row["state"] == "mastered" or hinted:
        return None                                     # hinted answers never prove learning
    if is_retest:
        retests = _j(row, "retests") + [{"item": ref, "date": today_s, "verdict": "correct"}]
        interventions = _j(row, "interventions") + [{"kind": "retest", "date": today_s, "item": ref, "outcome": "passed"}]
        conn.execute(
            """UPDATE weakness SET state = 'mastered', retests = ?, interventions = ?, retest_item = NULL,
                 mastered_at = ?, last_seen = ? WHERE competency = ?""",
            (json.dumps(retests), json.dumps(interventions), today_s, today_s, comp))
        return "mastered"
    if row["state"] == "retest_due":
        return None                                     # only the unseen item can confirm now
    examples = _j(row, "examples")
    if examples and today_s <= examples[-1]["date"]:
        return None                                     # same day as the error: the answer was just shown
    days = sorted(set(_j(row, "correct_days")) | {today_s})
    if len(days) >= 2:
        pick = _pick_retest(conn, comp, item)
        interventions = _j(row, "interventions")
        if pick:
            interventions.append({"kind": "retest_scheduled", "date": today_s, "item": pick})
        conn.execute(
            """UPDATE weakness SET state = 'retest_due', correct_days = ?, retest_item = ?, needs_content = ?,
                 interventions = ?, last_seen = ? WHERE competency = ?""",
            (json.dumps(days), pick, 0 if pick else 1, json.dumps(interventions), today_s, comp))
        return "retest_due"
    conn.execute("UPDATE weakness SET state = 'improving', correct_days = ?, last_seen = ? WHERE competency = ?",
                 (json.dumps(days), today_s, comp))
    return "improving" if row["state"] != "improving" else None


def mark_practised(conn: sqlite3.Connection, competencies: list[str], kind: str = "review",
                   today: date | None = None) -> None:
    """Corrective practice was assigned: log the intervention; a fresh detection becomes 'training'."""
    today_s = (today or date.today()).isoformat()
    for comp in dict.fromkeys(competencies):
        row = conn.execute("SELECT * FROM weakness WHERE competency = ?", (comp,)).fetchone()
        if row is None or row["state"] == "mastered":
            continue
        interventions = _j(row, "interventions") + [{"kind": kind, "date": today_s}]
        conn.execute("UPDATE weakness SET interventions = ?, state = CASE WHEN state = 'detected' THEN 'training' "
                     "ELSE state END WHERE competency = ?", (json.dumps(interventions), comp))


def retest_refs(conn: sqlite3.Connection, limit: int = 5) -> list[str]:
    rows = conn.execute("""SELECT retest_item FROM weakness WHERE state = 'retest_due' AND retest_item IS NOT NULL
                           ORDER BY severity DESC, last_seen LIMIT ?""", (limit,)).fetchall()
    return [r["retest_item"] for r in rows]


def listing(conn: sqlite3.Connection) -> list[dict]:
    order = "CASE state WHEN 'retest_due' THEN 0 WHEN 'training' THEN 1 WHEN 'detected' THEN 2 " \
            "WHEN 'improving' THEN 3 ELSE 4 END"
    out = []
    for r in conn.execute(f"SELECT * FROM weakness ORDER BY {order}, severity DESC, last_seen DESC"):
        d = dict(r)
        for k in ("correct_days", "examples", "items_failed", "interventions", "retests"):
            d[k] = json.loads(d[k])
        out.append(d)
    return out


def backfill(conn: sqlite3.Connection) -> int:
    """Rebuild weaknesses from past attempts (run once, when the table is new). Returns rows created."""
    if conn.execute("SELECT COUNT(*) FROM weakness").fetchone()[0]:
        return 0
    rows = conn.execute("SELECT context_id, item_id, verdict, hints_used, response, created_at FROM attempt "
                        "WHERE verdict IN ('correct', 'partial', 'incorrect') ORDER BY id").fetchall()
    for r in rows:
        s, item = content.resolve_item(r["context_id"], r["item_id"])
        if item is None or item.type == "card":
            continue
        observe(conn, s.id, item, r["verdict"], r["response"] or "", "", bool(r["hints_used"]),
                date.fromisoformat(r["created_at"][:10]))
    return conn.execute("SELECT COUNT(*) FROM weakness").fetchone()[0]
