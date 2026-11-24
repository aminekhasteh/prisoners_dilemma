"""Turn the tournament results into the small CSVs the figure scripts read (kept in data/ so figures redraw fast).
Usage: python3 prep_data.py RESULTS_DIR data [SUFFIX]
With RESULTS_DIR = results_m2 and SUFFIX = _m2 it writes the 282-player versions (ranks_by_setting_m2.csv, field_63_m2.csv).
RESULTS_DIR = scripts/article2_llm_field/results on branch article2-llm-field (the *_per_tournament.csv files).
Writes:
  data/ranks_by_setting.csv: the five LLM players and Tit for Tat (k92r), mean / min / max rank out of 277 and the
      number of tournaments, for every (condition, noise, turns).
  data/field_63.csv: all 277 players at 63 turns, no noise: mean rank and mean of the median score per turn over the
      20 tournaments."""
import sys
from pathlib import Path
import pandas as pd

RES, OUT = Path(sys.argv[1]), Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
SUF = sys.argv[3] if len(sys.argv) > 3 else ""
d = pd.concat([pd.read_csv(RES / f"{c}_per_tournament.csv") for c in ("standard", "noise1", "noise5")])
keep = d[(d.llm == 1) | (d.Name == "k92r")]
r = (keep.groupby(["condition", "noise", "turns", "Name"])
     .agg(mean_rank=("rank", "mean"), min_rank=("rank", "min"), max_rank=("rank", "max"),
          tournaments=("seed", "nunique"), cooperation_rate=("cooperation_rate", "mean")).reset_index())
r.to_csv(OUT / f"ranks_by_setting{SUF}.csv", index=False, float_format="%.4f")
f = d[(d.condition == "standard") & (d.turns == 63)]
f = (f.groupby(["Name", "llm"]).agg(mean_rank=("rank", "mean"), mean_score=("median_score", "mean"),
                                   tournaments=("seed", "nunique")).reset_index().sort_values("mean_rank"))
f.to_csv(OUT / f"field_63{SUF}.csv", index=False, float_format="%.5f")
print(r.pivot_table(index="Name", columns=["condition", "turns"], values="mean_rank").round(1).to_string())
print(r.groupby(["condition", "turns"]).tournaments.max().to_string())
