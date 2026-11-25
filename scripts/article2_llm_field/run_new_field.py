"""Article 2: add the newly elicited LLM strategies, memory-1 and memory-2, to the 282-player field.

The new strategies come from scripts/llm_strategy_elicitation (two prompt wordings pooled, n = 100 per cell):
new_llm_memory1.csv (p0 and P(C) after CC, CD, DC, DD, own move first) and new_llm_memory2.csv (same layout as
pal2026_memory2.csv; a model may have no memory-2 rows). They become "LLM: <label>" and "LLM-m2: <label>" players from
index 282 on (8 memory-1 + 7 memory-2 = 15 players, 297 in all, with the files of 2026-11-24).

Only the new players' matches are played: against Knight's 272, the five Pal memory-1 and five Pal memory-2 players,
and among themselves (15 x 282 + 105 = 4,335 pairs per tournament). Everything else is read from the existing pair
files: results/pairs (Pal memory-1) and results_m2/pairs (Pal memory-2), so a tournament can only be combined after
both of those have finished it. Pair seeds depend only on (seed, turns, noise, i, j, repetition), as in
run_llm_field.py, so the old pairs are exactly what a full 294-player run would replay.

Usage (axelrod venv, OPENBLAS_NUM_THREADS=1):
  python run_new_field.py standard --turns 63
  python run_new_field.py noise5
Outputs in results_new/: pairs/ (resumable jsonl), <condition>_per_tournament.csv, <condition>_summary.csv."""
import argparse, csv, re, time
from pathlib import Path

import numpy as np
import run_llm_field as base
import run_m2_field as m2f

HERE = Path(__file__).resolve().parent
# The models in the 297-player field (files as of c000af9). Rows for later models (appended to the same CSVs) are left
# out here, so the player indices, and with them the pair seeds, stay fixed; run_m3_field.py adds the later ones.
FIELD_M1 = ["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5", "gpt-6.1-sol", "gpt-6.1-terra", "gpt-6-luna",
            "llama-3.3-70b-rerun", "gemini-2.5-pro-rerun"]
FIELD_M2 = FIELD_M1[:7]


