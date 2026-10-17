"""Question-bank quality control (run by the tests and by `python -m tcfquest.content_qc`).

Checks that keyed content is fair and auditable:
- keyed answers are spread across positions (no letter > 45 % in a set of 8+ questions);
- the explanation of the right option starts with "Yes" (the key and its justification agree);
- reserved (assessment) choice questions have exactly 4 options, like the TCF;
- no duplicated question text with the same passage/audio across the bank;
- counts per section, level and pool, so gaps are visible.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from . import content

MAX_SHARE = 0.45


def issues() -> list[str]:
    out = []
    seen: dict[tuple, str] = {}
    for s in content.all_sets().values():
        choices = [i for i in content.scored(s.items) if isinstance(i, content.ChoiceItem)]
        keyed = [i for i in choices if not i.prompt_line]               # guided-call items keep their story order
        if len(keyed) >= 8 and s.context in ("exam", "academy", "toolbox", "practice"):
            pos = Counter([o.id for o in i.options].index(i.answer) for i in keyed)
            letter, n = pos.most_common(1)[0]
            if n / len(keyed) > MAX_SHARE:
                out.append(f"{s.id}: {round(100 * n / len(keyed))} % of answers in position {letter + 1}")
        for i in choices:
            right = next(o for o in i.options if o.id == i.answer)
            if s.context in ("exam", "academy", "toolbox") and not right.explanation.lower().startswith("yes"):
                out.append(f"{s.id}/{i.id}: the right option's explanation doesn't start with 'Yes'")
            if i.pool == "assessment" and len(i.options) != 4:
                out.append(f"{s.id}/{i.id}: reserved questions need 4 options")
            key = (i.question.strip().lower(), (i.passage or (i.audio.text if i.audio else "")).strip().lower(),
                   (i.prompt_line.text if i.prompt_line else ""), tuple(sorted(o.text for o in i.options)))
            if key in seen and seen[key] != f"{s.id}/{i.id}":
                out.append(f"{s.id}/{i.id}: duplicates {seen[key]}")
            seen.setdefault(key, f"{s.id}/{i.id}")
    return out


def counts() -> dict:
    table: dict[str, Counter] = defaultdict(Counter)
    for s in content.all_sets().values():
        for i in content.scored(s.items):
            table[f"{i.tcf_target.section}/{i.pool}"][i.level] += 1
    return {k: dict(sorted(v.items())) | {"total": sum(v.values())} for k, v in sorted(table.items())}


if __name__ == "__main__":
    for k, v in counts().items():
        print(f"{k:16s} {v}")
    probs = issues()
    print(f"\n{len(probs)} issue(s)")
    for p in probs:
        print(" -", p)
