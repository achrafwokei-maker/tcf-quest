"""Strict exam engine: weekly trials now; section and full mocks reuse it (M12).

Rules (deterministic, server-enforced):
- sections run in order, each with its own countdown that starts when the learner begins it;
- listening audio plays once; questions go forward only; no hints, no feedback, no answer keys
  until the whole exam is finished;
- when a section's time is up it closes on the next request (unanswered = no answer);
- writing and speaking sections use the writing studio and the AI examiner in exam mode;
- items are reserved (assessment pool) and each exam can be taken once (unseen material).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

from . import content, db, estimates, speaking, weakness, writing

ROOT = Path(__file__).resolve().parents[2]
EXAMS_FILE = ROOT / "content" / "exams" / "exams.json"
GRACE_S = 5
EXAM_WEIGHT = 0.6                  # unseen, timed items: stronger evidence than practice (0.4)
SKILL = {"CO": "listening", "CE": "reading", "EO": "speaking", "EE": "writing"}


class SectionDef(BaseModel):
    section: str
    minutes: float | None = None
    writing_task: str | None = None
    writing_tasks: list[str] | None = None   # full mock: T1–T3 share one countdown, in any order
    eo_task: str | None = None
    adaptive: int | None = None        # serve this many items, chosen one at a time by level (staircase)
    official_timing: bool = False      # take the minutes from the verified exam config


EXAM_CONFIG = ROOT / "content" / "exam" / "tcf-canada.v1.json"


@lru_cache(maxsize=None)
def official_minutes() -> dict[str, float]:
    return {s["id"]: s["minutes"] for s in json.loads(EXAM_CONFIG.read_text())["sections"]}


def _tasks(sec: dict) -> list[str]:
    return sec.get("writing_tasks") or ([sec["writing_task"]] if sec.get("writing_task") else [])


class ExamDef(BaseModel):
    id: str
    kind: str
    title: str
    set: str
    label: str
    sections: list[SectionDef] = Field(min_length=1)


@lru_cache(maxsize=None)
def exams() -> dict[str, ExamDef]:
    data = json.loads(EXAMS_FILE.read_text())
    out = {e["id"]: ExamDef.model_validate(e) for e in data["exams"]}
    for e in out.values():                          # every exam must point at reserved, valid content
        s = content.get_set(e.set)
        assert s is not None and s.context == "exam", e.id
        for sec in e.sections:
            for wt in (sec.writing_tasks or ([sec.writing_task] if sec.writing_task else [])):
                assert writing.get_task(wt) is not None, wt
            if sec.eo_task:
                assert speaking.get_task(sec.eo_task) is not None, sec.eo_task
    return out


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _ts() -> str:
    return _now().isoformat(sep=" ", timespec="seconds")


def _since(ts: str | None) -> float:
    return (_now() - datetime.fromisoformat(ts)).total_seconds() if ts else 0.0


class ExamError(Exception):
    def __init__(self, status: int, msg: str):
        super().__init__(msg)
        self.status = status


def section_items(e: ExamDef, section: str) -> list:
    return [i for i in content.scored(content.get_set(e.set).items) if i.tcf_target.section == section]


def served(e: ExamDef, sec: dict) -> list:
    """The items this section shows: a fixed list, or the adaptive picks made so far."""
    if sec.get("adaptive"):
        pool = {i.id: i for i in section_items(e, sec["section"])}
        return [pool[i] for i in sec.get("order", [])]
    return section_items(e, sec["section"])


def total_items(e: ExamDef, sec: dict) -> int:
    return sec["adaptive"] if sec.get("adaptive") else len(section_items(e, sec["section"]))


def _pick_next(e: ExamDef, sec: dict) -> None:
    """Staircase: choose the unused item closest to the current target level (ties: the easier one)."""
    if len(sec["order"]) >= sec["adaptive"]:
        return
    used = set(sec["order"])
    left = [i for i in section_items(e, sec["section"]) if i.id not in used]
    if not left:
        sec["adaptive"] = len(sec["order"])
        return
    target = sec["level"]
    best = min(left, key=lambda i: (abs(estimates.CEFR.index(i.level) - target), estimates.CEFR.index(i.level), i.id))
    sec["order"].append(best.id)


def _limit_s(e: ExamDef, sec: dict) -> int:
    if sec.get("official_timing") and sec["section"] != "EO":
        return int(official_minutes()[sec["section"]] * 60)
    if sec["section"] == "EO":
        prep, talk = speaking.timings()[speaking.get_task(sec["eo_task"]).task]
        return prep + talk
    return int(sec["minutes"] * 60)


def _load(conn, aid):
    row = conn.execute("SELECT * FROM exam_attempt WHERE id = ?", (aid,)).fetchone()
    if row is None:
        raise ExamError(404, "Unknown exam attempt")
    return row, exams()[row["exam_id"]], json.loads(row["sections"]), json.loads(row["answers"]), json.loads(row["plays"])


def _save(conn, aid, **cols):
    sets = ", ".join(f"{k} = ?" for k in cols)
    conn.execute(f"UPDATE exam_attempt SET {sets} WHERE id = ?",
                 [json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for v in cols.values()] + [aid])


def taken(conn: sqlite3.Connection) -> dict[str, dict]:
    return {r["exam_id"]: dict(r) for r in conn.execute(
        "SELECT exam_id, id, status, started_at, completed_at FROM exam_attempt ORDER BY id")}


def listing(conn: sqlite3.Connection) -> dict:
    done = taken(conn)
    last = conn.execute("SELECT MAX(completed_at) FROM exam_attempt WHERE kind = 'weekly' AND status = 'completed'").fetchone()[0]
    days = int(_since(last) // 86400) if last else None
    out = []
    for e in exams().values():
        t = done.get(e.id)
        blocked = None if t else already_seen(conn, e)
        out.append({"id": e.id, "kind": e.kind, "title": e.title, "label": e.label, "blocked_by_seen": blocked,
                    "sections": [s.model_dump() | {"limit_s": _limit_s(e, s.model_dump())} for s in e.sections],
                    "status": t["status"] if t else "available", "attempt_id": t["id"] if t else None})
    diag = next((x for x in out if x["kind"] == "diagnostic"), None)
    next_weekly = next((x for x in out if x["kind"] == "weekly" and x["status"] != "completed"), None)
    return {"exams": out, "days_since_last_weekly": days,
            "diagnostic": {"status": diag["status"], "attempt_id": diag["attempt_id"]} if diag else None,
            "weekly_due": next_weekly is not None and (days is None or days >= 7),
            "next_weekly": next_weekly["id"] if next_weekly else None}


def already_seen(conn: sqlite3.Connection, e: ExamDef) -> str | None:
    """Section mocks and the full mock share a bank: an exam can't reuse anything already answered."""
    for sec in e.sections:
        d = sec.model_dump()
        if sec.section in ("CO", "CE") and not sec.adaptive:
            ids = [i.id for i in section_items(e, sec.section)]
            if ids and conn.execute(f"SELECT 1 FROM attempt WHERE context = 'exam' AND item_id IN ({','.join('?' * len(ids))}) LIMIT 1",
                                    ids).fetchone():
                return SKILL[sec.section]
        for wt in _tasks(d):
            if conn.execute("SELECT 1 FROM writing_submission WHERE task_id = ? AND mode = 'exam' AND status = 'submitted'", (wt,)).fetchone():
                return "writing"
        if sec.eo_task and conn.execute("SELECT 1 FROM eo_session WHERE task_id = ? AND mode = 'exam' AND status = 'ended'",
                                        (sec.eo_task,)).fetchone():
            return "speaking"
    return None


