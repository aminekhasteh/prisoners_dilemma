"""XGBoost + SHAP and the noise flip, redone on the 272-strategy data of Knight et al. 2025.

Same recipe as scripts/train_and_explain.py, audit_holdout.py and noise_flip.py (Glynatsi 2024 data), with what this
data allows: 100 no-noise tournaments (5 lengths x 20 seeds) and 20 noisy ones (63 turns; 13 at 1%, 7 at 5%).
Every tournament has the same 272 players, there is no probabilistic ending, and "group" = one tournament file.
Usage: python model_and_flip.py data/knight272.parquet results/ figures/"""
import sys
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold, GroupShuffleSplit

SEED, N_BOOT = 42, 1000
FEATURES = ["CC_to_C_rate", "CD_to_C_rate", "DC_to_C_rate", "DD_to_C_rate", "Cooperation_rating",
            "Cooperation_rating_max", "Cooperation_rating_min", "Cooperation_rating_median", "Cooperation_rating_mean",
            "Cooperation_rating_comp_to_max", "Cooperation_rating_comp_to_min", "Cooperation_rating_comp_to_median",
            "Cooperation_rating_comp_to_mean", "repetitions", "turns", "noise", "probend",
            "Makes_use_of_game", "Makes_use_of_length", "SSE", "Stochastic", "memory_usage", "has_noise", "has_probend"]
X = "Cooperation_rating_comp_to_median"
STRATEGY_FEATURES = {"Makes_use_of_game", "Makes_use_of_length", "Stochastic", "SSE", "memory_usage",
                     "CC_to_C_rate", "CD_to_C_rate", "DC_to_C_rate", "DD_to_C_rate"}
LABELS = {"CC_to_C_rate": "CC to C rate", "CD_to_C_rate": "CD to C rate", "DC_to_C_rate": "DC to C rate", "DD_to_C_rate": "DD to C rate",
          "Cooperation_rating": r"$C_r$", "Cooperation_rating_max": r"$C_{max}$", "Cooperation_rating_min": r"$C_{min}$",
          "Cooperation_rating_median": r"$C_{median}$", "Cooperation_rating_mean": r"$C_{mean}$",
          "Cooperation_rating_comp_to_max": r"$C_r / C_{max}$", "Cooperation_rating_comp_to_min": r"$C_r / C_{min}$",
          "Cooperation_rating_comp_to_median": r"$C_r / C_{median}$", "Cooperation_rating_comp_to_mean": r"$C_r / C_{mean}$",
          "repetitions": r"$k$", "turns": r"$n$", "noise": r"$p_n$", "probend": r"$p_e$", "Makes_use_of_game": "makes use of game",
          "Makes_use_of_length": "makes use of length", "SSE": "SSE", "Stochastic": "stochastic", "memory_usage": "memory usage",
          "has_noise": "has noise", "has_probend": "has probend"}

df = pd.read_parquet(sys.argv[1]).replace([np.inf, -np.inf], 999)
RES, FIG = sys.argv[2], sys.argv[3]
SUBSETS = {"all": df, "standard": df[df.noise == 0], "noise": df[df.noise > 0]}
names = df["Name"].unique()

def tsplit(d):
    tr, te = next(GroupShuffleSplit(1, test_size=0.2, random_state=SEED).split(d, groups=d["tournament"]))
    return d.iloc[tr], d.iloc[te]

def fit(train, features=FEATURES):
    return xgb.XGBRegressor(random_state=SEED, tree_method="hist", n_jobs=4).fit(train[features], train["Normalized_Rank"])

def score(model, test, features=FEATURES):
    p = model.predict(test[features]); return r2_score(test.Normalized_Rank, p), mean_absolute_error(test.Normalized_Rank, p)

rows, models, tests = [], {}, {}
def rec(subset, check, r2, mae, n):
    rows.append(dict(subset=subset, check=check, R2=r2, MAE=mae, test_rows=n)); print(f"{subset:<9} {check:<40} R2={r2:.3f} MAE={mae:.3f} n={n}", flush=True)

for name, d in SUBSETS.items():
    train, test = tsplit(d)
    m = fit(train); models[name], tests[name] = m, test
    rec(name, "unseen tournaments", *score(m, test), len(test))
    sc = []
    for _, held in GroupKFold(5, shuffle=True, random_state=SEED).split(names, groups=names):
        held = set(names[held]); part = test[test.Name.isin(held)]
        sc.append((*score(fit(train[~train.Name.isin(held)]), part), len(part)))
    r2, mae, n = np.mean(sc, axis=0); rec(name, "unseen strategies and tournaments", r2, mae, int(n))
    if name in ("all", "standard"):
        for label, feats in {"ratio to median only": [X], "without ratio to median": [f for f in FEATURES if f != X],
                             "without all cooperation ratios": [f for f in FEATURES if "comp_to" not in f],
                             "without strategy-specific features": [f for f in FEATURES if f not in STRATEGY_FEATURES]}.items():
            rec(name, label, *score(fit(train, feats), test, feats), len(test))
