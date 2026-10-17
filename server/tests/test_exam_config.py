"""Consistency checks for the versioned exam configs in content/exam (milestone 0)."""

import json
from pathlib import Path

EXAM_DIR = Path(__file__).resolve().parents[2] / "content" / "exam"


def load(name: str) -> dict:
    return json.loads((EXAM_DIR / name).read_text())


def test_tcf_canada_sections_add_up():
    cfg = load("tcf-canada.v1.json")
    sections = {s["id"]: s for s in cfg["sections"]}
    assert set(sections) == {"CO", "CE", "EE", "EO"}  # no 'structures de la langue' in TCF Canada
    assert all(s["compulsory"] for s in sections.values())
    assert sum(s["minutes"] for s in sections.values()) == cfg["total_minutes"] == 167
    assert sections["CO"]["items"] == sections["CE"]["items"] == 39
    assert sections["CO"]["audio_plays"] == 1


def test_speaking_tasks_fill_twelve_minutes():
    eo = next(s for s in load("tcf-canada.v1.json")["sections"] if s["id"] == "EO")
    assert sum(t["minutes"] for t in eo["tasks"]) == eo["minutes"] == 12
    assert [t["preparation_minutes"] for t in eo["tasks"]] == [0, 2, 0]


def test_writing_word_counts():
    ee = next(s for s in load("tcf-canada.v1.json")["sections"] if s["id"] == "EE")
    words = {t["id"]: (t["words"]["min"], t["words"]["max"]) for t in ee["tasks"]}
    assert words == {"EE-T1": (60, 120), "EE-T2": (120, 150), "EE-T3": (120, 180)}


def test_nclc_bands_are_contiguous_and_ordered():
    levels = load("ircc-tcf-nclc.v1.json")["levels"]
    assert [lvl["nclc"] for lvl in levels] == [10, 9, 8, 7, 6, 5, 4]
    for skill in ("speaking", "listening", "reading", "writing"):
        bands = [lvl[skill] for lvl in reversed(levels)]  # NCLC 4 → 10
        for lo, hi in bands:
            assert lo <= hi
        for (_, prev_hi), (next_lo, _) in zip(bands, bands[1:]):
            assert next_lo == prev_hi + 1, f"gap or overlap in {skill}"
    top = levels[0]
    assert top["listening"][1] == top["reading"][1] == 699
    assert top["speaking"][1] == top["writing"][1] == 20
