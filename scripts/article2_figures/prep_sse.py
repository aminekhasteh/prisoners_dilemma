"""Inputs for llm_sse.py: SSE, rank and nice / nasty for the 35 LLM players and for Knight et al.'s 272 strategies,
all at 63 turns with no noise, ranked in the same 307-player field.

  data/sse_llm.csv    copied from results_m3/llm_sse.csv (sse_llm.py, PR #22): sse_played (Article 1's SSE, from the
                      CC/CD/DC/DD -> C rates in play against Knight's field), sse_vector, mean_rank (307 players),
                      nice_rule and p_never_first_63 (chance of never being the first to defect in a 63-turn game against
                      Always Cooperate, from the elicited tables). Article 1's rule: nice = never the first to defect.
                      An independent replay here (2,000 games each against Always Cooperate) gave the same label for all
                      35. A nasty player with p_never_first_63 >= 0.95 is drawn as "nearly nice".
  data/sse_field.csv  one row per Knight strategy: median SSE over Knight et al.'s twenty 63-turn no-noise tournaments
                      (their CC/CD/DC/DD_to_C rates, the same formula as Article 1), Article 1's nice / nasty group, and
                      mean rank in the 307-player field.

Usage: python3 prep_sse.py LLM_SSE_CSV KNIGHT_DATA_DIR KNIGHT_SSE_CSV RANKS_CSV data
  LLM_SSE_CSV     scripts/article2_llm_field/results_m3/llm_sse.csv (branch claude/project-thread-hb9k8l, PR #22)
  KNIGHT_DATA_DIR Data/knight2026/src/data
  KNIGHT_SSE_CSV  article1/knight2026/results/sse_all_circular.csv (Article 1's 272-strategy nice / nasty groups)
  RANKS_CSV       scripts/article2_llm_field/results_m3/standard63_summary.csv (307 players)"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

llm_csv, knight_dir, knight_sse, ranks_csv, out = map(Path, sys.argv[1:6])

# Article 1's SSE (scripts/knight272/build_dataset.py): squared distance of p = (CC, CD, DC, DD -> C) from the plane of
# zero-determinant strategies, R, S, T, P = 3, 0, 5, 1
Cm = np.array([[2.0, 2.0], [-1.0, 4.0], [4.0, -1.0], [0.0, 0.0]])
PROJ = np.eye(4) - Cm @ np.linalg.pinv(Cm)
sse = lambda p: (((p - np.array([1.0, 1.0, 0.0, 0.0])) @ PROJ.T) ** 2).sum(axis=1)

llm = pd.read_csv(llm_csv)
keep = ["Name", "memory", "source", "sse_played", "sse_vector", "mean_rank", "nice_rule", "p_never_first_63",
        "p_CC", "p_CD", "p_DC", "p_DD"]
llm[keep].to_csv(out / "sse_llm.csv", index=False, float_format="%.4f")

rates = ["CC_to_C_rate", "CD_to_C_rate", "DC_to_C_rate", "DD_to_C_rate"]
fs = sorted(f for f in (knight_dir / "full_tournament").glob("full_63_turns_*_seed_summary.csv") if not f.name.startswith("._"))
k = pd.concat([pd.read_csv(f) for f in fs])
k["SSE"] = sse(k[rates].to_numpy())
field = k.groupby("Name").SSE.median().rename("sse").reset_index()
# Article 1's file drops parameters from names ("Soft Go By Majority: 10" -> "Soft Go By Majority"), so match on the
# base name; where variants sharing a base name disagree, the group is "mixed" (none of the labelled classics are)
grp = pd.read_csv(knight_sse)[["Name", "group"]]
grp["Name"] = grp.Name.str.replace(" (Tit For Tat)", "", regex=False)   # Article 1 tagged k92r for its labels
grp = grp.groupby("Name").group.agg(lambda g: g.iloc[0] if g.nunique() == 1 else "mixed")
field["group"] = field.Name.str.split(":").str[0].map(grp)
rk = pd.read_csv(ranks_csv)[["Name", "rank"]].rename(columns={"rank": "mean_rank"})
field = field.merge(rk, on="Name", how="left", validate="1:1")
assert field.group.notna().all() and field.mean_rank.notna().all(), field[field.isna().any(axis=1)]
field.to_csv(out / "sse_field.csv", index=False, float_format="%.6g")
print(len(fs), "Knight 63-turn tournaments,", len(field), "strategies;", (llm.nice_rule == "nice").sum(), "nice LLM players")
