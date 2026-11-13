"""Out-of-sample test: the XGBoost model trained on Glynatsi et al.'s no-noise tournaments (195 strategies,
Models/v2/model_no_noise_no_probend.json) predicts the rank of strategies it has never seen, in Knight et al.'s
272-strategy no-noise round robins.

"New" = the 63 original Fortran entries + library strategies whose name is not among the 195.
Per strategy: predicted normalized rank = mean prediction over its 100 tournament rows; actual = mean normalized rank.
Usage: python test_old_model.py data/knight272.parquet ../../Models/v2/model_no_noise_no_probend.json data/strategy_names_195.txt results/ figures/"""
import sys
import numpy as np, pandas as pd, xgboost as xgb
from scipy.stats import spearmanr, kendalltau
from sklearn.metrics import r2_score, mean_absolute_error
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

FEATURES = ["CC_to_C_rate", "CD_to_C_rate", "DC_to_C_rate", "DD_to_C_rate", "Cooperation_rating",
            "Cooperation_rating_max", "Cooperation_rating_min", "Cooperation_rating_median", "Cooperation_rating_mean",
            "Cooperation_rating_comp_to_max", "Cooperation_rating_comp_to_min", "Cooperation_rating_comp_to_median",
            "Cooperation_rating_comp_to_mean", "repetitions", "turns", "noise", "probend",
            "Makes_use_of_game", "Makes_use_of_length", "SSE", "Stochastic", "memory_usage", "has_noise", "has_probend"]

df = pd.read_parquet(sys.argv[1]).replace([np.inf, -np.inf], 999)
df = df[df.noise == 0].copy()
model = xgb.XGBRegressor(); model.load_model(sys.argv[2])
assert list(model.get_booster().feature_names) == FEATURES
old = {l.strip() for l in open(sys.argv[3]) if l.strip()}
RENAMED = {"Soft Go By Majority", "Hard Go By Majority", "Slow Tit For Two Tats", "Fool Me Forever"}  # old names, library renamed
base = lambda n: n.split(":")[0].strip()
def is_old(n, fortran):
    if fortran: return False
    b = base(n)
    if b in old or n in old: return True
    if b.replace("Soft ", "").replace("Hard ", "") in {o.replace("Soft ", "").replace("Hard ", "").replace(" 5", "").replace(" 10", "").replace(" 20", "").replace(" 40", "") for o in old}: return True
    return b.replace("First by ", "") in old or b.replace("Second by ", "") in old
df["pred"] = model.predict(df[FEATURES])
s = df.groupby("Name").agg(actual=("Normalized_Rank", "mean"), pred=("pred", "mean"), fortran=("fortran", "first")).reset_index()
s["group"] = ["seen (in the 195)" if is_old(n, f) else ("new: 1980 Fortran entry" if f else "new: library strategy") for n, f in zip(s.Name, s.fortran)]
s["actual_place"] = s.actual.rank(method="min").astype(int); s["pred_place"] = s.pred.rank(method="min").astype(int)
s["error"] = s.pred - s.actual
s.sort_values("actual").to_csv(sys.argv[4] + "old_model_on_272.csv", index=False)

lines = []
def report(name, d):
    rho, tau = spearmanr(d.pred, d.actual)[0], kendalltau(d.pred, d.actual)[0]
    lines.append(f"{name:<28} n={len(d):3d}  R²={r2_score(d.actual, d.pred):.3f}  Spearman={rho:.3f}  Kendall={tau:.3f}  MAE={mean_absolute_error(d.actual, d.pred):.3f} (~{mean_absolute_error(d.actual, d.pred) * 271:.0f} places)")
report("all 272", s); report("seen (in the 195)", s[s.group.str.startswith("seen")])
new = s[s.group.str.startswith("new")]
report("new (never seen)", new); report("  new: 1980 Fortran", s[s.group == "new: 1980 Fortran entry"]); report("  new: library", s[s.group == "new: library strategy"])
rows = df[df.Name.isin(new.Name)]
lines.append(f"row level, new strategies (100 tournaments each): R²={r2_score(rows.Normalized_Rank, rows.pred):.3f}")
lines.append("\nworst misses among new strategies (error = predicted - actual normalized rank; + means model thought it worse):")
w = new.reindex(new.error.abs().sort_values(ascending=False).index).head(12)
lines.append(w[["Name", "group", "actual_place", "pred_place", "actual", "pred", "error"]].round(3).to_string(index=False))
lines.append("\nbest new strategies, actual vs predicted place:")
lines.append(new.sort_values("actual").head(10)[["Name", "actual_place", "pred_place"]].to_string(index=False))
lines.append("\nruns outside the training range: turns 63-308 (trained on 1-200), repetitions 250 (trained on 10-100), N=272 (trained on 3-195)")
open(sys.argv[4] + "old_model_on_272.txt", "w").write("\n".join(lines)); print("\n".join(lines))

# figure
plt.rcParams.update({"font.family": ["DejaVu Sans"], "font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#c9c8c3", "axes.labelcolor": "#52514e", "xtick.color": "#52514e", "ytick.color": "#52514e",
                     "axes.grid": True, "grid.color": "#ecebe7", "axes.axisbelow": True, "savefig.dpi": 200, "savefig.bbox": "tight"})
fig, ax = plt.subplots(figsize=(8.5, 8))
ax.plot([0, 1], [0, 1], color="#8a8984", lw=1, ls="--", zorder=1)
styles = [("seen (in the 195)", "#c9c8c3", "o", 22), ("new: library strategy", "#2a78d6", "o", 46), ("new: 1980 Fortran entry", "#eb6834", "s", 46)]
for g, c, m, sz in styles:
    d = s[s.group == g]
    ax.scatter(d.actual, d.pred, s=sz, c=c, marker=m, edgecolor="white", linewidth=0.6, zorder=3 if g != styles[0][0] else 2, label=f"{g} ({len(d)})")
for _, r in w.head(6).iterrows():
    ax.annotate(base(r.Name), (r.actual, r.pred), xytext=(6, 4), textcoords="offset points", fontsize=9.5, color="#1b1b1b")
k = s[s.Name == "k92r"].iloc[0]
ax.annotate("k92r (Tit for Tat)", (k.actual, k.pred), xytext=(6, -12), textcoords="offset points", fontsize=9.5, fontweight="bold")
nr = new
ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02); ax.set_aspect("equal")
ax.set_xlabel("Actual normalized rank in the 272-strategy tournaments (0 = first)"); ax.set_ylabel("Rank predicted by the model trained on 195 strategies")
ax.legend(frameon=False, loc="upper left", fontsize=10)
fig.text(0.0, 1.04, "A model trained on 195 strategies, tested on ones it never saw", fontsize=15, fontweight="bold", transform=ax.transAxes)
fig.text(0.0, 1.005, f"New strategies: R² {r2_score(nr.actual, nr.pred):.2f}, Spearman {spearmanr(nr.pred, nr.actual)[0]:.2f}. "
         "One dot per strategy, averaged over 100 no-noise tournaments.", fontsize=10.5, color="#52514e", transform=ax.transAxes)
fig.savefig(sys.argv[5] + "old_model_on_new_strategies.png"); print("figure ok")
