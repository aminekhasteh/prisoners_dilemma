"""Append higher-effort variants to the tournament strategy files (run after combine.py and the memory-3 export).

Each variant has one run per memory (memory-1 in the SI wording, memory-2 and memory-3 in the CL wording), so its
memory-1 player and its memory-2/3 players come from different wordings: do not use this variant for a memory-depth
comparison. It is also appended to the by-wording files under its real wording.
  python add_effort_variants.py
"""
import csv
from pathlib import Path

from combine import counts, wording_rows
from estimate import label

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "article2_llm_field"
VARIANTS = {"claude-sonnet-5-5-xhigh": ("Claude Sonnet 5.5 (effort xhigh)", {
    "memory1": "claude-sonnet-5-5_si_effort-xhigh", "memory2": "claude-sonnet-5-5_clean_effort-xhigh_m2",
    "memory3": "claude-sonnet-5-5_clean_effort-xhigh_m3"})}


def append(path, rows, model):
    old = list(csv.DictReader(open(path)))
    old = [r for r in old if r["model"] != model]
    fields = list(old[0])
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(old)
        w.writerows({k: r.get(k, "") for k in fields} for r in rows)


for model, (lab, tags) in VARIANTS.items():
    c1 = counts(tags["memory1"])
    keys = [("memory1", "round1", "", "")] + [("memory1", "later", "", o) for o in ("CC", "CD", "DC", "DD")]
    v = tuple(c1[k][0] / c1[k][1] for k in keys)
    append(OUT / "new_llm_memory1.csv", [{"model": model, "label": lab, **{c: f"{x:.2f}" for c, x in
            zip(["p0", "CC", "CD", "DC", "DD"], v)}, "n": min(c1[k][1] for k in keys), "note": label(v),
            "max_wording_gap": "nan", "wordings": "si",
            "player_type": "single wording (si)"}], model)
    c2 = counts(tags["memory2"])
    append(OUT / "new_llm_memory2.csv", [{"model": model, "scenario": k[1], "prev2": k[2], "prev1": k[3],
            "count_C": a, "n": n, "p_C": round(a / n, 4)} for k, (a, n) in sorted(c2.items())], model)
    r1, _ = wording_rows(model, lab, "si", tags["memory1"], c1)
    append(OUT / "new_llm_memory1_by_wording.csv", [r1], model)
    _, r2 = wording_rows(model, lab, "clean", tags["memory2"], c2)
    append(OUT / "new_llm_memory2_by_wording.csv", r2, model)
    rows3 = list(csv.DictReader(open(HERE / "results" / f"{tags['memory3']}_memory3.csv")))
    for r in rows3:
        r["model"] = model
    append(OUT / "new_llm_memory3.csv", rows3, model)
    print(model, "memory-1", v, "| memory-2 rows", len(c2), "| memory-3 rows", len(rows3))
