"""Article 2: drop five LLM-derived memory-one strategies into Knight et al.'s 272-player field (277 players).

The five strategies are the memory-one fits in Pal et al. 2026 (arXiv 2601.09849), Table S12. Each has a first-move
cooperation probability p0 and four probabilities of cooperating after CC, CD, DC, DD (own move first).

Settings copy Knight et al. 2025's full tournaments (src/run_full_tournament*.py in Zenodo 17250038): a round robin
with the default payoffs (R=3, S=0, T=5, P=1), fixed match lengths that the players are not told
(match_attributes length = inf), 250 repetitions per seed, self-interactions left out of the scores, players ranked by
the median over repetitions of their mean score per turn.

  condition   noise  turns                     seeds
  standard    0      63, 77, 151, 156, 308     the 20 seeds in data/full_tournament
  noise1      0.01   63                        the 13 seeds in data/full_tournament_1_percent_noise
  noise5      0.05   63                        the 7 seeds in data/full_tournament_5_percent_noise

Only the new matches are played: each LLM player against the 272 and against the other four. The 272 x 272 part comes
from Knight's per-seed files (scores.gz = each player's total score in each repetition, cooperation_rates.gz =
pairwise cooperation rates, stored transposed). For repetition r, a 272 player's new total is Knight's total plus what
it scored in repetition r of its matches against the five LLM players. That is the same quantity axelrod's ResultSet
ranks on, so the 277-player ranking is the one a full rerun would give, up to the randomness of the new matches.
If fewer repetitions are played than Knight's 250 (for a quick run), repetition r reuses new repetition r mod n.

The 63 original Fortran entries are called straight from libstrategies.so (as in ../knight272/replay_moves.py). The
library players use axelrod 4.14; its Meta* players have bigger teams than the 4.10 Knight used, so the teams are
cut back to the strategies that existed in 4.10, which reproduces Knight's team sizes exactly (checked by name).

Usage (the axelrod venv, ~/.local/share/axelrod-probe-venv; set OPENBLAS_NUM_THREADS=1):
  python run_llm_field.py standard                       # full run of one condition
  python run_llm_field.py noise5 --seeds 0 --turns 63 --reps 2     # quick timing run
  python run_llm_field.py standard --validate 40 --reps 250        # check the engine against Knight's payoffs
Outputs go to results/: pairs/ (raw new matches, resumable), <condition>_per_tournament.csv, <condition>_summary.csv,
timing_<condition>.csv."""
import argparse, csv, json, math, multiprocessing as mp, os, re, shutil, sys, tempfile, time, warnings
from ctypes import CDLL, byref, c_float, c_int
from pathlib import Path

warnings.filterwarnings("ignore")
import numpy as np
import axelrod as axl
import importlib
axl_meta = importlib.import_module("axelrod.strategies.meta")

C, D = axl.Action.C, axl.Action.D
HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
MAIN = Path.home() / "projects/prisoners_dilemma"                       # untracked data lives in the main checkout
DEFAULTS = dict(knight=next((p for p in (REPO / "Data/knight2026/src/data", MAIN / "Data/knight2026/src/data") if p.exists()),
                            REPO / "Data/knight2026/src/data"),
                traits=HERE.parent / "knight272/data/strategy_traits.csv",
                lib=next((p for p in (HERE.parent / "knight272/lib/libstrategies.so",
                                      MAIN / "article1/knight2026/lib/libstrategies.so") if p.exists()),
                         HERE.parent / "knight272/lib/libstrategies.so"),
                out=HERE / "results")
CONDITIONS = {"standard": (0.0, "full_tournament", [63, 77, 151, 156, 308]),
              "noise1": (0.01, "full_tournament_1_percent_noise", [63]),
              "noise5": (0.05, "full_tournament_5_percent_noise", [63])}
PAYOFF = {(C, C): (3, 3), (C, D): (0, 5), (D, C): (5, 0), (D, D): (1, 1)}

