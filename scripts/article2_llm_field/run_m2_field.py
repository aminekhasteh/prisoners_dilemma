"""Article 2, memory-1 vs memory-2: add Pal et al.'s five memory-2 strategies to the 277-player field (282 players).

The memory-2 strategies are Table S11 / S25 of Pal et al. 2026 (pal2026_memory2.csv): a first-move probability, four
second-move probabilities given round 1's outcome, and sixteen later-round probabilities given the outcomes of the
last two rounds (own move first). Same tournament settings and merging as run_llm_field.py, which this script imports.

Only the memory-2 players' matches are played: against Knight's 272, against the five memory-1 LLM players and among
themselves (1,395 pairs per tournament). The memory-1 players' own matches are read from run_llm_field.py's pair files
(results/pairs/), so a condition can only be combined after run_llm_field.py has finished that tournament.

Usage (axelrod venv, OPENBLAS_NUM_THREADS=1):
  python run_m2_field.py noise5
  python run_m2_field.py standard --turns 63
Outputs in results_m2/: pairs/ (resumable jsonl), <condition>_per_tournament.csv, <condition>_summary.csv."""
import argparse, csv, re, sys, time
from pathlib import Path

import numpy as np
import axelrod as axl
import run_llm_field as base

C, D = axl.Action.C, axl.Action.D
HERE = Path(__file__).resolve().parent
NAMES = {"claude-sonnet-4": "Claude Sonnet 4", "gemini-2.5-pro": "Gemini 2.5 Pro", "gpt-4o": "GPT-4o",
         "gpt-5": "GPT-5", "llama-3.3-70b": "Llama 3.3 70B"}
ACT = {"C": C, "D": D}


def load_memory2(path=HERE / "pal2026_memory2.csv"):
    """{model: (p0, {round-1 outcome: p}, {(outcome t-2, outcome t-1): p})}, outcomes as (own, opponent) actions."""
    out = {}
    for r in csv.DictReader(open(path)):
        p0, r2, later = out.setdefault(r["model"], [None, {}, {}])
        p, o = float(r["p_C"]), lambda s: (ACT[s[0]], ACT[s[1]])
        if r["scenario"] == "round1":
            out[r["model"]][0] = p
        elif r["scenario"] == "round2":
            r2[o(r["prev1"])] = p
        else:
            later[(o(r["prev2"]), o(r["prev1"]))] = p
    assert all(v[0] is not None and len(v[1]) == 4 and len(v[2]) == 16 for v in out.values())
    return out


class MemoryTwoLLM(axl.Player):
    """Move 1 with p0, move 2 given round 1, then given the last two rounds. Uses its own seeded RNG; probabilities of
    exactly 0 or 1 are played without a draw, since axl.Match does not seed deterministic players."""
    name = "Memory Two LLM"
    classifier = dict(memory_depth=2, stochastic=True, long_run_time=False, inspects_source=False,
                      manipulates_source=False, manipulates_state=False, makes_use_of=set())

    def __init__(self, label="Memory Two LLM", model="claude-sonnet-4"):
        self.model = model
        self.p0, self.r2, self.later = M2[model]
        super().__init__()
        self.name = label
        probs = [self.p0, *self.r2.values(), *self.later.values()]
        self.classifier["stochastic"] = any(0 < p < 1 for p in probs)

    def __repr__(self):
        return self.name

    def _draw(self, p):
        if p in (0, 1):
            return C if p == 1 else D
        return self._random.random_choice(p)

    def strategy(self, opponent):
        t = len(self.history)
        if t == 0:
            return self._draw(self.p0)
        last = (self.history[-1], opponent.history[-1])
        if t == 1:
            return self._draw(self.r2[last])
        return self._draw(self.later[((self.history[-2], opponent.history[-2]), last)])


M2 = load_memory2()
_base_make = base.make_player


def make_player(spec):
    if spec[1] == "m2":
        return MemoryTwoLLM(label=spec[0], model=spec[2])
    return _base_make(spec)


base.make_player = make_player                                            # play_pair looks this up in base


