"""Nice / nasty for all 272 players, read off Knight et al.'s pairwise cooperation-rate matrices.

Axelrod: nice = never the first to defect. Until someone defects, every opponent looks like Cooperator, and a nice
opponent never defects first. So in these data a nice strategy is one that cooperated on every turn of every match
against every other nice strategy: the largest group, containing Cooperator, with 100% mutual cooperation in all
100 no-noise tournaments (5 lengths x 20 seeds x 250 repetitions). Everything else defected first at least once.
Match length was hidden from the players in these runs, so there is no end-game group here.
Usage: python niceness_from_matrix.py <knight data dir> data/niceness_matrix.csv"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

src, out = Path(sys.argv[1]) / "full_tournament", sys.argv[2]
names = [l.strip().strip('"') for l in open(src / "players.index") if l.strip()]
files = sorted(src.glob("full_*_cooperation_rates.gz"))
# the archive stores the transpose (main.py), so .T gives rows = "my cooperation rate against them"
lo = np.ones((len(names), len(names)))
for f in files:
    lo = np.minimum(lo, np.loadtxt(f, delimiter=",").T)        # lowest cooperation rate of row player vs column player
i_coop, i_def = names.index("Cooperator"), names.index("Defector")
assert lo[i_coop].min() == 1 and np.loadtxt(files[0], delimiter=",").T[i_def].max() == 0, "rows are not 'my cooperation rate vs them'"

full = lo >= 1 - 1e-12
nice = set(np.flatnonzero(full[:, i_coop]))                   # never defected against Cooperator
while True:                                                    # drop anyone who defected against a member (self-play included)
    bad = {i for i in nice if not all(full[i, j] for j in nice)}
    if not bad: break
    worst = max(bad, key=lambda i: sum(not full[i, j] for j in nice)); nice.discard(worst)
rows = [dict(Name=n, label_matrix="nice" if i in nice else "nasty", min_coop_vs_cooperator=lo[i, i_coop],
             min_coop_vs_nice=min(lo[i, j] for j in nice), always_cooperates_with_cooperator=bool(full[i, i_coop]))
        for i, n in enumerate(names)]
d = pd.DataFrame(rows); d.to_csv(out, index=False)
print(len(files), "matrices;", d.label_matrix.value_counts().to_dict(),
      "; cooperate fully with Cooperator but not nice:", d[(d.label_matrix == "nasty") & d.always_cooperates_with_cooperator].Name.tolist())