def start(conn: sqlite3.Connection, exam_id: str) -> dict:
    e = exams().get(exam_id)
    if e is None:
        raise ExamError(404, "Unknown exam")
    t = taken(conn).get(exam_id)
    if t and t["status"] == "in_progress":
        return public(conn, t["id"])
    if t:
        raise ExamError(409, "This exam has already been taken: its questions are no longer unseen.")
    seen = already_seen(conn, e)
    if seen:
        raise ExamError(409, f"Some of these questions were already used in another exam ({seen}): they're no longer unseen.")
    sections = [s.model_dump() | {"started_at": None, "ended_at": None, "timed_out": False, "index": 0,
                                  "writing_submission_id": None, "writing_submission_ids": [], "eo_session_id": None}
                for s in e.sections]
    cur = conn.execute("INSERT INTO exam_attempt (exam_id, kind, sections, started_at) VALUES (?, ?, ?, ?)",
                       (e.id, e.kind, json.dumps(sections), _ts()))
    return public(conn, cur.lastrowid)


def _check_time(conn, aid) -> None:
    """Close the current section if its time is up (and the exam if it was the last)."""
    row, e, sections, answers, plays = _load(conn, aid)
    if row["status"] != "in_progress" or row["section_index"] >= len(sections):
        return
    sec = sections[row["section_index"]]
    if sec["started_at"] and not sec["ended_at"] and _since(sec["started_at"]) > _limit_s(e, sec) + GRACE_S:
        _submit_drafts(conn, sec)
        if sec["section"] == "EO" and sec["eo_session_id"]:
            speaking.end(conn, sec["eo_session_id"], "time")
        _close_section(conn, aid, timed_out=True)


def _submit_drafts(conn, sec: dict) -> None:
    for sid in sec.get("writing_submission_ids") or ([sec["writing_submission_id"]] if sec.get("writing_submission_id") else []):
        sub = writing.submission(conn, sid)
        if sub and sub["status"] == "draft":
            writing.submit(conn, sid)


