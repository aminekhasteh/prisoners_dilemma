"""Article 2: add memory-3 LLM strategies, and models elicited after the 297-player field, to that field.

new_llm_memory3.csv (clean wording, 50 trials per scenario) gives each model a first-move probability, four round-2
probabilities given round 1, sixteen round-3 probabilities given rounds 1 and 2, and sixty-four later-round
probabilities given the last three rounds (own move first). Players are "LLM-m3: <label>", with labels from
new_llm_memory1.csv, at indices 297 on. Models in new_llm_memory1/2.csv that are not in run_new_field.FIELD_M1/M2
(rows appended later, e.g. claude-sonnet-5-5-xhigh) come after the memory-3 players as "LLM: " and "LLM-m2: ".
With the files of 149c8c9: 8 memory-3 players (297-304), then Sonnet 5.5 xhigh memory-1 (305) and memory-2 (306),
307 players. The first seven memory-3 players keep the indices of the 7-model version, so its pairs stay valid.

Only the batch's matches are played: against the 297 and among themselves (10 x 297 + 45 = 3,015 pairs per
tournament). The rest is read from results/pairs (Pal memory-1), results_m2/pairs (Pal memory-2) and
results_new/pairs (the 15 newly elicited memory-1 and memory-2 players). The first 297 players are built exactly as in
run_new_field.py, so pair indices and seeds line up.

Usage (axelrod venv, OPENBLAS_NUM_THREADS=1):
  python run_m3_field.py standard --turns 63
  python run_m3_field.py noise5
Outputs in results_m3/: pairs/ (resumable jsonl), <condition>_per_tournament.csv, <condition>_summary.csv."""
import argparse, csv, re, sys, time
from pathlib import Path

import numpy as np
import axelrod as axl
import run_llm_field as base
import run_m2_field as m2f
import run_new_field as newf

C, D = axl.Action.C, axl.Action.D
HERE = Path(__file__).resolve().parent
ACT = {"C": C, "D": D}


def load_memory3(path=HERE / "new_llm_memory3.csv"):
    """{model: (p0, {o1: p}, {(o1, o2): p}, {(o_t-3, o_t-2, o_t-1): p})}, outcomes as (own, opponent) actions."""
    out = {}
    o = lambda s: (ACT[s[0]], ACT[s[1]])
    for r in csv.DictReader(open(path)):
        v = out.setdefault(r["model"], [None, {}, {}, {}])
        p = float(r["p_C"])
        if r["scenario"] == "round1":
            v[0] = p
        elif r["scenario"] == "round2":
            v[1][o(r["prev1"])] = p
        elif r["scenario"] == "round3":
            v[2][(o(r["prev2"]), o(r["prev1"]))] = p
        else:
            v[3][(o(r["prev3"]), o(r["prev2"]), o(r["prev1"]))] = p
    assert all(v[0] is not None and len(v[1]) == 4 and len(v[2]) == 16 and len(v[3]) == 64 for v in out.values())
    return out


M3 = {}


class MemoryThreeLLM(axl.Player):
    """Move 1 with p0, move 2 given round 1, move 3 given rounds 1-2, then given the last three rounds. Own seeded RNG;
    probabilities of exactly 0 or 1 are played without a draw, since axl.Match does not seed deterministic players."""
    name = "Memory Three LLM"
    classifier = dict(memory_depth=3, stochastic=True, long_run_time=False, inspects_source=False,
                      manipulates_source=False, manipulates_state=False, makes_use_of=set())

    def __init__(self, label="Memory Three LLM", model="claude-opus-5-5"):
        self.model = model
        self.p0, self.r2, self.r3, self.later = M3[model]
        super().__init__()
        self.name = label
        probs = [self.p0, *self.r2.values(), *self.r3.values(), *self.later.values()]
        self.classifier["stochastic"] = any(0 < p < 1 for p in probs)

    def __repr__(self):
        return self.name

    def _draw(self, p):
        if p in (0, 1):
            return C if p == 1 else D
        return self._random.random_choice(p)

    def strategy(self, opponent):
        t = len(self.history)
        out = lambda k: (self.history[-k], opponent.history[-k])
        if t == 0:
            return self._draw(self.p0)
        if t == 1:
            return self._draw(self.r2[out(1)])
        if t == 2:
            return self._draw(self.r3[(out(2), out(1))])
        return self._draw(self.later[(out(3), out(2), out(1))])


