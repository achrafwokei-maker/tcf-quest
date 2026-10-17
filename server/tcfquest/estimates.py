"""Skill estimates (CEFR range + confidence) from weighted evidence. Deterministic, no AI.

Model: a one-parameter logistic (Rasch-style) ability θ per skill on a 0–6 scale (A1 = 0–1, …,
C2 = 5–6). An item at CEFR level L has difficulty L, so a learner in the middle of band L succeeds
about 75 % of the time on level-L items. θ is the weighted maximum a posteriori estimate:
- each attempt counts by its evidence weight (hints, replays and proxies already lower it;
  disputed and technical attempts have weight 0; immediate re-queued retries are ignored);
- partial answers count as half correct;
- a weak prior from the self-rating keeps a handful of answers from producing extreme levels.

The range is θ ± one standard error, so it narrows as evidence accumulates. Confidence:
none (no evidence) · low (< 15 full-item equivalents) · medium · high (≥ 25 and SE ≤ 0.5). Speaking and writing stay "low" at most until real
spoken/written tasks are assessed (keyed proxies only, milestones M4/M6).
"""

from __future__ import annotations

import json
import math
import sqlite3

from . import content

CEFR = ["A1", "A2", "B1", "B2", "C1", "C2"]
SKILLS = ("listening", "reading", "speaking", "writing")
PROXY_SKILLS = ("speaking", "writing")
SLOPE = 2.2                  # P(correct) = 75 % in the middle of the item's band
PRIOR_SD = 1.5
FULL_ITEM = 0.4              # evidence weight of one full practice item
SELF_MID = {1: 0.5, 2: 1.0, 3: 2.0, 4: 3.0, 5: 4.0}   # middle of the self-rating band (onboarding.SELF_BAND)
GRID = [i / 20 for i in range(0, 121)]               # θ from 0 to 6 in steps of 0.05


def _p(theta: float, d: float) -> float:
    return 1 / (1 + math.exp(-SLOPE * (theta - d)))


def band(theta: float) -> str:
    return CEFR[min(5, max(0, int(theta)))]


def estimate(observations: list[tuple[float, float, float]], prior_mean: float) -> dict:
    """observations: (item difficulty 0–5, credit 0/0.5/1, weight). Returns θ, SE, range, equivalents."""
    used = [(d, c, w) for d, c, w in observations if w > 0]
    if not used:
        return {"theta": None, "se": None, "cefr_low": None, "cefr_high": None, "items": 0, "equivalents": 0.0}

    def log_post(t: float) -> float:
        ll = sum(w * (c * math.log(_p(t, d)) + (1 - c) * math.log(1 - _p(t, d))) for d, c, w in used)
        return ll - (t - prior_mean) ** 2 / (2 * PRIOR_SD ** 2)

    theta = max(GRID, key=log_post)
    info = sum(w * SLOPE ** 2 * _p(theta, d) * (1 - _p(theta, d)) for d, _, w in used) + 1 / PRIOR_SD ** 2
    se = 1 / math.sqrt(info)
    return {"theta": round(theta, 2), "se": round(se, 2), "cefr_low": band(theta - se), "cefr_high": band(theta + se),
            "items": len(used), "equivalents": round(sum(w for _, _, w in used) / FULL_ITEM, 1)}


def confidence(skill: str, est: dict, real_tasks: int = 0) -> str:
    if not est["items"]:
        return "none"
    if est["equivalents"] >= 25 and est["se"] <= 0.5:
        level = "high"
    elif est["equivalents"] >= 15:
        level = "medium"
    else:
        level = "low"
    if skill in PROXY_SKILLS:
        # Keyed proxies only → low. Three or more AI-scored real tasks with agreeing scorings → up to medium.
        return "medium" if real_tasks >= 3 and level in ("medium", "high") else "low"
    return level


def observations(conn: sqlite3.Connection, skill: str) -> list[tuple[float, float, float]]:
    out = []
    for r in conn.execute("""SELECT context_id, item_id, verdict, score, evidence_weight, flags FROM attempt
                             WHERE skill = ? AND verdict IN ('correct', 'partial', 'incorrect')
                               AND evidence_weight > 0""", (skill,)):
        if "requeue" in json.loads(r["flags"]):
            continue                                    # retried right after seeing the answer
        if r["context_id"] in ("writing", "speaking"):   # AI-scored task: partial credit = rubric mean
            from . import speaking, writing
            task = (writing if r["context_id"] == "writing" else speaking).get_task(r["item_id"])
            if task is not None:
                out.append((float(CEFR.index(task.level)), float(r["score"]), r["evidence_weight"]))
            continue
        _, item = content.resolve_item(r["context_id"], r["item_id"])
        if item is None:
            continue
        credit = {"correct": 1.0, "partial": 0.5, "incorrect": 0.0}[r["verdict"]]
        out.append((float(CEFR.index(item.level)), credit, r["evidence_weight"]))
    return out


def prior(conn: sqlite3.Connection) -> float:
    row = conn.execute("SELECT self_rating FROM profile WHERE id = 1").fetchone()
    return SELF_MID.get(row["self_rating"] if row else None, 1.5)


def update(conn: sqlite3.Connection, skills: tuple[str, ...] = SKILLS, source: str = "practice") -> dict:
    """Recompute and store the estimates; log a history row whenever a range or confidence changes."""
    mean = prior(conn)
    out = {}
    for skill in skills:
        est = estimate(observations(conn, skill), mean)
        real = conn.execute("SELECT COUNT(*) FROM attempt WHERE skill = ? AND flags LIKE '%ai_scored%' "
                            "AND flags NOT LIKE '%low_agreement%' AND evidence_weight > 0", (skill,)).fetchone()[0]
        conf = confidence(skill, est, real)
        lo, hi = est["cefr_low"], est["cefr_high"]
        if lo is not None and lo == hi and conf != "high":       # always a range until evidence is strong
            hi = CEFR[min(5, CEFR.index(hi) + 1)]
        old = conn.execute("SELECT cefr_low, cefr_high, confidence FROM skill_profile WHERE skill = ?", (skill,)).fetchone()
        conn.execute(
            """INSERT INTO skill_profile (skill, cefr_low, cefr_high, confidence, evidence, updated_at)
               VALUES (?, ?, ?, ?, ?, datetime('now'))
               ON CONFLICT (skill) DO UPDATE SET cefr_low = excluded.cefr_low, cefr_high = excluded.cefr_high,
                 confidence = excluded.confidence, evidence = excluded.evidence, updated_at = excluded.updated_at""",
            (skill, lo, hi, conf, est["items"]))
        if lo is not None and (old is None or (old["cefr_low"], old["cefr_high"], old["confidence"]) != (lo, hi, conf)):
            conn.execute("INSERT INTO progress_history (skill, cefr_low, cefr_high, confidence, source) VALUES (?, ?, ?, ?, ?)",
                         (skill, lo, hi, conf, source))
        out[skill] = {**est, "cefr_low": lo, "cefr_high": hi, "confidence": conf}
    return out
