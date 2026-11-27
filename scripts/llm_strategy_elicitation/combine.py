"""Turn the saved replies into tournament strategies: pooled players (an extension) and wording-specific players.

Pooled players (an extension of Pal et al., not a single prompt). For each model, the counts of the `clean` and `si`
runs are added (100 trials per scenario), so the strategy is the model's average behaviour over the two wordings.
The pooled vector can sit far from both wordings: Llama 3.3 70B cooperates after DC with probability 0.04 in the
clean wording, 0.88 in the SI wording, and 0.46 pooled. In memory-2 the two prompts also give different game
information (the clean prompt corrects the SI's misprinted opponent payoff for the previous round), so a pooled
memory-2 player mixes two games. Use the pooled players only as an explicitly labeled robustness extension.

Wording-specific players are for comparisons. A claim about memory depth should compare clean memory-1, clean
memory-2 and clean memory-3 (new_llm_memory3.csv is clean only) in the same field: run_wording_field.py does that.

Writes, in ../article2_llm_field/:

  new_llm_memory1.csv             pooled: model, label, p0, CC, CD, DC, DD, n, note, max_wording_gap, wordings,
                                  player_type  (own move first)
  new_llm_memory2.csv             pooled: same columns as pal2026_memory2.csv (model, scenario, prev2, prev1, count_C,
                                  n, p_C)
  new_llm_memory1_by_wording.csv  one row per model and wording: model, wording, tag, label, p0..DD, n, note
  new_llm_memory2_by_wording.csv  one row per model, wording and scenario: model, wording, tag, scenario, prev2,
                                  prev1, count_C, n, p_C

and a per-wording table results/wording_comparison.csv with Fisher tests of clean vs si for every scenario (the
p-values are per scenario and unadjusted). Run add_effort_variants.py afterwards: it appends the effort variants to
the pooled files and to the by-wording files.

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
# model id -> (display label used in the tournament, {wording: run tag}). The model ids of the reruns differ from
# Pal et al.'s ("llama-3.3-70b", "gemini-2.5-pro") so both versions can be loaded into the same field.
MODELS = {m: (lab, {"clean": f"{m}_clean", "si": f"{m}_si"}) for m, lab in [
    ("claude-opus-5-5", "Claude Opus 5.5"),
    ("claude-sonnet-5-5", "Claude Sonnet 5.5"),
    ("claude-haiku-5-5", "Claude Haiku 5.5"),
    ("gpt-6.1-sol", "GPT-6.1 Sol"),
    ("gpt-6.1-terra", "GPT-6.1 Terra"),
    ("gpt-6-luna", "GPT-6 Luna"),
]}
# Paper settings (temperature 0, top_p 1e-8), OpenRouter's default host routing, both wordings.
MODELS["llama-3.3-70b-rerun"] = ("Llama 3.3 70B (2026 rerun)", {"clean": "llama-3.3-70b", "si": "llama-3.3-70b_si"})
# Memory-1 only (memory-2 was not run), paper wording only.
MODELS["gemini-2.5-pro-rerun"] = ("Gemini 2.5 Pro (2026 rerun)", {"si": "gemini-2.5-pro_si"})


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


POOLED = "pooled clean+si (extension)"
M1_KEYS = [("memory1", "round1", "", "")] + [("memory1", "later", "", o) for o in ("CC", "CD", "DC", "DD")]


def wording_rows(model, lab, wording, tag, c):
    """By-wording memory-1 row (or None if the run has no memory-1) and memory-2 rows for one run's counts c."""
    m1 = None
    if all(k in c for k in M1_KEYS):
        v = tuple(c[k][0] / c[k][1] for k in M1_KEYS)
        m1 = {"model": model, "wording": wording, "tag": tag, "label": f"{lab} [{wording}]",
              **{n: f"{x:.2f}" for n, x in zip(["p0", "CC", "CD", "DC", "DD"], v)},
              "n": min(c[k][1] for k in M1_KEYS), "note": label(v)}
    m2 = [{"model": model, "wording": wording, "tag": tag, "scenario": k[1], "prev2": k[2], "prev1": k[3],
           "count_C": a, "n": n, "p_C": round(a / n, 4)} for k, (a, n) in c.items() if k[0] == "memory2"]
    return m1, m2


