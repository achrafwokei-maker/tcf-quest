"""Planner v1: what to study today, why, and what it should improve. Deterministic rules, no AI.

Inputs: available minutes, due reviews and retests, active weaknesses (severity), skill estimates,
campaign priorities, the exam date (preparation phase) and what has already been played.

1. Retrieval review first, when anything is due (at most 40 % of the session; after a break of
   3+ days the review is capped at 5 so a missed week never becomes a backlog).
2. Then the best-scoring sets that fit the remaining time. A set scores for:
   - unseen items that practise an active weakness (4 × severity each weakness)
   - finishing what was started (+5)
   - the campaign's priority skills (+2 / +1.2 / +0.6)
   - level fit: items about half a band below the estimated ability ≈ 70–80 % success (≤ +3)
   - unseen content share (+1); phase emphasis (+1)
   Sets with no unseen item are never re-proposed (no memorising the same answers); a set
   finished today is skipped.
3. If nothing fits, the top set is offered as a partial session (sessions save and resume).
"""

from __future__ import annotations

import math
import sqlite3
from datetime import date

from . import analysis, content, estimates, notebook, onboarding, weakness

CEFR = estimates.CEFR
SECTION_NAME = {"CO": "listening", "CE": "reading", "EO": "speaking", "EE": "writing"}
TASK_PHRASE = {"EO-T1": "speaking task 1", "EO-T2": "speaking task 2", "EO-T3": "speaking task 3",
               "EE-T1": "writing task 1", "EE-T2": "writing task 2", "EE-T3": "writing task 3"}
WINDOW_WEEKS = {"lt1m": 3, "3m": 12, "6m": 26}
PHASES = [  # (weeks to exam upper bound, weights) – phases overlap, they never block each other
    (3, {"foundations": 10, "technique": 30, "timed": 60}),
    (8, {"foundations": 25, "technique": 40, "timed": 35}),
    (16, {"foundations": 40, "technique": 40, "timed": 20}),
    (10_000, {"foundations": 60, "technique": 30, "timed": 10}),
]
PHASE_LABEL = {"foundations": "Repair French foundations", "technique": "Develop exam technique",
               "timed": "Timed practice and mocks"}


