"""Test how the "noise flip" depends on the range of noise and game length.

The flip is the gap in mean normalized rank between strategies above and below
their tournament's median cooperation rate (lower rank = better). Here the unit
is the tournament, and intervals resample tournaments.

  flip_by_range.csv    gap at the paper's range (noise, ending chance <= 0.1) and
                       the full range, with the paper's Table 4 correlation.
  flip_by_horizon.csv  gap by game length, fixed against the expected length
                       (1 / ending chance). Realized lengths are not in the data.
  flip_meaning.csv     same strategies in the same lineup: does their cooperation
                       rate under noise still rank them as it does without noise?

Exact duplicate tournaments in the source files are dropped first.

Usage: python scripts/audit_flip.py [path/to/combined_dataset.parquet]
"""
import sys

import numpy as np
import pandas as pd

from train_and_explain import DATA, RESULTS, SEED

X = "Cooperation_rating_comp_to_median"
Y = "Normalized_Rank"
N_BOOT = 2000
PAPER_TABLE4 = {"standard": -0.330, "noise": 0.326, "probend": -0.065, "probend_noise": 0.614}
LENGTHS = [0, 2, 5, 10, 20, 50, 100, 200, np.inf]
NOISE_LEVELS = [0, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1]


def tournament_gaps(d):
    above = d.assign(above=d[X] > 1).groupby(["seed", "above"])[Y].mean().unstack()
    both = above.dropna()  # nobody above the median: no gap to measure
    return both[True] - both[False]


def summarize(gaps, rng):
    v = gaps.to_numpy()
    boots = rng.choice(v, (N_BOOT, len(v))).mean(axis=1)
    low, high = np.percentile(boots, [2.5, 97.5])
    return {"tournaments": len(v), "gap": v.mean(), "ci_low": low, "ci_high": high,
            "cohens_d": v.mean() / v.std(ddof=1)}


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DATA
    df = pd.read_parquet(path, columns=["dataset", "seed", "Name", "turns", "noise", "probend",
                                        "Cooperation_rating", X, Y])
    before = len(df)
    df = df.drop_duplicates(["dataset", "seed", "Name"])
    print(f"dropped {before - len(df)} duplicate rows of {before}")
    rng = np.random.default_rng(SEED)
    by_set = {k: g for k, g in df.groupby("dataset")}

    restricted = {
        "standard": by_set["standard"],
        "noise": by_set["noise"].query("noise <= 0.1"),
        "probend": by_set["probend"].query("probend <= 0.1"),
        "probend_noise": by_set["probend_noise"].query("noise <= 0.1 and probend <= 0.1"),
    }
    rows = []
    for name, d_low in restricted.items():
        for label, d in (("paper range", d_low), ("full range", by_set[name])):
            medians = d.groupby("Name")[[X, Y]].median()
            tft = d.groupby("Name")[Y].median()
            rows.append({
                "setting": name, "range": label, **summarize(tournament_gaps(d), rng),
                "strategy_median_spearman": medians[X].corr(medians[Y], method="spearman"),
                "paper_table4_spearman": PAPER_TABLE4[name] if label == "paper range" else np.nan,
                "tit_for_tat_median_rank": tft["Tit For Tat"],
                "tit_for_tat_position_of_195": int(tft.rank()["Tit For Tat"]),
            })
    by_range = pd.DataFrame(rows)
    by_range.to_csv(RESULTS / "flip_by_range.csv", index=False)

    horizon = []
    for kind, d, length in (("fixed", by_set["standard"], lambda t: t["turns"]),
                            ("early end", by_set["probend"], lambda t: 1 / t["probend"])):
        gaps = tournament_gaps(d)
        params = d.groupby("seed")[["turns", "probend"]].first().reindex(gaps.index)
        bins = pd.cut(length(params), LENGTHS)
        for interval, g in gaps.groupby(bins, observed=True):
            horizon.append({"game": kind, "length_turns": str(interval), **summarize(g, rng)})
    by_horizon = pd.DataFrame(horizon)
    by_horizon.to_csv(RESULTS / "flip_by_horizon.csv", index=False)

    base = by_set["standard"].set_index(["seed", "Name"])["Cooperation_rating"]
    noisy = by_set["noise"]
    meaning = []
    for interval, d in noisy.groupby(pd.cut(noisy["noise"], NOISE_LEVELS), observed=True):
        pair = pd.DataFrame({"noisy": d.set_index(["seed", "Name"])["Cooperation_rating"]})
        pair["clean"] = base.reindex(pair.index)
        rho = pair.dropna().groupby(level="seed").apply(
            lambda t: t["noisy"].corr(t["clean"], method="spearman"))
        meaning.append({"noise": str(interval), "tournaments": d["seed"].nunique(),
                        "mean_within_tournament_spearman": rho.mean()})
    by_meaning = pd.DataFrame(meaning)
    by_meaning.to_csv(RESULTS / "flip_meaning.csv", index=False)

    pd.set_option("display.width", 220, "display.max_columns", 30)
    for table in (by_range, by_horizon, by_meaning):
        print(table.round(3).to_string(), "\n")


if __name__ == "__main__":
    main()
