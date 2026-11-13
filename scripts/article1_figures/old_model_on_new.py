"""Predicted vs actual rank for the 272 strategies, using the no-noise model trained on the 195-strategy tournaments.
Shapes stay clear of the article's move code (circle = cooperate, square = defect): seen strategies are small grey dots,
new library strategies blue dots, 1980 Fortran entries green triangles.
The R² and Spearman values in the subtitle are computed from the same file.
Usage: python3 old_model_on_new.py data/old_model_on_272.csv out.png"""
import sys, warnings, logging
warnings.filterwarnings("ignore"); logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, INK2, MUTED, LINE = "#1b1b1b", "#3d3c39", "#6b6a66", "#e6e5e1"
SEEN, LIB, FORT = "#c9c8c3", "#2a78d6", "#1a9e6e"
d = pd.read_csv(sys.argv[1])
seen = d[d.group.str.startswith("seen")]
new = d[~d.group.str.startswith("seen")]
lib, fort = new[new.fortran == 0], new[new.fortran == 1]


def fit(g):
    """R² and Spearman correlation (Pearson on ranks) of predicted against actual rank."""
    r2 = 1 - ((g.actual - g.pred) ** 2).sum() / ((g.actual - g.actual.mean()) ** 2).sum()
    return r2, g.actual.rank().corr(g.pred.rank())


plt.rcParams["font.family"] = ["DejaVu Sans"]
fig, ax = plt.subplots(figsize=(9, 8.6))
fig.subplots_adjust(left=0.11, right=0.97, bottom=0.09, top=0.86)
ax.plot([0, 1], [0, 1], color=MUTED, lw=1.1, ls=(0, (4, 3)), zorder=1)
ax.scatter(seen.actual, seen.pred, s=22, color=SEEN, lw=0, zorder=2, label="seen in training (%d)" % len(seen))
ax.scatter(lib.actual, lib.pred, s=60, color=LIB, edgecolor="white", lw=0.8, zorder=3, label="new: library strategy (%d)" % len(lib))
ax.scatter(fort.actual, fort.pred, s=70, marker="^", color=FORT, edgecolor="white", lw=0.8, zorder=3,
           label="new: 1980 Fortran entry (%d)" % len(fort))
LAB = {"Bush Mosteller": (-98, 8), "k53r": (8, -2), "k57r": (8, -8), "UsuallyCooperates": (8, 4), "k52r": (8, 4),
       "k37r": (-36, 6), "k32r": (8, 4), "k92r": (8, -12)}
for name, (dx, dy) in LAB.items():
    r = d[d.Name.str.split(":").str[0] == name]
    if r.empty: continue
    r = r.iloc[0]
    txt = "k92r (Tit for Tat)" if name == "k92r" else name
    ax.annotate(txt, (r.actual, r.pred), xytext=(dx, dy), textcoords="offset points", fontsize=10.5,
                color=INK, fontweight="bold" if name == "k92r" else "normal")
    if name == "k92r":
        ax.scatter([r.actual], [r.pred], s=150, facecolor="none", edgecolor=INK, lw=1.3, zorder=4)
ax.set_xlim(-0.03, 1.03); ax.set_ylim(-0.06, 1.03)
ax.set_xlabel("Actual normalized rank in the 272-strategy tournaments (0 = first)", fontsize=12, color=INK2)
ax.set_ylabel("Rank predicted by the model trained on 195 strategies", fontsize=12, color=INK2)
ax.grid(color=LINE, lw=0.8); ax.set_axisbelow(True)
for s in ("top", "right"): ax.spines[s].set_visible(False)
for s in ("left", "bottom"): ax.spines[s].set_color(SEEN)
ax.tick_params(colors=MUTED, labelsize=11)
ax.legend(loc="upper left", frameon=False, fontsize=11)
fig.text(0.11, 0.955, "A model trained on 195 strategies, tested on ones it never saw", fontsize=16, fontweight="bold", color=INK)
fig.text(0.11, 0.905, "One point per strategy, averaged over 100 no-noise tournaments. On the dashed line = perfect guess.\n"
         "New strategies: R² %.2f, Spearman %.2f. Seen strategies: R² %.2f, Spearman %.2f." % (*fit(new), *fit(seen)),
         fontsize=11, color=MUTED, linespacing=1.4, va="center")
fig.savefig(sys.argv[2], dpi=200, facecolor="white")
print("ok")