def weeks_to_exam(p, today: date) -> int | None:
    if p is None:
        return None
    if p["exam_date"]:
        return max(0, (date.fromisoformat(p["exam_date"]) - today).days // 7)
    keys = p.keys()
    return WINDOW_WEEKS.get(p["exam_window"]) if "exam_window" in keys else None


def phase_for(weeks: int | None) -> dict:
    weights = next(w for limit, w in PHASES if (weeks if weeks is not None else 10_000) < limit or limit == 10_000)
    focus = max(weights, key=weights.get)
    return {"weeks_to_exam": weeks, "focus": focus, "label": PHASE_LABEL[focus], "weights": weights,
            "note": "Timed practice: weekly trials, section mocks and the full TCF mock are in Examens."}


def _theta(conn: sqlite3.Connection, skill: str) -> float:
    r = conn.execute("SELECT cefr_low, cefr_high FROM skill_profile WHERE skill = ?", (skill,)).fetchone()
    if r and r["cefr_low"] and r["cefr_high"]:
        return (CEFR.index(r["cefr_low"]) + CEFR.index(r["cefr_high"]) + 1) / 2
    return estimates.prior(conn)


def _priorities(conn: sqlite3.Connection) -> list[str]:
    try:
        return [p["skill"] for p in onboarding.campaign(conn)["priorities"]]
    except onboarding.Incomplete:
        return []


def _set_minutes(s: content.ExerciseSet) -> int:
    return s.mission.minutes if s.mission else max(3, math.ceil(len(content.scored(content.playable(s))) * 0.8))


def _status(conn: sqlite3.Connection, set_id: str) -> tuple[str, str | None, int]:
    r = conn.execute("SELECT status, updated_at, step FROM mission_progress WHERE mission_id = ?",
                     (f"set:{set_id}",)).fetchone()
    return (r["status"], r["updated_at"], r["step"]) if r else ("not_started", None, 0)


def candidates(conn: sqlite3.Connection, today: date, phase: dict) -> list[dict]:
    seen = weakness.attempted_items(conn)
    active = [w for w in weakness.listing(conn) if w["state"] != "mastered"]
    prios = _priorities(conn)
    fx = analysis.active_focus(conn, today)                  # what the last assessment asked to train
    out = []
    for s in content.all_sets().values():
        if s.context not in ("practice", "mission", "academy", "toolbox"):
            continue
        items = content.scored(content.playable(s))
        status, updated, step = _status(conn, s.id)
        unseen = [i for i in items if i.id not in seen]
        if status == "completed" and updated and updated[:10] == today.isoformat():
            continue
        if not unseen and status != "in_progress":
            continue                                           # replaying known answers proves nothing
        comps = {c for i in unseen for c in i.competencies}
        targeted = [w for w in active if w["competency"] in comps]
        skill = SECTION_NAME[s.tcf_target.section]
        level = sum(CEFR.index(i.level) for i in (unseen or items)) / len(unseen or items)
        fit = max(0.0, 3 - 1.5 * abs(level - (_theta(conn, skill) - 0.5)))
        prio = {0: 2.0, 1: 1.2, 2: 0.6}.get(prios.index(skill), 0) if skill in prios else 0
        grammar_share = sum(any(c.startswith(("gram.", "vocab.")) for c in i.competencies) for i in unseen) / max(1, len(unseen))
        phase_bonus = (phase["weights"]["foundations"] / 60) * grammar_share + \
                      (phase["weights"]["technique"] / 60) * (1 if s.tcf_target.task else 0)
        focus_bonus = 0.0
        for f in fx:
            hit = [c for c in f["competencies"] if c in comps]
            if f["skill"] == skill or (f["skill"] == "language" and grammar_share > 0):
                focus_bonus += f["weight"]
            focus_bonus += 1.5 * len(hit)
        lesson = 0.0                                     # a different approach: teach, don't just drill
        if s.context in ("academy", "toolbox"):
            sections_here = {i.tcf_target.section for i in items}
            for w in active:
                taught = w["competency"] in comps
                if w["rethink"] and taught:
                    lesson += 3.0
                elif taught:
                    lesson += 1.0
                if w["cause"] == "technique" and s.context == "academy" and \
                        {"listening": "CO", "reading": "CE"}.get(w["skill"]) in sections_here:
                    lesson += 2.0
                if w["cause"] == "french" and s.context == "toolbox" and taught:
                    lesson += 1.5
        factors = {
            "lesson": round(min(lesson, 6.0), 2),
            "focus": round(focus_bonus, 2),
            "weakness": round(sum(4 * w["severity"] for w in targeted), 2),
            "continue": 5.0 if status == "in_progress" and step > 0 else 0.0,     # really started
            "priority": prio, "fit": round(fit, 2),
            "fresh": round(len(unseen) / max(1, len(items)), 2), "phase": round(phase_bonus, 2),
        }
        out.append({"set": s, "status": status, "score": round(sum(factors.values()), 2), "factors": factors,
                    "targeted": targeted, "skill": skill, "minutes": _set_minutes(s), "unseen": len(unseen)})
    return sorted(out, key=lambda c: (-c["score"], c["set"].id))


def _reason(c: dict) -> str:
    s, f = c["set"], c["factors"]
    task = TASK_PHRASE.get(s.tcf_target.task or "", f"{c['skill']} ({s.tcf_target.section})")
    parts = []
    if f.get("lesson", 0) >= 3:
        parts.append("Drills haven't fixed a weak point yet, so this lesson explains it differently first.")
    elif f.get("lesson"):
        parts.append("It's a short lesson on one of your weak points.")
    if f.get("focus"):
        parts.append("Your last assessment showed this needs work, so it's favoured this week.")
    if c["targeted"]:
        names = ", ".join(w["competency"] for w in c["targeted"][:2])
        parts.append(f"It has new questions on your weak points ({names}), so improvement is tested on unseen material.")
    if f["continue"]:
        parts.append("You already started it, and it resumes where you stopped.")
    if f["priority"] >= 2:
        parts.append(f"{c['skill'].capitalize()} is your top priority.")
    if not parts or f["fit"] >= 2.5:
        parts.append("Its level fits your current estimate (about 70–80 % success).")
    return f"Trains {task}. " + " ".join(parts)


def _improves(c: dict) -> list[str]:
    s = c["set"]
    out = [w["competency"] for w in c["targeted"][:3]]
    out.append(f"{c['skill']} estimate" + (f" · {TASK_PHRASE[s.tcf_target.task]}" if s.tcf_target.task in TASK_PHRASE else ""))
    return out


def _step_for_set(c: dict, minutes: int, partial: bool = False) -> dict:
    s = c["set"]
    return {"kind": "mission" if s.context == "mission" else "practice", "set_id": s.id, "title": s.title,
            "level": s.level, "minutes": minutes, "partial": partial, "status": c["status"],
            "tcf_target": s.tcf_target.model_dump(), "reason": _reason(c), "improves": _improves(c),
            "score": c["score"], "factors": c["factors"],
            "objective": s.mission.objective if s.mission else None,
            "objective_en": s.mission.objective_en if s.mission else None}


def plan(conn: sqlite3.Connection, minutes: int | None = None, today: date | None = None) -> dict:
    today = today or date.today()
    p = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    available = max(5, minutes or (p["daily_minutes"] if p else 20))
    last = conn.execute("SELECT MAX(day) FROM study_day WHERE day < ?", (today.isoformat(),)).fetchone()[0]
    gap = (today - date.fromisoformat(last)).days if last else 0
    welcome_back = gap >= 3
    phase = phase_for(weeks_to_exam(p, today))
    steps, used = [], 0

    due = notebook.due_count(conn, today)
    retests = len(weakness.retest_refs(conn))
    cap = 5 if welcome_back else notebook.DAILY_REVIEW_CAP
    n = min(due + retests, cap, max(2, int(available * 0.4 / 0.5)))
    if n:
        r_min = max(2, math.ceil(n * 0.5))
        weak = [w["competency"] for w in weakness.listing(conn) if w["state"] != "mastered"][:3]
        steps.append({"kind": "review", "set_id": "revisions", "title": "Révisions", "minutes": r_min, "count": n,
                      "retests": min(retests, n), "partial": False,
                      "reason": ("Spaced retrieval: recalling your own mistakes at the right moment is what makes them stick."
                                 + (f" Includes {min(retests, n)} new question(s) to confirm a weak point is fixed." if retests else "")),
                      "improves": weak or ["your notebook"]})
        used += r_min

    ranked = candidates(conn, today, phase)
    for c in ranked:
        if used + c["minutes"] <= available:
            steps.append(_step_for_set(c, c["minutes"]))
            used += c["minutes"]
    if not any(s["kind"] != "review" for s in steps) and ranked:
        left = max(5, available - used)
        steps.append(_step_for_set(ranked[0], min(left, ranked[0]["minutes"]), partial=left < ranked[0]["minutes"]))
        used += min(left, ranked[0]["minutes"])

    from . import exam
    ex = exam.listing(conn)
    trial = None
    if ex["next_weekly"]:
        e = next(x for x in ex["exams"] if x["id"] == ex["next_weekly"])
        trial = {"exam_id": e["id"], "title": e["title"], "minutes": round(sum(s["limit_s"] for s in e["sections"]) / 60),
                 "due": ex["weekly_due"], "status": e["status"], "attempt_id": e["attempt_id"],
                 "days_since_last": ex["days_since_last_weekly"],
                 "reason": "Once a week, an unseen four-skill trial under exam rules checks what really transferred "
                           "and resets your plan for the next week."}
    diag = ex.get("diagnostic") or {}
    assessed = diag.get("status") == "completed"
    if trial and not assessed and trial["status"] != "in_progress":
        trial["due"] = False                               # the level check comes first for a new learner
        trial["reason"] = "After your level check: " + trial["reason"][0].lower() + trial["reason"][1:]
    mock = None
    full = next((x for x in ex["exams"] if x["kind"] == "full" and x["status"] != "completed" and not x["blocked_by_seen"]), None)
    if full:
        weeklies = sum(1 for x in ex["exams"] if x["kind"] == "weekly" and x["status"] == "completed")
        weeks = phase["weeks_to_exam"]
        last_full = conn.execute("SELECT MAX(completed_at) FROM exam_attempt WHERE kind = 'full'").fetchone()[0]
        recent = last_full and (today - date.fromisoformat(last_full[:10])).days < 14
        recommended = assessed and not recent and (weeklies >= 2 or (weeks is not None and weeks <= 6))
        mock = {"exam_id": full["id"], "title": full["title"], "minutes": round(sum(s["limit_s"] for s in full["sections"]) / 60),
                "recommended": bool(recommended), "status": full["status"], "attempt_id": full["attempt_id"],
                "reason": ("Your exam is close: a full mock under official timings shows your stamina and timing." if weeks is not None and weeks <= 6
                           else "You've done two weekly trials: a full mock now checks endurance over 2 h 47.")}
    return {"date": today.isoformat(), "minutes_available": available, "minutes_planned": used, "weekly_trial": trial,
            "diagnostic": {"status": diag.get("status", "available"), "attempt_id": diag.get("attempt_id")}, "mock": mock,
            "welcome_back": welcome_back, "days_away": gap if welcome_back else 0, "phase": phase,
            "steps": steps, "content_exhausted": not ranked,
            "rethink": [w["competency"] for w in weakness.listing(conn) if w["rethink"] and w["state"] != "mastered"]}


def best_mission(conn: sqlite3.Connection, today: date | None = None) -> dict | None:
    """The top story mission (for the Home mission card), even if it doesn't fit today's minutes."""
    today = today or date.today()
    p = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    ranked = [c for c in candidates(conn, today, phase_for(weeks_to_exam(p, today))) if c["set"].context == "mission"]
    return _step_for_set(ranked[0], ranked[0]["minutes"]) if ranked else None

