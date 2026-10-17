"""Rubric-bound writing feedback from the local model (Ollama + Qwen3). Unofficial estimates only.

Safeguards:
- the model fills a fixed JSON schema (criteria 0–5, corrections, strengths, priorities, a
  revised version, a CEFR band) that is validated; invalid output is retried once, then fails;
- double scoring: two independent runs; per-criterion difference > 1 → "low" agreement, the
  learner sees a range and the evidence weighs half as much;
- a correction is kept only if its "original" text really appears in the learner's text, and only
  known categories can feed the weakness model (the AI never invents a weakness category);
- Ollama off or failing → the submission stays saved with feedback "failed" and can be retried.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import unicodedata
from typing import Literal

import httpx
from pydantic import BaseModel, Field, ValidationError

from . import ai, db, writing

PROMPT_VERSION = "ee-rubric-v3"
TIMEOUT_S = float(os.environ.get("TCFQUEST_AI_TIMEOUT", "240"))
CRITERIA = ("task", "coherence", "vocabulary", "grammar", "register")
CRITERION_LABEL = {
    "task": "Réalisation de la tâche", "coherence": "Cohérence et organisation", "vocabulary": "Lexique",
    "grammar": "Grammaire", "register": "Registre et adaptation au destinataire",
}
CATEGORIES = {
    "accord": "gram.accord", "conjugaison": "gram.conjugaison", "temps": "gram.temps-du-passe",
    "mode": "gram.subjonctif-conditionnel", "pronoms": "gram.pronoms", "prepositions": "gram.prepositions",
    "determinants": "gram.determinants", "syntaxe": "gram.syntaxe", "orthographe": "orth.orthographe",
    "accents": "orth.accents", "ponctuation": "orth.ponctuation", "vocabulaire": "vocab.precision",
    "registre": "ee.registre", "connecteurs": "ee.connecteurs",
}
Category = Literal["accord", "conjugaison", "temps", "mode", "pronoms", "prepositions", "determinants", "syntaxe",
                   "orthographe", "accents", "ponctuation", "vocabulaire", "registre", "connecteurs", "autre"]
CEFRBand = Literal["A1", "A2", "B1", "B2", "C1", "C2"]


class Correction(BaseModel):
    original: str = Field(min_length=1, max_length=200)
    corrected: str = Field(min_length=1, max_length=200)
    explanation: str = Field(min_length=3, max_length=300)
    category: Category
    kind: Literal["error", "style"] = "error"         # only errors feed the weakness model
    source: Literal["ai", "rule"] = "ai"


class Criterion(BaseModel):
    score: int = Field(ge=0, le=5)
    comment: str = Field(min_length=3, max_length=300)


class Scores(BaseModel):
    criteria: dict[Literal["task", "coherence", "vocabulary", "grammar", "register"], Criterion]


class Rubric(BaseModel):
    criteria: dict[Literal["task", "coherence", "vocabulary", "grammar", "register"], Criterion]
    corrections: list[Correction] = Field(max_length=10)
    strengths: list[str] = Field(min_length=1, max_length=3)
    priorities: list[str] = Field(min_length=1, max_length=3)
    revised_version: str = Field(min_length=20)
    cefr_estimate: CEFRBand


CRIT_SCHEMA = {"type": "object", "properties": {"score": {"type": "integer", "minimum": 0, "maximum": 5},
                                                "comment": {"type": "string"}}, "required": ["score", "comment"]}


def scores_schema() -> dict:
    return {"type": "object", "properties": {"criteria": {"type": "object", "properties": {c: CRIT_SCHEMA for c in CRITERIA},
                                                          "required": list(CRITERIA)}}, "required": ["criteria"]}


def schema() -> dict:
    crit = CRIT_SCHEMA
    return {
        "type": "object",
        "properties": {
            "criteria": {"type": "object", "properties": {c: crit for c in CRITERIA}, "required": list(CRITERIA)},
            "corrections": {"type": "array", "maxItems": 10, "items": {"type": "object", "properties": {
                "original": {"type": "string"}, "corrected": {"type": "string"}, "explanation": {"type": "string"},
                "category": {"type": "string", "enum": list(CATEGORIES) + ["autre"]},
                "kind": {"type": "string", "enum": ["error", "style"]}},
                "required": ["original", "corrected", "explanation", "category", "kind"]}},
            "strengths": {"type": "array", "items": {"type": "string"}},
            "priorities": {"type": "array", "items": {"type": "string"}},
            "revised_version": {"type": "string"},
            "cefr_estimate": {"type": "string", "enum": ["A1", "A2", "B1", "B2", "C1", "C2"]},
        },
        "required": ["criteria", "corrections", "strengths", "priorities", "revised_version", "cefr_estimate"],
    }


TASK_FOCUS = {
    "EE-T1": "un message (60–120 mots) : tous les points de la consigne traités, registre adapté au destinataire "
             "(tu/vous, formules d'appel et de fin), informations claires.",
    "EE-T2": "un compte rendu d'expérience ou un récit (120–150 mots) : récit chronologique au passé "
             "(passé composé / imparfait), commentaires ou opinions, but de la consigne atteint (conseiller, convaincre…).",
    "EE-T3": "une comparaison de deux points de vue (120–180 mots) : les deux documents reformulés (pas copiés), "
             "comparés avec des connecteurs, puis une opinion personnelle justifiée.",
}


def build_messages(task: writing.WritingTask, text: str, words: int) -> list[dict]:
    r = writing.word_ranges()[task.task]
    docs = "".join(f"\n{d.title} : {d.text}" for d in task.documents)
    system = (
        "Tu es un correcteur expérimenté du TCF Canada (expression écrite). Tu évalues un texte d'entraînement "
        "avec la grille ci-dessous. Tu es exigeant, précis et bienveillant. Réponds uniquement en JSON.\n"
        "Grille (0 à 5 par critère) : 0 = absent ou incompréhensible, 1 = A1, 2 = A2, 3 = B1, 4 = B2, 5 = C1/C2.\n"
        "- task : la consigne est-elle entièrement réalisée (tous les points, destinataire, but) ?\n"
        "- coherence : organisation, paragraphes, connecteurs, progression logique.\n"
        "- vocabulary : étendue et précision du lexique.\n"
        "- grammar : correction des formes (accords, conjugaisons, temps, syntaxe, orthographe).\n"
        "- register : adaptation au destinataire et au type de texte.\n"
        "Corrections : relis le texte mot par mot. Signale d'abord TOUTES les erreurs (kind = error) : accents "
        "(a/à, ou/où), élisions (si il → s'il), accords, conjugaisons, temps, prépositions, déterminants, orthographe. "
        "Ensuite seulement, au plus 3 suggestions de style (kind = style) pour des formes correctes mais améliorables. "
        "« original » est l'extrait EXACT et COURT (1 à 6 mots) qui contient le problème, copié du texte ; "
        "« corrected » remplace seulement cet extrait. Maximum 10 corrections, sans doublon. "
        "« explanation » et « comment » sont rédigés en ANGLAIS simple ; "
        "« strengths » et « priorities » en anglais, une phrase chacune ; « revised_version » est le texte de "
        "l'apprenant amélioré en français, mêmes idées, longueur dans la fourchette demandée ; « cefr_estimate » "
        "est une estimation du niveau du texte. Ne note pas la longueur : elle est vérifiée par l'application."
    )
    user = (f"Tâche : {task.task} — {TASK_FOCUS[task.task]}\nConsigne : {task.prompt}\nDestinataire : {task.recipient}"
            f"{docs}\nFourchette : {r['min']}–{r['max']} mots (le texte en compte {words}).\n\n"
            f"Texte de l'apprenant :\n<<<\n{text}\n>>>\n\n"
            "Do not flag gender agreement (désolé/désolée, content/contente…) when the writer's gender is unknown. "
            "Write every « comment », « explanation », « strengths » and « priorities » in ENGLISH. Keep French only in "
            "« original », « corrected » and « revised_version ».")
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s).replace("’", "'").lower()
    return re.sub(r"\s+", " ", s).strip()


# Deterministic checks for frequent slips (rules decide; the AI explains the rest).
RULES = [
    (r"\b([Ss])i (il|ils)\b", lambda m: f"{m[1]}'{m[2]}", "orthographe", "Elision: « si » + il(s) becomes « s'il(s) »."),
    (r"(?<!parce )\b([Qq])ue (il|ils|elle|elles|on)\b", lambda m: f"{m[1]}u'{m[2]}", "orthographe", "Elision: « que » before a vowel becomes « qu' »."),
    (r"\b([Pp])arce que (il|ils|elle|elles|on)\b", lambda m: f"{m[1]}arce qu'{m[2]}", "orthographe", "Elision: « parce que » before a vowel becomes « parce qu' »."),
    (r"\b([Jj])e ((?:[aeiouyéèêâîô]|hab|hés|hon)\w*)", lambda m: f"{m[1]}'{m[2]}", "orthographe", "Elision: « je » before a vowel or mute h becomes « j' »."),
    (r"\b([Cc])e est\b", lambda m: f"{m[1]}'est", "orthographe", "Elision: « ce est » becomes « c'est »."),
    (r"\b(a) (\d{1,2} ?h|\d{1,2} heures?|midi|minuit)\b", lambda m: f"à {m[2]}", "accents", "Preposition « à » (with an accent) before a time; « a » is the verb avoir."),
]


def rule_corrections(text: str) -> list[Correction]:
    out = []
    for pattern, fix, category, why in RULES:
        for m in re.finditer(pattern, text):
            out.append(Correction(original=m[0], corrected=fix(m), explanation=why, category=category,
                                  kind="error", source="rule"))
    return out


def gender_only(original: str, corrected: str) -> bool:
    """True when the 'correction' only adds a gender marker like (e), (es), ·e: the writer's gender is unknown."""
    stripped = re.sub(r"\((?:e|es|s|ne|le)\)|·(?:e|es)", "", corrected)
    return _norm(stripped) == _norm(original)


