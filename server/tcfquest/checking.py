"""Deterministic answer checking (blueprint section E.2). Rules decide; AI is never involved here."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Literal

Verdict = Literal["correct", "partial", "incorrect"]

# Word pairs where the accent changes the word (a ≠ à). Missing these accents is a real error.
MEANINGFUL_ACCENTS = {
    "a": "à", "ou": "où", "du": "dû", "la": "là", "sur": "sûr", "mur": "mûr", "des": "dès",
    "tache": "tâche", "jeune": "jeûne", "cote": "côte", "pecher": "pêcher", "peche": "pêche",
    "mais": "maïs", "eut": "eût", "fut": "fût",
}
_ACCENT_WORDS = set(MEANINGFUL_ACCENTS) | set(MEANINGFUL_ACCENTS.values())


@dataclass
class Result:
    verdict: Verdict
    score: float                 # 1, 0.5 or 0
    note: str | None = None      # short teaching note shown with the verdict
    details: dict = field(default_factory=dict)


def normalize(text: str) -> str:
    """Case, apostrophe style, spacing and outer/inner punctuation do not matter."""
    t = unicodedata.normalize("NFC", text).lower()
    t = t.replace("’", "'").replace("ʼ", "'").replace(" ", " ").replace(" ", " ")
    t = re.sub(r"[.,;:!?«»\"“”()\[\]…]", " ", t)
    t = re.sub(r"\s*'\s*", "'", t)
    return re.sub(r"\s+", " ", t).strip()


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def _levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _common_prefix(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def check_typed(response: str, answers: list[str]) -> Result:
    """Type-the-missing-word items. `answers[0]` is the main answer, the rest are alternatives."""
    given = normalize(response)
    targets = [normalize(a) for a in answers]
    if not given:
        return Result("incorrect", 0, "No answer given.")
    if given in targets:
        return Result("correct", 1)

    # Same letters once accents are removed?
    for target in targets:
        if strip_accents(given) == strip_accents(target):
            g_words, t_words = given.split(), target.split()
            for gw, tw in zip(g_words, t_words):
                if gw != tw and (gw in _ACCENT_WORDS or tw in _ACCENT_WORDS):
                    return Result("incorrect", 0, f"« {gw} » and « {tw} » are different words: the accent changes the meaning.",
                                  {"contrast": [gw, tw]})
            return Result("correct", 1, f"Watch the accent: « {target} ».", {"accent": True})

    main = targets[0]
    # One-letter slip in a long word, not in the grammatical ending.
    if len(main) >= 7 and _levenshtein(given, main) == 1 and given[-2:] == main[-2:]:
        return Result("partial", 0.5, f"Almost: « {main} ». Check the spelling.", {"typo": True})

    # Right stem, wrong ending (agreement or conjugation).
    prefix = _common_prefix(strip_accents(given), strip_accents(main))
    if prefix >= 4 and prefix >= len(main) - 3 and abs(len(given) - len(main)) <= 3:
        return Result("partial", 0.5, f"Right word, wrong ending: « {main} ». Check agreement or conjugation.", {"ending": True})

    return Result("incorrect", 0)


def check_choice(response: str, answer: str) -> Result:
    return Result("correct", 1) if response == answer else Result("incorrect", 0)


def check_arrange(response: list[str], answers: list[list[str]]) -> Result:
    """Word-tile items. Tiles are compared without punctuation or case."""
    given = [normalize(t) for t in response]
    valid = [[normalize(t) for t in order] for order in answers]
    if given in valid:
        return Result("correct", 1)
    canonical = valid[0]
    if sorted(given) == sorted(canonical):
        wrong = [i for i, (g, c) in enumerate(zip(given, canonical)) if g != c]
        if len(wrong) == 2 and wrong[1] == wrong[0] + 1:
            return Result("partial", 0.5, "Almost: two words are swapped.", {"wrong_positions": wrong})
        return Result("incorrect", 0, None, {"wrong_positions": wrong})
    return Result("incorrect", 0, None, {"wrong_positions": [i for i, (g, c) in enumerate(zip(given, canonical)) if g != c]})


def check_multi(response: list[str], answers: list[str]) -> Result:
    """Checklist items: all right and nothing wrong = correct; mostly right = partial."""
    chosen, right = set(response or []), set(answers)
    hits, wrong = len(chosen & right), len(chosen - right)
    if hits == len(right) and wrong == 0:
        return Result("correct", 1)
    if hits * 2 >= len(right) and wrong <= 1:
        missed = len(right) - hits
        note = "Almost: " + ", ".join(p for p in (
            f"{missed} missing" if missed else "", f"{wrong} not needed" if wrong else "") if p) + "."
        return Result("partial", 0.5, note, {"missed": sorted(right - chosen), "extra": sorted(chosen - right)})
    return Result("incorrect", 0, None, {"missed": sorted(right - chosen), "extra": sorted(chosen - right)})
