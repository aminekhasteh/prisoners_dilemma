"""Turn a JSONL run into strategies, in the same CSV formats as ../article2_llm_field/pal2026_*.csv.

  python estimate.py fake_test                       # writes results/<tag>_memory1.csv and <tag>_memory2.csv
  python estimate.py gemini-2.5-pro --compare gemini-2.5-pro   # also compares with Pal et al.'s numbers

The first valid answer of each trial counts (re-asks after an invalid reply are the same trial).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

from scipy.stats import fisher_exact

HERE = Path(__file__).resolve().parent
PAL = HERE.parent / "article2_llm_field"

# Table S2 of the SI: (p0; CC, CD, DC, DD), own move first.
NAMED = {
    "ALLC": (1, 1, 1, 1, 1), "ALLD": (0, 0, 0, 0, 0), "TFT": (1, 1, 0, 1, 0), "WSLS": (1, 1, 0, 0, 1),
    "GRIM": (1, 1, 0, 0, 0), "Forgiver": (1, 1, 0, 1, 1),
}


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def label(v):
    """A named memory-1 strategy only when the vector is exactly that strategy's; otherwise '~' and the nearest name
    (e.g. Sonnet 5.5 effort xhigh, DD = 0.08, is ~GRIM, not GRIM). The simulator always uses the numbers, so this
    only affects reporting."""
    name, gap = min(((k, max(abs(a - b) for a, b in zip(v, s))) for k, s in NAMED.items()), key=lambda t: t[1])
    if name == "TFT" and v[2] > 0.1 and v[4] > 0.1 and gap > 0.1:
        return "~GTFT"
    return name if gap < 1e-9 else f"~{name}"


def holm(ps):
    """Holm-adjusted p-values for one family of tests (same order as ps)."""
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


def load(tag):
    counts = defaultdict(lambda: [0, 0])  # key -> [count_C, n]
    seen, meta, invalid, cost, thinking = set(), {}, 0, 0.0, []
    for line in (HERE / "results" / "raw" / f"{tag}.jsonl").read_text().splitlines():
        r = json.loads(line)
        cost += r["cost_usd"]
        if r.get("thinking_tokens"):
            thinking.append(r["thinking_tokens"])
        if r["choice"] is None:
            invalid += 1
            continue
        if (r["key"], r["trial"]) in seen:
            continue
        seen.add((r["key"], r["trial"]))
        c = counts[r["key"]]
        c[0] += r["choice"] == "C"
        c[1] += 1
        meta[r["key"]] = r
    return counts, meta, invalid, cost, thinking


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--model-name", help="name written in the 'model' column (default: the tag)")
    ap.add_argument("--compare", help="Pal et al. model name to compare with, e.g. gemini-2.5-pro")
    args = ap.parse_args()
    name = args.model_name or args.tag
    counts, meta, invalid, cost, thinking = load(args.tag)
    print(f"{args.tag}: {sum(n for _, n in counts.values())} valid trials, {invalid} invalid replies, ${cost:.4f}"
          + (f", median thinking tokens {sorted(thinking)[len(thinking)//2]}" if thinking else ""))

    # memory-1 style experiments -> one row per treatment
    rows, long = [], []
    groups = defaultdict(dict)
    for key, (k, n) in counts.items():
        r = meta[key]
        lo, hi = wilson(k, n)
        long.append({"model": name, "experiment": r["experiment"], "treatment": r["treatment"], "kind": r["kind"],
                     "prev3": r.get("prev3", ""), "prev2": r["prev2"], "prev1": r["prev1"], "count_C": k, "n": n, "p_C": round(k / n, 4),
                     "wilson_lo": round(lo, 4), "wilson_hi": round(hi, 4)})
        if r["experiment"] not in ("memory2", "memory3"):
            groups[(r["experiment"], r["treatment"])]["p0" if r["kind"] == "round1" else r["prev1"]] = k / n
    exp_map = {"memory1": "framing", "framing": "framing", "stopping": "stopping_w", "gains": "equal_gains_x"}
    for (exp, treat), g in sorted(groups.items()):
        if len(g) < 5:
            continue
        v = (g["p0"], g["CC"], g["CD"], g["DC"], g["DD"])
        value = {"memory1": "(no special instruction)"}.get(exp, treat.split("=")[-1])
        if exp == "framing":
            from prompts import FRAMINGS
            value = FRAMINGS[treat]
        rows.append({"table": "new", "treatment": exp_map[exp], "value": value, "model": name,
                     **{k: f"{x:.2f}" for k, x in zip(["p0", "CC", "CD", "DC", "DD"], v)}, "note": label(v)})

    res = HERE / "results"
    long.sort(key=lambda d: (d["experiment"], d["treatment"], d["kind"], d["prev3"], d["prev2"], d["prev1"]))
    with open(res / f"{args.tag}_scenarios.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(long[0]))
        w.writeheader()
        w.writerows(long)
    if rows:
        with open(res / f"{args.tag}_memory1.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        for r in rows:
            print(f"  {r['treatment']:14s} {r['value'][:40]:40s} p0 {r['p0']} CC {r['CC']} CD {r['CD']} "
                  f"DC {r['DC']} DD {r['DD']}  {r['note']}")
    m2 = [d for d in long if d["experiment"] == "memory2"]
    if m2:
        with open(res / f"{args.tag}_memory2.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["model", "scenario", "prev2", "prev1", "count_C", "n", "p_C"])
            w.writeheader()
            for d in m2:
                w.writerow({"model": name, "scenario": d["kind"], "prev2": d["prev2"], "prev1": d["prev1"],
                            "count_C": d["count_C"], "n": d["n"], "p_C": d["p_C"]})

    m3 = [d for d in long if d["experiment"] == "memory3"]
    if m3:
        with open(res / f"{args.tag}_memory3.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["model", "scenario", "prev3", "prev2", "prev1", "count_C", "n", "p_C"])
            w.writeheader()
            for d in m3:
                w.writerow({"model": name, "scenario": d["kind"], "prev3": d["prev3"], "prev2": d["prev2"],
                            "prev1": d["prev1"], "count_C": d["count_C"], "n": d["n"], "p_C": d["p_C"]})

    if args.compare:
        compare(args.compare, long)


def _pal_key(r):
    """Map one of our scenario rows to (Pal treatment, Pal value, kind, prev1)."""
    from prompts import FRAMINGS
    exp, treat = r["experiment"], r["treatment"]
    if exp == "memory1":
        return ("framing", "(no special instruction)", r["kind"], r["prev1"])
    if exp == "framing":
        return ("framing", FRAMINGS[treat], r["kind"], r["prev1"])
    if exp == "stopping":
        return ("stopping_w", treat.split("=")[1], r["kind"], r["prev1"])
    if exp == "gains":
        return ("equal_gains_x", treat.split("=")[1], r["kind"], r["prev1"])
    return None


def compare(pal_model, long):
    """Side by side with Pal et al. (memory-1 tables S12-S24, memory-2 table S11), with Fisher's exact test."""
    pal1, pal2 = {}, {}
    for r in csv.DictReader(open(PAL / "pal2026_memory1_treatments.csv")):
        if r["model"] == pal_model:
            for k in ["p0", "CC", "CD", "DC", "DD"]:
                kind, prev1 = ("round1", "") if k == "p0" else ("later", k)
                pal1[(r["treatment"], r["value"], kind, prev1)] = (round(float(r[k]) * 50), 50)
    for r in csv.DictReader(open(PAL / "pal2026_memory2.csv")):
        if r["model"] == pal_model:
            pal2[(r["scenario"], r["prev2"], r["prev1"])] = (int(r["count_C"]), int(r["n"]))
    print(f"\nComparison with Pal et al. ({pal_model}); p = Fisher's exact test per scenario, unadjusted; * = p < 0.05")
    print(f"  {'scenario':58s} {'ours':>7s} {'paper':>7s}   diff      p")
    by_exp = defaultdict(lambda: [0, 0, 0.0])
    ps = defaultdict(list)
    for d in long:
        if d["experiment"] == "memory2":
            ref = pal2.get((d["kind"], d["prev2"], d["prev1"]))
        else:
            ref = pal1.get(_pal_key(d))
        if ref is None:
            continue
        k2, n2 = ref
        p = fisher_exact([[d["count_C"], d["n"] - d["count_C"]], [k2, n2 - k2]])[1]
        diff = d["count_C"] / d["n"] - k2 / n2
        e = by_exp[d["experiment"]]
        e[0] += 1
        e[1] += p < 0.05
        ps[d["experiment"]].append(p)
        e[2] += abs(diff)
        hist = f"{d['prev2']}>{d['prev1']}" if d["prev2"] else d["prev1"]
        sc = f"{d['experiment']} {d['treatment'][:24]} {d['kind']} {hist}"
        print(f"  {sc:58s} {d['count_C']:>3d}/{d['n']:<3d} {k2:>3d}/{n2:<3d} {diff:+6.2f} {p:7.3f}{' *' if p < 0.05 else ''}")
    for exp, (n, bad, tot) in by_exp.items():
        n_holm = sum(q < 0.05 for q in holm(ps[exp]))
        print(f"  {exp}: {bad} of {n} scenarios differ at p < 0.05 unadjusted, {n_holm} after Holm adjustment within "
              f"the {n} {exp} scenarios; mean |diff| {tot / n:.2f}")


if __name__ == "__main__":
    main()
