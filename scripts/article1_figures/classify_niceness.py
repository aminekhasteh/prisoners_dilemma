"""Label every strategy nice / nasty / end-game by replaying matches and checking who defects first.

Axelrod's definition: a strategy is nice if it is never the first to defect. The dataset only has aggregate
transition rates, which can't tell a first defection from a delayed retaliation, so instead each strategy plays
a fixed set of probe opponents (plus a copy of itself) and we look at the first defection in each match.

  nice      never defected first (alone or on the same turn as the opponent) in any match
  end-game  defected first only in the last 3 turns of a match (exploits a known match length)
  nasty     defected first earlier than that in at least one match

Matches are 200 turns, 2 repetitions when either side is stochastic. The Meta*/NMWE* ensembles run 50 turns,
1 repetition, no self-play: they run dozens of strategies per move and take ~3 s per 50-turn match on this CPU.
Runtime on the i5-3570 with 3 workers is about 10 minutes. Needs the axelrod library (tested with 4.14) and runs
best single-threaded per worker: OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1.

Usage: python classify_niceness.py data/strategy_names.txt data/niceness.csv
(strategy_names.txt = the 195 names in the standard tournaments of Data/combined_dataset.parquet)"""
import csv, sys, warnings, multiprocessing as mp
warnings.filterwarnings("ignore")
import axelrod as axl

C, D = axl.Action.C, axl.Action.D
TURNS, REPS, SLOW_TURNS, ENDGAME = 200, 2, 50, 3
SLOW = ("Meta", "NMWE", "Nice Meta")
PROBES = ["Cooperator", "Defector", "Tit For Tat", "Suspicious Tit For Tat", "Grudger", "Alternator", "Random",
          "Tit For 2 Tats", "Win-Stay Lose-Shift", "Prober", "Hard Prober", "Cycler CCD", "Tricky Defector", "Bully",
          "Go By Majority", "Gradual", "Handshake", "Calculator", "Joss", "GTFT"]


class FoolMeForever(axl.Player):
    """Removed from the library: defect until the opponent defects, then cooperate forever."""
    name = "Fool Me Forever"
    classifier = dict(memory_depth=float("inf"), stochastic=False, long_run_time=False, inspects_source=False,
                      manipulates_source=False, manipulates_state=False, makes_use_of=set())

    def strategy(self, opponent):
        return C if opponent.defections > 0 else D


# the dataset was made with an older library version; map its names onto current classes
LOOKUP = {s.name: s for s in axl.strategies}
LOOKUP["Fool Me Forever"] = FoolMeForever
for old in ["Davis", "Feld", "Grofman", "Joss", "Nydegger", "Shubik", "Stein and Rapoport", "Tullock"]:
    LOOKUP[old] = LOOKUP["First by " + old]
for old in ["Champion", "Eatherley", "Tester"]:
    LOOKUP[old] = LOOKUP["Second by " + old]
for n in ["", " 5", " 10", " 20", " 40"]:
    LOOKUP["Soft Go By Majority" + n] = LOOKUP["Go By Majority" + n]
LOOKUP["Slow Tit For Two Tats"] = LOOKUP["Slow Tit For Two Tats 2"]


def first_defection(h1, h2):
    """(turn, player 1 defected, player 2 defected) at the first turn anyone defects, or None."""
    for t, (a, b) in enumerate(zip(h1, h2)):
        if a == D or b == D:
            return t, a == D, b == D
    return None


def classify(name):
    slow = name.startswith(SLOW)
    turns = SLOW_TURNS if slow else TURNS
    matches, first, early = 0, 0, 0
    earliest = None
    for k, probe in enumerate(PROBES if slow else PROBES + [name]):
        stochastic = axl.Classifiers["stochastic"](LOOKUP[name]()) or axl.Classifiers["stochastic"](LOOKUP[probe]())
        for r in range(1 if slow or not stochastic else REPS):
            p1, p2 = LOOKUP[name](), LOOKUP[probe]()
            axl.Match((p1, p2), turns=turns, seed=1000 * k + r).play()
            matches += 1
            fd = first_defection(p1.history, p2.history)
            if fd and fd[1]:
                first += 1
                early += fd[0] < turns - ENDGAME
                earliest = fd[0] if earliest is None else min(earliest, fd[0])
    label = "nice" if first == 0 else "end-game" if early == 0 else "nasty"
    return dict(Name=name, label=label, matches=matches, share_first_defect=round(first / matches, 4),
                earliest_first_defect=earliest, turns=turns)


if __name__ == "__main__":
    names = sorted({l.strip() for l in open(sys.argv[1]) if l.strip()})
    missing = [n for n in names if n not in LOOKUP]
    assert not missing, f"no library class for {missing}"
    names.sort(key=lambda n: not n.startswith(SLOW))           # slow ones first so they don't finish last
    rows = []
    with mp.Pool(3) as pool:
        for k, row in enumerate(pool.imap_unordered(classify, names), 1):
            rows.append(row)
            if k % 20 == 0 or k == len(names):
                print(f"{k}/{len(names)}", flush=True)
    rows.sort(key=lambda r: r["Name"])
    with open(sys.argv[2], "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    counts = {l: sum(r["label"] == l for r in rows) for l in ("nice", "nasty", "end-game")}
    print(counts)
