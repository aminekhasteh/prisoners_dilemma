"""Article 2: wording-specific players at memory 1, 2 and 3 in one field, for memory-depth comparisons.

The pooled players of run_new_field.py / run_m3_field.py add the clean and SI wordings together. That is a labeled
extension, not a single prompt, and the two wordings can disagree (Llama 3.3 70B cooperates after DC with probability
0.04 clean, 0.88 SI, 0.46 pooled; in memory-2 the clean prompt also corrects the SI's misprinted opponent payoff, so
the two wordings describe different games). A claim about memory depth should compare players elicited with the same
prompt. This script builds Knight's 272 plus, for every model that has all the depths in one wording:

  "LLM[<w>]: <label>"     memory-1, from new_llm_memory1_by_wording.csv
  "LLM-m2[<w>]: <label>"  memory-2, from new_llm_memory2_by_wording.csv
  "LLM-m3[<w>]: <label>"  memory-3, from new_llm_memory3.csv (clean wording only, so only for --wording clean)

With the files of 2026-11-25 and --wording clean: 7 models (Opus, Sonnet, Haiku 5.5, GPT-6.1 Sol and Terra, GPT-6
Luna, Llama 3.3 70B rerun) x 3 depths = 21 players, 293 in all, 21 x 272 + 210 = 5,922 new pairs per tournament. Sonnet
5.5 effort xhigh is left out (its memory-1 run used the SI wording) and Gemini 2.5 Pro rerun too (SI memory-1 only).
All of these pairs are played here, so nothing depends on other result folders. Same settings, seeds and merging as
run_llm_field.py (pair seeds come from the player indices, so this field's pairs are its own).

Usage (axelrod venv, OPENBLAS_NUM_THREADS=1):
  python run_wording_field.py standard --turns 63 --wording clean
Outputs in results_<wording>/: pairs/ (resumable jsonl), <condition>_per_tournament.csv, <condition>_summary.csv."""
import argparse, csv, re, sys, time
from collections import defaultdict
from pathlib import Path

import numpy as np
import run_llm_field as base
import run_m2_field as m2f
import run_m3_field as m3f                                                   # registers the "m3" player kind

HERE = Path(__file__).resolve().parent


