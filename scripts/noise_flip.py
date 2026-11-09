"""Check the "noise flip" for Article 1 and save the numbers behind its chart.

Does cooperating more than the tournament's median player go with a better or
worse normalized rank (lower = better), with and without noise? Answers it two
ways: from the raw tournament data, and from SHAP on the saved v2 models.
Intervals resample whole tournaments (seeds). Run train_and_explain.py first.

Output: Results/noise_flip_bins.csv, Results/noise_flip_summary.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.model_selection import GroupShuffleSplit

from train_and_explain import DATA, FEATURES, MODELS, N_BOOT, RESULTS, SEED, SHAP_SAMPLE, SUBSETS

X = "Cooperation_rating_comp_to_median"
EDGES = [0, 0.25, 0.5, 0.75, 0.9, 1.1, 1.25, 1.5, 2, 3, np.inf]
SETTINGS = {
    "no_noise_no_probend": ("no noise", "fixed length"),
    "no_noise_has_probend": ("no noise", "probabilistic end"),
    "has_noise_no_probend": ("noise", "fixed length"),
    "has_noise_has_probend": ("noise", "probabilistic end"),
}


def above_minus_below(d):
    """Mean rank of above-median cooperators minus below-median ones, per seed."""
    above = d[X] > 1
    g = d.assign(above=above).groupby(["seed", "above"])["Normalized_Rank"].mean().unstack()
    return (g[True] - g[False]).dropna()


def seed_ci(values, rng):
    v = values.to_numpy()
    boots = [rng.choice(v, len(v)).mean() for _ in range(N_BOOT)]
    return v.mean(), *np.percentile(boots, [2.5, 97.5])


def main():
    df = pd.read_parquet(DATA).replace([np.inf, -np.inf], 999)
    rng = np.random.default_rng(SEED)
    bins, summary = [], []
    for name, (noise, ending) in SETTINGS.items():
        sub = SUBSETS[name](df)
        finite = sub[sub[X] < 999]

        # Raw data: all tournaments in this setting
        gap, low, high = seed_ci(above_minus_below(finite), rng)
        rho = finite[[X, "Normalized_Rank"]].corr(method="spearman").iloc[0, 1]

        # Model: same held-out seeds and SHAP sample as train_and_explain.py
        idx = next(GroupShuffleSplit(1, test_size=0.2, random_state=SEED).split(sub, groups=sub["seed"]))[1]
        test = sub.iloc[idx]
        sample = test.sample(min(SHAP_SAMPLE, len(test)), random_state=SEED)
        model = xgb.XGBRegressor()
        model.load_model(MODELS / f"model_{name}.json")
        values = shap.TreeExplainer(model).shap_values(sample[FEATURES])
        col = pd.Series(values[:, FEATURES.index(X)], index=sample.index)

        ok = sample[X] < 999
        summary.append({
            "subset": name, "noise": noise, "ending": ending,
            "rows": len(sub), "share_ratio_infinite": float((sub[X] >= 999).mean()),
            "share_above_median": float((finite[X] > 1).mean()),
            "raw_spearman": rho,
            "raw_rank_gap_above_minus_below": gap, "gap_ci_low": low, "gap_ci_high": high,
            "shap_spearman": pd.concat([sample.loc[ok, X], col[ok]], axis=1).corr(method="spearman").iloc[0, 1],
            "shap_mean_above": col[ok & (sample[X] > 1)].mean(),
            "shap_mean_below": col[ok & (sample[X] <= 1)].mean(),
        })

        cut = pd.cut(finite[X], EDGES, right=False)
        raw = finite.groupby(cut, observed=True).agg(rows=("Normalized_Rank", "size"),
                                                     mean_rank=("Normalized_Rank", "mean"))
        sh = col[ok].groupby(pd.cut(sample.loc[ok, X], EDGES, right=False), observed=True).mean()
        for interval, row in raw.iterrows():
            bins.append({"subset": name, "noise": noise, "ending": ending, "bin": str(interval),
                         "rows": int(row["rows"]), "mean_rank": row["mean_rank"],
                         "mean_shap": sh.get(interval, np.nan)})

    # Does the direction depend on how much noise, or how likely an early end?
    # Each sweep varies one factor from the fixed-length, no-noise baseline.
    usable = df[df[X] < 999]
    sweeps = {
        "noise_level": (usable[(usable.has_noise == 1) & (usable.has_probend == 0)], "noise",
                        [0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0]),
        "probend_level": (usable[(usable.has_noise == 0) & (usable.has_probend == 1)], "probend",
                          [0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0]),
    }
    for label, (d, col, edges) in sweeps.items():
        for level, g in d.groupby(pd.cut(d[col], edges), observed=True):
            gap, low, high = seed_ci(above_minus_below(g), rng)
            summary.append({"subset": f"{label} {level}", "rows": len(g), "seeds": g["seed"].nunique(),
                            "raw_rank_gap_above_minus_below": gap, "gap_ci_low": low, "gap_ci_high": high})

    pd.DataFrame(bins).to_csv(RESULTS / "noise_flip_bins.csv", index=False)
    s = pd.DataFrame(summary)
    s.to_csv(RESULTS / "noise_flip_summary.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_rows", 200)
    print(s.round(4).to_string())
    print(pd.DataFrame(bins).round(4).to_string())


if __name__ == "__main__":
    main()
