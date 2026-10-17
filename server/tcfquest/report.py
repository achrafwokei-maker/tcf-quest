"""Post-assessment report (diagnostic and weekly trials). Deterministic, built from stored evidence.

Answers: how each skill went, where the estimate stands (range + confidence), which strengths and
error categories appeared in THIS assessment, what the evidence can't tell, what to prioritise, and
what the plan will do next. Never an official score, never an NCLC conversion of practice results.
Writing/speaking parts are included as soon as their AI feedback is ready (the report is rebuilt
on every read until then).
"""

from __future__ import annotations

import json
import sqlite3

from . import analysis, estimates, planner

CEFR = estimates.CEFR
SKILL_NAME = {"listening": "Listening", "reading": "Reading", "writing": "Writing", "speaking": "Speaking"}


def _skill_estimates(conn) -> dict:
    return {r["skill"]: dict(r) for r in conn.execute("SELECT skill, cefr_low, cefr_high, confidence, evidence FROM skill_profile")}


def _mid(est: dict | None) -> float | None:
    if not est or not est.get("cefr_low"):
        return None
    return (CEFR.index(est["cefr_low"]) + CEFR.index(est["cefr_high"])) / 2


def _refs(results: dict, exam_set: str) -> set[str]:
    refs = set()
    for s in results["sections"]:
        for q in s.get("review") or []:
            refs.add(f"{exam_set}--{q['item_id']}")
        for wid in s.get("writing_submission_ids") or ([s["writing_submission_id"]] if s.get("writing_submission_id") else []):
            refs.add(f"writing--submission-{wid}")
        if s.get("eo_session_id"):
            refs.add(f"speaking--session-{s['eo_session_id']}")
    return refs


def _ai_part(conn, s: dict) -> dict:
    ids = s.get("writing_submission_ids") or []
    if len(ids) > 1:                                    # full mock: combine T1–T3
        parts = [_ai_part(conn, {"writing_submission_id": i}) for i in ids]
        done = [p for p in parts if p.get("mean") is not None]
        out = {"status": "pending" if any(p["status"] == "pending" for p in parts) else ("done" if done else parts[0]["status"]),
               "tasks": parts}
        if done:
            out |= {"mean": round(sum(p["mean"] for p in done) / len(done), 2),
                    "agreement": "low" if any(p["agreement"] == "low" for p in done) else "high",
                    "cefr_estimate": " / ".join(p["cefr_estimate"] for p in done),
                    "strengths": [x for p in done for x in p["strengths"][:1]], "priorities": [x for p in done for x in p["priorities"][:1]]}
        if any(p.get("word_range_problem") for p in parts):
            out["word_range_problem"] = True
        return out
    if s.get("writing_submission_id"):
        row = conn.execute("SELECT feedback, feedback_status, word_count, word_range_ok FROM writing_submission WHERE id = ?",
                           (s["writing_submission_id"],)).fetchone()
    else:
        row = conn.execute("SELECT feedback, feedback_status FROM eo_session WHERE id = ?", (s["eo_session_id"],)).fetchone()
    if row is None:
        return {"status": "none"}
    status = "pending" if row["feedback_status"] == "running" else row["feedback_status"]
    out = {"status": status}
    if row["feedback"]:
        fb = json.loads(row["feedback"])
        out |= {"mean": fb["mean"], "agreement": fb["agreement"], "cefr_estimate": fb["cefr_estimate"],
                "strengths": fb["strengths"], "priorities": fb["priorities"],
                "criteria": {k: {"label": v["label"], "low": v["low"], "high": v["high"]} for k, v in fb["criteria"].items()}}
    if "word_range_ok" in row.keys() and row["word_range_ok"] == 0:
        out["word_range_problem"] = True
    return out