def narrow(c: Correction) -> Correction:
    """Shrink a whole-sentence correction to the words that changed (plus one word of context),
    so the learner sees the real mistake and it can be matched against their text."""
    import difflib
    a, b = c.original.split(), c.corrected.split()
    if len(a) <= 6:
        return c
    ops = [op for op in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes() if op[0] != "equal"]
    if not ops:
        return c
    i1, i2 = max(0, ops[0][1] - 1), min(len(a), ops[-1][2] + 1)
    j1, j2 = max(0, ops[0][3] - 1), min(len(b), ops[-1][4] + 1)
    return c.model_copy(update={"original": " ".join(a[i1:i2]), "corrected": " ".join(b[j1:j2])})


def clean(r: Rubric, text: str) -> Rubric:
    """Keep corrections that quote a short span of the learner's text, change something, and aren't
    duplicates; add the deterministic rule findings first."""
    t = _norm(text)
    kept, seen = [], set()
    for c in rule_corrections(text) + [narrow(x) for x in r.corrections]:
        o = _norm(c.original).strip(" ?!.,;:")
        key = (o, _norm(c.corrected).strip(" ?!.,;:"))
        if o not in t or o == key[1] or key in seen or len(o.split()) > 8 or gender_only(c.original, c.corrected):
            continue
        if any(o in s[0] or s[0] in o for s in seen if c.source == "ai"):   # same spot already corrected
            continue
        seen.add(key)
        kept.append(c)
    return r.model_copy(update={"corrections": kept[:12]})


