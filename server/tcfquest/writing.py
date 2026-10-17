"""Writing studio (EE T1–T3): original tasks, drafts, timers, deterministic word-range rules.

Rules decide (word count, word range, timing, saving); the AI only gives bounded feedback
(see writing_ai.py), always labelled as an unofficial estimate.

Word count: a word is a group of characters between two spaces ("c'est" = 1, "aujourd'hui" = 1,
"2026" = 1); lone punctuation doesn't count. FEI doesn't publish its exact counting rule, so the
studio shows the range with this rule and warns near the limits.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from . import content

ROOT = Path(__file__).resolve().parents[2]
TASKS_FILE = ROOT / "content" / "writing" / "ee-tasks.json"
EXAM_FILE = ROOT / "content" / "exam" / "tcf-canada.v1.json"
EETask = Literal["EE-T1", "EE-T2", "EE-T3"]
# Suggested split of the 60-minute writing paper for single-task exam practice (not an official rule).
EXAM_SPLIT_S = {"EE-T1": 15 * 60, "EE-T2": 20 * 60, "EE-T3": 25 * 60}
GRACE_S = 30


class Document(BaseModel):
    title: str
    text: str = Field(min_length=40)


class WritingTask(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9-]+$")
    task: EETask
    level: content.Level
    title: str
    prompt: str = Field(min_length=40)
    recipient: str
    documents: list[Document] = Field(default_factory=list)
    competencies: list[str] = Field(min_length=1)
    pool: content.Pool = "training"

    @model_validator(mode="after")
    def documents_match_task(self):
        if (self.task == "EE-T3") != (len(self.documents) == 2):
            raise ValueError("EE-T3 tasks need exactly two documents; other tasks none")
        return self


class Template(BaseModel):
    title: str
    steps: list[str] = Field(min_length=3)
    phrases: list[str] = Field(min_length=3)
    avoid: str


class TaskFile(BaseModel):
    version: int
    review_status: content.ReviewStatus
    templates: dict[EETask, Template]
    tasks: list[WritingTask] = Field(min_length=3)

    @model_validator(mode="after")
    def unique_and_complete(self):
        ids = [t.id for t in self.tasks]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate writing task ids")
        if {t.task for t in self.tasks} != {"EE-T1", "EE-T2", "EE-T3"}:
            raise ValueError("every writing task type needs at least one task")
        return self


@lru_cache(maxsize=None)
def task_file() -> TaskFile:
    return TaskFile.model_validate_json(TASKS_FILE.read_text())


@lru_cache(maxsize=None)
def word_ranges() -> dict[str, dict]:
    exam = json.loads(EXAM_FILE.read_text())
    ee = next(s for s in exam["sections"] if s["id"] == "EE")
    return {t["id"]: t["words"] for t in ee["tasks"]}


def get_task(task_id: str) -> WritingTask | None:
    return next((t for t in task_file().tasks if t.id == task_id), None)


def count_words(text: str) -> int:
    return sum(1 for tok in text.split() if re.search(r"\w", tok))


def range_status(task: str, words: int) -> dict:
    r = word_ranges()[task]
    ok = r["min"] <= words <= r["max"]
    return {"min": r["min"], "max": r["max"], "count": words, "ok": ok,
            "state": "ok" if ok else ("short" if words < r["min"] else "long")}


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _elapsed_s(row) -> float:
    return (_now() - datetime.fromisoformat(row["started_at"])).total_seconds()


def public_task(t: WritingTask) -> dict:
    return {**t.model_dump(), "words": word_ranges()[t.task], "exam_seconds": EXAM_SPLIT_S[t.task]}


def submission(conn: sqlite3.Connection, sid: int) -> dict | None:
    row = conn.execute("SELECT * FROM writing_submission WHERE id = ?", (sid,)).fetchone()
    if row is None:
        return None
    out = dict(row)
    out["feedback"] = json.loads(out["feedback"]) if out["feedback"] else None
    out["feedback_status"] = "pending" if out["feedback_status"] == "running" else out["feedback_status"]
    out["range"] = range_status(row["task"], row["word_count"])
    out["remaining_s"] = (max(0, int(row["time_limit_s"] - _elapsed_s(row)))
                          if row["time_limit_s"] and row["status"] == "draft" else None)
    return out


def start(conn: sqlite3.Connection, task_id: str, mode: str, time_limit_s: int | None = None,
          exam: bool = False) -> dict:
    """exam=True: called by the exam engine (reserved tasks allowed, a fresh submission every time)."""
    t = get_task(task_id)
    if t is None or (t.pool != "training" and not exam):
        raise KeyError(task_id)
    if exam:
        cur = conn.execute("INSERT INTO writing_submission (task_id, task, mode, time_limit_s, started_at, updated_at) "
                           "VALUES (?, ?, 'exam', ?, ?, ?)", (task_id, t.task, time_limit_s,
                                                             _now().isoformat(sep=" ", timespec="seconds"),
                                                             _now().isoformat(sep=" ", timespec="seconds")))
        return submission(conn, cur.lastrowid)
    row = conn.execute("SELECT id FROM writing_submission WHERE task_id = ? AND mode = ? AND status = 'draft' "
                       "ORDER BY id DESC LIMIT 1", (task_id, mode)).fetchone()
    if row:
        return submission(conn, row["id"])
    cur = conn.execute("INSERT INTO writing_submission (task_id, task, mode, time_limit_s, started_at, updated_at) "
                       "VALUES (?, ?, ?, ?, ?, ?)",
                       (task_id, t.task, mode, EXAM_SPLIT_S[t.task] if mode == "exam" else None,
                        _now().isoformat(sep=" ", timespec="seconds"), _now().isoformat(sep=" ", timespec="seconds")))
    conn.commit()
    return submission(conn, cur.lastrowid)


class Locked(Exception):
    pass


def save(conn: sqlite3.Connection, sid: int, text: str) -> dict:
    row = conn.execute("SELECT * FROM writing_submission WHERE id = ?", (sid,)).fetchone()
    if row is None:
        raise KeyError(sid)
    if row["status"] != "draft":
        raise Locked("Already submitted.")
    if row["time_limit_s"] and _elapsed_s(row) > row["time_limit_s"] + GRACE_S:
        raise Locked("Time is up: the text saved at the end of the timer is the one submitted.")
    conn.execute("UPDATE writing_submission SET text = ?, word_count = ?, updated_at = ? WHERE id = ?",
                 (text, count_words(text), _now().isoformat(sep=" ", timespec="seconds"), sid))
    conn.commit()
    return submission(conn, sid)


def submit(conn: sqlite3.Connection, sid: int) -> dict:
    row = conn.execute("SELECT * FROM writing_submission WHERE id = ?", (sid,)).fetchone()
    if row is None:
        raise KeyError(sid)
    if row["status"] != "draft":
        raise Locked("Already submitted.")
    timed_out = 1 if row["time_limit_s"] and _elapsed_s(row) > row["time_limit_s"] else 0
    ok = range_status(row["task"], row["word_count"])["ok"]
    conn.execute("""UPDATE writing_submission SET status = 'submitted', submitted_at = ?, timed_out = ?,
                      word_range_ok = ?, feedback_status = CASE WHEN word_count > 0 THEN 'pending' ELSE 'none' END
                    WHERE id = ?""", (_now().isoformat(sep=" ", timespec="seconds"), timed_out, 1 if ok else 0, sid))
    conn.commit()
    return submission(conn, sid)


def listing(conn: sqlite3.Connection) -> dict:
    last = {r["task_id"]: dict(r) for r in conn.execute(
        "SELECT task_id, MAX(id) AS id, status, feedback_status FROM writing_submission GROUP BY task_id")}
    tasks = [{**public_task(t), "last": last.get(t.id)} for t in task_file().tasks if t.pool == "training"]
    return {"tasks": tasks, "templates": {k: v.model_dump() for k, v in task_file().templates.items()}}


def history(conn: sqlite3.Connection, task_id: str) -> list[dict]:
    return [dict(r) for r in conn.execute(
        "SELECT id, mode, status, word_count, word_range_ok, timed_out, feedback_status, submitted_at "
        "FROM writing_submission WHERE task_id = ? AND status = 'submitted' ORDER BY id DESC", (task_id,))]