def build(conn: sqlite3.Connection, aid: int) -> dict:
    row = conn.execute("SELECT * FROM exam_attempt WHERE id = ?", (aid,)).fetchone()
    from . import exam
    e = exam.exams()[row["exam_id"]]
    results = json.loads(row["results"])
    est = _skill_estimates(conn)
    profile = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    goal = profile["target_cefr"] if profile else "B2"

    skills, strengths, limits, pending = [], [], [], False
    for s in results["sections"]:
        skill = s["skill"]
        entry = {"skill": skill, "section": s["section"], "estimate": est.get(skill), "timed_out": s["timed_out"],
                 "time_used_s": s["time_used_s"], "limit_s": s["limit_s"]}
        if s.get("review") is not None:
            entry |= {"correct": s["correct"], "total": s["total"], "unanswered": s.get("unanswered", 0),
                      "adaptive_final_level": s.get("adaptive_final_level")}
            right = [q for q in s["review"] if q["correct"]]
            if right:
                top = max(right, key=lambda q: CEFR.index(q["level"]))
                strengths.append(f"{SKILL_NAME[skill]}: correct up to {top['level']} ({top['competency']}).")
            limits.append(f"{SKILL_NAME[skill]}: {s['total']} questions only, so the range stays wide until more evidence comes in.")
        else:
            part = _ai_part(conn, s)
            entry["ai"] = part
            pending |= part["status"] == "pending"
            if part.get("strengths"):
                strengths += [f"{SKILL_NAME[skill]}: {x}" for x in part["strengths"][:1]]
            limits.append(f"{SKILL_NAME[skill]}: scored by a local AI on one task, an unofficial estimate"
                          + (" (the two readings disagreed)" if part.get("agreement") == "low" else "") + ".")
            if skill == "speaking":
                limits.append("Speaking: judged on the transcript (content and language), never on pronunciation.")
            if part.get("word_range_problem"):
                limits.append("Writing: outside the word range. In the real test this can make the paper « A1 non atteint ».")
        skills.append(entry)
    limits.append("This is a practice estimate, not an official TCF result, and it is not converted to an NCLC level.")

    refs = _refs(results, e.set)
    errors: dict[str, list[str]] = {}
    ai_errors, retests = [], []
    for w in conn.execute("SELECT competency, category, items_failed, severity, state FROM weakness WHERE state != 'mastered'"):
        failed = set(json.loads(w["items_failed"]))
        if refs & failed:
            errors.setdefault(w["category"], []).append(w["competency"])
            if any(r.startswith(("writing--", "speaking--")) for r in refs & failed) and \
                    w["competency"].startswith(("gram.", "orth.", "vocab.")):
                ai_errors.append(w["competency"])
            retests.append(w["competency"])

    tim = analysis.timing(results)
    causes = analysis.root_causes(results, est, ai_errors)
    ai_scores = {s["skill"]: s["ai"]["mean"] for s in skills if s.get("ai", {}).get("mean") is not None}
    focus = analysis.focus(results, ai_scores, causes, tim)
    analysis.persist(conn, aid, focus, not pending, causes)

    gaps = []
    for skill in ("listening", "reading", "writing", "speaking"):
        m = _mid(est.get(skill))
        conf = (est.get(skill) or {}).get("confidence", "none")
        gap = CEFR.index(goal) - (m if m is not None else 0)
        gaps.append((round(gap, 1), {"none": 3, "low": 2, "medium": 1, "high": 0}[conf], skill))
    gaps.sort(reverse=True)
    priorities = []
    for gap, _, skill in gaps[:2]:
        e_ = est.get(skill) or {}
        where = f"{e_.get('cefr_low')}–{e_.get('cefr_high')}" if e_.get("cefr_low") else "not measured yet"
        priorities.append({"skill": skill, "gap": gap,
                           "reason": f"{SKILL_NAME[skill]} is furthest from your {goal} goal (estimate {where})."})
    if errors:
        top = sorted(((len(v), k) for k, v in errors.items()), reverse=True)[0][1]
        priorities.append({"skill": None, "gap": None,
                           "reason": f"Most frequent error type in this assessment: {top} ({', '.join(errors[top][:3])})."})

    plan = planner.plan(conn)
    return {
        "timing": [t for t in tim if t["problem"]] or tim[:2], "root_causes": causes[:8], "focus": focus,
        "retests": retests[:6],
        "kind": e.kind, "goal": {"cefr": goal, "nclc": profile["target_nclc"] if profile else None},
        "skills": skills, "strengths": strengths[:5], "error_categories": errors, "limits": limits,
        "priorities": priorities,
        "next": {"steps": [{"title": s["title"], "minutes": s["minutes"], "reason": s["reason"]} for s in plan["steps"][:3]],
                 "weekly_trial": plan["weekly_trial"]},
        "complete": not pending,
        "label": "Practice estimate. Not an official TCF result.",
    }
