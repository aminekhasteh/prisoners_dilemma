"""SSE (Article 1's distance from the zero-determinant plane) for every LLM player in the 307-player Article 2 field,
next to its mean tournament rank.

SSE needs a memory-one vector p = P(C | CC, CD, DC, DD), own move first. Two versions are reported:

  sse_vector  From the elicited probabilities, no games played.
              memory-1: the four numbers as elicited.
              memory-2 / memory-3: P(C | last round = s) is the plain mean of P(C | earlier rounds, s) over the 4
              (memory-2) or 16 (memory-3) possible earlier histories, using the "later rounds" table. Opening
              moves (round 1-3 tables) are left out. This weights every earlier history equally.
  sse_played  Article 1's own definition: the CC/CD/DC/DD -> C rates axelrod's ResultSet would report for the player
              (per opponent: share of visits to state s followed by C; then the mean over opponents of the
              non-zero rates, as in ResultSet.summarise), from matches against Knight's 272 players. Here every
              earlier history is weighted by how often real opponents lead the player into it.
              Played at 63 turns, no noise, --reps repetitions, against the 272 minus the long_run_time players
              (Meta*, NMWE*, ...), which are too slow for this box; --with-slow puts them back.

Mean rank comes from results_m3/standard63_summary.csv (307 players, 63 turns, 20 seeds, no noise).

Usage (axelrod venv, OPENBLAS_NUM_THREADS=1):
  python sse_llm.py                       # vector SSE only, instant
  python sse_llm.py --play --reps 5       # adds sse_played
Output: results_m3/llm_sse.csv"""
import argparse, csv, sys, time
from collections import Counter
import multiprocessing as mp
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "knight272"))
from build_dataset import sse                                   # Article 1's SSE, unchanged

import axelrod as axl
import run_llm_field as base
import run_m2_field as m2f
import run_new_field as newf
import run_m3_field as m3f

C, D = axl.Action.C, axl.Action.D
STATES = [(C, C), (C, D), (D, C), (D, D)]


def llm_specs():
    """The 35 LLM players in run_m3_field.py's order and names."""
    all_m1 = newf.load_memory1()
    all_m2 = m2f.load_memory2(HERE / "new_llm_memory2.csv")
    m2f.M2.update(all_m2)
    m3f.M3.update(m3f.load_memory3())
    label = {m: lab for m, lab, *_ in all_m1}
    specs = [(name, "llm", (p0, fv), False) for name, p0, fv in base.LLM_STRATEGIES]
    specs += [(f"LLM-m2: {m2f.NAMES[m]}", "m2", m, False) for m in m2f.NAMES]
    specs += [(f"LLM: {lab}", "llm", (p0, fv), False) for m, lab, p0, fv in all_m1 if m in newf.FIELD_M1]
    specs += [(f"LLM-m2: {label[m]}", "m2", m, False) for m in label if m in newf.FIELD_M2]
    specs += [(f"LLM-m3: {label[m]}", "m3", m, False) for m in label if m in m3f.M3]
    specs += [(f"LLM: {lab}", "llm", (p0, fv), False) for m, lab, p0, fv in all_m1 if m not in newf.FIELD_M1]
    specs += [(f"LLM-m2: {label[m]}", "m2", m, False) for m in label if m in all_m2 and m not in newf.FIELD_M2]
    return specs


def vector(spec):
    """Memory-one vector: elicited (m1) or the uniform mean over earlier histories (m2, m3); also the spread."""
    name, kind, arg, _ = spec
    if kind == "llm":
        return np.array(arg[1], float), np.zeros(4)
    later = m2f.M2[arg][2] if kind == "m2" else m3f.M3[arg][3]
    by = {s: [p for h, p in later.items() if h[-1] == s] for s in STATES}
    assert all(len(v) == (4 if kind == "m2" else 16) for v in by.values())
    return np.array([np.mean(by[s]) for s in STATES]), np.array([np.ptp(by[s]) for s in STATES])


