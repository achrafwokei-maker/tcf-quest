"""Mistake notebook, spaced reviews and competency mastery (blueprint LEARNING_SYSTEM, H.2).

Mistakes: one row per item. A wrong or partial answer opens (or re-opens) it; correct answers
later push the next review further away: 1 → 3 → 7 → 14 → 30 days. After three successful
reviews in a row (interval reaches 14 days) the mistake counts as mastered.

Mastery: a simple Bayesian-knowledge-tracing-style probability per competency, moved by each
answer in proportion to its evidence weight. A competency is mastered at p ≥ 0.85 with at least
5 attempts on at least 2 different days and one unhinted correct answer.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta

from . import content

INTERVALS = [1, 3, 7, 14, 30]
MASTERED_AFTER = 14
DAILY_REVIEW_CAP = 10


def _display(item, response) -> str:
    if isinstance(item, (content.ChoiceItem,)):
        return next((o.text for o in item.options if o.id == response), str(response))
    if isinstance(item, content.MultiItem):
        chosen = set(response or [])
        return " · ".join(o.text for o in item.options if o.id in chosen) or "—"
    if isinstance(response, list):
        return " ".join(response)
    return "" if response is None else str(response)


def _correct(item) -> str:
    if isinstance(item, content.ChoiceItem):
        return next(o.text for o in item.options if o.id == item.answer)
    if isinstance(item, content.MultiItem):
        return " · ".join(o.text for o in item.options if o.id in item.answers)
    if isinstance(item, content.ArrangeItem):
        return " ".join(item.answers[0])
    return item.answers[0]


def _prompt(item) -> str:
    if isinstance(item, (content.ChoiceItem, content.MultiItem)):
        return item.question
    if isinstance(item, content.TypeItem):
        return item.sentence + (f" ({item.base_form})" if item.base_form else "")
    return item.translation or "Remettez les mots dans l'ordre."


def _explanation(item, response) -> str:
    if isinstance(item, content.ChoiceItem):
        chosen = next((o for o in item.options if o.id == response), None)
        right = next(o for o in item.options if o.id == item.answer)
        return f"{chosen.explanation} {right.explanation}" if chosen and chosen.id != item.answer else right.explanation
    if isinstance(item, content.MultiItem):
        return " ".join(o.explanation for o in item.options if o.id in item.answers)
    return item.explanation


def record(conn: sqlite3.Connection, set_id: str, item, verdict: str, response, today: date | None = None) -> str | None:
    """Update the notebook after an answer. Returns 'opened' | 'reopened' | 'progress' | 'mastered' | None."""
    today = today or date.today()
    row = conn.execute("SELECT * FROM mistake WHERE item_id = ?", (item.id,)).fetchone()
    if verdict in ("incorrect", "partial"):
        tomorrow = (today + timedelta(days=1)).isoformat()
        if row is None:
            conn.execute(
                """INSERT INTO mistake (skill, category, item_id, set_id, context, learner_answer, correction,
                                        explanation, recurrence, status, interval_days, next_review)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 'open', 1, ?)""",
                (content_skill(item), item.competencies[0], item.id, set_id, _prompt(item), _display(item, response),
                 _correct(item), _explanation(item, response), tomorrow))
            return "opened"
        conn.execute(
            """UPDATE mistake SET recurrence = recurrence + 1, status = 'open', interval_days = 1, next_review = ?,
                 learner_answer = ?, last_seen = datetime('now') WHERE id = ?""",
            (tomorrow, _display(item, response), row["id"]))
        return "reopened"
    if verdict == "correct" and row is not None and row["status"] != "mastered":
        # Only answers on or after the review date move the schedule (no cramming the same day).
        if row["next_review"] > today.isoformat():
            return None
        step = INTERVALS.index(row["interval_days"]) + 1 if row["interval_days"] in INTERVALS else 1
        interval = INTERVALS[min(step, len(INTERVALS) - 1)]
        status = "mastered" if interval >= MASTERED_AFTER else "improving"
        conn.execute(
            """UPDATE mistake SET interval_days = ?, status = ?, next_review = ?, last_seen = datetime('now')
               WHERE id = ?""",
            (interval, status, (today + timedelta(days=interval)).isoformat(), row["id"]))
        return "mastered" if status == "mastered" else "progress"
    return None


SKILL_OF_SECTION = {"CO": "listening", "CE": "reading", "EO": "speaking", "EE": "writing"}


def content_skill(item) -> str:
    return SKILL_OF_SECTION[item.tcf_target.section]


def update_mastery(conn: sqlite3.Connection, item, verdict: str, weight: float, hinted: bool, today: date | None = None) -> None:
    """Move p_known for each competency of the item, scaled by the evidence weight."""
    if weight <= 0 or verdict not in ("correct", "partial", "incorrect"):
        return
    today_s = (today or date.today()).isoformat()
    strength = min(1.0, weight / 0.4)           # a full practice item = 1
    unhinted = 1 if verdict == "correct" and not hinted else 0
    for comp in item.competencies:
        row = conn.execute("SELECT * FROM mastery WHERE competency = ?", (comp,)).fetchone()
        p = row["p_known"] if row else 0.2
        if verdict == "correct":
            p = p + (1 - p) * 0.3 * strength
        elif verdict == "partial":
            p = p + (1 - p) * 0.1 * strength
        else:
            p = p - p * 0.35 * strength
        days = set(json.loads(row["days_seen"])) if row else set()
        days.add(today_s)
        conn.execute(
            """INSERT INTO mastery (competency, p_known, attempts, days_seen, last_seen, unhinted_correct)
               VALUES (?, ?, 1, ?, ?, ?)
               ON CONFLICT (competency) DO UPDATE SET p_known = excluded.p_known, attempts = mastery.attempts + 1,
                 days_seen = excluded.days_seen, last_seen = excluded.last_seen,
                 unhinted_correct = MAX(mastery.unhinted_correct, excluded.unhinted_correct)""",
            (comp, round(p, 4), json.dumps(sorted(days)), today_s, unhinted))


def is_mastered(row) -> bool:
    return (row["p_known"] >= 0.85 and row["attempts"] >= 5
            and len(json.loads(row["days_seen"])) >= 2 and bool(row["unhinted_correct"]))


def due(conn: sqlite3.Connection, today: date | None = None, limit: int = DAILY_REVIEW_CAP) -> list[sqlite3.Row]:
    today = (today or date.today()).isoformat()
    return conn.execute(
        """SELECT * FROM mistake WHERE status != 'mastered' AND next_review <= ?
           ORDER BY next_review, last_seen LIMIT ?""", (today, limit)).fetchall()


def due_count(conn: sqlite3.Connection, today: date | None = None) -> int:
    today = (today or date.today()).isoformat()
    return conn.execute("SELECT COUNT(*) FROM mistake WHERE status != 'mastered' AND next_review <= ?",
                        (today,)).fetchone()[0]


def mark_understood(conn: sqlite3.Connection, mistake_id: int, today: date | None = None) -> bool:
    today = today or date.today()
    cur = conn.execute(
        """UPDATE mistake SET status = 'improving', interval_days = 3, next_review = ? WHERE id = ? AND status != 'mastered'""",
        ((today + timedelta(days=3)).isoformat(), mistake_id))
    return cur.rowcount == 1


def listing(conn: sqlite3.Connection, today: date | None = None) -> dict:
    today_s = (today or date.today()).isoformat()
    rows = [dict(r) for r in conn.execute("SELECT * FROM mistake ORDER BY status = 'mastered', next_review, recurrence DESC")]
    for r in rows:
        r["due"] = r["status"] != "mastered" and r["next_review"] <= today_s
    return {
        "due_today": min(due_count(conn, today), DAILY_REVIEW_CAP),
        "open": [r for r in rows if r["status"] != "mastered"],
        "mastered": [r for r in rows if r["status"] == "mastered"],
    }
