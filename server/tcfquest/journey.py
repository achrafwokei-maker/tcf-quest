"""The adventure: one continuous journey to TCF Canada readiness, built from existing data.

A presentation layer only. Content, scoring, weaknesses, estimates and exam records keep their own
rules; finishing a node never awards a level. The journey file (content/journey/journey.json) fixes the
recognizable main route (6 chapters grouped by TCF task, a weekly trial as each chapter's boss, the full
mock as the finale). Personalisation:
- upcoming nodes in the current chapter are ordered by the planner's scores (weak points, focus,
  priorities, level fit) and the active weekly focus;
- nodes far below the learner's estimate are marked optional, never removed;
- recovery side missions (due reviews/retests, a lesson for a stuck weak point) attach to the current
  position, and the learner returns to the main route afterwards;
- "Continue" resumes the exact mission in progress, else the most useful next step.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from functools import lru_cache
from pathlib import Path

from . import analysis, content, estimates, exam, notebook, planner, speaking, weakness, writing

ROOT = Path(__file__).resolve().parents[2]
JOURNEY_FILE = ROOT / "content" / "journey" / "journey.json"
CEFR = estimates.CEFR
SKILL = {"CO": "listening", "CE": "reading", "EO": "speaking", "EE": "writing"}
TASK_LABEL = {"EO-T1": "speaking task 1", "EO-T2": "speaking task 2", "EO-T3": "speaking task 3",
              "EE-T1": "writing task 1", "EE-T2": "writing task 2", "EE-T3": "writing task 3",
              "CO": "listening", "CE": "reading"}


@lru_cache(maxsize=None)
def spec() -> dict:
    return json.loads(JOURNEY_FILE.read_text())


def _level_mid(conn, skill: str) -> float | None:
    r = conn.execute("SELECT cefr_low, cefr_high FROM skill_profile WHERE skill = ?", (skill,)).fetchone()
    return (CEFR.index(r["cefr_low"]) + CEFR.index(r["cefr_high"])) / 2 if r and r["cefr_low"] else None


def _pick_variant(conn, ids: list[str]) -> str:
    """Level versions of one story (e.g. Belleville A2/B1): keep the one already started, else match the level."""
    for sid in ids:
        if conn.execute("SELECT 1 FROM mission_progress WHERE mission_id = ? AND (step > 0 OR status = 'completed')",
                        (f"set:{sid}",)).fetchone():
            return sid
    mid = _level_mid(conn, "speaking") if _level_mid(conn, "speaking") is not None else estimates.prior(conn) - 0.5
    return ids[-1] if mid >= 1.5 else ids[0]


class Ctx:
    """Everything the node builders need, loaded once per request."""

    def __init__(self, conn: sqlite3.Connection, today: date):
        self.conn, self.today = conn, today
        self.seen = weakness.attempted_items(conn)
        self.ex = exam.listing(conn)
        self.exams = {x["id"]: x for x in self.ex["exams"]}
        p = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
        self.profile = p
        self.phase = planner.phase_for(planner.weeks_to_exam(p, today))
        self.cands = {c["set"].id: c for c in planner.candidates(conn, today, self.phase)}
        self.focus = analysis.active_focus(conn, today)
        self.prios = planner._priorities(conn)


def _set_node(ctx: Ctx, sid: str) -> dict:
    s = content.get_set(sid)
    items = content.scored(content.playable(s))
    row = ctx.conn.execute("SELECT status, step FROM mission_progress WHERE mission_id = ?", (f"set:{sid}",)).fetchone()
    unseen = [i for i in items if i.id not in ctx.seen]
    if (row and row["status"] == "completed") or (items and not unseen):
        state = "done"
    elif row and row["status"] == "in_progress" and row["step"] > 0:
        state = "in_progress"
    else:
        state = "available"
    skill = SKILL[s.tcf_target.section]
    task = s.tcf_target.task or s.tcf_target.section
    c = ctx.cands.get(sid)
    level = sum(CEFR.index(i.level) for i in items) / max(1, len(items))
    mid = _level_mid(ctx.conn, skill)
    optional = state != "done" and mid is not None and mid - level >= 1.5
    return {"ref": f"set:{sid}", "kind": "academy" if s.context == "academy" else "lesson" if s.context == "toolbox" else
            "mission" if s.context == "mission" else "practice",
            "title": f"{s.title} · {s.level}" if s.context == "practice" else s.title.replace("Académie · ", ""), "task": task, "skill": skill, "level": s.level,
            "minutes": planner._set_minutes(s), "state": state, "optional": optional,
            "score": c["score"] if c else 0.0, "route": f"/set/{sid}",
            "reason": planner._reason(c) if c else f"Trains {TASK_LABEL.get(task, task)}."}


def _task_score(ctx: Ctx, skill: str) -> float:
    s = 2.0 + sum(f["weight"] for f in ctx.focus if f["skill"] == skill)
    if skill in ctx.prios:
        s += {0: 2.0, 1: 1.2, 2: 0.6}.get(ctx.prios.index(skill), 0)
    return round(s, 2)


def _writing_node(ctx: Ctx, tid: str) -> dict:
    t = writing.get_task(tid)
    rows = [r["status"] for r in ctx.conn.execute(
        "SELECT status FROM writing_submission WHERE task_id = ? AND mode = 'training'", (tid,))]
    state = "done" if "submitted" in rows else "in_progress" if "draft" in rows else "available"
    return {"ref": f"ee:{tid}", "kind": "writing", "title": t.title, "task": t.task, "skill": "writing", "level": t.level,
            "minutes": writing.EXAM_SPLIT_S[t.task] // 60 + 2, "state": state, "optional": False,
            "score": _task_score(ctx, "writing"), "route": f"/ecrit/{tid}",
            "reason": f"Real {TASK_LABEL[t.task]}: write it, then read the feedback on content and language."}


def _speaking_node(ctx: Ctx, tid: str) -> dict:
    t = speaking.get_task(tid)
    rows = [dict(r) for r in ctx.conn.execute(
        "SELECT status, feedback_status FROM eo_session WHERE task_id = ? AND mode = 'training'", (tid,))]
    if any(r["status"] == "ended" and r["feedback_status"] != "none" for r in rows):
        state = "done"
    elif any(r["status"] in ("prep", "active") for r in rows):
        state = "in_progress"
    else:
        state = "available"
    prep, talk = speaking.timings()[t.task]
    return {"ref": f"eo:{tid}", "kind": "speaking", "title": t.title, "task": t.task, "skill": "speaking", "level": t.level,
            "minutes": round((prep + talk) / 60) + 2, "state": state, "optional": False,
            "score": _task_score(ctx, "speaking"), "route": f"/oral/{tid}",
            "reason": f"Real {TASK_LABEL[t.task]} with the AI examiner, at the official timing."}


def _exam_node(ctx: Ctx, eid: str, boss: bool) -> dict:
    x = ctx.exams[eid]
    state = {"completed": "done", "in_progress": "in_progress"}.get(x["status"], "available")
    if state == "available" and x["blocked_by_seen"]:
        state = "skipped"
    minutes = round(sum(s["limit_s"] for s in x["sections"]) / 60)
    kind = "diagnostic" if x["kind"] == "diagnostic" else "final" if x["kind"] == "full" else "boss"
    reason = {"diagnostic": "Measures each of the four skills, so every next step fits your real level.",
              "boss": "An unseen four-skill trial under exam rules: it shows what really stuck and resets next week's plan.",
              "final": "The complete TCF Canada under official timings: stamina, timing and readiness."}[kind]
    return {"ref": f"exam:{eid}", "kind": kind, "title": x["title"], "task": "TCF", "skill": None, "level": None,
            "minutes": minutes, "state": state, "optional": False, "score": 0.0,
            "route": f"/examen/{x['attempt_id']}" if x["attempt_id"] else "/examen",
            "action": None if x["attempt_id"] else {"type": "start_exam", "exam_id": eid}, "reason": reason}


def _node(ctx: Ctx, ref: str, boss: bool = False) -> dict:
    kind, _, val = ref.partition(":")
    if kind == "onboarding":
        done = bool(ctx.profile and ctx.profile["onboarded_at"])
        return {"ref": "onboarding", "kind": "briefing", "title": "Briefing TCF Canada et objectif", "task": "TCF", "skill": None,
                "level": None, "minutes": 5, "state": "done" if done else "available", "optional": False, "score": 0.0,
                "route": "/bienvenue", "reason": "Understand the four sections and set your target."}
    if kind == "set":
        return _set_node(ctx, _pick_variant(ctx.conn, val.split("|")) if "|" in val else val)
    if kind == "ee":
        return _writing_node(ctx, val)
    if kind == "eo":
        return _speaking_node(ctx, val)
    return _exam_node(ctx, val, boss)


def _side_missions(ctx: Ctx) -> list[dict]:
    out = []
    due = notebook.due_count(ctx.conn, ctx.today)
    retests = len(weakness.retest_refs(ctx.conn))
    n = min(due + retests, notebook.DAILY_REVIEW_CAP)
    if n:
        out.append({"ref": "side:reviews", "kind": "review", "title": f"{n} review{'s' if n > 1 else ''}",
                    "minutes": max(2, round(n * 0.5)), "state": "available", "route": "/set/revisions",
                    "action": {"type": "start_reviews"},
                    "reason": "Your own mistakes, back at the right moment" + (" (including a new question to confirm a fix)" if retests else "") + "."})
    from . import vocab
    vo = vocab.overview(ctx.conn, ctx.today)
    if vo["session_size"] and ctx.profile and ctx.profile["onboarded_at"]:      # shown only after the briefing
        out.append({"ref": "side:vocab", "kind": "review", "title": f"{vo['session_size']} words", "minutes": max(2, round(vo["session_size"] * 0.4)),
                    "state": "available", "route": "/vocabulaire",
                    "reason": f"{vo['due']} to review and {vo['new_today']} new expressions you'll use in the TCF."})
    lesson = next((c for c in ctx.cands.values() if c["factors"].get("lesson", 0) >= 3), None)
    if lesson:
        out.append({"ref": f"set:{lesson['set'].id}", "kind": "lesson", "title": lesson["set"].title, "minutes": lesson["minutes"],
                    "state": "available", "route": f"/set/{lesson['set'].id}", "reason": planner._reason(lesson)})
    return out


def node_type(x: dict) -> str:
    """One of the seven map node types: listening, reading, speaking, writing, strategy, revision, boss."""
    if x["kind"] in ("boss", "final", "diagnostic"):
        return "boss"
    if x["kind"] == "review":
        return "revision"
    if x["kind"] in ("academy", "lesson", "briefing"):
        return "strategy"
    return x.get("skill") or "listening"


def build(conn: sqlite3.Connection, today: date | None = None) -> dict:
    today = today or date.today()
    ctx = Ctx(conn, today)
    share = spec()["unlock_share"]
    chapters, prev_open, prev_ok = [], True, True
    for ch in spec()["chapters"]:
        nodes = [_node(ctx, r) for r in ch["nodes"]]
        core = [x for x in nodes if not x["optional"]]
        done_share = sum(x["state"] == "done" for x in core) / max(1, len(core))
        boss = _node(ctx, ch["boss"], boss=True) if ch.get("boss") else None
        unlocked = prev_open and prev_ok
        if boss and boss["state"] == "available":
            ready = done_share >= share and (ctx.ex["diagnostic"] or {}).get("status") == "completed"
            if boss["kind"] == "boss" and not ctx.ex["weekly_due"]:
                ready = False
                boss["hint"] = f"Available {7 - (ctx.ex['days_since_last_weekly'] or 0)} day(s) after your last weekly trial."
            if not ready:
                boss["state"] = "locked"
                boss.setdefault("hint", f"Opens when {round(share * 100)} % of this chapter is done.")
        if ch["n"] == 0:
            complete = all(x["state"] == "done" for x in nodes)
        else:
            complete = bool(boss and boss["state"] in ("done", "skipped"))
        # Personal order: work in progress first, then the planner's most useful steps (fixed order breaks ties).
        order = {x["ref"]: i for i, x in enumerate(nodes)}
        upcoming = sorted([x for x in nodes if x["state"] in ("in_progress", "available")],
                          key=lambda x: (x["state"] != "in_progress", x["optional"], -x["score"], order[x["ref"]]))
        for i, x in enumerate(upcoming):
            x["rank"] = i + 1
        chapters.append({k: ch[k] for k in ("n", "title", "subtitle", "place", "goal")} | {
            "nodes": nodes, "boss": boss, "unlocked": unlocked, "complete": complete,
            "progress": round(done_share, 2), "upcoming": [x["ref"] for x in upcoming]})
        for x in nodes + ([boss] if boss else []):
            x["type"] = node_type(x)
            if not unlocked and x["state"] != "done":
                x["state"] = "locked"
                x.setdefault("hint", "Opens as you progress in the previous chapter.")
            x["recommended"] = bool(x.get("rank") and x["rank"] <= 2 and x["state"] in ("available", "in_progress") and unlocked)
        chapters[-1]["cefr"] = ch.get("cefr")
        prev_open = unlocked
        prev_ok = complete or (ch["n"] > 0 and done_share >= share) or (ch["n"] == 0 and nodes[0]["state"] == "done")
    current = next((c for c in chapters if c["unlocked"] and not c["complete"]), chapters[-1])
    total = sum(len(c["nodes"]) + (1 if c["boss"] else 0) for c in chapters)
    done = sum(sum(x["state"] == "done" for x in c["nodes"]) + (1 if c["boss"] and c["boss"]["state"] == "done" else 0) for c in chapters)
    for s in (side := _side_missions(ctx)):
        s["type"] = node_type(s)
    return {"destination": spec()["destination"], "chapters": chapters, "current_chapter": current["n"],
            "cefr_note": spec().get("cefr_note"),
            "side_missions": side, "progress": round(done / max(1, total), 2),
            "label": "Your journey shows where you are. Your levels are measured separately (Progression)."}


def _find(j: dict, ref: str) -> tuple[dict, dict] | None:
    for c in j["chapters"]:
        for x in c["nodes"] + ([c["boss"]] if c["boss"] else []):
            if x["ref"] == ref:
                return c, x
    return None


def continue_step(conn: sqlite3.Connection, today: date | None = None) -> dict:
    """The single primary action: resume, recover, or go to the next most useful step."""
    j = build(conn, today)
    chapters = [c for c in j["chapters"] if c["unlocked"]]
    cur = next(c for c in j["chapters"] if c["n"] == j["current_chapter"])

    def pack(c: dict, x: dict, why_prefix: str = "", following: dict | None = None) -> dict:
        steps = c["nodes"] + ([c["boss"]] if c["boss"] else [])
        pos = next((i for i, s in enumerate(steps) if s["ref"] == x["ref"]), None)
        return {"node": x, "chapter": {"n": c["n"], "title": c["title"], "place": c["place"]},
                "where": f"Chapter {c['n']} · {c['title']}" + (f" · step {pos + 1} of {len(steps)}" if pos is not None else ""),
                "why": (why_prefix + x["reason"]).strip(),
                "next": following["title"] if following else None, "progress": j["progress"]}

    def next_main(c: dict, skip: str | None = None) -> dict | None:
        for ref in c["upcoming"]:
            hit = _find(j, ref)
            if hit and ref != skip and not hit[1]["optional"]:
                return hit[1]
        if c["boss"] and c["boss"]["state"] in ("available", "in_progress"):
            return c["boss"]
        return None

    # 1. An exam or mission already in progress: resume it exactly.
    for c in chapters:
        for x in c["nodes"] + ([c["boss"]] if c["boss"] else []):
            if x["state"] == "in_progress" and x["kind"] in ("diagnostic", "boss", "final"):
                return pack(c, x, "Resume where you stopped. ")
    for c in chapters:
        for x in c["nodes"]:
            if x["state"] == "in_progress":
                return pack(c, x, "Resume where you stopped. ", next_main(c, x["ref"]))
    main = next_main(cur)
    if main is None:                                    # chapter done but boss not open yet: move on
        later = next((c for c in chapters if c["n"] > cur["n"] and not c["complete"]), None)
        if later and next_main(later):
            cur, main = later, next_main(later)
    # 2. A short recovery side mission first, then straight back to the main route.
    side = next((s for s in j["side_missions"] if s["ref"] == "side:reviews"), None)
    if side and main and main["kind"] not in ("diagnostic",):
        out = pack(cur, side, "", main)
        out["where"] = f"Chapter {cur['n']} · {cur['title']} · quick detour"
        out["why"] = side["reason"] + f" Then back to « {main['title']} »."
        return out
    if main:
        return pack(cur, main, "", next_main(cur, main["ref"]))
    return {"node": None, "chapter": {"n": cur["n"], "title": cur["title"], "place": cur["place"]},
            "where": f"Chapter {cur['n']} · {cur['title']}", "why": "You've done everything open for now. Free practice is in Entraînement.",
            "next": None, "progress": j["progress"]}