pd.DataFrame(rows).to_csv(RES + "holdout_r2.csv", index=False)

# SHAP: importance with bootstrap over test tournaments, beeswarm for the standard setting
rng = np.random.default_rng(SEED); imps = []
for name in SUBSETS:
    test = tests[name]
    vals = shap.TreeExplainer(models[name]).shap_values(test[FEATURES]); a = np.abs(vals)
    t = test["tournament"].to_numpy(); uniq = np.unique(t); idx = {u: np.flatnonzero(t == u) for u in uniq}
    boots = np.array([a[np.concatenate([idx[u] for u in rng.choice(uniq, len(uniq))])].mean(0) for _ in range(N_BOOT)])
    imps.append(pd.DataFrame(dict(model=name, feature=FEATURES, mean_abs_shap=a.mean(0), ci_low=np.percentile(boots, 2.5, 0),
                                  ci_high=np.percentile(boots, 97.5, 0))).sort_values("mean_abs_shap", ascending=False))
    if name == "standard":
        plt.figure()
        shap.summary_plot(vals, test[FEATURES], feature_names=[LABELS[f] for f in FEATURES], max_display=15, show=False)
        plt.gcf().set_size_inches(10, 7)
        plt.xlabel("SHAP value (impact on normalized rank; negative = better rank)")
        plt.title("Feature impact on normalized rank: 272 strategies, no noise")
        plt.tight_layout(); plt.savefig(FIG + "shap_standard.png", dpi=200, bbox_inches="tight"); plt.close()
        sv = pd.DataFrame(vals, columns=FEATURES, index=test.index)
        dirs = [dict(feature=f, mean_abs_shap=sv[f].abs().mean(), spearman_value_vs_shap=test[f].corr(sv[f], method="spearman")) for f in FEATURES]
        pd.DataFrame(dirs).sort_values("mean_abs_shap", ascending=False).to_csv(RES + "shap_direction_standard.csv", index=False)
pd.concat(imps).to_csv(RES + "shap_importance_ci.csv", index=False)

# Noise flip: mean rank of above-median cooperators minus below-median ones, per tournament
def gap(d):
    g = d.assign(above=d[X] > 1).groupby(["tournament", "above"])["Normalized_Rank"].mean().unstack()
    return (g[True] - g[False]).dropna()
def ci(v):
    v = v.to_numpy(); b = [rng.choice(v, len(v)).mean() for _ in range(N_BOOT)]
    return v.mean(), *np.percentile(b, [2.5, 97.5]), len(v)
flip = []
for label, d in [("no noise, all 5 lengths", df[df.noise == 0]), ("no noise, 63 turns", df[(df.noise == 0) & (df.turns == 63)]),
                 ("1% noise, 63 turns", df[df.noise == 0.01]), ("5% noise, 63 turns", df[df.noise == 0.05])] + \
                [(f"no noise, {t} turns", df[(df.noise == 0) & (df.turns == t)]) for t in (77, 151, 156, 308)]:
    m, lo, hi, n = ci(gap(d))
    flip.append(dict(subset=label, tournaments=n, rank_gap_above_minus_below=m, ci_low=lo, ci_high=hi,
                     spearman=d[[X, "Normalized_Rank"]].corr(method="spearman").iloc[0, 1], median_coop=d.Cooperation_rating_median.mean()))
flip = pd.DataFrame(flip); flip.to_csv(RES + "noise_flip_summary.csv", index=False); print(flip.round(3).to_string())
bins = []
for label, d in [("standard", df[df.noise == 0]), ("noise 1%", df[df.noise == 0.01]), ("noise 5%", df[df.noise == 0.05])]:
    b = d.groupby(pd.cut(d[X], [0, 0.25, 0.5, 0.75, 0.9, 1.1, 1.25, 1.5, 2, 3, np.inf], right=False), observed=True)["Normalized_Rank"].agg(["size", "mean"])
    bins.append(b.assign(subset=label).reset_index())
pd.concat(bins).to_csv(RES + "noise_flip_bins.csv", index=False); print(pd.concat(bins).round(3).to_string())
print(pd.concat(imps).query("model != 'noise'").groupby("model").head(10).round(4).to_string())