ORDER = {"round1": 0, "round2": 1, "later": 2}


def sort_m2(rows, models):
    rows.sort(key=lambda r: (models.index(r["model"]), r.get("wording", ""), ORDER[r["scenario"]], r["prev1"],
                             r["prev2"]))


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("wrote", path)


def main():
    m1_rows, m2_rows, cmp_rows = [], [], []
    w1_rows, w2_rows = [], []
    for model, (lab, tags) in MODELS.items():
        per = {w: counts(t) for w, t in tags.items()}
        for w, c in per.items():
            r1, r2 = wording_rows(model, lab, w, tags[w], c)
            w1_rows += [r1] if r1 else []
            w2_rows += r2
        keys = sorted(set().union(*per.values()))
        pooled = {k: [sum(per[w][k][0] for w in per), sum(per[w][k][1] for w in per)] for k in keys}
        gaps = []
        for k in keys:
            if len(per) < 2:
                continue
            (a, na), (b, nb) = per["clean"][k], per["si"][k]
            p = fisher_exact([[a, na - a], [b, nb - b]])[1]
            gaps.append(abs(a / na - b / nb))
            cmp_rows.append({"model": model, "experiment": k[0], "kind": k[1], "prev2": k[2], "prev1": k[3],
                             "clean": f"{a}/{na}", "si": f"{b}/{nb}", "diff": round(a / na - b / nb, 3),
                             "fisher_p": round(p, 4)})
        m1 = [("memory1", "round1", "", "")] + [("memory1", "later", "", o) for o in ("CC", "CD", "DC", "DD")]
        v = tuple(pooled[k][0] / pooled[k][1] for k in m1)
        m1_gap = max(abs(per["clean"][k][0] / per["clean"][k][1] - per["si"][k][0] / per["si"][k][1])
                     for k in m1) if len(per) == 2 else float("nan")
        m1_rows.append({"model": model, "label": lab, **{c: f"{x:.2f}" for c, x in zip(["p0", "CC", "CD", "DC", "DD"], v)},
                        "n": min(pooled[k][1] for k in m1), "note": label(v), "max_wording_gap": f"{m1_gap:.2f}",
                        "wordings": "+".join(per),
                        "player_type": POOLED if len(per) > 1 else f"single wording ({next(iter(per))})"})
        for k in keys:
            if k[0] != "memory2":
                continue
            c, n = pooled[k]
            m2_rows.append({"model": model, "scenario": k[1], "prev2": k[2], "prev1": k[3], "count_C": c, "n": n,
                            "p_C": round(c / n, 4)})
        n_sig = sum(r["fisher_p"] < 0.05 for r in cmp_rows if r["model"] == model)
        print(f"{lab:28s} p0 {v[0]:.2f} CC {v[1]:.2f} CD {v[2]:.2f} DC {v[3]:.2f} DD {v[4]:.2f}  {label(v):10s} "
              + (f"pooled; wordings differ in {n_sig} of {len(keys)} scenarios (p<0.05, unadjusted), largest gap "
                 f"{max(gaps):.2f}" if gaps else "one wording only"))
        for w in per:
            r = next((x for x in w1_rows if x["model"] == model and x["wording"] == w), None)
            if r and len(per) > 1:
                print(f"  {w:5s} {'':20s} p0 {r['p0']} CC {r['CC']} CD {r['CD']} DC {r['DC']} DD {r['DD']}  {r['note']}")

    models = list(MODELS)
    sort_m2(m2_rows, models)
    sort_m2(w2_rows, models)
    for path, rows in [(OUT / "new_llm_memory1.csv", m1_rows), (OUT / "new_llm_memory2.csv", m2_rows),
                       (OUT / "new_llm_memory1_by_wording.csv", w1_rows),
                       (OUT / "new_llm_memory2_by_wording.csv", w2_rows),
                       (HERE / "results" / "wording_comparison.csv", cmp_rows)]:
        write_csv(path, rows)


if __name__ == "__main__":
    main()
