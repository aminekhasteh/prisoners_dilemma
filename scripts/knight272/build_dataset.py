"""Turn the Knight et al. 2026 per-seed summaries (Zenodo 17250038) into one table shaped like our Glynatsi-based
Data/combined_dataset.parquet: one row per strategy per tournament, with Normalized_Rank, SSE and the cooperation ratios.

A "tournament" here is one (setting, turns, seed) file: a 272-player round robin, 250 repetitions.
  standard : no noise, turns in {63, 77, 151, 156, 308}, 20 seeds each  -> 100 tournaments
  noise 1% : 63 turns only, 13 seeds;  noise 5% : 63 turns only, 7 seeds
Usage: python build_dataset.py <knight data dir> data/strategy_traits.csv data/knight272.parquet"""
import re, sys
from pathlib import Path
import numpy as np
import pandas as pd


SETTINGS = {"full_tournament": 0.0, "full_tournament_1_percent_noise": 0.01, "full_tournament_5_percent_noise": 0.05}

# SSE (Knight et al., "Recognising and evaluating the effectiveness of extortion"): squared distance of the memory-one
# vector p = (CC, CD, DC, DD -> C) from the plane of zero-determinant strategies, for R, S, T, P = 3, 0, 5, 1.
C = np.array([[2.0, 2.0], [-1.0, 4.0], [4.0, -1.0], [0.0, 0.0]])       # columns: (S_x - P), (S_y - P)
PROJ = np.eye(4) - C @ np.linalg.pinv(C)

def sse(p):
    r = (p - np.array([1.0, 1.0, 0.0, 0.0])) @ PROJ.T
    return (r ** 2).sum(axis=1)

if __name__ == "__main__":
    src, traits_csv, out = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    frames = []
    for folder, noise in SETTINGS.items():
        for f in sorted((src / folder).glob("full_*_seed_summary.csv")):
            turns, reps, seed = map(int, re.match(r"full_(\d+)_turns_(\d+)_repetitions_(\d+)_seed", f.name).groups())
            d = pd.read_csv(f)
            d["turns"], d["repetitions"], d["seed"], d["noise"], d["size"] = turns, reps, seed, noise, len(d)
            d["tournament"] = f"{'std' if noise == 0 else f'noise{int(noise * 100)}'}_{turns}_{seed}"
            frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df["Normalized_Rank"] = df["Rank"] / (df["size"] - 1)
    rates = ["CC_to_C_rate", "CD_to_C_rate", "DC_to_C_rate", "DD_to_C_rate"]
    df["SSE"] = sse(df[rates].to_numpy())
    g = df.groupby("tournament")["Cooperation_rating"]
    for stat in ("max", "min", "median", "mean"):
        df[f"Cooperation_rating_{stat}"] = g.transform(stat)
        df[f"Cooperation_rating_comp_to_{stat}"] = df["Cooperation_rating"] / df[f"Cooperation_rating_{stat}"]
    df = df.merge(pd.read_csv(traits_csv), on="Name", how="left", validate="m:1")
    assert df["fortran"].notna().all()
    depth = df["Memory_depth"].astype(float)
    df["memory_usage"] = np.where(np.isinf(depth), 1.0, np.minimum(depth / df["turns"], 1.0))
    df.loc[depth.isna(), "memory_usage"] = np.nan
    df["has_noise"] = (df["noise"] > 0).astype(int)
    df["probend"], df["has_probend"] = 0.0, 0
    df["dataset"] = np.where(df["noise"] > 0, "noise", "standard")
    df.to_parquet(out, index=False)
    print(df.groupby(["noise", "turns"])["tournament"].nunique())
    print(df.shape, "missing rates:", df[rates].isna().sum().to_dict())