def _close_section(conn, aid, timed_out: bool = False) -> None:
    row, e, sections, answers, plays = _load(conn, aid)
    sec = sections[row["section_index"]]
    sec["ended_at"], sec["timed_out"] = _ts(), timed_out
    nxt = row["section_index"] + 1
    _save(conn, aid, sections=sections, section_index=nxt)
    if nxt >= len(sections):
        complete(conn, aid)


def begin_section(conn: sqlite3.Connection, aid: int) -> dict:
    _check_time(conn, aid)
    row, e, sections, answers, plays = _load(conn, aid)
    if row["status"] != "in_progress":
        raise ExamError(409, "The exam is finished.")
    sec = sections[row["section_index"]]
    if sec["started_at"] is None:
        sec["started_at"] = _ts()
        if sec["section"] == "EE":
            sec["writing_submission_ids"] = [writing.start(conn, wt, "exam", _limit_s(e, sec), exam=True)["id"] for wt in _tasks(sec)]
            sec["writing_submission_id"] = sec["writing_submission_ids"][0]
        if sec["section"] == "EO":
            sec["eo_session_id"] = speaking.start(conn, sec["eo_task"], "exam", exam=True)["id"]
        if sec.get("adaptive"):
            sec["order"], sec["level"] = [], max(0, min(4, round(estimates.prior(conn))))
            _pick_next(e, sec)
        _save(conn, aid, sections=sections)
    return public(conn, aid)


def _current_item(e, sec):
    items = served(e, sec)
    return items[sec["index"]] if sec["index"] < len(items) else None


def play(conn: sqlite3.Connection, aid: int, item_id: str) -> dict:
    _check_time(conn, aid)
    row, e, sections, answers, plays = _load(conn, aid)
    sec = sections[row["section_index"]] if row["section_index"] < len(sections) else None
    item = _current_item(e, sec) if sec and sec["started_at"] and not sec["ended_at"] else None
    if item is None or item.id != item_id or item.type != "listen":
        raise ExamError(409, "This audio is not the current question.")
    if plays.get(item_id, 0) >= 1:
        raise ExamError(409, "In the exam, each recording is played only once.")
    plays[item_id] = 1
    _save(conn, aid, plays=plays)
    return {"text": item.audio.text, "speaker": item.audio.speaker}


def answer(conn: sqlite3.Connection, aid: int, item_id: str, response: str | None) -> dict:
    _check_time(conn, aid)
    row, e, sections, answers, plays = _load(conn, aid)
    if row["status"] != "in_progress":
        raise ExamError(409, "The exam is finished.")
    sec = sections[row["section_index"]]
    item = _current_item(e, sec) if sec["started_at"] and not sec["ended_at"] else None
    if item is None or item.id != item_id:
        raise ExamError(409, "Time is up for this section, or this is not the current question.")
    if item.type == "listen" and not plays.get(item_id):
        raise ExamError(409, "Listen to the recording first.")
    answers[item_id] = {"response": response, "at": _ts()}
    sec["index"] += 1
    if sec.get("adaptive"):
        sec["level"] = max(0, min(4, sec["level"] + (1 if response == item.answer else -1)))
        _pick_next(e, sec)
    _save(conn, aid, answers=answers, sections=sections)
    if sec["index"] >= total_items(e, sec):
        _close_section(conn, aid)
    return public(conn, aid)


def finish_section(conn: sqlite3.Connection, aid: int) -> dict:
    """Close the current section early (remaining questions unanswered) or after EE/EO is done."""
    _check_time(conn, aid)
    row, e, sections, answers, plays = _load(conn, aid)
    if row["status"] != "in_progress":
        return public(conn, aid)
    sec = sections[row["section_index"]]
    if not sec["started_at"]:
        raise ExamError(409, "This section hasn't started.")
    _submit_drafts(conn, sec)
    if sec["section"] == "EO" and sec["eo_session_id"]:
        speaking.end(conn, sec["eo_session_id"], "learner")
    _close_section(conn, aid)
    return public(conn, aid)


