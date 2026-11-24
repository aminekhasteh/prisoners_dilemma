"""Ranks of the memory-1 and memory-2 LLM players in the 282-player field (Knight's 272 + 5 memory-1 + 5 memory-2).
Usage: python3 prep_m2.py RESULTS_M2_DIR data
RESULTS_M2_DIR = scripts/article2_llm_field/results_m2 on branch article2-llm-field. Reads whichever of
standard_per_tournament.csv (all five lengths), standard63_per_tournament.csv (63 turns only, used if the full file
is missing), noise1_per_tournament.csv and noise5_per_tournament.csv exist.
Writes data/m2_ranks.csv: one row per (setting, player) for the ten LLM players and Tit for Tat (k92r), with
model (shared by the memory-1 and memory-2 version), memory (1 or 2), mean_rank out of 282 and tournaments.
setting: s63 = 63 turns, no noise; slen = no noise, mean over the five lengths (each length weighted equally);
n1 / n5 = 63 turns at 1% / 5% noise."""
import sys
from pathlib import Path
import pandas as pd

RES, OUT = Path(sys.argv[1]), Path(sys.argv[2])
std = RES / "standard_per_tournament.csv"
std = std if std.exists() else RES / "standard63_per_tournament.csv"
parts = [pd.read_csv(std)] + [pd.read_csv(RES / f) for f in ("noise1_per_tournament.csv", "noise5_per_tournament.csv")
                              if (RES / f).exists()]
d = pd.concat(parts)
d = d[(d.llm == 1) | (d.Name == "k92r")].copy()
d["model"] = d.Name.str.replace(r"^LLM(-m2)?: ", "LLM: ", regex=True)
d["memory"] = d.Name.str.startswith("LLM-m2").map({True: 2, False: 1})
by = (d.groupby(["condition", "turns", "model", "memory"])
      .agg(mean_rank=("rank", "mean"), tournaments=("seed", "nunique")).reset_index())
rows = []
s = by[by.condition == "standard"]
rows.append(s[s.turns == 63].assign(setting="s63"))
if s.turns.nunique() > 1:
    rows.append(s.groupby(["model", "memory"]).agg(mean_rank=("mean_rank", "mean"), tournaments=("tournaments", "sum"),
                                                    lengths=("turns", "nunique")).reset_index().assign(setting="slen"))
for c, k in (("noise1", "n1"), ("noise5", "n5")):
    if (by.condition == c).any():
        rows.append(by[by.condition == c].assign(setting=k))
r = pd.concat(rows)[["setting", "model", "memory", "mean_rank", "tournaments"] + (["lengths"] if "lengths" in pd.concat(rows) else [])]
r.to_csv(OUT / "m2_ranks.csv", index=False, float_format="%.4f")
print(r.pivot_table(index="model", columns=["setting", "memory"], values="mean_rank").round(1).to_string())
