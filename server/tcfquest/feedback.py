"""Learner feedback on answers and the review queue (blueprint "Feedback system").

Kinds and effects:
  too_easy / too_hard / unclear  → noted for the planner and content review; evidence unchanged
  dispute   ("my answer should be accepted") → evidence removed until reviewed; accept adds the answer
  technical → evidence removed; reviewed as "done" (stays removed)
"""

from __future__ import annotations

import json
import sqlite3

from . import checking, content, db

KINDS = ("too_easy", "too_hard", "unclear", "dispute", "technical")
NOTED_ONLY = {"too_easy", "too_hard", "unclear"}
REWRITE_AFTER_ACCEPTED_DISPUTES = 3
REWRITE_AFTER_UNCLEAR = 2


class FlagError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def response_key(item, response) -> str:
    """The comparable form of an answer, stored when a dispute is accepted."""
    if isinstance(item, content.MultiItem):
        return ",".join(sorted(response or []))
    if isinstance(item, content.ArrangeItem):
        return " ".join(checking.normalize(t) for t in (response or []))
    if isinstance(item, content.TypeItem):
        return checking.normalize(str(response or ""))
    return str(response)


def original_id(item_id: str) -> str:
    composite = content.split_composite(item_id)
    return composite[1] if composite else item_id


def is_accepted(conn: sqlite3.Connection, item, response) -> bool:
    row = conn.execute("SELECT 1 FROM accepted_answer WHERE item_id = ? AND response_key = ?",
                       (original_id(item.id), response_key(item, response))).fetchone()
    return row is not None


