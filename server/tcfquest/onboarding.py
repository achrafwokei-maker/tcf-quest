"""Conversational onboarding: autosaved answers, completion, and the personal TCF campaign.

Rules come from the experience blueprint (B, H.5) and Part II (R3, R6). Self-rating and the
section of concern only choose starting content and wording; they are never measurements.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Literal

from pydantic import BaseModel, Field

from . import content, db

STEPS = ("language", "welcome", "briefing", "target", "timing", "comfort", "concern",
         "daily_time", "preference", "challenge", "route", "explorer", "campaign")
SKILLS = ("listening", "reading", "speaking", "writing")
SECTION_OF_SKILL = {"listening": "CO", "reading": "CE", "speaking": "EO", "writing": "EE"}
SKILL_OF_SECTION = {v: k for k, v in SECTION_OF_SKILL.items()}
CEFR = ["A1", "A2", "B1", "B2", "C1", "C2"]

PLAN_MODE = {"lt1m": "final_review", "3m": "sprint", "6m": "balanced", "later": "learning_first", "undecided": "learning_first"}
PLAN_LABEL = {
    "final_review": "Final review: exam simulations, templates and warm-ups, no new grammar",
    "sprint": "Sprint: mostly exam-format practice and timed sections",
    "balanced": "Balanced: half learning missions, half exam-format practice",
    "learning_first": "Learning first: mostly story missions, some exam-format practice",
}
# Self-rating → provisional band (blueprint B.2 step 5); never stored as an estimate.
SELF_BAND = {1: ("A1", "A1"), 2: ("A1", "A2"), 3: ("A2", "B1"), 4: ("B1", "B2"), 5: ("B2", "C1")}


class TargetBySkill(BaseModel):
    listening: int = Field(ge=4, le=10)
    reading: int = Field(ge=4, le=10)
    speaking: int = Field(ge=4, le=10)
    writing: int = Field(ge=4, le=10)


class Answers(BaseModel):
    """Everything onboarding can collect. All optional while in progress."""
    ui_language: Literal["en", "fr"] | None = None
    knows_exam: bool | None = None
    briefing_done: bool | None = None
    quiz: dict[str, str] | None = None
    target_choice: Literal["nclc_specific", "nclc7", "nclc9", "c1", "best", "unsure"] | None = None
    target_nclc: int | None = Field(default=None, ge=4, le=10)
    target_by_skill: TargetBySkill | None = None
    exam_window: Literal["lt1m", "3m", "6m", "later", "undecided"] | None = None
    exam_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    self_rating: int | None = Field(default=None, ge=1, le=5)
    concern: Literal["listening", "reading", "speaking", "writing", "unsure"] | None = None
    daily_minutes: Literal[10, 20, 30, 45, 60] | None = None
    preference: Literal["short", "conversation", "explanations", "timed", "balanced"] | None = None
    start_route: Literal["evaluate", "train"] | None = None
    display_name: str | None = Field(default=None, max_length=40)
    avatar_now: bool | None = None


def challenge_set_for(self_rating: int | None) -> str:
    """Band of the first mini-challenge (blueprint B.2 step 5, Part II R4)."""
    return "defi-a" if (self_rating or 1) <= 2 else "defi-b"


def load(conn: sqlite3.Connection) -> dict:
    row = conn.execute("SELECT * FROM onboarding WHERE id = 1").fetchone()
    if row is None:
        return {"step": "language", "answers": {}, "completed": False}
    return {"step": row["step"], "answers": json.loads(row["answers"]), "completed": row["completed_at"] is not None}


def save(conn: sqlite3.Connection, step: str, patch: dict) -> dict:
    if step not in STEPS:
        raise ValueError("unknown step")
    current = load(conn)["answers"]
    merged = {**current, **{k: v for k, v in patch.items()}}
    Answers.model_validate(merged)  # reject anything invalid before saving
    conn.execute(
        """INSERT INTO onboarding (id, step, answers) VALUES (1, ?, ?)
           ON CONFLICT (id) DO UPDATE SET step = excluded.step, answers = excluded.answers, updated_at = datetime('now')""",
        (step, json.dumps(merged)),
    )
    return load(conn)


def start_over_from_profile(conn: sqlite3.Connection) -> dict:
    """Re-run onboarding for an existing learner, prefilled from their profile."""
    p = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    answers: dict = {}
    if p:
        answers = {
            "ui_language": p["ui_language"], "display_name": p["display_name"],
            "daily_minutes": p["daily_minutes"] if p["daily_minutes"] in (10, 20, 30, 45, 60) else 20,
            "target_nclc": p["target_nclc"],
        }
        for key, col in (("exam_window", "exam_window"), ("self_rating", "self_rating"),
                         ("preference", "learning_preference"), ("start_route", "start_route")):
            if p[col] is not None:
                answers[key] = p[col]
    conn.execute(
        """INSERT INTO onboarding (id, step, answers, completed_at) VALUES (1, 'language', ?, NULL)
           ON CONFLICT (id) DO UPDATE SET step = 'language', answers = excluded.answers,
             completed_at = NULL, updated_at = datetime('now')""",
        (json.dumps(answers),),
    )
    return load(conn)


class Incomplete(Exception):
    pass


def complete(conn: sqlite3.Connection) -> dict:
    a = Answers.model_validate(load(conn)["answers"])
    missing = [f for f in ("ui_language", "exam_window", "self_rating", "daily_minutes", "start_route")
               if getattr(a, f) is None]
    if missing:
        raise Incomplete(", ".join(missing))

    choice = a.target_choice or "unsure"
    by_skill = a.target_by_skill.model_dump() if a.target_by_skill else None
    if choice == "nclc_specific":
        target_nclc = min(by_skill.values()) if by_skill else (a.target_nclc or 7)
    else:
        target_nclc = {"nclc7": 7, "nclc9": 9, "c1": 9, "best": 9, "unsure": 7}[choice]
    if choice == "unsure" and a.target_nclc:
        target_nclc = a.target_nclc
    target_cefr = {"best": "C2", "c1": "C1"}.get(choice, "C1")
    name = (a.display_name or "").strip() or "Explorer"
    concern = None if a.concern in (None, "unsure") else a.concern

    with db.transaction(conn):
        conn.execute(
            """
            INSERT INTO profile (id, display_name, goal, target_cefr, target_nclc, exam_date, daily_minutes,
                                 hardest_skills, ui_language, onboarded_at, target_nclc_by_skill, exam_window,
                                 plan_mode, self_rating, concern_section, learning_preference, start_route,
                                 exam_briefing_done)
            VALUES (1, :name, 'tcf_canada', :cefr, :nclc, :exam_date, :minutes, :hardest, :lang, datetime('now'),
                    :by_skill, :window, :mode, :rating, :concern, :pref, :route, :briefing)
            ON CONFLICT (id) DO UPDATE SET
              display_name = excluded.display_name, goal = excluded.goal, target_cefr = excluded.target_cefr,
              target_nclc = excluded.target_nclc, exam_date = excluded.exam_date,
              daily_minutes = excluded.daily_minutes, hardest_skills = excluded.hardest_skills,
              ui_language = excluded.ui_language, onboarded_at = COALESCE(profile.onboarded_at, excluded.onboarded_at),
              target_nclc_by_skill = excluded.target_nclc_by_skill, exam_window = excluded.exam_window,
              plan_mode = excluded.plan_mode, self_rating = excluded.self_rating,
              concern_section = excluded.concern_section, learning_preference = excluded.learning_preference,
              start_route = excluded.start_route,
              exam_briefing_done = MAX(profile.exam_briefing_done, excluded.exam_briefing_done)
            """,
            {"name": name, "cefr": target_cefr, "nclc": target_nclc, "exam_date": a.exam_date,
             "minutes": a.daily_minutes, "hardest": json.dumps([concern] if concern else []),
             "lang": a.ui_language, "by_skill": json.dumps(by_skill) if by_skill else None,
             "window": a.exam_window, "mode": PLAN_MODE[a.exam_window], "rating": a.self_rating,
             "concern": concern, "pref": a.preference or "balanced", "route": a.start_route,
             "briefing": 1 if (a.briefing_done or a.knows_exam) else 0},
        )
        for skill in SKILLS:
            conn.execute("INSERT OR IGNORE INTO skill_profile (skill) VALUES (?)", (skill,))
        conn.execute("UPDATE onboarding SET step = 'campaign', completed_at = datetime('now') WHERE id = 1")
    return campaign(conn)


def _challenge_results(conn: sqlite3.Connection, set_id: str) -> list[dict]:
    """First try per item in the onboarding challenge (re-queued retries ignored)."""
    rows = conn.execute(
        "SELECT item_id, verdict FROM attempt WHERE context_id = ? ORDER BY id", (set_id,)).fetchall()
    first: dict[str, str] = {}
    for r in rows:
        first.setdefault(r["item_id"], r["verdict"])
    s = content.get_set(set_id)
    sections = {i.id: i.tcf_target.section for i in s.items} if s else {}
    return [{"item_id": k, "verdict": v, "section": sections.get(k)} for k, v in first.items()]


def provisional_band(self_rating: int, set_id: str, results: list[dict]) -> tuple[str, str]:
    lo, hi = SELF_BAND.get(self_rating, ("A1", "A2"))
    answered = [r for r in results if r["verdict"] != "skipped"]
    if answered:
        score = sum(r["verdict"] == "correct" for r in answered) / len(answered)
        if set_id == "defi-a" and score >= 0.75 and hi != "C2":
            hi = CEFR[CEFR.index(hi) + 1]
        if set_id == "defi-b" and score <= 0.25 and lo != "A1":
            lo = CEFR[CEFR.index(lo) - 1]
    if lo == hi:  # always a range: one self-rating and a few items are weak evidence
        hi = CEFR[min(CEFR.index(hi) + 1, len(CEFR) - 1)]
    return lo, hi


def priorities(concern: str | None, results: list[dict]) -> list[dict]:
    out: list[dict] = []

    def add(skill: str, reason: str):
        if skill not in [p["skill"] for p in out] and len(out) < 3:
            out.append({"skill": skill, "section": SECTION_OF_SKILL[skill], "reason": reason})

    if concern:
        add(concern, "You told me it worries you most. We'll measure it early and train it often.")
    for r in results:
        if r["verdict"] in ("incorrect", "partial") and r["section"]:
            add(SKILL_OF_SECTION[r["section"]], "You stumbled on it in the first challenge.")
    add("speaking", "Not measured yet, and speaking needs the most regular practice.")
    for skill in ("writing", "listening", "reading"):
        add(skill, "Not measured yet. Your level check will tell us more.")
    return out


def campaign(conn: sqlite3.Connection) -> dict:
    p = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    if p is None:
        raise Incomplete("profile")
    rating = p["self_rating"] or 2
    set_id = challenge_set_for(rating)
    results = _challenge_results(conn, set_id)
    lo, hi = provisional_band(rating, set_id, results)
    assessed = conn.execute("SELECT 1 FROM exam_attempt WHERE kind = 'diagnostic' AND status = 'completed'").fetchone() \
        is not None or any(r["evidence"] >= 30 for r in conn.execute("SELECT evidence FROM skill_profile"))
    mode = p["plan_mode"] or "learning_first"
    minutes = p["daily_minutes"]
    by_skill = json.loads(p["target_nclc_by_skill"]) if p["target_nclc_by_skill"] else None
    return {
        "name": p["display_name"],
        "objective": {"nclc": p["target_nclc"], "nclc_by_skill": by_skill, "cefr_goal": p["target_cefr"]},
        "start": {"provisional": not assessed, "cefr_low": lo, "cefr_high": hi,
                  "basis": "Your self-rating and the first challenge. Not a measurement yet."},
        "gap": "Measured after your level check." if not assessed else None,
        "priorities": priorities(p["concern_section"], results),
        "rhythm": {"daily_minutes": minutes, "weekly_hours": round(minutes * 5 / 60, 1),
                   "plan_mode": mode, "plan_label": PLAN_LABEL[mode], "exam_window": p["exam_window"]},
        "route": p["start_route"],
        "challenge": {"set_id": set_id, "answered": len([r for r in results if r["verdict"] != "skipped"]),
                      "correct": len([r for r in results if r["verdict"] == "correct"])},
        "next_steps": [
            {"title": "Premiers pas practice sets", "status": "available", "link": "/entrainement"},
            {"title": "Le Marché de Belleville (speaking, task 2)", "status": "next milestone"},
            {"title": "Your level check, in four short parts (about 25 minutes)", "link": "/examen",
             "status": "done" if assessed else "available"},
        ],
    }
