"""Post-exam intelligence (M9): timing, possible root causes, retests, and next week's focus.

Deterministic rules; a cause is only named when the evidence supports it, otherwise "unknown".
- timing:    the section ran out of time with ≥ 2 unanswered questions, or the last answers were
             wrong after a slow start (answers given in the final 10 % of the time).
- technique: wrong answers on intention / implicit-meaning / main-idea / viewpoint questions while
             factual questions at the same or a higher level were right (the French was there; the
             reading strategy wasn't).
- french:    wrong answers on questions at or below the learner's estimated level, or language
             errors (grammar, spelling, vocabulary) in writing/speaking.
The focus lists the skills and competencies the planner should favour for 7 days.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta

from . import estimates

CEFR = estimates.CEFR
TECHNIQUE = ("inference", "point-de-vue", "intention", "idee-principale", "nuance", "consequence", "cause")


def _is_technique(comp: str) -> bool:
    return any(t in comp for t in TECHNIQUE)


def timing(results: dict) -> list[dict]:
    out = []
    for s in results["sections"]:
        if s.get("review") is None:
            continue
        name = {"CO": "Listening", "CE": "Reading"}[s["section"]]
        un = s.get("unanswered", 0)
        if s["timed_out"] and un >= 2:
            out.append({"section": s["section"], "problem": "out_of_time",
                        "note": f"{name}: time ran out with {un} question(s) unanswered. Practise answering under the clock."})
        elif s["time_used_s"] < 0.4 * s["limit_s"] and s["total"] and s["correct"] / s["total"] < 0.6:
            out.append({"section": s["section"], "problem": "rushed",
                        "note": f"{name}: finished in {s['time_used_s'] // 60} min out of {s['limit_s'] // 60} with many errors. Use the time to re-read the question and check each option."})
        elif s["total"]:
            per = s["time_used_s"] / max(1, s["total"] - un)
            out.append({"section": s["section"], "problem": None,
                        "note": f"{name}: about {round(per)} s per question, no timing problem."})
    return out


def root_causes(results: dict, est: dict, ai_errors: list[str]) -> list[dict]:
    causes = []
    for s in results["sections"]:
        review = s.get("review")
        if not review:
            continue
        low = est.get(s["skill"], {}).get("cefr_low")
        low_i = CEFR.index(low) if low else None
        right_levels = [CEFR.index(q["level"]) for q in review if q["correct"] and not _is_technique(q["competency"])]
        timed_out = s["timed_out"] and s.get("unanswered", 0) >= 2
        for q in review:
            if q["correct"]:
                continue
            lvl = CEFR.index(q["level"])
            if not q["answered"] and timed_out:
                cause, why = "timing", "left unanswered when time ran out"
            elif _is_technique(q["competency"]) and any(r >= lvl for r in right_levels):
                cause, why = "technique", f"factual questions at {q['level']} or above were right"
            elif low_i is not None and lvl <= low_i:
                cause, why = "french", f"missed at {q['level']}, within your estimated level"
            else:
                continue                                   # above the estimate: expected, not a diagnosis
            causes.append({"competency": q["competency"], "cause": cause, "evidence": why, "skill": s["skill"]})
    for comp in ai_errors:
        causes.append({"competency": comp, "cause": "french", "evidence": "language error in your writing or speaking",
                       "skill": None})
    seen, out = set(), []
    for c in causes:                                       # one line per competency, first reason kept
        if c["competency"] not in seen:
            seen.add(c["competency"])
            out.append(c)
    return out


def focus(results: dict, ai_scores: dict[str, float], causes: list[dict], tim: list[dict]) -> list[dict]:
    scored = []
    for s in results["sections"]:
        if s.get("review") is not None and s["total"]:
            scored.append((s["correct"] / s["total"], s["skill"]))
        elif s["skill"] in ai_scores:
            scored.append((ai_scores[s["skill"]] / 5, s["skill"]))
    scored.sort()
    out = []
    for ratio, skill in scored[:2]:
        if ratio >= 0.8:
            continue
        comps = [c["competency"] for c in causes if c["skill"] == skill][:4]
        why = f"{round(ratio * 100)} % in this assessment"
        if any(t["problem"] == "out_of_time" and {"CO": "listening", "CE": "reading"}[t["section"]] == skill for t in tim):
            why += ", and time ran out"
        out.append({"skill": skill, "competencies": comps, "weight": round(2.5 * (1 - ratio), 2), "reason": why + "."})
    lang = [c["competency"] for c in causes if c["skill"] is None][:4]
    if lang:
        out.append({"skill": "language", "competencies": lang, "weight": 1.5, "reason": "Language errors found in writing or speaking."})
    return out


def persist(conn: sqlite3.Connection, aid: int, focus_list: list[dict], complete: bool, causes: list[dict]) -> None:
    """Store next week's focus (overwritten until the report is complete) and record causes on weaknesses."""
    row = conn.execute("SELECT complete FROM plan_focus WHERE attempt_id = ?", (aid,)).fetchone()
    if row and row["complete"]:
        return
    done = conn.execute("SELECT completed_at FROM exam_attempt WHERE id = ?", (aid,)).fetchone()["completed_at"]
    until = (datetime.fromisoformat(done).date() + timedelta(days=7)).isoformat()
    conn.execute("""INSERT INTO plan_focus (attempt_id, valid_until, focus, complete) VALUES (?, ?, ?, ?)
                    ON CONFLICT (attempt_id) DO UPDATE SET focus = excluded.focus, complete = excluded.complete""",
                 (aid, until, json.dumps(focus_list, ensure_ascii=False), 1 if complete else 0))
    for c in causes:
        conn.execute("UPDATE weakness SET cause = ? WHERE competency = ? AND cause = 'unknown'", (c["cause"], c["competency"]))


def active_focus(conn: sqlite3.Connection, today: date | None = None) -> list[dict]:
    today_s = (today or date.today()).isoformat()
    row = conn.execute("SELECT focus FROM plan_focus WHERE valid_until >= ? ORDER BY attempt_id DESC LIMIT 1",
                       (today_s,)).fetchone()
    return json.loads(row["focus"]) if row else []