def _attempt(conn: sqlite3.Connection, attempt_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM attempt WHERE id = ?", (attempt_id,)).fetchone()
    if row is None:
        raise FlagError(404, "Unknown attempt")
    return row


def _add_flag_marker(conn: sqlite3.Connection, attempt: sqlite3.Row, marker: str, weight: float | None) -> None:
    flags = json.loads(attempt["flags"])
    if marker not in flags:
        flags.append(marker)
    if weight is None:
        conn.execute("UPDATE attempt SET flags = ? WHERE id = ?", (json.dumps(flags), attempt["id"]))
    else:
        conn.execute("UPDATE attempt SET flags = ?, evidence_weight = ? WHERE id = ?",
                     (json.dumps(flags), weight, attempt["id"]))


def add_flag(conn: sqlite3.Connection, attempt_id: int, kind: str, note: str = "") -> dict:
    if kind not in KINDS:
        raise FlagError(422, "Unknown feedback kind")
    attempt = _attempt(conn, attempt_id)
    if kind == "dispute" and attempt["verdict"] not in ("incorrect", "partial"):
        raise FlagError(409, "Only answers marked wrong can be disputed")
    if conn.execute("SELECT 1 FROM feedback_flag WHERE attempt_id = ? AND kind = ?", (attempt_id, kind)).fetchone():
        raise FlagError(409, "Already reported")

    removes_evidence = kind in ("dispute", "technical")
    with db.transaction(conn):
        cur = conn.execute(
            """INSERT INTO feedback_flag (attempt_id, item_id, kind, note, status, original_weight)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (attempt_id, attempt["item_id"], kind, note.strip()[:500],
             "noted" if kind in NOTED_ONLY else "open",
             attempt["evidence_weight"] if removes_evidence else None),
        )
        _add_flag_marker(conn, attempt, {"dispute": "disputed", "technical": "technical"}.get(kind, kind),
                         0.0 if removes_evidence else None)
    return {"id": cur.lastrowid, "kind": kind,
            "status": "noted" if kind in NOTED_ONLY else "open",
            "evidence_removed": removes_evidence}


def _flag(conn: sqlite3.Connection, flag_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM feedback_flag WHERE id = ?", (flag_id,)).fetchone()
    if row is None:
        raise FlagError(404, "Unknown report")
    if row["status"] != "open":
        raise FlagError(409, "Already resolved")
    return row


def _resolve(conn: sqlite3.Connection, flag_id: int, status: str, note: str) -> None:
    conn.execute("UPDATE feedback_flag SET status = ?, resolution_note = ?, resolved_at = datetime('now') WHERE id = ?",
                 (status, note.strip()[:500], flag_id))


def accept_dispute(conn: sqlite3.Connection, flag_id: int, note: str = "") -> dict:
    """The learner was right: their answer becomes an accepted answer and counts as correct."""
    flag = _flag(conn, flag_id)
    if flag["kind"] != "dispute":
        raise FlagError(409, "Only disputes can be accepted")
    attempt = _attempt(conn, flag["attempt_id"])
    item = _item_for(attempt)
    key = response_key(item, json.loads(attempt["response"]))
    with db.transaction(conn):
        conn.execute("INSERT OR IGNORE INTO accepted_answer (item_id, response_key, source_flag_id) VALUES (?, ?, ?)",
                     (item.id, key, flag_id))
        # Every open dispute with the same answer is resolved the same way.
        same = [r for r in conn.execute(
            """SELECT f.id AS fid, f.original_weight, a.id AS aid, a.response FROM feedback_flag f
               JOIN attempt a ON a.id = f.attempt_id
               WHERE (f.item_id = ? OR f.item_id LIKE '%--' || ?) AND f.kind = 'dispute' AND f.status = 'open'""",
            (item.id, item.id))
            if response_key(item, json.loads(r["response"])) == key]
        for r in same:
            conn.execute("UPDATE attempt SET verdict = 'correct', correct = 1, score = 1, evidence_weight = ? WHERE id = ?",
                         (r["original_weight"] or 0.0, r["aid"]))
            _resolve(conn, r["fid"], "accepted", note)
        # The learner was right: that mistake leaves the notebook.
        conn.execute("DELETE FROM mistake WHERE item_id = ?", (item.id,))
    return {"accepted": len(same), "response_key": key}


def reject_dispute(conn: sqlite3.Connection, flag_id: int, note: str) -> dict:
    """The key stands: the evidence comes back as it was, with a reason for the learner."""
    if not note.strip():
        raise FlagError(422, "Give a short reason")
    flag = _flag(conn, flag_id)
    if flag["kind"] != "dispute":
        raise FlagError(409, "Only disputes can be rejected")
    with db.transaction(conn):
        conn.execute("UPDATE attempt SET evidence_weight = ? WHERE id = ?", (flag["original_weight"] or 0.0, flag["attempt_id"]))
        _resolve(conn, flag_id, "rejected", note)
        # The learner sees the reason next to the mistake in their notebook.
        conn.execute("UPDATE mistake SET review_note = ? WHERE item_id = ?", (note.strip()[:500], original_id(flag["item_id"])))
    return {"rejected": 1}


def close_technical(conn: sqlite3.Connection, flag_id: int, note: str = "") -> dict:
    flag = _flag(conn, flag_id)
    if flag["kind"] != "technical":
        raise FlagError(409, "Only technical reports can be closed this way")
    _resolve(conn, flag_id, "accepted", note)  # evidence stays removed
    return {"closed": 1}


def _item_for(attempt: sqlite3.Row):
    _, item = content.resolve_item(attempt["context_id"], attempt["item_id"])
    if item is None:
        raise FlagError(409, "The item no longer exists in the content")
    return item


def review_queue(conn: sqlite3.Connection) -> dict:
    open_rows = conn.execute(
        """SELECT f.*, a.response, a.verdict, a.context_id FROM feedback_flag f
           JOIN attempt a ON a.id = f.attempt_id
           WHERE f.status = 'open' ORDER BY f.created_at""").fetchall()
    reports = []
    for r in open_rows:
        _, item = content.resolve_item(r["context_id"], r["item_id"])
        response = json.loads(r["response"])
        reports.append({
            "id": r["id"], "kind": r["kind"], "note": r["note"], "created_at": r["created_at"],
            "item_id": r["item_id"], "set_id": r["context_id"], "verdict": r["verdict"],
            "prompt": _prompt_of(item), "learner_answer": _display_answer(item, response),
            "expected": _expected_of(item),
        })
    counts = {row["item_id"]: row for row in conn.execute(
        """SELECT item_id,
                  SUM(kind = 'dispute' AND status = 'accepted') AS accepted_disputes,
                  SUM(kind = 'unclear') AS unclear,
                  SUM(kind = 'too_easy') AS too_easy,
                  SUM(kind = 'too_hard') AS too_hard
           FROM feedback_flag GROUP BY item_id""")}
    to_fix = []
    for item_id, c in counts.items():
        reasons = []
        if c["accepted_disputes"] >= REWRITE_AFTER_ACCEPTED_DISPUTES:
            reasons.append(f"{c['accepted_disputes']} answers accepted after dispute: the key or prompt needs rewriting")
        if c["unclear"] >= REWRITE_AFTER_UNCLEAR:
            reasons.append(f"{c['unclear']} learners found the explanation unclear")
        if reasons:
            to_fix.append({"item_id": item_id, "reasons": reasons})
    return {"reports": reports, "items_to_fix": to_fix,
            "difficulty_votes": {k: {"too_easy": v["too_easy"], "too_hard": v["too_hard"]}
                                 for k, v in counts.items() if v["too_easy"] or v["too_hard"]}}


def _prompt_of(item) -> str | None:
    if item is None:
        return None
    if isinstance(item, (content.ChoiceItem, content.MultiItem)):
        return item.question
    if isinstance(item, content.TypeItem):
        return item.sentence
    return item.translation or "Arrange the words"


def _expected_of(item) -> str | None:
    if item is None:
        return None
    if isinstance(item, content.MultiItem):
        return " · ".join(o.text for o in item.options if o.id in item.answers)
    if isinstance(item, content.ChoiceItem):
        return next(o.text for o in item.options if o.id == item.answer)
    if isinstance(item, content.ArrangeItem):
        return " ".join(item.answers[0])
    return " / ".join(item.answers)


def _display_answer(item, response) -> str:
    if isinstance(item, content.MultiItem):
        return " · ".join(o.text for o in item.options if o.id in set(response or []))
    if isinstance(item, content.ChoiceItem):
        return next((o.text for o in item.options if o.id == response), str(response))
    if isinstance(response, list):
        return " ".join(response)
    return "" if response is None else str(response)