# name, p0, (P(C|CC), P(C|CD), P(C|DC), P(C|DD)); own move first. Pal et al. 2026, Table S12.
LLM_STRATEGIES = [("LLM: Claude Sonnet 4", 1.00, (1.00, 0.00, 1.00, 1.00)),   # Forgiver
                  ("LLM: Gemini 2.5 Pro", 0.82, (1.00, 0.00, 0.02, 0.42)),    # about WSLS
                  ("LLM: GPT-4o", 1.00, (1.00, 0.00, 0.00, 0.00)),            # Grim
                  ("LLM: GPT-5", 1.00, (1.00, 0.00, 0.54, 1.00)),             # about Forgiver
                  ("LLM: Llama 3.3 70B", 1.00, (1.00, 0.26, 0.98, 0.56))]     # about GTFT


class StochasticStartMemoryOne(axl.MemoryOnePlayer):
    """Memory-one player whose first move is C with probability p0, drawn from the player's own seeded RNG."""
    name = "Stochastic Start Memory One"

    def __init__(self, label="Stochastic Start Memory One", p0=1.0, four_vector=(1, 0, 1, 0)):
        self.p0 = p0
        super().__init__(four_vector=four_vector, initial=C)
        self.name = label

    def __repr__(self):
        return self.name

    def _post_init(self):
        super()._post_init()
        if 0 < self.p0 < 1:
            self.classifier["stochastic"] = True
            self.classifier["memory_depth"] = 1

    def strategy(self, opponent):
        if not self.history:
            if self.p0 in (0, 1):                     # deterministic players are not seeded by axl.Match
                return C if self.p0 == 1 else D
            return self._random.random_choice(self.p0)
        return super().strategy(opponent)


_LIB = None


def fortran_lib():
    """One private copy of the shared library per process: the Fortran keeps state between calls."""
    global _LIB
    if _LIB is None:
        tmp = tempfile.mkdtemp(prefix=f"fortran{os.getpid()}_")
        _LIB = CDLL(shutil.copy(ARGS.lib, Path(tmp) / "libstrategies.so"))
    return _LIB


class FortranPlayer(axl.Player):
    """An original 1980 entry, called with the arguments the axelrod-fortran adapter passes: opponent's last move,
    turn number, both running scores, a random number, own last move."""
    name = "Fortran"
    classifier = dict(memory_depth=float("inf"), stochastic=True, long_run_time=False, inspects_source=False,
                      manipulates_source=False, manipulates_state=False, makes_use_of=set())

    def __init__(self, fname="k92r"):
        self.fname = fname
        super().__init__()
        self.name = fname
        self.f = getattr(fortran_lib(), fname.lower() + "_")
        self.f.restype = c_int
        self.k = self.l = 0

    def strategy(self, opponent):
        t = len(self.history)
        if t:
            p = PAYOFF[(self.history[-1], opponent.history[-1])]
            self.k += p[0]; self.l += p[1]
        j = int(t > 0 and opponent.history[-1] == D); ja = int(t > 0 and self.history[-1] == D)
        a = self.f(byref(c_int(j)), byref(c_int(t + 1)), byref(c_int(self.k)), byref(c_int(self.l)),
                   byref(c_float(self._random.random())), byref(c_int(ja)))
        return D if a else C


def knight_players(traits_file):
    """The 272 in players.index order, as (name, kind, arg, slow) specs."""
    rows = list(csv.DictReader(open(traits_file)))
    return [(r["Name"], "fortran" if r["fortran"] == "1" else "lib",
             r["Name"] if r["fortran"] == "1" else r["python_class"], r["long_run_time"] == "1") for r in rows]


def limit_meta_teams(specs):
    """Cut Meta teams back to the strategies axelrod 4.10 had: Knight's library players, the Python twins of the
    Fortran entries, and the two TfT duplicates Knight left out."""
    rows = list(csv.DictReader(open(ARGS.traits)))
    by = {s.name: s for s in axl.all_strategies}
    known = {by[r["python_class"]] for r in rows if r["python_class"] in by} | {axl.Alexei, axl.ContriteTitForTat}
    axl_meta.ordinary_strategies = [s for s in axl_meta.ordinary_strategies if s in known]


