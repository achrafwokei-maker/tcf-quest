"""Helpers to author reserved question sets compactly. The right answer is placed at position k mod 4,
so keys are evenly spread. Each entry: (level, competency, question, stimulus, speaker_or_None, (right, why), [(wrong, why) x3])."""
import json
from pathlib import Path

SETS = Path(__file__).resolve().parents[2] / "content" / "sets"
PURPOSE = {"CO": "Unseen listening item (TCF format: one play, four answers).",
           "CE": "Unseen reading item (TCF format: document, question, four answers)."}


def build(set_id, title, level, entries, purpose, context="exam"):
    items, k = [], {"CO": 0, "CE": 0}
    for n, (sec, (lvl, comp, q, stim, speaker, right, wrongs)) in enumerate(entries):
        pos = k[sec] % 4
        k[sec] += 1
        opts = [{"text": t, "explanation": e} for t, e in wrongs]
        opts.insert(pos, {"text": right[0], "explanation": right[1] if right[1].startswith("Yes") else "Yes: " + right[1]})
        for letter, o in zip("abcd", opts):
            o["id"] = letter
        it = {"id": f"{set_id}-{sec.lower()}-{n:02d}", "type": "listen" if sec == "CO" else "select", "pool": "assessment",
              "level": lvl, "tcf_target": {"section": sec, "purpose": PURPOSE[sec]}, "competencies": [comp, f"{sec.lower()}.tcf"],
              "instructions": "Écoutez le document et répondez à la question." if sec == "CO" else "Lisez le document et répondez à la question.",
              "question": q, "options": opts, "answer": "abcd"[pos]}
        if sec == "CO":
            it["audio"] = {"text": stim, "speaker": speaker or "Narratrice"}
        else:
            it["passage"] = stim
        items.append(it)
    d = {"id": set_id, "version": 1, "title": title, "review_status": "reviewed", "level": level, "context": context,
         "tcf_target": {"section": "CO", "purpose": purpose}, "items": items}
    (SETS / f"{set_id}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2))
    return len(items)
