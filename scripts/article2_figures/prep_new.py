"""Ranks of every LLM player in the field with the new models (Knight's 272 + Pal's 5 memory-1 and 5 memory-2 + 15 from
the new elicitation = 297 players). Usage: python3 prep_new.py RESULTS_NEW_DIR data
RESULTS_NEW_DIR = scripts/article2_llm_field/results_new on branch article2-llm-field. Reads whichever of
standard63_per_tournament.csv, standard_per_tournament.csv (its 63-turn rows), noise1_per_tournament.csv and
noise5_per_tournament.csv exist. Writes data/new_ranks.csv: setting (s63, n1, n5), Name, model (name without the
memory prefix), memory (1 or 2), source, mean_rank, tournaments, players (field size)."""
import sys
from pathlib import Path
import pandas as pd

RES, OUT = Path(sys.argv[1]), Path(sys.argv[2])
parts = []
for f, key in (("standard63_per_tournament.csv", "s63"), ("standard_per_tournament.csv", "s63"),
               ("noise1_per_tournament.csv", "n1"), ("noise5_per_tournament.csv", "n5")):
    if (RES / f).exists() and not any(k == key for k, _ in parts):
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
r = pd.concat(rows)[["setting", "Name", "model", "memory", "source", "mean_rank", "tournaments", "players"]]
r.to_csv(OUT / "new_ranks.csv", index=False, float_format="%.4f")
print(r.sort_values(["setting", "mean_rank"]).to_string(index=False))
