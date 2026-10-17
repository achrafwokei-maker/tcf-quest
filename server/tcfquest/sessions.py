"""Exercise-set sessions: the shared lifecycle, saving and resume (blueprint E.1, I.2).

A session lives in mission_progress under the key "set:<id>". Its state is:
  order   – item ids in play order (wrong items are appended once at the end)
  index   – position of the next unanswered item
  results – verdict per position (so a re-queued item can have two results)
  requeued – item ids already re-queued (each at most once)
Every submit is saved as an `attempt` before the response is returned.
"""

from __future__ import annotations

import json
import math
import sqlite3
from datetime import date

from . import checking, content, db, estimates, feedback, notebook, weakness

SKILL_OF_SECTION = {"CO": "listening", "CE": "reading", "EO": "speaking", "EE": "writing"}

# Evidence weights (blueprint H.1)
BASE_WEIGHT = {"diagnostic": 1.0, "mission": 0.4, "practice": 0.4, "review": 0.4, "onboarding": 0.1}
# Choosing or arranging words is not speaking or writing: those items count as weak "proxy" evidence.
PROXY_FACTOR = 0.25


def _key(set_id: str) -> str:
    return f"set:{set_id}"


def load_state(conn: sqlite3.Connection, s: content.ExerciseSet) -> dict:
    row = conn.execute("SELECT status, state FROM mission_progress WHERE mission_id = ?", (_key(s.id),)).fetchone()
    if row is None:
        return new_state(conn, s)
    state = json.loads(row["state"])
    if state.get("version") != s.version:  # content changed since the session started
        return new_state(conn, s)
    state["status"] = row["status"]
    return state


def new_state(conn: sqlite3.Connection, s: content.ExerciseSet) -> dict:
    state = {"version": s.version, "order": [i.id for i in content.playable(s)], "index": 0, "results": [], "requeued": [],
             "started_at": conn.execute("SELECT datetime('now')").fetchone()[0]}
    _save(conn, s.id, "in_progress", state)
    state["status"] = "in_progress"
    return state


def _save(conn: sqlite3.Connection, set_id: str, status: str, state: dict) -> None:
    clean = {k: v for k, v in state.items() if k != "status"}
    conn.execute(
        """
        INSERT INTO mission_progress (mission_id, status, step, state, updated_at, completed_at)
        VALUES (?, ?, ?, ?, datetime('now'), CASE WHEN ? = 'completed' THEN datetime('now') END)
        ON CONFLICT (mission_id) DO UPDATE SET status = excluded.status, step = excluded.step,
          state = excluded.state, updated_at = excluded.updated_at,
          completed_at = COALESCE(excluded.completed_at, mission_progress.completed_at)
        """,
        (_key(set_id), status, state["index"], json.dumps(clean), status),
    )


def evidence_weight(context: str, hints_used: int, plays: int, audio_off: bool, item_type: str,
                    section: str = "CO") -> float:
    w = BASE_WEIGHT.get(context, 0.4)
    if section in ("EO", "EE"):
        w *= PROXY_FACTOR
    if hints_used:
        w *= 0.5
    if item_type == "listen":
        if audio_off:
            return 0.0  # not listening evidence
        if plays >= 3:
            w *= 0.5
        elif plays == 2:
            w *= 0.8
    return round(w, 3)


def _correct_display(item) -> str:
    if isinstance(item, content.MultiItem):
        return " · ".join(o.text for o in item.options if o.id in item.answers)
    if isinstance(item, content.ChoiceItem):
        return next(o.text for o in item.options if o.id == item.answer)
    if isinstance(item, content.ArrangeItem):
        return " ".join(item.answers[0])
    return item.answers[0]


def _option_explanations(item, chosen: str | None) -> dict:
    if not isinstance(item, content.ChoiceItem):
        return {}
    right = next(o for o in item.options if o.id == item.answer)
    out = {"correct_explanation": right.explanation}
    picked = next((o for o in item.options if o.id == chosen), None)
    if picked and picked.id != item.answer:
        out["chosen_explanation"] = picked.explanation
    return out


class OutOfSync(Exception):
    """The browser answered an item that is not the current one (double submit, stale tab)."""