STRATEGY_BY_NAME = {s.name: s for s in axl.all_strategies}


def make_player(spec):
    name, kind, arg, _ = spec
    if kind == "fortran":
        return FortranPlayer(arg)
    if kind == "llm":
        return StochasticStartMemoryOne(label=name, p0=arg[0], four_vector=arg[1])
    p = STRATEGY_BY_NAME[arg]()
    assert str(p) == name, (str(p), name)
    return p


def play_pair(task):
    """All repetitions of one new pairing. Returns per-repetition totals and summed cooperation counts."""
    i, j, turns, noise, seed, reps = task
    t0 = time.time()
    a, b = make_player(SPECS[i]), make_player(SPECS[j])
    scores = np.zeros((reps, 2), dtype=np.int64); coop = np.zeros(2, dtype=np.int64)
    for r in range(reps):
        s = int(np.random.SeedSequence([seed, turns, round(noise * 1000), i, j, r]).generate_state(1)[0])
        m = axl.Match((a, b), turns=turns, noise=noise, seed=s, match_attributes={"length": float("inf")})
        for x, y in m.play():
            p = PAYOFF[(x, y)]
            scores[r, 0] += p[0]; scores[r, 1] += p[1]
            coop[0] += x == C; coop[1] += y == C
    return dict(i=i, j=j, scores=scores.tolist(), coop=coop.tolist(), seconds=time.time() - t0)


def run_pairs(tasks, partial):
    """Play the tasks on a fork pool, appending each finished pair to a jsonl file so a stopped run can resume."""
    done = {}
    if partial.exists():
        for line in open(partial):
            d = json.loads(line); done[(d["i"], d["j"])] = d
    todo = [t for t in tasks if (t[0], t[1]) not in done]
    todo.sort(key=lambda t: not (SPECS[t[0]][3] or SPECS[t[1]][3]))           # slow Meta pairs first
    if todo:
        with open(partial, "a") as out, mp.get_context("fork").Pool(ARGS.processes) as pool:
            for n, d in enumerate(pool.imap_unordered(play_pair, todo, chunksize=1), 1):
                out.write(json.dumps(d) + "\n"); out.flush(); done[(d["i"], d["j"])] = d
                if n % 50 == 0 or n == len(todo):
                    print(f"  {n}/{len(todo)} pairs", flush=True)
    return done


def knight_files(folder, turns, seed):
    base = ARGS.knight / folder
    f = sorted(base.glob(f"full_{turns}_turns_*_repetitions_{seed}_seed_summary.csv"))
    assert len(f) == 1, (folder, turns, seed, f)
    stem = str(f[0])[: -len("summary.csv")]
    return stem, int(re.search(r"_(\d+)_repetitions_", f[0].name).group(1))