def play_one(task):
    """Per-opponent state -> C rates for one LLM player against one opponent (all reps pooled)."""
    i, j, turns, reps = task
    a, b = base.make_player(base.SPECS[i]), base.make_player(base.SPECS[j])
    cnt = Counter()
    for r in range(reps):
        s = int(np.random.SeedSequence([7, turns, i, j, r]).generate_state(1)[0])
        moves = axl.Match((a, b), turns=turns, seed=s, match_attributes={"length": float("inf")}).play()
        for (x0, y0), (x1, _) in zip(moves, moves[1:]):
            cnt[((x0, y0), x1)] += 1
    rates = []
    for st in STATES:
        tot = cnt[(st, C)] + cnt[(st, D)]
        rates.append(cnt[(st, C)] / tot if tot else None)
    return i, j, rates


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--play", action="store_true")
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--turns", type=int, default=63)
    ap.add_argument("--processes", type=int, default=2)
    ap.add_argument("--with-slow", action="store_true")
    ap.add_argument("--limit", type=int, help="only the first N LLM players (timing)")
    ap.add_argument("--ranks", type=Path, default=HERE / "results_m3/standard63_summary.csv")
    ap.add_argument("--out", type=Path, default=HERE / "results_m3/llm_sse.csv")
    for k, v in base.DEFAULTS.items():
        if k != "out":
            ap.add_argument(f"--{k}", type=Path, default=v)
    args = base.ARGS = ap.parse_args()

    llm = llm_specs()[: args.limit]
    knight = base.knight_players(args.traits)
    base.SPECS = knight + llm
    base.limit_meta_teams(base.SPECS)
    rank = {r["Name"]: r for r in csv.DictReader(open(args.ranks))}

    rows = []
    for k, s in enumerate(llm):
        p, spread = vector(s)
        r = rank.get(s[0], {})
        rows.append(dict(Name=s[0], memory={"llm": 1, "m2": 2, "m3": 3}[s[1]],
                         source="Pal et al. 2026" if k < 10 else "new elicitation",
                         **{f"v_{st}": round(x, 4) for st, x in zip(("CC", "CD", "DC", "DD"), p)},
                         sse_vector=round(float(sse(p[None])[0]), 4),
                         max_spread=round(float(spread.max()), 3),
                         mean_rank=r.get("rank", ""), normalized_rank=r.get("normalized_rank", "")))

    if args.play:
        opp = [j for j, s in enumerate(knight) if args.with_slow or not s[3]]
        n0 = len(knight)
        tasks = [(n0 + k, j, args.turns, args.reps) for k in range(len(llm)) for j in opp]
        print(f"{len(tasks)} pairs ({len(llm)} LLM x {len(opp)} opponents) x {args.reps} reps, {args.turns} turns",
              flush=True)
        t0 = time.time()
        per = {}
        with mp.get_context("fork").Pool(args.processes) as pool:      # as run_llm_field.run_pairs
            for n, (i, j, rates) in enumerate(pool.imap_unordered(play_one, tasks, chunksize=8), 1):
                per.setdefault(i - n0, []).append(rates)
                if n % 1000 == 0:
                    print(f"  {n}/{len(tasks)} in {time.time() - t0:.0f} s", flush=True)
        print(f"played in {time.time() - t0:.0f} s", flush=True)
        for k, row in enumerate(rows):
            q = []
            for si in range(4):
                vals = [r[si] for r in per[k] if r[si]]                 # ResultSet.summarise: mean of non-zero rates
                q.append(float(np.mean(vals)) if vals else 0.0)
            q = np.array(q)
            row.update({f"p_{st}": round(x, 4) for st, x in zip(("CC", "CD", "DC", "DD"), q)})
            row["sse_played"] = round(float(sse(q[None])[0]), 4)
            row["opponents"] = len(opp)

    rows.sort(key=lambda r: float(r["mean_rank"] or 1e9))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(f"wrote {args.out}")
    for r in rows:
        print(f"  {r['Name']:44} rank {float(r['mean_rank'] or 0):6.1f}  sse_vector {r['sse_vector']:.3f}"
              + (f"  sse_played {r['sse_played']:.3f}" if "sse_played" in r else ""))


if __name__ == "__main__":
    main()
