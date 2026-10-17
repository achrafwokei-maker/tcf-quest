"""Spread keyed answers across positions in reserved sets (deterministic: item k gets its answer at
position k mod 4). Options are relabelled a–d; explanations refer to text, not letters, so they stay valid.
Only for sets nobody has taken yet. Usage: python3 scripts/content/rebalance.py trial-1 trial-2 diagnostic-1"""
import json, sys
from pathlib import Path

SETS = Path(__file__).resolve().parents[2] / "content" / "sets"
for sid in sys.argv[1:]:
    p = SETS / f"{sid}.json"
    d = json.loads(p.read_text())
    k = 0
    for it in d["items"]:
        if it.get("type") not in ("select", "listen") or len(it["options"]) != 4:
            continue
        right = next(o for o in it["options"] if o["id"] == it["answer"])
        others = [o for o in it["options"] if o is not right]
        order = others[:]
        order.insert(k % 4, right)
        for letter, o in zip("abcd", order):
            o["id"] = letter
        it["options"], it["answer"] = order, "abcd"[k % 4]
        k += 1
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2))
    print(sid, k, "items rebalanced")