def complete(conn: sqlite3.Connection, aid: int) -> None:
    """Score CO/CE deterministically, store evidence, link EE/EO feedback. Runs once."""
    row, e, sections, answers, plays = _load(conn, aid)
    if row["status"] == "completed":
        return
    results = {"sections": [], "label": e.label}
    for sec in sections:
        entry = {"section": sec["section"], "skill": SKILL[sec["section"]], "timed_out": sec["timed_out"],
                 "time_used_s": int(min(_limit_s(e, sec), (datetime.fromisoformat(sec["ended_at"]) - datetime.fromisoformat(sec["started_at"])).total_seconds()))
                 if sec["started_at"] and sec["ended_at"] else 0, "limit_s": _limit_s(e, sec)}
        if sec["section"] in ("CO", "CE"):
            items = served(e, sec) if sec.get("adaptive") else section_items(e, sec["section"])
            review = []
            for it in items:
                a = answers.get(it.id)
                resp = a["response"] if a else None
                correct = resp == it.answer
                review.append({"item_id": it.id, "level": it.level, "competency": it.competencies[0],
                               "question": it.question, "response": resp, "answer": it.answer, "correct": correct,
                               "answered": a is not None,
                               "options": [{"id": o.id, "text": o.text, "explanation": o.explanation} for o in it.options],
                               "passage": it.passage, "transcript": it.audio.text if it.audio else None})
                if a is not None:
                    conn.execute(
                        """INSERT INTO attempt (item_id, content_ver, skill, competency, mode, context, context_id, response,
                                                correct, score, hints_used, duration_ms, verdict, evidence_weight, flags)
                           VALUES (?, ?, ?, ?, 'exam', 'exam', ?, ?, ?, ?, 0, NULL, ?, ?, '[]')""",
                        (it.id, f"{e.set}@1", SKILL[sec["section"]], it.competencies[0], e.set, json.dumps(resp),
                         1 if correct else 0, 1.0 if correct else 0.0, "correct" if correct else "incorrect", EXAM_WEIGHT))
                    if not correct:
                        right = next(o.text for o in it.options if o.id == it.answer)
                        chosen = next((o.text for o in it.options if o.id == resp), "")
                        weakness.observe(conn, e.set, it, "incorrect", chosen, right, hinted=False)
            entry |= {"correct": sum(r["correct"] for r in review), "total": total_items(e, sec),
                      "adaptive_final_level": estimates.CEFR[sec["level"]] if sec.get("adaptive") else None,
                      "unanswered": sum(not r["answered"] for r in review), "review": review}
        elif sec["section"] == "EE":
            entry |= {"writing_submission_id": sec["writing_submission_id"],
                      "writing_submission_ids": sec.get("writing_submission_ids") or [sec["writing_submission_id"]]}
        else:
            entry |= {"eo_session_id": sec["eo_session_id"]}
        results["sections"].append(entry)
    minutes = max(1, round(_since(row["started_at"]) / 60))
    conn.execute("INSERT INTO study_day (day, minutes) VALUES (date('now'), ?) "
                 "ON CONFLICT (day) DO UPDATE SET minutes = study_day.minutes + excluded.minutes", (minutes,))
    _save(conn, aid, status="completed", completed_at=_ts(), results=results)
    estimates.update(conn, ("listening", "reading"), source="diagnostic" if e.kind == "diagnostic" else e.kind)
    from . import report
    _save(conn, aid, report=report.build(conn, aid))


def public(conn: sqlite3.Connection, aid: int) -> dict:
    """What the browser may see. Answer keys and results only once the exam is completed."""
    row, e, sections, answers, plays = _load(conn, aid)
    out = {"id": aid, "exam_id": e.id, "title": e.title, "label": e.label, "kind": e.kind, "status": row["status"],
           "section_index": row["section_index"], "started_at": row["started_at"],
           "sections": [{"section": s["section"], "limit_s": _limit_s(e, s), "started": bool(s["started_at"]),
                         "ended": bool(s["ended_at"]), "timed_out": s["timed_out"],
                         "items": total_items(e, s) if s["section"] in ("CO", "CE") else None}
                        for s in sections]}
    if row["status"] == "completed":
        out["results"] = json.loads(row["results"])
        from . import report
        out["report"] = report.build(conn, aid)            # fresh: includes EE/EO feedback once it's ready
        return out
    sec = sections[row["section_index"]]
    cur = {"section": sec["section"], "started": bool(sec["started_at"]),
           "remaining_s": max(0, int(_limit_s(e, sec) - _since(sec["started_at"]))) if sec["started_at"] else _limit_s(e, sec)}
    if sec["section"] in ("CO", "CE") and sec["started_at"]:
        item = _current_item(e, sec)
        if item is not None:
            p = content.public_item(item)
            p.pop("audio", None)                                    # audio only through the one-play endpoint
            cur |= {"item": p, "position": sec["index"] + 1, "total": total_items(e, sec),
                    "played": bool(plays.get(item.id))}
    if sec["section"] == "EE":
        tasks = [writing.public_task(writing.get_task(wt)) for wt in _tasks(sec)]
        cur |= {"writing_task": tasks[0], "writing_tasks": tasks,
                "writing_submission_id": sec["writing_submission_id"],
                "writing_submission_ids": sec.get("writing_submission_ids") or []}
    if sec["section"] == "EO":
        cur |= {"eo_task": speaking.public_task(speaking.get_task(sec["eo_task"])), "eo_session_id": sec["eo_session_id"]}
    out["current"] = cur
    return out
