"""Speaking tasks EO T1–T3 with a local AI examiner. Timing and turn rules are deterministic;
the AI (Qwen3 via Ollama) only writes the examiner's next short line, inside strict limits.

T1 entretien dirigé (2 min): personal questions, follow-ups.
T2 interaction (2 min preparation + 3 min 30): the examiner plays a role and answers ONLY from the
   scenario facts (hidden from the learner), including one surprise.
T3 point de vue (4 min 30): the learner argues; the examiner relances with nuance questions.
If the AI is off, deterministic fallback lines keep the task going (and the session records it).
"""

from __future__ import annotations

import json
import random
import re
import sqlite3
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Literal

import httpx
from pydantic import BaseModel, Field, model_validator

from . import ai, content

ROOT = Path(__file__).resolve().parents[2]
TASKS_FILE = ROOT / "content" / "speaking" / "eo-tasks.json"
EXAM_FILE = ROOT / "content" / "exam" / "tcf-canada.v1.json"
EOTask = Literal["EO-T1", "EO-T2", "EO-T3"]
GRACE_S = 15
CLOSING = "Merci, c'est terminé pour cette partie."


class SpeakingTask(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9-]+$")
    task: EOTask
    level: content.Level
    title: str
    examiner: Literal["Examinateur", "Examinatrice"]
    instructions: str = Field(min_length=30)
    opening: str
    role: str | None = None
    facts: dict[str, str] = Field(default_factory=dict)     # T2 only, never shown to the learner
    targets: list[str] = Field(default_factory=list)        # T2: what the learner should find out
    questions: list[str] = Field(default_factory=list)      # T1 seed questions
    challenges: list[str] = Field(default_factory=list)     # T3 relances
    competencies: list[str] = Field(min_length=1)
    pool: content.Pool = "training"

    @model_validator(mode="after")
    def task_fields(self):
        if self.task == "EO-T1" and len(self.questions) < 4:
            raise ValueError("EO-T1 needs at least 4 seed questions")
        if self.task == "EO-T2" and not (self.role and len(self.facts) >= 4 and len(self.targets) >= 3 and "imprévu" in self.facts):
            raise ValueError("EO-T2 needs a role, 4+ facts including an 'imprévu', and 3+ targets")
        if self.task == "EO-T3" and len(self.challenges) < 1:
            raise ValueError("EO-T3 needs at least one relance")
        return self


class Guide(BaseModel):
    title: str
    tips: list[str] = Field(min_length=2)
    phrases: list[str] = Field(min_length=3)


class TaskFile(BaseModel):
    version: int
    review_status: content.ReviewStatus
    guides: dict[EOTask, Guide]
    tasks: list[SpeakingTask]

    @model_validator(mode="after")
    def complete(self):
        if {t.task for t in self.tasks} != {"EO-T1", "EO-T2", "EO-T3"}:
            raise ValueError("every speaking task type needs at least one task")
        if len({t.id for t in self.tasks}) != len(self.tasks):
            raise ValueError("duplicate speaking task ids")
        return self


@lru_cache(maxsize=None)
def task_file() -> TaskFile:
    return TaskFile.model_validate_json(TASKS_FILE.read_text())


@lru_cache(maxsize=None)
def timings() -> dict[str, tuple[int, int]]:
    """(preparation seconds, speaking seconds) per task, from the verified exam config."""
    eo = next(s for s in json.loads(EXAM_FILE.read_text())["sections"] if s["id"] == "EO")
    return {t["id"]: (int(t["preparation_minutes"] * 60), int((t["minutes"] - t["preparation_minutes"]) * 60))
            for t in eo["tasks"]}


def get_task(task_id: str) -> SpeakingTask | None:
    return next((t for t in task_file().tasks if t.id == task_id), None)


def public_task(t: SpeakingTask) -> dict:
    prep, talk = timings()[t.task]
    return {"id": t.id, "task": t.task, "level": t.level, "title": t.title, "examiner": t.examiner,
            "instructions": t.instructions, "targets": t.targets, "prep_s": prep, "talk_s": talk}


# ---------- sessions ----------

def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _ts() -> str:
    return _now().isoformat(sep=" ", timespec="seconds")


def _since(ts: str | None) -> float:
    return (_now() - datetime.fromisoformat(ts)).total_seconds() if ts else 0.0


class Ended(Exception):
    pass


def _row(conn, sid):
    row = conn.execute("SELECT * FROM eo_session WHERE id = ?", (sid,)).fetchone()
    if row is None:
        raise KeyError(sid)
    return row