def _ask(task: writing.WritingTask, text: str, words: int, seed: int, model_cls, fmt: dict, extra: str = ""):
    last_error: Exception | None = None
    messages = build_messages(task, text, words)
    if extra:
        messages[-1] = {**messages[-1], "content": messages[-1]["content"] + "\n\n" + extra}
    for attempt in range(2):                                   # one retry on invalid output
        payload = {"model": ai.MODEL, "stream": False, "think": False, "format": fmt,
                   "options": {"temperature": 0.3, "seed": seed + attempt, "num_ctx": 8192},
                   "messages": messages}
        r = httpx.post(f"{ai.OLLAMA_URL}/api/chat", json=payload, timeout=TIMEOUT_S)
        r.raise_for_status()
        try:
            return model_cls.model_validate_json(r.json()["message"]["content"])
        except (ValidationError, KeyError, ValueError) as e:
            last_error = e
    raise ValueError(f"invalid rubric output: {last_error}")


def score_once(task: writing.WritingTask, text: str, words: int, seed: int) -> Rubric:
    return clean(_ask(task, text, words, seed, Rubric, schema()), text)


def score_criteria(task: writing.WritingTask, text: str, words: int, seed: int) -> Scores:
    """Second, independent scoring of the criteria only (faster; used for the agreement check)."""
    return _ask(task, text, words, seed, Scores, scores_schema(),
                "Pour cette deuxième lecture, donne uniquement les notes des cinq critères avec un commentaire court.")