def load_memory1(path=HERE / "new_llm_memory1.csv"):
    return [(r["model"], r["label"], float(r["p0"]), tuple(float(r[k]) for k in ("CC", "CD", "DC", "DD")))
            for r in csv.DictReader(open(path))]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("condition", choices=base.CONDITIONS)
    ap.add_argument("--turns", type=int, nargs="+")
    ap.add_argument("--seeds", type=int, nargs="+")
    ap.add_argument("--reps", type=int, default=250)
    ap.add_argument("--processes", type=int, default=4)
    ap.add_argument("--m1-out", type=Path, default=HERE / "results", help="Pal memory-1 pairs (run_llm_field.py)")
    ap.add_argument("--m2-out", type=Path, default=HERE / "results_m2", help="Pal memory-2 pairs (run_m2_field.py)")
    ap.add_argument("--old-reps", type=int, default=250, help="repetitions in the older pair files")
    ap.add_argument("--new-m1", type=Path, default=HERE / "new_llm_memory1.csv")
    ap.add_argument("--new-m2", type=Path, default=HERE / "new_llm_memory2.csv")
    for k, v in base.DEFAULTS.items():
        ap.add_argument(f"--{k}", type=Path, default=HERE / "results_new" if k == "out" else v)
    args = base.ARGS = ap.parse_args()
    noise, folder, lengths = base.CONDITIONS[args.condition]
    turns_list = args.turns or lengths
    seeds = args.seeds or sorted({int(m.group(1)) for f in (args.knight / folder).glob(f"full_{turns_list[0]}_turns_*_seed_summary.csv")
                                  if (m := re.search(r"_(\d+)_seed_summary", f.name))})

    new_m1 = [r for r in load_memory1(args.new_m1) if r[0] in FIELD_M1]
    new_m2 = {m: v for m, v in m2f.load_memory2(args.new_m2).items() if m in FIELD_M2}
    assert [r[0] for r in new_m1] == FIELD_M1 and list(new_m2) == FIELD_M2
    label = {m: lab for m, lab, *_ in new_m1}
    assert set(new_m2) <= set(label), "memory-2 models missing from the memory-1 file (labels come from it)"
    assert not set(new_m2) & set(m2f.M2)
    m2f.M2.update(new_m2)

    specs = base.knight_players(args.traits)
    idx = [l.strip().strip('"') for l in open(args.knight / folder / "players.index")]
    assert [s[0] for s in specs] == idx
    n_old = len(specs)                                                           # 272
    specs += [(name, "llm", (p0, fv), False) for name, p0, fv in base.LLM_STRATEGIES]
    pal1 = range(n_old, len(specs))                                              # 272-276
    specs += [(f"LLM-m2: {m2f.NAMES[m]}", "m2", m, False) for m in m2f.NAMES]
    pal2 = range(pal1.stop, len(specs))                                          # 277-281
    specs += [(f"LLM: {lab}", "llm", (p0, fv), False) for _, lab, p0, fv in new_m1]
    specs += [(f"LLM-m2: {label[m]}", "m2", m, False) for m in label if m in new_m2]
    new = range(pal2.stop, len(specs))                                           # 282 on
    names = [s[0] for s in specs]
    assert len(set(names)) == len(names), "duplicate player names"
    base.SPECS = specs
    base.limit_meta_teams(specs)
    for s in specs:
        base.make_player(s)
    kind = {i: (2 if s[1] == "m2" else 1) for i, s in enumerate(specs) if s[1] in ("llm", "m2")}
    source = {i: ("Pal et al. 2026" if i < new.start else "new elicitation") for i in kind}

    args.out.mkdir(parents=True, exist_ok=True); (args.out / "pairs").mkdir(exist_ok=True)
    tag = args.condition if args.reps == 250 else f"{args.condition}_{args.reps}reps"
    n_pal1_pairs = 5 * n_old + 10
    n_pal2_pairs = 5 * (n_old + 5) + 10
    per_t = []
    for turns in turns_list:
        for seed in seeds:
            stem, knight_reps = base.knight_files(folder, turns, seed)
            tasks = [(i, j, turns, noise, seed, args.reps) for i in new for j in range(len(specs)) if j < new.start or j > i]
            print(f"{args.condition} new: {turns} turns, seed {seed}, {len(tasks)} pairs x {args.reps} reps", flush=True)
            t0 = time.time()
            fname = f"{args.condition}_{turns}t_seed{seed}_{args.reps}reps.jsonl"
            got = base.run_pairs(tasks, args.out / "pairs" / fname)
            wanted = {(t[0], t[1]) for t in tasks}
            pairs = {k: v for k, v in got.items() if k in wanted}
            print(f"  done in {time.time() - t0:.0f} s wall", flush=True)
            oname = f"{args.condition}_{turns}t_seed{seed}_{args.old_reps}reps.jsonl"
            old1 = {k: v for k, v in m2f.read_pairs(args.m1_out / "pairs" / oname).items()
                    if k[0] in pal1 and k[1] < pal2.start}
            old2 = {k: v for k, v in m2f.read_pairs(args.m2_out / "pairs" / oname).items()
                    if k[0] in pal2 and k[1] < new.start}
            if len(old1) != n_pal1_pairs or len(old2) != n_pal2_pairs:
                print(f"  older pairs missing (memory-1 {len(old1)} of {n_pal1_pairs}, memory-2 {len(old2)} of "
                      f"{n_pal2_pairs}); run run_llm_field.py and run_m2_field.py first", flush=True)
                continue
            pairs.update(old1); pairs.update(old2)
            for row in base.combine(pairs, n_old, turns, stem, knight_reps):
                i = names.index(row["Name"])
                row["memory"] = kind.get(i, ""); row["source"] = source.get(i, "")
                per_t.append(dict(condition=args.condition, noise=noise, turns=turns, seed=seed, reps=args.reps, **row))
            base.write(args.out / f"{tag}_per_tournament.csv", per_t)

    by = {}
    for r in per_t:
        by.setdefault(r["Name"], []).append(r)
    summ = [dict(Name=n, llm=rs[0]["llm"], memory=rs[0]["memory"], source=rs[0]["source"], tournaments=len(rs),
                 **{k: float(np.mean([r[k] for r in rs])) for k in
                    ["mean_score", "median_score", "rank", "normalized_rank", "cooperation_rate"]})
            for n, rs in by.items()]
    summ.sort(key=lambda r: r["normalized_rank"])
    if summ:
        base.write(args.out / f"{tag}_summary.csv", summ)
    print(f"\n{args.condition}: LLM players among {len(specs)}")
    for r in summ:
        if r["llm"]:
            print(f"  {r['Name']:28} rank {r['rank']:6.1f}  norm rank {r['normalized_rank']:.3f}  "
                  f"score {r['mean_score']:.3f}  coop {r['cooperation_rate']:.3f}")


if __name__ == "__main__":
    main()