def public(conn: sqlite3.Connection, sid: int) -> dict:
    row = _row(conn, sid)
    out = dict(row)
    out["turns"] = json.loads(row["turns"])
    out["feedback"] = json.loads(row["feedback"]) if row["feedback"] else None
    out["feedback_status"] = "pending" if out["feedback_status"] == "running" else out["feedback_status"]
    if row["status"] == "prep":
        out["remaining_s"] = max(0, int(row["prep_s"] - _since(row["started_at"])))
    elif row["status"] == "active":
        out["remaining_s"] = max(0, int(row["talk_s"] - _since(row["talk_started_at"])))
    else:
        out["remaining_s"] = 0
    return out


def _examiner_turn(text: str, fallback: bool = False) -> dict:
    return {"role": "examiner", "text": text, "fallback": fallback, "at": _ts()}


def start(conn: sqlite3.Connection, task_id: str, mode: str, exam: bool = False) -> dict:
    """exam=True: called by the exam engine (reserved tasks allowed)."""
    t = get_task(task_id)
    if t is None or (t.pool != "training" and not exam):
        raise KeyError(task_id)
    prep, talk = timings()[t.task]
    status = "prep" if prep else "active"
    turns = [] if prep else [_examiner_turn(t.opening)]
    now = _ts()
    cur = conn.execute(
        """INSERT INTO eo_session (task_id, task, mode, status, turns, prep_s, talk_s, started_at, talk_started_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (t.id, t.task, mode, status, json.dumps(turns, ensure_ascii=False), prep, talk, now, None if prep else now))
    return public(conn, cur.lastrowid)


def begin(conn: sqlite3.Connection, sid: int) -> dict:
    """End the preparation (early, or when its time is up) and let the examiner open."""
    row = _row(conn, sid)
    if row["status"] == "prep":
        t = get_task(row["task_id"])
        conn.execute("UPDATE eo_session SET status = 'active', talk_started_at = ?, turns = ? WHERE id = ?",
                     (_ts(), json.dumps([_examiner_turn(t.opening)], ensure_ascii=False), sid))
    return public(conn, sid)


def _time_up(row) -> bool:
    return row["status"] == "active" and _since(row["talk_started_at"]) > row["talk_s"] + GRACE_S


def end(conn: sqlite3.Connection, sid: int, reason: str = "learner") -> dict:
    row = _row(conn, sid)
    if row["status"] != "ended":
        learner = [t for t in json.loads(row["turns"]) if t["role"] == "learner"]
        conn.execute("""UPDATE eo_session SET status = 'ended', ended_at = ?, end_reason = ?,
                          feedback_status = ? WHERE id = ?""",
                     (_ts(), reason, "pending" if learner else "none", sid))
    return public(conn, sid)


def turn(conn: sqlite3.Connection, sid: int, text: str, source: str, confidence: float | None = None,
         asr_status: str | None = None, recording_id: int | None = None) -> dict:
    row = _row(conn, sid)
    if row["status"] == "prep" and _since(row["started_at"]) >= row["prep_s"]:
        begin(conn, sid)
        row = _row(conn, sid)
    if row["status"] != "active":
        raise Ended("This task has ended." if row["status"] == "ended" else "Preparation time is still running.")
    if _time_up(row):
        end(conn, sid, "time")
        raise Ended("Time is up for this task.")
    turns = json.loads(row["turns"])
    turns.append({"role": "learner", "text": text.strip(), "source": source, "confidence": confidence,
                  "asr_status": asr_status, "recording_id": recording_id, "at": _ts()})
    t = get_task(row["task_id"])
    remaining = row["talk_s"] - _since(row["talk_started_at"])
    fallbacks = row["ai_fallbacks"]
    if remaining <= 8:
        turns.append(_examiner_turn(CLOSING))
    else:
        line, used_fallback = examiner_reply(t, turns)
        fallbacks += used_fallback
        turns.append(_examiner_turn(line, used_fallback))
    conn.execute("UPDATE eo_session SET turns = ?, ai_fallbacks = ? WHERE id = ?",
                 (json.dumps(turns, ensure_ascii=False), fallbacks, sid))
    if remaining <= 8:
        return end(conn, sid, "time")
    return public(conn, sid)


# ---------- the examiner ----------

PROMPT_VERSION = "eo-examiner-v2"


def examiner_messages(t: SpeakingTask, turns: list[dict]) -> list[dict]:
    rules = ("Tu es l'examinateur ou l'examinatrice du TCF Canada (expression orale). Réponds en français oral naturel, "
             "en UNE ou DEUX phrases courtes, sans Markdown, sans liste, sans émoji. Ne corrige jamais le candidat, ne "
             "parle pas à sa place, ne donne pas de conseils. ")
    if t.task == "EO-T1":
        asked = [x["text"] for x in turns if x["role"] == "examiner"]
        rules += ("Tâche 1, entretien dirigé : pose UNE question à la fois sur la vie du candidat (identité, travail, "
                  "études, loisirs, projets). Rebondis brièvement sur sa dernière réponse, puis pose une nouvelle question. "
                  f"Exemples de questions : {' / '.join(t.questions)}. Ne repose pas une question déjà posée : {' / '.join(asked)}.")
    elif t.task == "EO-T2":
        facts = "; ".join(f"{k} : {v}" for k, v in t.facts.items() if k != "imprévu")
        rules += (f"Tâche 2, interaction : tu joues le rôle suivant : {t.role}. Le candidat doit obtenir des informations. "
                  f"Réponds UNIQUEMENT à sa question avec ces informations : {facts}. N'invente rien d'autre : si on te "
                  "demande autre chose, dis que tu ne sais pas ou que tu vas te renseigner. Ne donne pas toutes les "
                  "informations d'un coup : si la question est générale, demande ce qu'il veut savoir. "
                  f"IMPORTANT, cette information est prioritaire sur toutes les autres : {t.facts['imprévu']}. Dès que le "
                  "candidat aborde ce sujet, dis-le clairement. Ne pose pas de questions, sauf pour faire préciser une "
                  "question floue. Reste poli et naturel.")
    else:
        rules += (f"Tâche 3, point de vue. La question posée : « {t.opening} ». Laisse le candidat développer. Ne donne "
                  "jamais ton opinion. Relance avec une question qui l'oblige à préciser, nuancer ou donner un exemple, "
                  f"par exemple : {' / '.join(t.challenges)}.")
    msgs = [{"role": "system", "content": rules}]
    for x in turns:
        msgs.append({"role": "assistant" if x["role"] == "examiner" else "user", "content": x["text"]})
    return msgs


def clean_line(text: str) -> str:
    text = re.sub(r"[*_#`>\[\]]", "", text).replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip().strip('"«» ')
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = " ".join(parts[:2]).strip()
    return out[:240].rsplit(" ", 1)[0] + "…" if len(out) > 240 else out


def fallback_line(t: SpeakingTask, turns: list[dict]) -> str:
    asked = {x["text"] for x in turns if x["role"] == "examiner"}
    if t.task == "EO-T1":
        left = [q for q in t.questions if q not in asked]
        return left[0] if left else "Et pouvez-vous m'en dire un peu plus ?"
    if t.task == "EO-T2":
        return "Pardon, je vérifie… Pouvez-vous reformuler votre question, s'il vous plaît ?"
    left = [q for q in t.challenges if q not in asked]
    return left[0] if left else "Pouvez-vous donner un exemple concret ?"


def examiner_reply(t: SpeakingTask, turns: list[dict]) -> tuple[str, int]:
    """(line, 1 if the deterministic fallback was used)."""
    payload = {"model": ai.MODEL, "stream": False, "think": False,
               "format": {"type": "object", "properties": {"reply": {"type": "string"}}, "required": ["reply"]},
               "options": {"temperature": 0.6, "seed": random.randint(1, 10_000), "num_ctx": 4096, "num_predict": 120},
               "messages": examiner_messages(t, turns)}
    try:
        r = httpx.post(f"{ai.OLLAMA_URL}/api/chat", json=payload, timeout=60)
        r.raise_for_status()
        line = clean_line(json.loads(r.json()["message"]["content"])["reply"])
        if len(line) >= 3:
            return line, 0
    except (httpx.HTTPError, ValueError, KeyError):
        pass
    return fallback_line(t, turns), 1


def listing(conn: sqlite3.Connection) -> dict:
    last = {r["task_id"]: dict(r) for r in conn.execute(
        "SELECT task_id, MAX(id) AS id, status, feedback_status FROM eo_session GROUP BY task_id")}
    return {"tasks": [{**public_task(t), "last": last.get(t.id)} for t in task_file().tasks if t.pool == "training"],
            "guides": {k: v.model_dump() for k, v in task_file().guides.items()}}


def history(conn: sqlite3.Connection, task_id: str) -> list[dict]:
    return [dict(r) for r in conn.execute(
        "SELECT id, mode, status, end_reason, feedback_status, started_at FROM eo_session "
        "WHERE task_id = ? AND status = 'ended' ORDER BY id DESC", (task_id,))]
