"""Avatar skins and the rule that unlocks them.

A skin unlocks when the learner's WEAKEST skill reaches its CEFR level, measured by
evidence-backed estimates (cefr_low). Points/XP never unlock skins.
"""

from __future__ import annotations

import sqlite3

CEFR = ["A1", "A2", "B1", "B2", "C1", "C2"]

SKINS = [
    {"id": "a1", "name": "Le Voyageur", "level": "A1"},
    {"id": "a2", "name": "Le Flâneur", "level": "A2"},
    {"id": "b1", "name": "Le Parisien", "level": "B1"},
    {"id": "b2", "name": "L'Orateur", "level": "B2"},
    {"id": "c1", "name": "L'Érudit", "level": "C1"},
    {"id": "c2", "name": "Le Maître", "level": "C2"},
]
SKIN_IDS = {s["id"] for s in SKINS}


def reached_level(conn: sqlite3.Connection) -> str:
    """Lowest evidence-backed CEFR level across the four skills; A1 until all four have at least medium confidence."""
    rows = conn.execute("SELECT cefr_low, evidence, confidence FROM skill_profile").fetchall()
    if len(rows) < 4 or any(r["evidence"] == 0 or r["cefr_low"] not in CEFR
                            or r["confidence"] not in ("medium", "high") for r in rows):
        return "A1"
    return min((r["cefr_low"] for r in rows), key=CEFR.index)


def skins_for(conn: sqlite3.Connection) -> list[dict]:
    reached = CEFR.index(reached_level(conn))
    return [{**s, "unlocked": CEFR.index(s["level"]) <= reached} for s in SKINS]


def is_unlocked(conn: sqlite3.Connection, skin_id: str) -> bool:
    return any(s["id"] == skin_id and s["unlocked"] for s in skins_for(conn))