def submit(conn: sqlite3.Connection, s: content.ExerciseSet, item_id: str, response, *,
           duration_ms: int | None = None, hints_used: int = 0, plays: int = 1,
           audio_off: bool = False, skipped: bool = False) -> dict:
    state = load_state(conn, s)
    if state["index"] >= len(state["order"]) or state["order"][state["index"]] != item_id:
        raise OutOfSync()
    item = content.item_by_id(s, item_id)

    if isinstance(item, content.CardItem):
        return _advance_card(conn, s, state, item_id)

    if skipped:
        result = checking.Result("incorrect", 0)
        verdict = "skipped"
    elif feedback.is_accepted(conn, item, response):
        result = checking.Result("correct", 1, "Accepted answer (added after review).")
        verdict = "correct"
    elif isinstance(item, content.ChoiceItem):
        result = checking.check_choice(str(response), item.answer)
        verdict = result.verdict
    elif isinstance(item, content.ArrangeItem):
        result = checking.check_arrange([str(t) for t in (response or [])], item.answers)
        verdict = result.verdict
    elif isinstance(item, content.MultiItem):
        result = checking.check_multi([str(t) for t in (response or [])], item.answers)
        verdict = result.verdict
    else:
        result = checking.check_typed(str(response or ""), item.answers)
        verdict = result.verdict

    proxy = item.tcf_target.section in ("EO", "EE")
    flags = [f for f, on in (("hint", hints_used > 0), ("audio_off", audio_off), ("proxy", proxy)) if on]
    first_try = item_id not in state["requeued"]
    if not first_try:
        flags.append("requeue")
    weight = 0.0 if skipped else evidence_weight(s.context, hints_used, plays, audio_off, item.type,
                                                  item.tcf_target.section)

    with db.transaction(conn):
        cur = conn.execute(
            """
            INSERT INTO attempt (item_id, content_ver, skill, competency, mode, context, context_id, response,
                                 correct, score, hints_used, duration_ms, verdict, evidence_weight, flags)
            VALUES (?, ?, ?, ?, 'training', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item.id, f"{s.id}@{s.version}", SKILL_OF_SECTION[item.tcf_target.section], item.competencies[0], s.context, s.id,
             json.dumps(response), 1 if verdict == "correct" else 0, result.score, hints_used, duration_ms,
             verdict, weight, json.dumps(flags)),
        )
        # Wrong or partial on first try → comes back once at the end (blueprint E.1).
        requeue = verdict in ("incorrect", "partial") and first_try and not skipped
        if requeue:
            # Come back before any closing cards (e.g. "Mission accomplie"), never after them.
            pos = len(state["order"])
            while pos > state["index"] + 1 and isinstance(content.item_by_id(s, state["order"][pos - 1]), content.CardItem):
                pos -= 1
            state["order"].insert(pos, item_id)
            state["requeued"].append(item_id)
        state["results"].append({"item_id": item_id, "verdict": verdict, "score": result.score})
        notebook_event = weakness_event = None
        if not skipped:
            # Mistakes and mastery live on the original item, even inside a review session.
            src_set, src_item = content.resolve_item(s.id, item_id)
            target = src_item or item
            notebook_event = notebook.record(conn, src_set.id if src_set else s.id, target, verdict, response)
            notebook.update_mastery(conn, target, verdict, weight, hints_used > 0)
            weakness_event = weakness.observe(conn, src_set.id if src_set else s.id, target, verdict,
                                              notebook._display(target, response), notebook._correct(target),
                                              hints_used > 0)
            if weight > 0:
                estimates.update(conn, (SKILL_OF_SECTION[item.tcf_target.section],))
        state["index"] += 1
        status = "completed" if state["index"] >= len(state["order"]) else "in_progress"
        if status == "completed":
            _complete(conn, s, state)
        answered_xp = 0 if skipped else 10 + (5 if verdict == "correct" and first_try else 0)
        if answered_xp:
            conn.execute("INSERT INTO xp_event (amount, reason) VALUES (?, ?)", (answered_xp, f"item:{item.id}"))
        _save(conn, s.id, status, state)
    state["status"] = status

    return {
        "attempt_id": cur.lastrowid,
        "verdict": verdict,
        "score": result.score,
        "note": result.note,
        "details": result.details,
        "correct_answer": _correct_display(item),
        "explanation": getattr(item, "explanation", None),
        **_option_explanations(item, response if isinstance(response, str) else None),
        "transcript": item.audio.text if isinstance(item, content.ChoiceItem) and item.audio else None,
        "will_retry": requeue,
        "notebook": notebook_event,
        "weakness": weakness_event,
        "reply": item.reply.model_dump() if isinstance(item, content.ChoiceItem) and item.reply else None,
        "state": public_state(state, s),
    }


def _advance_card(conn: sqlite3.Connection, s: content.ExerciseSet, state: dict, item_id: str) -> dict:
    """Cards (story, method, language) are read, not answered: no attempt, no evidence, no XP."""
    with db.transaction(conn):
        state["results"].append({"item_id": item_id, "verdict": "seen", "score": 0})
        state["index"] += 1
        status = "completed" if state["index"] >= len(state["order"]) else "in_progress"
        if status == "completed":
            _complete(conn, s, state)
        _save(conn, s.id, status, state)
    state["status"] = status
    return {"verdict": "seen", "state": public_state(state, s)}


def _complete(conn: sqlite3.Connection, s: content.ExerciseSet, state: dict) -> None:
    """Completion XP and study minutes (time actually spent answering, rounded up)."""
    conn.execute("INSERT INTO xp_event (amount, reason) VALUES (?, ?)", (20, f"set:{s.id}"))
    ms = conn.execute(
        "SELECT COALESCE(SUM(duration_ms), 0) FROM attempt WHERE context_id = ? AND created_at >= ?",
        (s.id, state.get("started_at", "1970-01-01"))).fetchone()[0]
    minutes = max(1, math.ceil(ms / 60000)) if ms else 0
    if minutes:
        conn.execute(
            """INSERT INTO study_day (day, minutes) VALUES (?, ?)
               ON CONFLICT (day) DO UPDATE SET minutes = study_day.minutes + excluded.minutes""",
            (date.today().isoformat(), minutes))


def public_state(state: dict, s: content.ExerciseSet) -> dict:
    total = len(state["order"])
    current = state["order"][state["index"]] if state["index"] < total else None
    first_results = {}
    for r in state["results"]:
        if r["verdict"] != "seen":
            first_results.setdefault(r["item_id"], r["verdict"])
    return {
        "status": state.get("status", "in_progress"),
        "index": state["index"],
        "total": total,
        "current_item_id": current,
        "results": state["results"],
        "summary": {
            "items": len(content.scored(content.playable(s))),
            "correct_first_try": sum(1 for v in first_results.values() if v == "correct"),
        },
    }


def why(conn: sqlite3.Connection, s: content.ExerciseSet, item_id: str) -> dict | None:
    """Full explanation for an item, only once the learner has answered it (keys stay hidden before)."""
    item = content.item_by_id(s, item_id)
    answered = conn.execute("SELECT 1 FROM attempt WHERE context_id = ? AND item_id = ?", (s.id, item_id)).fetchone()
    if item is None or answered is None:
        return None
    out = {
        "item_id": item.id,
        "competencies": item.competencies,
        "tcf_target": item.tcf_target.model_dump(),
        "correct_answer": _correct_display(item),
        "explanation": getattr(item, "explanation", None),
    }
    if isinstance(item, content.MultiItem):
        out["options"] = [{"text": o.text, "correct": o.id in item.answers, "explanation": o.explanation} for o in item.options]
    if isinstance(item, content.ChoiceItem):
        out["options"] = [{"text": o.text, "correct": o.id == item.answer, "explanation": o.explanation} for o in item.options]
        if item.audio:
            out["transcript"] = item.audio.text
    if isinstance(item, content.ArrangeItem) and len(item.answers) > 1:
        out["also_accepted"] = [" ".join(a) for a in item.answers[1:]]
    if isinstance(item, content.TypeItem):
        out["also_accepted"] = item.answers[1:]
        out["hint"] = item.hint
    return out