def read_pairs(path):
    pairs = {}
    if path.exists():
        for line in open(path):
            try:
                d = base.json.loads(line)
            except base.json.JSONDecodeError:
                continue
            pairs[(d["i"], d["j"])] = d
    return pairs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("condition", choices=base.CONDITIONS)
    ap.add_argument("--turns", type=int, nargs="+")
    ap.add_argument("--seeds", type=int, nargs="+")
    ap.add_argument("--reps", type=int, default=250)
    ap.add_argument("--processes", type=int, default=4)
    ap.add_argument("--m1-out", type=Path, default=HERE / "results", help="where run_llm_field.py wrote its pairs")
    for k, v in base.DEFAULTS.items():
        ap.add_argument(f"--{k}", type=Path, default=HERE / "results_m2" if k == "out" else v)
    args = base.ARGS = ap.parse_args()
    noise, folder, lengths = base.CONDITIONS[args.condition]
    turns_list = args.turns or lengths
    seeds = args.seeds or sorted({int(m.group(1)) for f in (args.knight / folder).glob(f"full_{turns_list[0]}_turns_*_seed_summary.csv")
                                  if (m := re.search(r"_(\d+)_seed_summary", f.name))})

    specs = base.knight_players(args.traits)
    idx = [l.strip().strip('"') for l in open(args.knight / folder / "players.index")]
    assert [s[0] for s in specs] == idx
    n_old = len(specs)
    specs += [(name, "llm", (p0, fv), False) for name, p0, fv in base.LLM_STRATEGIES]
    m1 = range(n_old, len(specs))
    specs += [(f"LLM-m2: {NAMES[m]}", "m2", m, False) for m in NAMES]
    m2 = range(m1.stop, len(specs))
    base.SPECS = specs
    base.limit_meta_teams(specs)
    for s in specs:
        base.make_player(s)

    args.out.mkdir(parents=True, exist_ok=True); (args.out / "pairs").mkdir(exist_ok=True)
    tag = args.condition if args.reps == 250 else f"{args.condition}_{args.reps}reps"
    per_t, skipped = [], []
    for turns in turns_list:
        for seed in seeds:
            stem, knight_reps = base.knight_files(folder, turns, seed)
            tasks = [(i, j, turns, noise, seed, args.reps) for i in m2 for j in range(len(specs)) if j < m2.start or j > i]
            print(f"{args.condition} m2: {turns} turns, seed {seed}, {len(tasks)} pairs x {args.reps} reps", flush=True)
            t0 = time.time()
            new = base.run_pairs(tasks, args.out / "pairs" / f"{args.condition}_{turns}t_seed{seed}_{args.reps}reps.jsonl")
            wanted = {(t[0], t[1]) for t in tasks}
            pairs = {k: v for k, v in new.items() if k in wanted}
            old = read_pairs(args.m1_out / "pairs" / f"{args.condition}_{turns}t_seed{seed}_{args.reps}reps.jsonl")
            old = {k: v for k, v in old.items() if k[0] in m1 and k[1] < m2.start}
            if len(old) != 5 * n_old + 10:
                print(f"  memory-1 pairs missing ({len(old)} of {5 * n_old + 10}); run run_llm_field.py first", flush=True)
                skipped.append((turns, seed, "older pairs missing"))
                continue
            pairs.update(old)
            print(f"  done in {time.time() - t0:.0f} s wall", flush=True)
            for row in base.combine(pairs, n_old, turns, stem, knight_reps):
                row["memory"] = 2 if row["Name"].startswith("LLM-m2") else (1 if row["llm"] else "")
                per_t.append(dict(condition=args.condition, noise=noise, turns=turns, seed=seed, reps=args.reps, **row))
            base.write(args.out / f"{tag}_per_tournament.csv", per_t)

    by = {}
    for r in per_t:
        by.setdefault(r["Name"], []).append(r)
    summ = [dict(Name=n, llm=rs[0]["llm"], memory=rs[0]["memory"], tournaments=len(rs),
                 **{k: float(np.mean([r[k] for r in rs])) for k in
                    ["mean_score", "median_score", "rank", "normalized_rank", "cooperation_rate"]})
            for n, rs in by.items()]
    summ.sort(key=lambda r: r["normalized_rank"])
    complete = base.coverage(per_t, turns_list, seeds, skipped)
    if summ:
        base.write(args.out / base.summary_name(tag, complete), summ)
    print(f"\n{args.condition}: LLM players among {len(specs)}")
    for r in summ:
        if r["llm"]:
            print(f"  {r['Name']:26} rank {r['rank']:6.1f}  norm rank {r['normalized_rank']:.3f}  "
                  f"score {r['mean_score']:.3f}  coop {r['cooperation_rate']:.3f}")
    if not complete:
        sys.exit(1)


if __name__ == "__main__":
    main()
