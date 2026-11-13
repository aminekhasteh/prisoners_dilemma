"""Classifier traits for the 272 players of Knight et al. 2025 (Zenodo 17250038).

Python strategies: matched to the installed axelrod library (4.14) by repr or by name. Fortran entries: stochastic flag
from the archive's fortran_characteristics.json, and the classifier of the Python re-implementation where one exists.
Usage (axelrod venv): python strategy_traits.py <knight data dir> data/strategy_traits.csv"""
import csv, json, sys, warnings
warnings.filterwarnings("ignore")
import axelrod as axl

src, out = sys.argv[1], sys.argv[2]
names = [l.strip().strip('"') for l in open(f"{src}/full_tournament/players.index") if l.strip()]
fort = json.load(open(f"{src}/full_tournament/fortran_characteristics.json"))
by_repr = {str(s()): s for s in axl.strategies}
by_name = {s.name: s for s in axl.strategies}
by_repr_base = {}
for r, s in by_repr.items(): by_repr_base.setdefault(r.split(":")[0], s)

def find(n):
    return by_repr.get(n) or by_name.get(n) or by_name.get(n.split(":")[0]) or by_repr_base.get(n.split(":")[0])

rows = []
for n in names:
    is_fortran = n in fort
    cls = find(fort[n]["axelrod-python_class"].split(":")[0]) if is_fortran and fort[n]["axelrod-python_class"] else (None if is_fortran else find(n))
    row = dict(Name=n, fortran=int(is_fortran), python_class=cls.name if cls else "", author=fort[n]["author"] if is_fortran else "",
               original_rank=fort[n]["original_rank"] if is_fortran else "")
    if cls:
        p = cls(); c = dict(p.classifier); c.setdefault("makes_use_of", axl.Classifiers["makes_use_of"](p))
        row.update(Stochastic=int(c["stochastic"]), Memory_depth=c["memory_depth"],
                   Makes_use_of_game=int("game" in c["makes_use_of"]), Makes_use_of_length=int("length" in c["makes_use_of"]),
                   long_run_time=int(bool(c.get("long_run_time"))))
    else:
        # Fortran entry with no Python twin: the function gets the turn number and both running scores and keeps its own
        # variables between calls (compiled with -fno-automatic), so it can remember the whole match (memory depth inf).
        # It is never told the match length or the payoff matrix.
        row.update(Stochastic=int(fort[n]["stochastic"]), Memory_depth=float("inf"), Makes_use_of_game=0,
                   Makes_use_of_length=0, long_run_time=0)
    if is_fortran: row["Stochastic"] = int(fort[n]["stochastic"])
    rows.append(row)
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), "players;", sum(r["fortran"] for r in rows), "fortran;",
      "no class:", [r["Name"] for r in rows if not r["python_class"] and not r["fortran"]],
      "; fortran without python class:", sum(1 for r in rows if r["fortran"] and not r["python_class"]))