_prev_make = base.make_player                                              # run_m2_field's, which handles "m2"


def make_player(spec):
    if spec[1] == "m3":
        return MemoryThreeLLM(label=spec[0], model=spec[2])
    return _prev_make(spec)


base.make_player = make_player
_prev_params = base.spec_params


def spec_params(spec):
    if spec[1] == "m3":
        return [spec[0], "m3", spec[2], base._canon(M3[spec[2]])]
    return _prev_params(spec)


base.spec_params = spec_params


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("condition", choices=base.CONDITIONS)
    ap.add_argument("--turns", type=int, nargs="+")
    ap.add_argument("--seeds", type=int, nargs="+")
    ap.add_argument("--reps", type=int, default=250)
    ap.add_argument("--processes", type=int, default=4)
    ap.add_argument("--old-reps", type=int, default=250, help="repetitions in the older pair files")
    ap.add_argument("--m1-out", type=Path, default=HERE / "results")
    ap.add_argument("--m2-out", type=Path, default=HERE / "results_m2")
    ap.add_argument("--new-out", type=Path, default=HERE / "results_new")
    ap.add_argument("--new-m1", type=Path, default=HERE / "new_llm_memory1.csv")
    ap.add_argument("--new-m2", type=Path, default=HERE / "new_llm_memory2.csv")
    ap.add_argument("--new-m3", type=Path, default=HERE / "new_llm_memory3.csv")
    for k, v in base.DEFAULTS.items():
        ap.add_argument(f"--{k}", type=Path, default=HERE / "results_m3" if k == "out" else v)
    args = base.ARGS = ap.parse_args()
    noise, folder, lengths = base.CONDITIONS[args.condition]
    turns_list = args.turns or lengths
    seeds = args.seeds or sorted({int(m.group(1)) for f in (args.knight / folder).glob(f"full_{turns_list[0]}_turns_*_seed_summary.csv")
                                  if (m := re.search(r"_(\d+)_seed_summary", f.name))})

    # The 297-player field, built exactly as in run_new_field.py.
    all_m1 = newf.load_memory1(args.new_m1)
    all_m2 = m2f.load_memory2(args.new_m2)
    m2f.M2.update(all_m2)
    new_m1 = [r for r in all_m1 if r[0] in newf.FIELD_M1]
    new_m2 = {m: v for m, v in all_m2.items() if m in newf.FIELD_M2}
    assert [r[0] for r in new_m1] == newf.FIELD_M1 and list(new_m2) == newf.FIELD_M2
    label = {m: lab for m, lab, *_ in all_m1}
    specs = base.knight_players(args.traits)
    idx = [l.strip().strip('"') for l in open(args.knight / folder / "players.index")]
    assert [s[0] for s in specs] == idx
    n_old = len(specs)
    specs += [(name, "llm", (p0, fv), False) for name, p0, fv in base.LLM_STRATEGIES]
    pal1 = range(n_old, len(specs))
    specs += [(f"LLM-m2: {m2f.NAMES[m]}", "m2", m, False) for m in m2f.NAMES]
    pal2 = range(pal1.stop, len(specs))
    specs += [(f"LLM: {lab}", "llm", (p0, fv), False) for _, lab, p0, fv in new_m1]
    specs += [(f"LLM-m2: {label[m]}", "m2", m, False) for m in label if m in new_m2]
    new = range(pal2.stop, len(specs))
    assert len(specs) == 297, len(specs)

    M3.update(load_memory3(args.new_m3))
    assert set(M3) <= set(label), "memory-3 models missing from the memory-1 file (labels come from it)"
    specs += [(f"LLM-m3: {label[m]}", "m3", m, False) for m in label if m in M3]
    specs += [(f"LLM: {lab}", "llm", (p0, fv), False) for m, lab, p0, fv in all_m1 if m not in newf.FIELD_M1]
    specs += [(f"LLM-m2: {label[m]}", "m2", m, False) for m in label if m in all_m2 and m not in newf.FIELD_M2]
    m3 = range(new.stop, len(specs))                                             # the whole batch, 297 on
    names = [s[0] for s in specs]
    assert len(set(names)) == len(names), "duplicate player names"
    base.SPECS = specs
    base.limit_meta_teams(specs)
    for s in specs:
        base.make_player(s)
    kind = {i: {"llm": 1, "m2": 2, "m3": 3}[s[1]] for i, s in enumerate(specs) if s[1] in ("llm", "m2", "m3")}
    source = {i: ("Pal et al. 2026" if i < new.start else "new elicitation") for i in kind}

    args.out.mkdir(parents=True, exist_ok=True); (args.out / "pairs").mkdir(exist_ok=True)
    tag = args.condition if args.reps == 250 else f"{args.condition}_{args.reps}reps"
    want_old = {"m1": 5 * n_old + 10, "m2": 5 * (n_old + 5) + 10, "new": len(new) * pal2.stop + len(new) * (len(new) - 1) // 2}
    per_t, skipped = [], []
    for turns in turns_list:
        for seed in seeds:
            stem, knight_reps = base.knight_files(folder, turns, seed)
            tasks = [(i, j, turns, noise, seed, args.reps) for i in m3 for j in range(len(specs)) if j < m3.start or j > i]
            print(f"{args.condition} m3: {turns} turns, seed {seed}, {len(tasks)} pairs x {args.reps} reps", flush=True)
            t0 = time.time()
            fname = f"{args.condition}_{turns}t_seed{seed}_{args.reps}reps.jsonl"
            got = base.run_pairs(tasks, args.out / "pairs" / fname)
            wanted = {(t[0], t[1]) for t in tasks}
            pairs = {k: v for k, v in got.items() if k in wanted}
            print(f"  done in {time.time() - t0:.0f} s wall", flush=True)
            oname = f"{args.condition}_{turns}t_seed{seed}_{args.old_reps}reps.jsonl"
            old = {"m1": {k: v for k, v in m2f.read_pairs(args.m1_out / "pairs" / oname).items()
                          if k[0] in pal1 and k[1] < pal2.start},
                   "m2": {k: v for k, v in m2f.read_pairs(args.m2_out / "pairs" / oname).items()
                          if k[0] in pal2 and k[1] < new.start},
                   "new": {k: v for k, v in m2f.read_pairs(args.new_out / "pairs" / oname).items()
                           if k[0] in new and k[1] < m3.start}}
            if any(len(old[k]) != want_old[k] for k in old):
                print("  older pairs missing (" + ", ".join(f"{k} {len(old[k])} of {want_old[k]}" for k in old) +
                      "); run the earlier scripts first", flush=True)
                skipped.append((turns, seed, "older pairs missing"))
                continue
            for v in old.values():
                pairs.update(v)
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
    complete = base.coverage(per_t, turns_list, seeds, skipped)
    if summ:
        base.write(args.out / base.summary_name(tag, complete), summ)
    print(f"\n{args.condition}: LLM players among {len(specs)}")
    for r in summ:
        if r["llm"]:
            print(f"  {r['Name']:36} rank {r['rank']:6.1f}  norm rank {r['normalized_rank']:.3f}  "
                  f"score {r['mean_score']:.3f}  coop {r['cooperation_rate']:.3f}")
    if not complete:
        sys.exit(1)


if __name__ == "__main__":
    main()