def combine(pairs, n_old, turns, stem, knight_reps):
    """277-player scores, ranks and cooperation rates for one tournament."""
    n_new = len(SPECS) - n_old; N = n_old + n_new
    ks = np.loadtxt(stem + "scores.gz", delimiter=",")                   # (reps, 272) totals, self excluded
    if ks.shape[0] != knight_reps:
        ks = ks.T
    kc = np.loadtxt(stem + "cooperation_rates.gz", delimiter=",").T     # rows = player after transposing back
    summary = list(csv.DictReader(open(stem + "summary.csv")))
    med = {r["Name"]: float(r["Median_score"]) for r in summary}
    names = [s[0] for s in SPECS]
    check = np.median(ks / (turns * (n_old - 1)), axis=0)
    err = max(abs(check[i] - med[names[i]]) for i in range(n_old))
    assert err < 1e-6, f"Knight scores.gz does not match summary Median_score (max diff {err})"

    total = np.zeros((knight_reps, N)); coop = np.zeros((N, N))
    total[:, :n_old] = ks
    coop[:n_old, :n_old] = kc
    for (i, j), d in pairs.items():
        sc = np.array(d["scores"]); R = len(sc); idx = np.arange(knight_reps) % R
        total[:, i] += sc[idx, 0]; total[:, j] += sc[idx, 1]
        coop[i, j] = d["coop"][0] / (R * turns); coop[j, i] = d["coop"][1] / (R * turns)
    norm = total / (turns * (N - 1))
    median, mean = np.median(norm, axis=0), norm.mean(axis=0)
    order = sorted(range(N), key=lambda i: -median[i])                  # axelrod's ranking
    rank = np.empty(N, dtype=int); rank[order] = np.arange(N)
    np.fill_diagonal(coop, np.nan)
    coop_rate = np.nanmean(coop, axis=1)
    return [dict(Name=names[i], llm=int(i >= n_old), median_score=median[i], mean_score=mean[i], rank=int(rank[i]) + 1,
                 normalized_rank=rank[i] / (N - 1), cooperation_rate=coop_rate[i]) for i in range(N)]


def validate(n, folder, noise, turns, seed):
    """Play n random pairs from Knight's field and compare with their payoff matrix."""
    stem, _ = knight_files(folder, turns, seed)
    pm = np.loadtxt(stem + "payoff_matrix.gz", delimiter=",")
    rng = np.random.default_rng(0); n_old = 272
    fast = [k for k in range(n_old) if not SPECS[k][3]]
    fort = [k for k in fast if SPECS[k][1] == "fortran"]
    tasks = set()
    while len(tasks) < n:                                                # half the pairs involve a Fortran entry
        i = int(rng.choice(fort if len(tasks) % 2 == 0 else fast)); j = int(rng.choice(fast))
        if i != j:
            tasks.add((min(i, j), max(i, j)))
    tasks = [(i, j, turns, noise, seed, ARGS.reps) for i, j in sorted(tasks)]
    with mp.get_context("fork").Pool(ARGS.processes) as pool:
        res = pool.map(play_pair, tasks, chunksize=1)
    rows = []
    for d in res:
        i, j = d["i"], d["j"]; sc = np.array(d["scores"]) / turns
        ours, theirs = sc[:, 0].mean(), pm[i, j]
        se = sc[:, 0].std(ddof=1) / math.sqrt(len(sc)) if len(sc) > 1 else 0
        rows.append((SPECS[i][0], SPECS[j][0], ours, theirs, ours - theirs, se))
    rows.sort(key=lambda r: -abs(r[4]))
    print(f"{'player':28} {'opponent':28} {'ours':>7} {'Knight':>7} {'diff':>7} {'se':>6}")
    for r in rows[:15]:
        print(f"{r[0][:28]:28} {r[1][:28]:28} {r[2]:7.3f} {r[3]:7.3f} {r[4]:+7.3f} {r[5]:6.3f}")
    exact = sum(abs(r[4]) < 1e-9 for r in rows)
    print(f"{len(rows)} pairs: {exact} exact, max |diff| {max(abs(r[4]) for r in rows):.3f}, "
          f"{sum(abs(r[4]) > 3 * max(r[5], 1e-9) for r in rows)} beyond 3 SE")


