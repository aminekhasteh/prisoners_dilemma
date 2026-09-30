"""Revisited XGBoost + SHAP analysis (v2).

Changes from the original notebook (EDA.ipynb, section 2):
  1. Target is Normalized_Rank = Rank / (N - 1), the paper's dependent
     variable. Raw Rank mostly tracks tournament size N (3..195).
  2. Train/test split is grouped by tournament seed, so rows from the same
     tournament never appear on both sides.
  3. No StandardScaler. Trees don't need it, and the original SHAP values
     were computed on unscaled inputs for a model trained on scaled ones.
  4. Mean |SHAP| importances come with 95% bootstrap intervals
     (resampling test-set seeds).

An ablation on the full dataset reruns the original setup and each fix
one at a time so the effect of every change is visible.

Outputs: Results/*.csv, Plots/v2/*.png, Models/v2/*.json
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "Data" / "combined_dataset.parquet"
RESULTS = ROOT / "Results"
PLOTS = ROOT / "Plots" / "v2"
MODELS = ROOT / "Models" / "v2"

SEED = 42
SHAP_SAMPLE = 20_000
N_BOOT = 200

FEATURES = [
    "CC_to_C_rate", "CD_to_C_rate", "DC_to_C_rate", "DD_to_C_rate",
    "Cooperation_rating",
    "Cooperation_rating_max", "Cooperation_rating_min",
    "Cooperation_rating_median", "Cooperation_rating_mean",
    "Cooperation_rating_comp_to_max", "Cooperation_rating_comp_to_min",
    "Cooperation_rating_comp_to_median", "Cooperation_rating_comp_to_mean",
    "repetitions", "turns",
    "noise", "probend",
    "Makes_use_of_game", "Makes_use_of_length",
    "SSE", "Stochastic", "memory_usage",
    "has_noise", "has_probend",
]

LABELS = {
    "CC_to_C_rate": "CC to C rate",
    "CD_to_C_rate": "CD to C rate",
    "DC_to_C_rate": "DC to C rate",
    "DD_to_C_rate": "DD to C rate",
    "Cooperation_rating": r"$C_r$",
    "Cooperation_rating_max": r"$C_{max}$",
    "Cooperation_rating_min": r"$C_{min}$",
    "Cooperation_rating_median": r"$C_{median}$",
    "Cooperation_rating_mean": r"$C_{mean}$",
    "Cooperation_rating_comp_to_max": r"$C_r / C_{max}$",
    "Cooperation_rating_comp_to_min": r"$C_r / C_{min}$",
    "Cooperation_rating_comp_to_median": r"$C_r / C_{median}$",
    "Cooperation_rating_comp_to_mean": r"$C_r / C_{mean}$",
    "repetitions": r"$k$",
    "turns": r"$n$",
    "noise": r"$p_n$",
    "probend": r"$p_e$",
    "Makes_use_of_game": "makes use of game",
    "Makes_use_of_length": "makes use of length",
    "SSE": "SSE",
    "Stochastic": "stochastic",
    "memory_usage": "memory usage",
    "has_noise": "has noise",
    "has_probend": "has probend",
}

SUBSETS = {
    "all": lambda d: d,
    "has_noise_has_probend": lambda d: d[(d.has_noise == 1) & (d.has_probend == 1)],
    "has_noise": lambda d: d[d.has_noise == 1],
    "has_probend": lambda d: d[d.has_probend == 1],
    "no_noise_no_probend": lambda d: d[(d.has_noise == 0) & (d.has_probend == 0)],
    "no_noise_has_probend": lambda d: d[(d.has_noise == 0) & (d.has_probend == 1)],
    "has_noise_no_probend": lambda d: d[(d.has_noise == 1) & (d.has_probend == 0)],
}


def split(df, grouped):
    if grouped:
        gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED)
        train_idx, test_idx = next(gss.split(df, groups=df["seed"]))
        return df.iloc[train_idx], df.iloc[test_idx]
    return train_test_split(df, test_size=0.2, random_state=SEED)


def fit(train, target, scale=False):
    X = train[FEATURES]
    scaler = None
    if scale:
        scaler = StandardScaler().fit(X)
        X = scaler.transform(X)
    model = xgb.XGBRegressor(random_state=SEED, tree_method="hist", n_jobs=-1)
    model.fit(X, train[target])
    return model, scaler


def evaluate(model, scaler, test, target):
    X = test[FEATURES]
    if scaler is not None:
        X = scaler.transform(X)
    y, pred = test[target], model.predict(X)
    return {
        "R2": r2_score(y, pred),
        "MAE": mean_absolute_error(y, pred),
        "RMSE": np.sqrt(mean_squared_error(y, pred)),
    }


def run_ablation(df):
    """Original setup, then each fix applied cumulatively, on all data."""
    steps = [
        ("original: Rank, random split, scaled", "Rank", False, True),
        ("+ Normalized_Rank target", "Normalized_Rank", False, True),
        ("+ split by tournament seed", "Normalized_Rank", True, True),
        ("+ no scaler (final)", "Normalized_Rank", True, False),
    ]
    rows = []
    for label, target, grouped, scale in steps:
        train, test = split(df, grouped)
        model, scaler = fit(train, target, scale)
        m = evaluate(model, scaler, test, target)
        m.update({"Step": label, "Target": target,
                  "Train Size": len(train), "Test Size": len(test)})
        rows.append(m)
        print(f"  {label:<40} R2={m['R2']:.3f}  MAE={m['MAE']:.3f}")
    return pd.DataFrame(rows).set_index("Step")


def shap_with_ci(model, test, rng):
    sample = test.sample(min(SHAP_SAMPLE, len(test)), random_state=SEED)
    values = shap.TreeExplainer(model).shap_values(sample[FEATURES])
    abs_vals = np.abs(values)

    # Bootstrap over tournaments (seeds) in the SHAP sample
    seeds = sample["seed"].to_numpy()
    uniq = np.unique(seeds)
    rows_by_seed = {s: np.flatnonzero(seeds == s) for s in uniq}
    boots = np.empty((N_BOOT, len(FEATURES)))
    for b in range(N_BOOT):
        picked = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([rows_by_seed[s] for s in picked])
        boots[b] = abs_vals[idx].mean(axis=0)

    importance = pd.DataFrame({
        "feature": FEATURES,
        "mean_abs_shap": abs_vals.mean(axis=0),
        "ci_low": np.percentile(boots, 2.5, axis=0),
        "ci_high": np.percentile(boots, 97.5, axis=0),
    }).sort_values("mean_abs_shap", ascending=False)
    return sample, values, importance


def plot_beeswarm(values, sample, name):
    plt.figure()
    shap.summary_plot(values, sample[FEATURES],
                      feature_names=[LABELS[f] for f in FEATURES],
                      max_display=15, show=False)
    plt.gcf().set_size_inches(10, 7)
    plt.xlabel("SHAP value (impact on normalized rank; negative = better rank)")
    plt.title(f"Feature impact on normalized rank: {name.replace('_', ' ')}")
    plt.tight_layout()
    plt.savefig(PLOTS / f"SHAP_{name}.png", dpi=200, bbox_inches="tight")
    plt.close()


def plot_importance(importance, name):
    top = importance.head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh([LABELS[f] for f in top.feature], top.mean_abs_shap, color="#4C72B0")
    ax.errorbar(top.mean_abs_shap, range(len(top)),
                xerr=[top.mean_abs_shap - top.ci_low, top.ci_high - top.mean_abs_shap],
                fmt="none", ecolor="black", capsize=3)
    ax.set_xlabel("mean |SHAP| (95% bootstrap interval)")
    ax.set_title(f"Feature importance: {name.replace('_', ' ')}")
    fig.tight_layout()
    fig.savefig(PLOTS / f"importance_{name}.png", dpi=200)
    plt.close(fig)


def main():
    for d in (RESULTS, PLOTS, MODELS):
        d.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(DATA).replace([np.inf, -np.inf], 999)
    print(f"loaded {df.shape}")

    print("ablation (all data):")
    ablation = run_ablation(df)
    ablation.to_csv(RESULTS / "ablation.csv")

    rng = np.random.default_rng(SEED)
    metrics, importances = [], []
    for name, select in SUBSETS.items():
        sub = select(df)
        train, test = split(sub, grouped=True)
        model, _ = fit(train, "Normalized_Rank")
        m = evaluate(model, None, test, "Normalized_Rank")
        m.update({"Model": name, "Train Size": len(train), "Test Size": len(test)})
        metrics.append(m)
        print(f"{name:<25} R2={m['R2']:.3f}  MAE={m['MAE']:.3f}")

        model.save_model(MODELS / f"model_{name}.json")
        sample, values, importance = shap_with_ci(model, test, rng)
        importances.append(importance.assign(model=name))
        plot_beeswarm(values, sample, name)
        plot_importance(importance, name)

    pd.DataFrame(metrics).set_index("Model").to_csv(RESULTS / "model_evaluation_v2.csv")
    pd.concat(importances).to_csv(RESULTS / "shap_importance_ci.csv", index=False)
    print("done")


if __name__ == "__main__":
    main()
