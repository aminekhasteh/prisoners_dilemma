"""Ranks of every LLM player in the field with the new models (Knight's 272 + Pal's 5 memory-1 and 5 memory-2 + 15 from
the new elicitation = 297 players). Usage: python3 prep_new.py RESULTS_NEW_DIR data
RESULTS_NEW_DIR = scripts/article2_llm_field/results_new. Reads standard_per_tournament.csv (all five lengths; if it
is missing, standard63_per_tournament.csv, 63 turns only), noise1_per_tournament.csv and noise5_per_tournament.csv,
whichever exist. Writes data/new_ranks.csv: one row per (setting, player) for the 25 LLM players and Tit for Tat
(k92r), with model (name without the memory prefix), memory (1 or 2), source, mean_rank, tournaments and players
(field size).
setting: s63, s77, s151, s156, s308 = no noise at that game length; slen = no noise, mean over the lengths (each
length weighted equally, as in prep_m2.py); n1 / n5 = 63 turns at 1% / 5% noise."""
import sys
from pathlib import Path
import pandas as pd

RES, OUT = Path(sys.argv[1]), Path(sys.argv[2])
std = RES / "standard_per_tournament.csv"
std = pd.read_csv(std if std.exists() else RES / "standard63_per_tournament.csv")
parts = [("s%d" % t, std[std.turns == t]) for t in sorted(std.turns.unique())]
for f, key in (("noise1_per_tournament.csv", "n1"), ("noise5_per_tournament.csv", "n5")):
    if (RES / f).exists():
        d = pd.read_csv(RES / f)
        parts.append((key, d[d.turns == 63]))
rows = []
for key, d in parts:
    n = int(d.groupby("seed").Name.count().max())
    d = d[(d.llm == 1) | (d.Name == "k92r")].copy()
    d["model"] = d.Name.str.replace(r"^LLM(-m2)?: ", "", regex=True)
    d["memory"] = d.Name.str.startswith("LLM-m2").map({True: 2, False: 1})
    g = (d.groupby(["Name", "model", "memory"], dropna=False)
         .agg(source=("source", "first"), mean_rank=("rank", "mean"), tournaments=("seed", "nunique")).reset_index())
    rows.append(g.assign(setting=key, players=n))
lengths = [x for x in rows if x.setting.iloc[0] not in ("n1", "n5")]
if len(lengths) > 1:   # all lengths: the mean of the per-length means
    rows.append(pd.concat(lengths).groupby(["Name", "model", "memory"], dropna=False)
                .agg(source=("source", "first"), mean_rank=("mean_rank", "mean"), tournaments=("tournaments", "sum"),
                     players=("players", "max")).reset_index().assign(setting="slen"))
r = pd.concat(rows)[["setting", "Name", "model", "memory", "source", "mean_rank", "tournaments", "players"]]
r.to_csv(OUT / "new_ranks.csv", index=False, float_format="%.4f")
print(r.pivot_table(index="Name", columns="setting", values="mean_rank", sort=False).round(1).to_string())