def main():
    global ARGS, SPECS
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("condition", choices=CONDITIONS)
    ap.add_argument("--turns", type=int, nargs="+", help="default: the condition's lengths")
    ap.add_argument("--seeds", type=int, nargs="+", help="default: every seed Knight ran for the condition")
    ap.add_argument("--reps", type=int, default=250, help="repetitions per new pair (Knight: 250)")
    ap.add_argument("--processes", type=int, default=4)
    ap.add_argument("--validate", type=int, default=0, metavar="N", help="only check N Knight pairs, then stop")
    for k, v in DEFAULTS.items():
        ap.add_argument(f"--{k}", type=Path, default=v)
    ARGS = ap.parse_args()
    noise, folder, lengths = CONDITIONS[ARGS.condition]
    turns_list = ARGS.turns or lengths
    seeds = ARGS.seeds
    if seeds is None:
        seeds = sorted({int(m.group(1)) for f in (ARGS.knight / folder).glob(f"full_{turns_list[0]}_turns_*_seed_summary.csv")
                        if (m := re.search(r"_(\d+)_seed_summary", f.name))})

    SPECS = knight_players(ARGS.traits)
    idx = [l.strip().strip('"') for l in open(ARGS.knight / folder / "players.index")]
    assert [s[0] for s in SPECS] == idx, "traits order differs from players.index"
    n_old = len(SPECS)
    SPECS += [(name, "llm", (p0, fv), False) for name, p0, fv in LLM_STRATEGIES]
    limit_meta_teams(SPECS)
    for s in SPECS:                                                      # every name must match Knight's
        make_player(s)

    if ARGS.validate:
        return validate(ARGS.validate, folder, noise, turns_list[0], seeds[0])

    ARGS.out.mkdir(parents=True, exist_ok=True); (ARGS.out / "pairs").mkdir(exist_ok=True)
    llm = range(n_old, len(SPECS))
    per_t, timing = [], []
    for turns in turns_list:
        for seed in seeds:
            stem, knight_reps = knight_files(folder, turns, seed)
            tasks = [(i, j, turns, noise, seed, ARGS.reps) for j in range(len(SPECS)) for i in llm
                     if j < n_old or j > i]
            print(f"{ARGS.condition}: {turns} turns, seed {seed}, {len(tasks)} pairs x {ARGS.reps} reps", flush=True)
            t0 = time.time()
            partial = ARGS.out / "pairs" / f"{ARGS.condition}_{turns}t_seed{seed}_{ARGS.reps}reps.jsonl"
            pairs = run_pairs(tasks, partial)
            wanted = {(t[0], t[1]) for t in tasks}
            pairs = {k: v for k, v in pairs.items() if k in wanted}
            print(f"  done in {time.time() - t0:.0f} s wall", flush=True)
            for (i, j), d in pairs.items():
                timing.append(dict(condition=ARGS.condition, turns=turns, seed=seed, reps=ARGS.reps,
                                   player=SPECS[i][0], opponent=SPECS[j][0], slow=int(SPECS[j][3]),
                                   seconds=d["seconds"]))
            for row in combine(pairs, n_old, turns, stem, knight_reps):
                per_t.append(dict(condition=ARGS.condition, noise=noise, turns=turns, seed=seed, reps=ARGS.reps, **row))

    tag = ARGS.condition if ARGS.reps == 250 else f"{ARGS.condition}_{ARGS.reps}reps"
    write(ARGS.out / f"{tag}_per_tournament.csv", per_t)
    write(ARGS.out / f"timing_{tag}.csv", timing)
    by = {}
    for r in per_t:
        by.setdefault(r["Name"], []).append(r)
    summ = [dict(Name=n, llm=rs[0]["llm"], tournaments=len(rs),
                 **{k: float(np.mean([r[k] for r in rs])) for k in
                    ["mean_score", "median_score", "rank", "normalized_rank", "cooperation_rate"]})
            for n, rs in by.items()]
    summ.sort(key=lambda r: r["normalized_rank"])
    write(ARGS.out / f"{tag}_summary.csv", summ)
    print(f"\n{ARGS.condition}: LLM players among {len(SPECS)} (mean over {len(per_t) // len(SPECS)} tournaments)")
    for r in summ:
        if r["llm"]:
            print(f"  {r['Name']:22} rank {r['rank']:6.1f}  norm rank {r['normalized_rank']:.3f}  "
                  f"score {r['mean_score']:.3f}  coop {r['cooperation_rate']:.3f}")


def write(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main()
