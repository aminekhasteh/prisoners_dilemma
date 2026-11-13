"""Replay all 272 players of Knight et al. 2025 against the article's fixed cover opponent and save their moves.

Library strategies run through axelrod (4.14). The 63 original entries run as the original Fortran, called straight
from lib/libstrategies.so (built with gfortran from github.com/Axelrod-Python/TourExec), with the same arguments the
axelrod-fortran adapter passes: opponent's last move, turn number, both running scores, a random number, own last move.
Usage (axelrod venv): python replay_moves.py data/strategy_traits.csv data/niceness.csv data/cover_opponent_140.txt data/cover_moves_140.csv"""
import csv, shutil, sys, tempfile, warnings, random, multiprocessing as mp
from ctypes import CDLL, byref, c_float, c_int
from pathlib import Path
warnings.filterwarnings("ignore")
import axelrod as axl

C, D = axl.Action.C, axl.Action.D
HERE = Path(__file__).resolve().parent
OPP = open(sys.argv[3]).read().strip()
SEED = 2026
PAYOFF = {("C", "C"): (3, 3), ("C", "D"): (0, 5), ("D", "C"): (5, 0), ("D", "D"): (1, 1)}

class Scripted(axl.Player):
    """Plays the fixed opponent sequence, whatever the other player does."""
    name = "Scripted"
    classifier = dict(memory_depth=float("inf"), stochastic=False, long_run_time=False, inspects_source=False,
                      manipulates_source=False, manipulates_state=False, makes_use_of=set())
    def strategy(self, opponent):
        return C if OPP[len(self.history)] == "C" else D

def fortran_moves(fname):
    with tempfile.TemporaryDirectory() as tmp:                 # private copy: the Fortran keeps state between calls
        lib = CDLL(shutil.copy(HERE / "lib" / "libstrategies.so", Path(tmp) / f"{fname}.so"))
        f = getattr(lib, fname.lower() + "_"); f.restype = c_int
        rng = random.Random(SEED); mine, k, l = "", 0, 0
        for t in range(len(OPP)):
            j = 0 if t == 0 else int(OPP[t - 1] == "D"); ja = 0 if t == 0 else int(mine[-1] == "D")
            a = f(byref(c_int(j)), byref(c_int(t + 1)), byref(c_int(k)), byref(c_int(l)), byref(c_float(rng.random())), byref(c_int(ja)))
            mine += "D" if a else "C"
            p = PAYOFF[(mine[-1], OPP[t])]; k += p[0]; l += p[1]
        return mine

def play(row):
    if row["fortran"] == "1":
        return row["Name"], fortran_moves(row["Name"])
    cls = {s.name: s for s in axl.strategies}[row["python_class"]]
    p = cls(); axl.Match((p, Scripted()), turns=len(OPP), seed=SEED).play()
    return row["Name"], "".join(str(a) for a in p.history)

if __name__ == "__main__":
    traits = list(csv.DictReader(open(sys.argv[1])))
    label = {r["Name"]: r["label"] for r in csv.DictReader(open(sys.argv[2]))}
    traits.sort(key=lambda r: r["long_run_time"] != "1")       # slow ensembles first
    with mp.get_context("fork").Pool(4) as pool:
        moves = dict(pool.imap_unordered(play, traits, chunksize=1))
    with open(sys.argv[4], "w", newline="") as out:
        w = csv.writer(out); w.writerow(["Name", "moves", "stochastic", "label", "fortran"])
        for r in sorted(traits, key=lambda r: r["Name"]):
            w.writerow([r["Name"], moves[r["Name"]], r["Stochastic"], label[r["Name"]], r["fortran"]])
    print(len(moves), "players,", len(OPP), "turns")
