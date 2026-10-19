"""Rubric feedback for EO T1–T3 transcripts (unofficial estimates). Content and language only.

Never a pronunciation score. Transcription can be wrong, so:
- learner turns are marked reliable (typed, corrected by the learner, or recognised with
  confidence ≥ 0.75) or uncertain; grammar corrections and weaknesses only come from reliable
  turns, and every correction must quote a reliable turn;
- the evidence weight halves when most turns are uncertain or the two scorings disagree.
Deterministic speaking stats (words, turns, longest answer) are computed by the app, not the AI.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Literal

import httpx
from pydantic import BaseModel, Field, ValidationError

from . import ai, content, db, estimates, speaking, weakness, writing_ai
from .writing_ai import CATEGORIES, CRIT_SCHEMA, Correction, Criterion, _norm, rule_corrections

PROMPT_VERSION = "eo-rubric-v3"
RELIABLE_CONFIDENCE = 0.75
AI_WEIGHT = 0.2
CRITERIA = ("task", "interaction", "coherence", "vocabulary", "grammar")
LABELS = {
    "EO-T1": {"task": "Réponses développées", "interaction": "Interaction avec l'examinateur", "coherence": "Clarté et cohérence",
              "vocabulary": "Lexique", "grammar": "Grammaire"},
    "EO-T2": {"task": "Informations obtenues", "interaction": "Interaction et politesse", "coherence": "Questions claires et variées",
              "vocabulary": "Lexique", "grammar": "Grammaire"},
    "EO-T3": {"task": "Point de vue argumenté", "interaction": "Réaction aux relances", "coherence": "Organisation et connecteurs",
              "vocabulary": "Lexique", "grammar": "Grammaire"},
}
FOCUS = {
    "EO-T1": "task = le candidat développe-t-il ses réponses (détails, raisons, exemples) ; interaction = comprend-il et réagit-il naturellement ; coherence = réponses claires et enchaînées.",
    "EO-T2": "task = a-t-il obtenu les informations attendues ({targets}) ; interaction = ouverture et clôture polies, réactions aux réponses, reformulation, réaction à l'imprévu ; coherence = questions claires, variées (inversion, est-ce que, question indirecte).",
    "EO-T3": "task = opinion claire, au moins deux arguments, exemples concrets, nuance ; interaction = répond-il vraiment aux relances ; coherence = organisation (introduction, arguments, conclusion) et connecteurs.",
}


class Scores(BaseModel):
    criteria: dict[Literal["task", "interaction", "coherence", "vocabulary", "grammar"], Criterion]


class Rubric(Scores):
    corrections: list[Correction] = Field(max_length=10)
    strengths: list[str] = Field(min_length=1, max_length=3)
    priorities: list[str] = Field(min_length=1, max_length=3)
    better_answer: str = Field(min_length=20)
    targets_obtained: list[int] = Field(default_factory=list, max_length=10)
    cefr_estimate: writing_ai.CEFRBand


def reliable(turn: dict) -> bool:
    return turn.get("source") in ("typed", "corrected") or (
        turn.get("asr_status") == "ok" and (turn.get("confidence") or 0) >= RELIABLE_CONFIDENCE)


def stats(turns: list[dict]) -> dict:
    learner = [t for t in turns if t["role"] == "learner"]
    counts = [len(t["text"].split()) for t in learner]
    return {"turns": len(learner), "words": sum(counts), "longest": max(counts, default=0),
            "average": round(sum(counts) / len(counts), 1) if counts else 0,
            "uncertain_turns": sum(not reliable(t) for t in learner)}


def schema(full: bool = True) -> dict:
    crit = {"type": "object", "properties": {c: CRIT_SCHEMA for c in CRITERIA}, "required": list(CRITERIA)}
    if not full:
        return {"type": "object", "properties": {"criteria": crit}, "required": ["criteria"]}
    s = writing_ai.schema()
    s["properties"]["criteria"] = crit
    s["properties"].pop("revised_version")
    s["properties"]["better_answer"] = {"type": "string"}
    s["properties"]["targets_obtained"] = {"type": "array", "items": {"type": "integer"}}
    s["required"] = ["criteria", "corrections", "strengths", "priorities", "better_answer", "targets_obtained", "cefr_estimate"]
    return s


def messages(t: speaking.SpeakingTask, turns: list[dict], full: bool) -> list[dict]:
    lines = []
    for x in turns:
        if x["role"] == "examiner":
            lines.append(f"EXAMINATEUR : {x['text']}")
        else:
            lines.append(f"CANDIDAT{'' if reliable(x) else ' [transcription incertaine]'} : {x['text']}")
    targets = "; ".join(f"{i}. {g}" for i, g in enumerate(t.targets))
    system = (
        "Tu es un examinateur expérimenté du TCF Canada (expression orale). Tu évalues la transcription d'un entraînement "
        "avec la grille ci-dessous (0 à 5 par critère : 0 = rien, 1 = A1, 2 = A2, 3 = B1, 4 = B2, 5 = C1/C2). "
        "Tu évalues le CONTENU et la LANGUE uniquement, JAMAIS la prononciation : c'est une transcription automatique. "
        f"Critères : {FOCUS[t.task].format(targets=targets)} vocabulary = étendue et précision ; grammar = correction des formes. "
        "Les passages marqués [transcription incertaine] peuvent contenir des erreurs de reconnaissance : n'en tire aucune "
        "correction de grammaire et ne les pénalise pas pour la langue. "
        "Corrections : extraits EXACTS et COURTS (1 à 6 mots) des répliques fiables du CANDIDAT, kind = error pour les vraies "
        "erreurs, kind = style pour au plus 3 améliorations. « comment », « explanation », « strengths » et « priorities » sont "
        "en ANGLAIS simple, une phrase chacun. « better_answer » : une meilleure version d'UNE réplique fiable du candidat, en français, "
        "à l'oral naturel. « targets_obtained » : numéros des informations obtenues (tâche 2 seulement, sinon liste vide). "
        "Réponds uniquement en JSON.")
    if not full:
        system += " Pour cette deuxième lecture, donne uniquement les notes des cinq critères avec un commentaire court."
    user = f"Tâche : {t.task} — {t.title}\nConsigne : {t.instructions}\n" + (f"Informations attendues : {targets}\n" if t.targets else "") \
        + "\nTranscription :\n" + "\n".join(lines) \
        + ("\n\nDo not flag gender agreement (désolé/désolée…) when the speaker's gender is unknown. Write every « comment », « explanation », « strengths » and « priorities » in ENGLISH. Keep French "
           "only in « original », « corrected » and « better_answer ».")
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _ask(t, turns, full: bool, seed: int):
    model_cls, last = (Rubric if full else Scores), None
    for attempt in range(2):
        payload = {"model": ai.MODEL, "stream": False, "think": False, "format": schema(full),
                   "options": {"temperature": 0.3, "seed": seed + attempt, "num_ctx": 8192},
                   "messages": messages(t, turns, full)}
        content = ai.chat(payload, writing_ai.TIMEOUT_S)
        try:
            return model_cls.model_validate_json(content)
        except (ValidationError, KeyError, ValueError) as e:
            last = e
    raise ValueError(f"invalid rubric output: {last}")


def clean(r: Rubric, turns: list[dict], n_targets: int) -> Rubric:
    text = "\n".join(t["text"] for t in turns if t["role"] == "learner" and reliable(t))
    norm = _norm(text)
    kept, seen = [], set()
    for c in rule_corrections(text) + [writing_ai.narrow(x) for x in r.corrections]:
        o = _norm(c.original).strip(" ?!.,;:")
        key = (o, _norm(c.corrected).strip(" ?!.,;:"))
        if not o or o not in norm or o == key[1] or key in seen or len(o.split()) > 8 \
                or writing_ai.gender_only(c.original, c.corrected):
            continue
        seen.add(key)
        kept.append(c)
    targets = sorted({i for i in r.targets_obtained if 0 <= i < n_targets})
    return r.model_copy(update={"corrections": kept[:12], "targets_obtained": targets})


def combine(t: speaking.SpeakingTask, a: Rubric, b: Scores, st: dict) -> dict:
    criteria, agree = {}, True
    for c in CRITERIA:
        sa, sb = a.criteria[c].score, b.criteria[c].score
        agree &= abs(sa - sb) <= 1
        criteria[c] = {"label": LABELS[t.task][c], "score": (sa + sb) / 2, "low": min(sa, sb), "high": max(sa, sb),
                       "comment": a.criteria[c].comment}
    return {
        "criteria": criteria, "mean": round(sum(v["score"] for v in criteria.values()) / len(CRITERIA), 2),
        "agreement": "high" if agree else "low", "corrections": [c.model_dump() for c in a.corrections],
        "strengths": a.strengths, "priorities": a.priorities, "better_answer": a.better_answer,
        "targets": [{"text": g, "obtained": i in a.targets_obtained} for i, g in enumerate(t.targets)],
        "cefr_estimate": a.cefr_estimate, "stats": st,
        "label": "Unofficial practice estimate from a local AI, on content and language only. No pronunciation score: "
                 "the transcription itself can be wrong.",
    }


def record_evidence(conn: sqlite3.Connection, row, t: speaking.SpeakingTask, fb: dict) -> None:
    from .writing_evidence import Target
    tcf = content.TcfTarget(section="EO", task=t.task, purpose="Speaking task with the AI examiner (AI-scored estimate).")
    seen = set()
    for c in fb["corrections"]:
        comp = CATEGORIES.get(c["category"])
        if c.get("kind") != "error" or comp is None or comp in seen:
            continue
        seen.add(comp)
        weakness.observe(conn, "speaking", Target(f"session-{row['id']}", [comp], tcf, t.level),
                         "incorrect", c["original"], c["corrected"], hinted=False)
    if fb["criteria"]["task"]["high"] <= 2:
        weakness.observe(conn, "speaking", Target(f"session-{row['id']}", [t.competencies[0]], tcf, t.level),
                         "incorrect", "(task not fully done)", fb["criteria"]["task"]["comment"], hinted=False)
    st = fb["stats"]
    mostly_uncertain = st["turns"] and st["uncertain_turns"] / st["turns"] > 0.5
    weight = AI_WEIGHT / 2 if (fb["agreement"] == "low" or mostly_uncertain) else AI_WEIGHT
    flags = ["ai_scored"] + ([] if fb["agreement"] == "high" else ["low_agreement"]) + (["asr_uncertain"] if mostly_uncertain else [])
    score = fb["mean"] / 5
    verdict = "correct" if score >= 0.7 else "partial" if score >= 0.4 else "incorrect"
    conn.execute(
        """INSERT INTO attempt (item_id, content_ver, skill, competency, mode, context, context_id, response,
                                correct, score, hints_used, duration_ms, verdict, evidence_weight, flags)
           VALUES (?, ?, 'speaking', ?, ?, 'speaking', 'speaking', ?, ?, ?, 0, NULL, ?, ?, ?)""",
        (t.id, f"speaking@{PROMPT_VERSION}", t.competencies[0], row["mode"], json.dumps({"session": row["id"]}),
         1 if verdict == "correct" else 0, round(score, 3), verdict, weight, json.dumps(flags)))
    estimates.update(conn, ("speaking",))


def run(conn: sqlite3.Connection, sid: int) -> str:
    row = conn.execute("SELECT * FROM eo_session WHERE id = ?", (sid,)).fetchone()
    t = speaking.get_task(row["task_id"]) if row else None
    turns = json.loads(row["turns"]) if row else []
    if row is None or t is None or row["status"] != "ended" or not any(x["role"] == "learner" for x in turns):
        return "none"
    claimed = conn.execute("UPDATE eo_session SET feedback_status = 'running' WHERE id = ? "
                           "AND feedback_status IN ('pending', 'failed')", (sid,)).rowcount
    if not claimed:
        return "busy"
    try:
        a = clean(_ask(t, turns, True, 11), turns, len(t.targets))
        b = _ask(t, turns, False, 29)
    except (httpx.HTTPError, ValueError):
        conn.execute("UPDATE eo_session SET feedback_status = 'failed' WHERE id = ?", (sid,))
        return "failed"
    fb = combine(t, a, b, stats(turns))
    with db.transaction(conn):
        conn.execute("""UPDATE eo_session SET feedback = ?, feedback_status = 'done', feedback_model = ?, prompt_version = ?,
                          agreement = ? WHERE id = ?""",
                     (json.dumps(fb, ensure_ascii=False), ai.MODEL, PROMPT_VERSION, fb["agreement"], sid))
        record_evidence(conn, row, t, fb)
    return "done"