def load_by_wording(m1_path, m2_path, m3_path):
    """{wording: {model: {"label": str, 1: (p0, vec), 2: m2 tuple, 3: m3 tuple}}}."""
    out = defaultdict(lambda: defaultdict(dict))
    for r in csv.DictReader(open(m1_path)):
        d = out[r["wording"]][r["model"]]
        d["label"] = r["label"].rsplit(" [", 1)[0]
        d[1] = (float(r["p0"]), tuple(float(r[k]) for k in ("CC", "CD", "DC", "DD")))
    o = lambda s: (m2f.ACT[s[0]], m2f.ACT[s[1]])
    for r in csv.DictReader(open(m2_path)):                               # same layout as run_m2_field.load_memory2
        v = out[r["wording"]][r["model"]].setdefault(2, [None, {}, {}])
        p = float(r["p_C"])
        if r["scenario"] == "round1":
            v[0] = p
        elif r["scenario"] == "round2":
            v[1][o(r["prev1"])] = p
        else:
            v[2][(o(r["prev2"]), o(r["prev1"]))] = p
    for w in out.values():
        for d in w.values():
            if 2 in d:
                assert d[2][0] is not None and len(d[2][1]) == 4 and len(d[2][2]) == 16
                d[2] = tuple(d[2])
    for m, v in m3f.load_memory3(m3_path).items():
        out["clean"][m][3] = v
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("condition", choices=base.CONDITIONS)
    ap.add_argument("--wording", choices=["clean", "si"], default="clean")
    ap.add_argument("--turns", type=int, nargs="+")
    ap.add_argument("--seeds", type=int, nargs="+")
    ap.add_argument("--reps", type=int, default=250)
    ap.add_argument("--processes", type=int, default=4)
    ap.add_argument("--m1", type=Path, default=HERE / "new_llm_memory1_by_wording.csv")
    ap.add_argument("--m2", type=Path, default=HERE / "new_llm_memory2_by_wording.csv")
    ap.add_argument("--m3", type=Path, default=HERE / "new_llm_memory3.csv")
    for k, v in base.DEFAULTS.items():
        ap.add_argument(f"--{k}", type=Path, default=None if k == "out" else v)
    args = base.ARGS = ap.parse_args()
    args.out = args.out or HERE / f"results_{args.wording}"
    noise, folder, lengths = base.CONDITIONS[args.condition]
    turns_list = args.turns or lengths
    seeds = args.seeds or sorted({int(m.group(1)) for f in (args.knight / folder).glob(f"full_{turns_list[0]}_turns_*_seed_summary.csv")
                                  if (m := re.search(r"_(\d+)_seed_summary", f.name))})

    data = load_by_wording(args.m1, args.m2, args.m3)[args.wording]
    depths = (1, 2, 3) if args.wording == "clean" else (1, 2)
    models = [m for m, d in data.items() if all(k in d for k in depths) and "label" in d]
    left_out = sorted(set(data) - set(models))
    print(f"{args.wording} wording, depths {depths}: {len(models)} models; left out (missing a depth in this wording): "
          f"{', '.join(left_out) or 'none'}", flush=True)

    specs = base.knight_players(args.traits)
    idx = [l.strip().strip('"') for l in open(args.knight / folder / "players.index")]
    assert [s[0] for s in specs] == idx
    n_old = len(specs)
    tagw = f"[{args.wording}]"
    for m in models:                                    # memory-1 players, then memory-2, then memory-3
        p0, fv = data[m][1]
        specs.append((f"LLM{tagw}: {data[m]['label']}", "llm", (p0, fv), False))
    for m in models:
        m2f.M2[f"{m}{tagw}"] = data[m][2]
        specs.append((f"LLM-m2{tagw}: {data[m]['label']}", "m2", f"{m}{tagw}", False))
    if 3 in depths:
        for m in models:
            m3f.M3[f"{m}{tagw}"] = data[m][3]
            specs.append((f"LLM-m3{tagw}: {data[m]['label']}", "m3", f"{m}{tagw}", False))
    names = [s[0] for s in specs]
    assert len(set(names)) == len(names), "duplicate player names"
    base.SPECS = specs
    base.limit_meta_teams(specs)
    for s in specs:
        base.make_player(s)
    new = range(n_old, len(specs))
    kind = {i: {"llm": 1, "m2": 2, "m3": 3}[specs[i][1]] for i in new}

    args.out.mkdir(parents=True, exist_ok=True); (args.out / "pairs").mkdir(exist_ok=True)
    tag = args.condition if args.reps == 250 else f"{args.condition}_{args.reps}reps"
    per_t, missing = [], []
    for turns in turns_list:
        for seed in seeds:
            stem, knight_reps = base.knight_files(folder, turns, seed)
            tasks = [(i, j, turns, noise, seed, args.reps) for i in new for j in range(len(specs)) if j < n_old or j > i]
            print(f"{args.condition} {args.wording}: {turns} turns, seed {seed}, {len(tasks)} pairs x {args.reps} reps",
                  flush=True)
            t0 = time.time()
            got = base.run_pairs(tasks, args.out / "pairs" / f"{args.condition}_{turns}t_seed{seed}_{args.reps}reps.jsonl")
            wanted = {(t[0], t[1]) for t in tasks}
            pairs = {k: v for k, v in got.items() if k in wanted}
            print(f"  done in {time.time() - t0:.0f} s wall", flush=True)
            if len(pairs) != len(wanted):
                missing.append((turns, seed)); continue
            for row in base.combine(pairs, n_old, turns, stem, knight_reps):
                i = names.index(row["Name"])
                row["memory"] = kind.get(i, ""); row["wording"] = args.wording if i in kind else ""
                per_t.append(dict(condition=args.condition, noise=noise, turns=turns, seed=seed, reps=args.reps, **row))
            base.write(args.out / f"{tag}_per_tournament.csv", per_t)

    by = {}
    for r in per_t:
        by.setdefault(r["Name"], []).append(r)
    summ = [dict(Name=n, llm=rs[0]["llm"], memory=rs[0]["memory"], wording=rs[0]["wording"], tournaments=len(rs),
                 **{k: float(np.mean([r[k] for r in rs])) for k in
                    ["mean_score", "median_score", "rank", "normalized_rank", "cooperation_rate"]})
            for n, rs in by.items()]
    summ.sort(key=lambda r: r["normalized_rank"])
    if summ:
        base.write(args.out / f"{tag}_summary.csv", summ)
    for r in summ:
        if r["llm"]:
            print(f"  {r['Name']:40} rank {r['rank']:6.1f}  norm rank {r['normalized_rank']:.3f}  "
                  f"score {r['mean_score']:.3f}  coop {r['cooperation_rate']:.3f}")
    if missing:
        sys.exit(f"incomplete: {len(missing)} of {len(turns_list) * len(seeds)} tournaments have missing pairs: {missing}")


if __name__ == "__main__":
    main()
