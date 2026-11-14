"""Make the article's charts from saved results (no model training needed).
Usage: python3 make_figures.py data figures
Inputs (data/): noise_flip_summary.csv, holdout_r2.csv, shap_importance_ci.csv
(from the prisoners_dilemma repo, Results/ on branches revisit-normalized-rank and claude/project-thread-s27dmu).
"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Patch

RES = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
for f in fm.findSystemFonts():
    if "Inter" in f: fm.fontManager.addfont(f)
plt.rcParams.update({
    "font.family": ["Inter", "DejaVu Sans"], "font.size": 12,
    "axes.edgecolor": "#c9c8c3", "axes.labelcolor": "#52514e", "xtick.color": "#52514e",
    "ytick.color": "#52514e", "text.color": "#0b0b0b", "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": "#ecebe7", "grid.linewidth": 0.8,
    "axes.axisbelow": True, "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.dpi": 200, "savefig.bbox": "tight", "savefig.pad_inches": 0.25,
})
BLUE, ORANGE, AQUA, INK2, MUTED = "#2a78d6", "#eb6834", "#1baf7a", "#52514e", "#8a8984"

def title(fig, t, sub):
    ax = fig.axes[0]
    fig.text(0.0, 1.06, t, fontsize=16, fontweight="bold", ha="left", va="bottom", transform=ax.transAxes)
    fig.text(0.0, 1.015, sub, fontsize=11.5, color=INK2, ha="left", va="bottom", transform=ax.transAxes)

# 1. The noise flip, by noise level
s = pd.read_csv(RES / "noise_flip_summary.csv")
std = s[s.subset == "no_noise_no_probend"].iloc[0]
lv = s[s.subset.str.startswith("noise_level")].copy()
labels = {"(0.0, 0.01]": "up to 1%", "(0.01, 0.02]": "1–2%", "(0.02, 0.05]": "2–5%", "(0.05, 0.1]": "5–10%",
          "(0.1, 0.2]": "10–20%", "(0.2, 0.3]": "20–30%", "(0.3, 0.5]": "30–50%"}
lv["lab"] = lv.subset.str.replace("noise_level ", "").map(labels)
lv = lv.dropna(subset=["lab"])
rows = [("none", std.raw_rank_gap_above_minus_below, std.gap_ci_low, std.gap_ci_high)] + \
       list(zip(lv.lab, lv.raw_rank_gap_above_minus_below, lv.gap_ci_low, lv.gap_ci_high))
fig, ax = plt.subplots(figsize=(9, 5.6))
fig.subplots_adjust(left=0.1, right=0.98, top=0.78, bottom=0.12)
ax.axhspan(-0.2, 0, color=BLUE, alpha=0.06, lw=0); ax.axhspan(0, 0.6, color=ORANGE, alpha=0.06, lw=0)
ax.axhline(0, color=INK2, lw=1)
xs = list(range(len(rows)))
for x, (lab, g, lo, hi) in zip(xs, rows):
    c = BLUE if g < 0 else ORANGE
    ax.plot([x, x], [lo, hi], color=c, lw=2, solid_capstyle="round")
    # diamonds, not circles: in this series circles and squares mean cooperate and defect
    ax.scatter([x], [g], s=85, marker="D", color=c, edgecolor="white", linewidth=1.8, zorder=3)
    ax.annotate(f"{g:+.2f}".replace("-", "\u2212"), (x, g), xytext=(0, 12 if g >= 0 else -18), textcoords="offset points",
                ha="center", fontsize=10.5, color="#0b0b0b")
ax.plot(xs, [r[1] for r in rows], color=MUTED, lw=1, zorder=1)
ax.set_xticks(xs, [r[0] for r in rows]); ax.set_xlim(-0.5, len(rows) - 0.5); ax.set_ylim(-0.2, 0.6)
ax.set_xlabel("Noise: chance that any single move gets flipped")
ax.set_ylabel("Rank gap (above \u2212 below median)")
ax.text(len(rows) - 0.6, -0.17, "cooperating more than the median\ngoes with a better rank", color=BLUE, ha="right", va="bottom", fontsize=10.5)
ax.text(-0.35, 0.55, "cooperating more than the median goes with a worse rank", color=ORANGE, ha="left", va="center", fontsize=10.5)
ax.grid(axis="x", visible=False)
# title block sits above the plot, left-aligned with the y-axis label, and stays inside the plot's width
fig.text(0.02, 0.965, "A little noise turns cooperation from an asset into a liability", fontsize=16, fontweight="bold", ha="left", va="top")
fig.text(0.02, 0.905, "How much worse the above-median cooperators rank than the below-median ones, per tournament.\n"
         "Below zero, cooperating more pays. Lines are 95% intervals.", fontsize=11.5, color=INK2, ha="left", va="top", linespacing=1.4)
fig.savefig(OUT / "noise_flip_by_level.png"); plt.close(fig)

# 2. How much of winning the model explains
h = pd.read_csv(RES / "holdout_r2.csv")
sets = [("no_noise_no_probend", "Standard", 0.54), ("has_noise_no_probend", "Noisy", 0.37),
        ("no_noise_has_probend", "Probabilistic ending", 0.46), ("has_noise_has_probend", "Noisy + prob. ending", 0.54)]
def get(sub, chk): return float(h[(h.subset == sub) & (h.check == chk)].R2.iloc[0])
fig, ax = plt.subplots(figsize=(9, 4.8))
w = 0.26
series = [("Paper's linear model", BLUE, [p for _, _, p in sets]),
          ("XGBoost, new tournaments", ORANGE, [get(k, "paper range only") for k, _, _ in sets]),
          ("XGBoost, new tournaments and unseen strategies", AQUA, [get(k, "paper range, unseen strategies") for k, _, _ in sets])]
for i, (name, c, vals) in enumerate(series):
    bx = [j + (i - 1) * w for j in range(len(sets))]
    ax.bar(bx, vals, width=w - 0.03, color=c, label=name, zorder=2)
    for x, v in zip(bx, vals):
        ax.text(x, v + 0.015, f"{v:.2f}", ha="center", fontsize=9.5)
ax.set_xticks(range(len(sets)), [n for _, n, _ in sets]); ax.set_ylim(0, 1.08); ax.set_ylabel("R² (share of rank explained)")
ax.grid(axis="x", visible=False)
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=10)
title(fig, "A non-linear model explains much more of who wins",
      "Tournaments with noise and ending chance of 10% or less, the paper's range. Paper values are adjusted R².")
fig.savefig(OUT / "r2_by_setting.png"); plt.close(fig)

# 3. Feature importance, all settings pooled
imp = pd.read_csv(RES / "shap_importance_ci.csv")
imp = imp[imp.model == "all"].head(12).iloc[::-1]
names = {"Cooperation_rating_comp_to_median": "Cᵣ / C_median", "Cooperation_rating_comp_to_max": "Cᵣ / C_max",
         "CC_to_C_rate": "CC to C rate", "noise": "Noise (pₙ)", "probend": "Ending chance (pₑ)",
         "Cooperation_rating_comp_to_mean": "Cᵣ / C_mean", "memory_usage": "Memory usage",
         "CD_to_C_rate": "CD to C rate", "SSE": "SSE", "Cooperation_rating_mean": "C_mean",
         "Cooperation_rating_comp_to_min": "Cᵣ / C_min", "DC_to_C_rate": "DC to C rate"}
ratio = {"Cooperation_rating_comp_to_median", "Cooperation_rating_comp_to_max", "Cooperation_rating_comp_to_mean", "Cooperation_rating_comp_to_min"}
fig, ax = plt.subplots(figsize=(9, 5.4))
cols = [ORANGE if f in ratio else BLUE for f in imp.feature]
ys = list(range(len(imp)))
ax.barh(ys, imp.mean_abs_shap, color=cols, height=0.62, zorder=2)
ax.errorbar(imp.mean_abs_shap, ys, xerr=[imp.mean_abs_shap - imp.ci_low, imp.ci_high - imp.mean_abs_shap],
            fmt="none", ecolor="#0b0b0b", elinewidth=1, capsize=2, zorder=3)
ax.set_yticks(ys, [names[f] for f in imp.feature]); ax.set_xlabel("Mean |SHAP| (average shift in predicted rank)")
ax.grid(axis="y", visible=False)
ax.legend(handles=[Patch(color=ORANGE, label="Your cooperation compared with the field"), Patch(color=BLUE, label="Other features")],
          frameon=False, loc="lower right", fontsize=10)
title(fig, "How you compare with the crowd matters most",
      "Top 12 features, all four settings pooled. Black lines are 95% bootstrap intervals over tournaments.")
fig.savefig(OUT / "importance_all.png"); plt.close(fig)
print("done")
