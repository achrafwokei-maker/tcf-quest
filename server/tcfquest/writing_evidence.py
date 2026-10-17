"""Turn validated writing feedback into learning evidence (weaknesses + writing estimate).

Bounded on purpose: only known correction categories create weaknesses (one observation per
category per text), a very weak task-fulfilment score flags the task skill itself, and the
writing estimate gets a low-weight, AI-scored attempt (half weight again when the two scorings
disagree). The AI never changes an answer key or awards a level directly.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field

from . import content, estimates, weakness, writing_ai

AI_WEIGHT = 0.2            # half a keyed practice item: AI scoring is an estimate


@dataclass
class Target:
    """The minimal item shape weakness.observe() needs."""
    id: str
    competencies: list[str]
    tcf_target: content.TcfTarget
    level: str
    difficulty: int | None = None
    pool: str = "training"
    type: str = "writing"
    extra: dict = field(default_factory=dict)


def record(conn: sqlite3.Connection, row, task, fb: dict) -> None:
    sid = row["id"]
    tcf = content.TcfTarget(section="EE", task=task.task, purpose="Writing studio submission (AI-scored estimate).")
    seen: set[str] = set()
    for c in fb["corrections"]:
        if c.get("kind") != "error":
            continue                                           # style suggestions are not weaknesses
        comp = writing_ai.CATEGORIES.get(c["category"])
        if comp is None or comp in seen:
            continue
        seen.add(comp)
        weakness.observe(conn, "writing", Target(f"submission-{sid}", [comp], tcf, task.level),
                         "incorrect", c["original"], c["corrected"], hinted=False)
    if fb["criteria"]["task"]["high"] <= 2:
        weakness.observe(conn, "writing", Target(f"submission-{sid}", [task.competencies[0]], tcf, task.level),
                         "incorrect", "(task not fully done)", fb["criteria"]["task"]["comment"], hinted=False)
    score = fb["mean"] / 5
    verdict = "correct" if score >= 0.7 else "partial" if score >= 0.4 else "incorrect"
    weight = AI_WEIGHT if fb["agreement"] == "high" else AI_WEIGHT / 2
    flags = ["ai_scored"] + ([] if fb["agreement"] == "high" else ["low_agreement"])
    conn.execute(
        """INSERT INTO attempt (item_id, content_ver, skill, competency, mode, context, context_id, response,
                                correct, score, hints_used, duration_ms, verdict, evidence_weight, flags)
           VALUES (?, ?, 'writing', ?, ?, 'writing', 'writing', ?, ?, ?, 0, NULL, ?, ?, ?)""",
        (task.id, f"writing@{writing_ai.PROMPT_VERSION}", task.competencies[0], row["mode"],
         json.dumps({"submission": sid}), 1 if verdict == "correct" else 0, round(score, 3), verdict, weight,
         json.dumps(flags)))
    estimates.update(conn, ("writing",))