def combine(a: Rubric, b: Scores) -> dict:
    """Merge two independent scorings. Low agreement → ranges, half evidence weight."""
    criteria, agree = {}, True
    for c in CRITERIA:
        sa, sb = a.criteria[c].score, b.criteria[c].score
        agree &= abs(sa - sb) <= 1
        criteria[c] = {"label": CRITERION_LABEL[c], "score": (sa + sb) / 2, "low": min(sa, sb), "high": max(sa, sb),
                       "comment": a.criteria[c].comment}
    mean = sum(v["score"] for v in criteria.values()) / len(CRITERIA)
    return {
        "criteria": criteria, "mean": round(mean, 2), "agreement": "high" if agree else "low",
        "corrections": [c.model_dump() for c in a.corrections],
        "strengths": a.strengths, "priorities": a.priorities, "revised_version": a.revised_version,
        "cefr_estimate": a.cefr_estimate,
        "label": "Unofficial practice estimate from a local AI. Not a TCF score.",
    }


def run(conn: sqlite3.Connection, sid: int) -> str:
    """Score a submitted text; store the result. Returns the new feedback_status."""
    row = conn.execute("SELECT * FROM writing_submission WHERE id = ?", (sid,)).fetchone()
    task = writing.get_task(row["task_id"]) if row else None
    if row is None or task is None or row["status"] != "submitted" or not row["text"].strip():
        return "none"
    # Claim the job atomically: a second scheduler call (e.g. exam timeout + submit) does nothing.
    claimed = conn.execute("UPDATE writing_submission SET feedback_status = 'running' WHERE id = ? "
                           "AND feedback_status IN ('pending', 'failed')", (sid,)).rowcount
    if not claimed:
        return "busy"
    try:
        a = score_once(task, row["text"], row["word_count"], seed=11)
        b = score_criteria(task, row["text"], row["word_count"], seed=29)
    except (httpx.HTTPError, ValueError):
        conn.execute("UPDATE writing_submission SET feedback_status = 'failed' WHERE id = ?", (sid,))
        conn.commit()
        return "failed"
    fb = combine(a, b)
    from . import writing_evidence                              # weaknesses + writing estimate
    with db.transaction(conn):
        conn.execute("""UPDATE writing_submission SET feedback = ?, feedback_status = 'done', feedback_model = ?,
                          prompt_version = ?, agreement = ? WHERE id = ?""",
                     (json.dumps(fb, ensure_ascii=False), ai.MODEL, PROMPT_VERSION, fb["agreement"], sid))
        writing_evidence.record(conn, row, task, fb)
    return "done"
