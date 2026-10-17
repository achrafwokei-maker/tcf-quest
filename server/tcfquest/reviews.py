"""Review sessions: a virtual exercise set made of the learner's due mistakes (blueprint H.2, H.6).

Items are copied from their source sets with composite ids '<set>--<item>' so that answers,
"Why?", disputes and the notebook can always find the original item.
"""

from __future__ import annotations

import json
import sqlite3

from . import content, notebook, sessions, weakness

REVIEW_ID = "revisions"
_TARGET = content.TcfTarget(section="CO", purpose="Spaced review of your own mistakes, across all four sections.")


def build_set(refs: list[str]) -> content.ExerciseSet | None:
    items = []
    for ref in dict.fromkeys(refs):  # unique, in order
        src_set, item = content.resolve_item(None, ref)
        if item is None or item.type == "card":
            continue
        items.append(item.model_copy(update={"id": f"{src_set.id}--{item.id}"}))
    if not items:
        return None
    return content.ExerciseSet(id=REVIEW_ID, version=1, title="Révisions", level="mixed", context="review",
                               tcf_target=_TARGET, items=items)


def current(conn: sqlite3.Connection) -> content.ExerciseSet | None:
    row = conn.execute("SELECT state FROM mission_progress WHERE mission_id = ?", (f"set:{REVIEW_ID}",)).fetchone()
    if row is None:
        return None
    return build_set(json.loads(row["state"])["order"])


def start(conn: sqlite3.Connection) -> content.ExerciseSet | None:
    due = notebook.due(conn)
    refs = [f"{m['set_id']}--{m['item_id']}" for m in due if m["set_id"]]
    # Retests: unseen questions on weaknesses ready to be confirmed (never the item that was failed).
    room = max(0, notebook.DAILY_REVIEW_CAP - len(refs))
    refs += weakness.retest_refs(conn, min(room, 5))
    s = build_set(refs)
    if s is not None:
        sessions.new_state(conn, s)
        weakness.mark_practised(conn, [m["category"] for m in due])
    return s


def get_or_start(conn: sqlite3.Connection) -> content.ExerciseSet | None:
    """The review session in progress; else a new one if reviews are due; else the last one (for Why?/report)."""
    row = conn.execute("SELECT status FROM mission_progress WHERE mission_id = ?", (f"set:{REVIEW_ID}",)).fetchone()
    if row is not None and row["status"] == "in_progress":
        s = current(conn)
        if s is not None:
            return s
    return start(conn) or current(conn)
