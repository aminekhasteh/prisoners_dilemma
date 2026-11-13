"""Article-style charts for the 272-strategy rerun, from results/*.csv (same look as ../substack/make_figures.py).
Usage: python make_figures.py results/ figures/"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

RES, OUT = Path(sys.argv[1]), Path(sys.argv[2])
plt.rcParams.update({
    "font.family": ["DejaVu Sans"], "font.size": 12,
    "axes.edgecolor": "#c9c8c3", "axes.labelcolor": "#52514e", "xtick.color": "#52514e",
    "ytick.color": "#52514e", "text.color": "#0b0b0b", "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": "#ecebe7", "grid.linewidth": 0.8,
    "axes.axisbelow": True, "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.dpi": 200, "savefig.bbox": "tight", "savefig.pad_inches": 0.25,
})
BLUE, ORANGE, AQUA, INK2, MUTED = "#2a78d6", "#eb6834", "#1baf7a", "#52514e", "#8a8984"

def title(fig, t, sub):
    fig.text(0.0, 1.06, t, fontsize=16, fontweight="semibold", ha="left", va="bottom", transform=fig.axes[0].transAxes)
    fig.text(0.0, 1.015, sub, fontsize=11.5, color=INK2, ha="left", va="bottom", transform=fig.axes[0].transAxes)

# ---------- 1. Noise: does cooperating more than the median still pay? ----------
s = pd.read_csv(RES / "noise_flip_summary.csv").set_index("subset")
rows = [("none", "no noise, 63 turns"), ("1%", "1% noise, 63 turns"), ("5%", "5% noise, 63 turns")]
fig, ax = plt.subplots(figsize=(9, 5))
ax.axhspan(-0.35, 0, color=BLUE, alpha=0.06, lw=0); ax.axhspan(0, 0.15, color=ORANGE, alpha=0.06, lw=0)
ax.axhline(0, color=INK2, lw=1)
gs = [s.loc[k, "rank_gap_above_minus_below"] for _, k in rows]
ax.plot(range(len(rows)), gs, color=MUTED, lw=1, zorder=1)
for x, (lab, k) in enumerate(rows):
    g, lo, hi, n = s.loc[k, ["rank_gap_above_minus_below", "ci_low", "ci_high", "tournaments"]]
    c = BLUE if g < 0 else ORANGE
    ax.plot([x, x], [lo, hi], color=c, lw=2, solid_capstyle="round")
    ax.scatter([x], [g], s=70, color=c, edgecolor="white", linewidth=2, zorder=3)
    ax.annotate(f"{g:+.2f}", (x, g), xytext=(0, 12), textcoords="offset points", ha="center", fontsize=10.5)
    ax.annotate(f"{int(n)} tournaments", (x, g), xytext=(0, -20), textcoords="offset points", ha="center", fontsize=9.5, color=MUTED)
ax.set_xticks(range(len(rows)), [r[0] for r in rows]); ax.set_xlim(-0.5, len(rows) - 0.5); ax.set_ylim(-0.35, 0.15)
ax.set_xlabel("Noise: chance that any single move gets flipped"); ax.set_ylabel("Rank gap (above − below median)")
ax.text(len(rows) - 0.55, -0.33, "cooperating more than the median\ngoes with a better rank", color=BLUE, ha="right", va="bottom", fontsize=10.5)
ax.text(-0.45, 0.11, "cooperating more than the median goes with a worse rank", color=ORANGE, ha="left", va="center", fontsize=10.5)
ax.grid(axis="x", visible=False)
title(fig, "With 272 strategies, noise shrinks the edge but doesn't flip it by 5%",
      "Average normalized rank of above-median cooperators minus below-median ones. 63-turn games, Knight et al. 2025 data.")
fig.savefig(OUT / "noise_flip_by_level.png"); plt.close(fig)

# ---------- 2. How much of winning the model explains ----------
h = pd.read_csv(RES / "holdout_r2.csv")
def get(sub, chk): return float(h[(h.subset == sub) & (h.check == chk)].R2.iloc[0])
sets = [("standard", "No noise\n(100 tournaments)"), ("noise", "1% and 5% noise\n(20 tournaments)"), ("all", "All pooled")]
fig, ax = plt.subplots(figsize=(9, 4.8)); w = 0.34
series = [("XGBoost, new tournaments (same 272 strategies)", ORANGE, [get(k, "unseen tournaments") for k, _ in sets]),
          ("XGBoost, new tournaments and unseen strategies", AQUA, [get(k, "unseen strategies and tournaments") for k, _ in sets])]
for i, (name, c, vals) in enumerate(series):
    xs = [j + (i - 0.5) * w for j in range(len(sets))]
    ax.bar(xs, vals, width=w - 0.04, color=c, label=name, zorder=2)
    for x, v in zip(xs, vals): ax.text(x, v + 0.015, f"{v:.2f}", ha="center", fontsize=10)
ax.set_xticks(range(len(sets)), [n for _, n in sets]); ax.set_ylim(0, 1.12); ax.set_ylabel("R² (share of rank explained)")
ax.grid(axis="x", visible=False)
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=10)
title(fig, "The real test is a strategy the model has never seen",
      "272 strategies, Knight et al. 2025 data. Every tournament has the same players, so new tournaments are easy.")
fig.savefig(OUT / "r2_by_setting.png"); plt.close(fig)

# ---------- 3. Feature importance ----------
names = {"Cooperation_rating_comp_to_median": "Cᵣ / C_median", "Cooperation_rating_comp_to_max": "Cᵣ / C_max",
         "CC_to_C_rate": "CC to C rate", "noise": "Noise (pₙ)", "Cooperation_rating_comp_to_mean": "Cᵣ / C_mean",
         "memory_usage": "Memory usage", "CD_to_C_rate": "CD to C rate", "SSE": "SSE", "Cooperation_rating_mean": "C_mean",
         "Cooperation_rating_comp_to_min": "Cᵣ / C_min", "DC_to_C_rate": "DC to C rate", "DD_to_C_rate": "DD to C rate",
         "Cooperation_rating": "Cᵣ", "turns": "Turns (n)", "Makes_use_of_length": "Makes use of length",
         "Makes_use_of_game": "Makes use of game", "Stochastic": "Stochastic", "Cooperation_rating_median": "C_median",
         "Cooperation_rating_max": "C_max", "Cooperation_rating_min": "C_min", "has_noise": "Has noise"}
ratio = {k for k in names if "comp_to" in k}
allimp = pd.read_csv(RES / "shap_importance_ci.csv")
for model, fname, sub in [("all", "importance_all.png", "Top 12 features, no-noise and noisy tournaments pooled."),
                          ("standard", "importance_standard.png", "Top 12 features, the 100 no-noise tournaments.")]:
    imp = allimp[allimp.model == model].head(12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 5.4)); ys = range(len(imp))
    ax.barh(list(ys), imp.mean_abs_shap, color=[ORANGE if f in ratio else BLUE for f in imp.feature], height=0.62, zorder=2)
    ax.errorbar(imp.mean_abs_shap, list(ys), xerr=[imp.mean_abs_shap - imp.ci_low, imp.ci_high - imp.mean_abs_shap],
                fmt="none", ecolor="#0b0b0b", elinewidth=1, capsize=2, zorder=3)
    ax.set_yticks(list(ys), [names.get(f, f) for f in imp.feature]); ax.set_xlabel("Mean |SHAP| (average shift in predicted rank)")
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[Patch(color=ORANGE, label="Your cooperation compared with the field"), Patch(color=BLUE, label="Other features")],
              frameon=False, loc="lower right", fontsize=10)
    title(fig, "What the model leans on with 272 strategies", sub + " Black lines are 95% bootstrap intervals over tournaments.")
    fig.savefig(OUT / fname); plt.close(fig)
print("done")
