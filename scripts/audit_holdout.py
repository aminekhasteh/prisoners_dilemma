"""Check how far the v2 R² carries: unseen strategies, and the paper's range.

The v2 split holds out tournaments, but the same 195 strategies appear on both
sides. Here each fold also holds out a fifth of the strategies, and scores only
unseen strategies in unseen tournaments. Models are also fitted and scored on
noise / ending chance <= 0.1 only, and with groups of features removed.

Output: Results/holdout_r2.csv. Takes a while on all data.

Usage: python scripts/audit_holdout.py [path/to/combined_dataset.parquet]
"""
import sys

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

from train_and_explain import DATA, FEATURES, RESULTS, SEED, SUBSETS

X = "Cooperation_rating_comp_to_median"
PAPER_RANGE = {
    "no_noise_no_probend": lambda d: d,
    "no_noise_has_probend": lambda d: d[d.probend <= 0.1],
    "has_noise_no_probend": lambda d: d[d.noise <= 0.1],
    "has_noise_has_probend": lambda d: d[(d.noise <= 0.1) & (d.probend <= 0.1)],
}
STRATEGY_FEATURES = {"Makes_use_of_game", "Makes_use_of_length", "Stochastic", "SSE", "memory_usage",
                     "CC_to_C_rate", "CD_to_C_rate", "DC_to_C_rate", "DD_to_C_rate"}
FEATURE_SETS = {
    "ratio to median only": [X],
    "without ratio to median": [f for f in FEATURES if f != X],
    "without all cooperation ratios": [f for f in FEATURES if "comp_to" not in f],
    "without strategy-specific features": [f for f in FEATURES if f not in STRATEGY_FEATURES],
}


def seed_split(d):
    train, test = next(GroupShuffleSplit(1, test_size=0.2, random_state=SEED).split(d, groups=d["seed"]))
    return d.iloc[train], d.iloc[test]


def fit(train, features=FEATURES):
    return xgb.XGBRegressor(random_state=SEED, tree_method="hist", n_jobs=-1).fit(
        train[features], train["Normalized_Rank"])


def score(model, test, features=FEATURES):
    pred = model.predict(test[features])
    return r2_score(test["Normalized_Rank"], pred), mean_absolute_error(test["Normalized_Rank"], pred)


def record(rows, subset, check, r2, mae, test_rows):
    rows.append({"subset": subset, "check": check, "R2": r2, "MAE": mae, "test_rows": test_rows})
    print(f"{subset:<24} {check:<38} R2={r2:.3f} MAE={mae:.3f} n={test_rows}", flush=True)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DATA
    df = pd.read_parquet(path).replace([np.inf, -np.inf], 999)
    df = df.drop_duplicates(["dataset", "seed", "Name"])
    names = df["Name"].unique()
    rows = []

    for subset in ["all", *PAPER_RANGE]:
        train, test = seed_split(SUBSETS[subset](df))
        record(rows, subset, "unseen tournaments (v2)", *score(fit(train), test), len(test))
        scores = []
        for _, held in GroupKFold(5, shuffle=True, random_state=SEED).split(names, groups=names):
            held = set(names[held])
            part = test[test["Name"].isin(held)]
            scores.append((*score(fit(train[~train["Name"].isin(held)]), part), len(part)))
        r2, mae, n = np.mean(scores, axis=0)
        record(rows, subset, "unseen strategies and tournaments", r2, mae, int(n))
        if subset == "all":
            for label, features in FEATURE_SETS.items():
                record(rows, subset, label, *score(fit(train, features), test, features), len(test))

    for subset, select in PAPER_RANGE.items():
        train, test = seed_split(select(SUBSETS[subset](df)))
        record(rows, subset, "paper range only", *score(fit(train), test), len(test))
        scores = []
        for _, held in GroupKFold(5, shuffle=True, random_state=SEED).split(names, groups=names):
            held = set(names[held])
            part = test[test["Name"].isin(held)]
            scores.append((*score(fit(train[~train["Name"].isin(held)]), part), len(part)))
        r2, mae, n = np.mean(scores, axis=0)
        record(rows, subset, "paper range, unseen strategies", r2, mae, int(n))

    pd.DataFrame(rows).to_csv(RESULTS / "holdout_r2.csv", index=False)


if __name__ == "__main__":
    main()
