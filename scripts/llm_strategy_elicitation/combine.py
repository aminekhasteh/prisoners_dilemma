"""Pool the two prompt wordings of each model into one memory-1 and one memory-2 strategy for the tournament.

For each model, the counts of the `clean` and `si` runs are added (100 trials per scenario), so the strategy is the
model's average behaviour over the two wordings. Writes, in ../article2_llm_field/:

  new_llm_memory1.csv   model, label, p0, CC, CD, DC, DD, n, note, max_wording_gap  (own move first)
  new_llm_memory2.csv   same columns as pal2026_memory2.csv (model, scenario, prev2, prev1, count_C, n, p_C)

and a per-wording table results/wording_comparison.csv with Fisher tests of clean vs si for every scenario.

  python combine.py
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from scipy.stats import fisher_exact

from estimate import label, wilson

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "article2_llm_field"
MODELS = {  # tag prefix -> display label used in the tournament
    "claude-opus-5-5": "Claude Opus 5.5",
    "claude-sonnet-5-5": "Claude Sonnet 5.5",
    "claude-haiku-5-5": "Claude Haiku 5.5",
    "gpt-6.1-sol": "GPT-6.1 Sol",
    "gpt-6.1-terra": "GPT-6.1 Terra",
    "gpt-6-luna": "GPT-6 Luna",
}
WORDINGS = ("clean", "si")


def counts(tag):
    """{(experiment, kind, prev2, prev1): [count_C, n]} from the first valid answer of each trial."""
    out, seen = defaultdict(lambda: [0, 0]), set()
    for line in (HERE / "results" / "raw" / f"{tag}.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r["choice"] is None or (r["key"], r["trial"]) in seen:
            continue
        seen.add((r["key"], r["trial"]))
        c = out[(r["experiment"], r["kind"], r["prev2"], r["prev1"])]
        c[0] += r["choice"] == "C"
        c[1] += 1
    return out


def main():
    m1_rows, m2_rows, cmp_rows = [], [], []
    for model, lab in MODELS.items():
        per = {w: counts(f"{model}_{w}") for w in WORDINGS}
        keys = sorted(set(per["clean"]) | set(per["si"]))
        pooled = {k: [sum(per[w][k][0] for w in WORDINGS), sum(per[w][k][1] for w in WORDINGS)] for k in keys}
        gaps = []
        for k in keys:
            (a, na), (b, nb) = per["clean"][k], per["si"][k]
            p = fisher_exact([[a, na - a], [b, nb - b]])[1]
            gaps.append(abs(a / na - b / nb))
            cmp_rows.append({"model": model, "experiment": k[0], "kind": k[1], "prev2": k[2], "prev1": k[3],
                             "clean": f"{a}/{na}", "si": f"{b}/{nb}", "diff": round(a / na - b / nb, 3),
                             "fisher_p": round(p, 4)})
        m1 = [("memory1", "round1", "", "")] + [("memory1", "later", "", o) for o in ("CC", "CD", "DC", "DD")]
        v = tuple(pooled[k][0] / pooled[k][1] for k in m1)
        m1_gap = max(abs(per["clean"][k][0] / per["clean"][k][1] - per["si"][k][0] / per["si"][k][1]) for k in m1)
        m1_rows.append({"model": model, "label": lab, **{c: f"{x:.2f}" for c, x in zip(["p0", "CC", "CD", "DC", "DD"], v)},
                        "n": min(pooled[k][1] for k in m1), "note": label(v), "max_wording_gap": f"{m1_gap:.2f}"})
        for k in keys:
            if k[0] != "memory2":
                continue
            c, n = pooled[k]
            m2_rows.append({"model": model, "scenario": k[1], "prev2": k[2], "prev1": k[3], "count_C": c, "n": n,
                            "p_C": round(c / n, 4)})
        n_sig = sum(r["fisher_p"] < 0.05 for r in cmp_rows if r["model"] == model)
        print(f"{lab:18s} p0 {v[0]:.2f} CC {v[1]:.2f} CD {v[2]:.2f} DC {v[3]:.2f} DD {v[4]:.2f}  {label(v):10s} "
              f"wordings differ in {n_sig} of {len(keys)} scenarios (p<0.05), largest gap {max(gaps):.2f}")

    order = {"round1": 0, "round2": 1, "later": 2}
    m2_rows.sort(key=lambda r: (list(MODELS).index(r["model"]), order[r["scenario"]], r["prev1"], r["prev2"]))
    for path, rows in [(OUT / "new_llm_memory1.csv", m1_rows), (OUT / "new_llm_memory2.csv", m2_rows),
                       (HERE / "results" / "wording_comparison.csv", cmp_rows)]:
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print("wrote", path)


if __name__ == "__main__":
    main()
