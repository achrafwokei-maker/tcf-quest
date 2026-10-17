"""Vocabulary cards grouped by communicative function (TCF task), with spaced repetition.

Schedule: the card's box counts consecutive successful recalls; the next review comes after
1, 2, 4, 8, 16, 32 days. "again" resets to box 0 (tomorrow), "hard" repeats the same step shorter,
"good" moves up one box, "easy" two. Daily caps keep it light: at most 15 reviews and 8 new cards.
Self-graded, so it is a memory aid, never evidence of ability (skill estimates are untouched).
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from . import content, estimates

ROOT = Path(__file__).resolve().parents[2]
VOCAB_FILE = ROOT / "content" / "vocab" / "vocab.json"
STEPS = [1, 2, 4, 8, 16, 32]
MASTERED_BOX = 5
DAILY_REVIEWS, DAILY_NEW = 15, 8
Grade = Literal["again", "hard", "good", "easy"]
CEFR = estimates.CEFR


class Card(BaseModel):
    id: str = Field(pattern=r"^[a-z]+-\d{2}$")
    function: str
    fr: str = Field(min_length=2)
    en: str = Field(min_length=2)
    example: str = Field(min_length=8)
    level: content.Level
    tcf_target: content.TcfTarget


class FunctionDef(BaseModel):
    id: str
    label: str
    task: str
    blurb: str


class VocabFile(BaseModel):
    version: int
    review_status: content.ReviewStatus
    functions: list[FunctionDef]
    cards: list[Card]

    @model_validator(mode="after")
    def consistent(self):
        ids = [c.id for c in self.cards]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate card ids")
        fids = {f.id for f in self.functions}
        for c in self.cards:
            if c.function not in fids or not c.id.startswith(c.function):
                raise ValueError(f"card {c.id} does not match its function")
            core = re.sub(r"^(un |une |le |la |les |l')", "", c.fr.lower().split(" (")[0].split(" ...")[0])
            plain = "..." in c.fr or "(" in c.fr or "," in c.fr
            if not plain and core not in c.example.lower().replace("’", "'"):
                raise ValueError(f"card {c.id}: the example should use the expression")
        return self


@lru_cache(maxsize=None)
def deck() -> VocabFile:
    return VocabFile.model_validate_json(VOCAB_FILE.read_text())


def _cards() -> dict[str, Card]:
    return {c.id: c for c in deck().cards}


def _row(conn, cid):
    return conn.execute("SELECT * FROM vocab_progress WHERE card_id = ?", (cid,)).fetchone()


def _mid(conn: sqlite3.Connection) -> float:
    rows = conn.execute("SELECT cefr_low, cefr_high FROM skill_profile WHERE cefr_low IS NOT NULL").fetchall()
    if rows:
        return sum((CEFR.index(r["cefr_low"]) + CEFR.index(r["cefr_high"])) / 2 for r in rows) / len(rows)
    return estimates.prior(conn)


def _wanted_tasks(conn: sqlite3.Connection, today: date) -> set[str]:
    """Functions to teach first: those tied to tasks of active weak points or last assessment's focus."""
    from . import analysis
    tasks = {r["task"] for r in conn.execute("SELECT task FROM weakness WHERE state != 'mastered' AND task IS NOT NULL")}
    skills = {f["skill"] for f in analysis.active_focus(conn, today)}
    sec = {"listening": "CO", "reading": "CE", "speaking": "EO", "writing": "EE"}
    return tasks | {sec[s] for s in skills if s in sec}


def overview(conn: sqlite3.Connection, today: date | None = None) -> dict:
    today = today or date.today()
    prog = {r["card_id"]: dict(r) for r in conn.execute("SELECT * FROM vocab_progress")}
    due_ids = {cid for cid, p in prog.items() if p["due"] <= today.isoformat() and p["box"] < MASTERED_BOX}
    introduced_today = sum(1 for p in prog.values() if p["first_seen"] == today.isoformat())
    funcs = []
    for f in deck().functions:
        mine = [c for c in deck().cards if c.function == f.id]
        funcs.append({**f.model_dump(), "total": len(mine), "learned": sum(c.id in prog for c in mine),
                      "mastered": sum(prog.get(c.id, {}).get("box", 0) >= MASTERED_BOX for c in mine),
                      "due": sum(c.id in due_ids for c in mine)})
    new_left = max(0, DAILY_NEW - introduced_today)
    unseen = sum(1 for c in deck().cards if c.id not in prog)
    return {"functions": funcs, "total": len(deck().cards), "learned": len(prog),
            "mastered": sum(p["box"] >= MASTERED_BOX for p in prog.values()),
            "due": len(due_ids), "session_size": min(len(due_ids), DAILY_REVIEWS) + min(new_left, unseen),
            "new_today": min(new_left, unseen)}


def session(conn: sqlite3.Connection, today: date | None = None) -> list[dict]:
    """Due reviews first (oldest first, capped), then a few new cards chosen for you."""
    today = today or date.today()
    cards = _cards()
    prog = {r["card_id"]: dict(r) for r in conn.execute("SELECT * FROM vocab_progress")}
    due = sorted((p for p in prog.values() if p["due"] <= today.isoformat() and p["box"] < MASTERED_BOX),
                 key=lambda p: (p["due"], p["box"]))[:DAILY_REVIEWS]
    introduced_today = sum(1 for p in prog.values() if p["first_seen"] == today.isoformat())
    wanted, mid = _wanted_tasks(conn, today), _mid(conn)
    funcs = {f.id: f for f in deck().functions}

    def priority(c: Card):
        f = funcs[c.function]
        too_hard = CEFR.index(c.level) > mid + 1.5
        return (too_hard, f.task.split("-")[0] not in wanted and f.task not in wanted, c.id)

    new = sorted((c for c in deck().cards if c.id not in prog), key=priority)[:max(0, DAILY_NEW - introduced_today)]
    out = [{**cards[p["card_id"]].model_dump(), "new": False, "box": p["box"]} for p in due]
    out += [{**c.model_dump(), "new": True, "box": 0} for c in new]
    for x in out:
        x["function_label"] = funcs[x["function"]].label
    return out


def grade(conn: sqlite3.Connection, card_id: str, g: Grade, today: date | None = None) -> dict:
    today = today or date.today()
    if card_id not in _cards():
        raise KeyError(card_id)
    row = _row(conn, card_id)
    box = row["box"] if row else 0
    reps = (row["reps"] if row else 0) + 1
    lapses = row["lapses"] if row else 0
    if g == "again":
        box, lapses, days = 0, lapses + 1, 1
    elif g == "hard":
        days = max(1, STEPS[box] // 2)
    else:
        box = min(MASTERED_BOX, box + (2 if g == "easy" else 1))
        days = STEPS[box]
    if row is None and g != "again":
        box, days = 0, 1                              # first meeting: learn now, review tomorrow
    due = (today + timedelta(days=days)).isoformat()
    conn.execute(
        """INSERT INTO vocab_progress (card_id, box, due, reps, lapses, first_seen, last_seen)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT (card_id) DO UPDATE SET box = excluded.box, due = excluded.due, reps = excluded.reps,
             lapses = excluded.lapses, last_seen = excluded.last_seen""",
        (card_id, box, due, reps, lapses, today.isoformat(), today.isoformat()))
    return {"card_id": card_id, "box": box, "due": due, "mastered": box >= MASTERED_BOX}
