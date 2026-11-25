"""R² by setting as a small table image for the Article 1 Substack post (Substack has no tables).
Numbers: paper adjusted R² (in-sample) and XGBoost held-out R² from data/holdout_r2.csv, paper range only.
Usage: python3 r2_table.py data/holdout_r2.csv out.png"""
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

INK, MUTED, LINE, TILE = "#1b1b1b", "#6b6a66", "#c9c8c3", "#efeeea"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams["font.family"] = "DejaVu Sans"
h = pd.read_csv(sys.argv[1])
def get(sub, chk): return float(h[(h.subset == sub) & (h.check == chk)].R2.iloc[0])
SETS = [("no_noise_no_probend", "Standard", 0.54), ("has_noise_no_probend", "Noisy", 0.37),
        ("no_noise_has_probend", "Probabilistic ending", 0.46), ("has_noise_has_probend", "Noisy + prob. ending", 0.54)]
ROWS = [(n, p, get(k, "paper range only"), get(k, "paper range, unseen strategies")) for k, n, p in SETS]

fig = plt.figure(figsize=(10, 5.2), facecolor="white")
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 10); ax.set_ylim(0, 5.2); ax.axis("off")
fig.text(0.04, 0.94, "A non-linear model explains much more of who wins", fontsize=17, fontweight="bold", color=INK, va="top")
fig.text(0.04, 0.865, "R² (share of rank explained). Tournaments with noise and ending chance of 10% or less.", fontsize=12, color=MUTED, va="top")
X_LAB, XS = 0.4, (4.6, 6.4, 8.3)
heads = [("Linear model (paper)", "tested on the data\nit learned from", BLUE),
         ("XGBoost", "new tournaments,\nfamiliar strategies", ORANGE),
         ("XGBoost", "new tournaments\nand new strategies", AQUA)]
y_head = 3.95
for x, (t, s, c) in zip(XS, heads):
    ax.text(x, y_head, t, ha="center", fontsize=12.5, fontweight="bold", color=c)
    ax.text(x, y_head - 0.12, s, ha="center", va="top", fontsize=10, color=MUTED, linespacing=1.25)
ax.plot([X_LAB, 9.6], [y_head - 0.72, y_head - 0.72], color=INK, lw=1.2)
for i, (name, *vals) in enumerate(ROWS):
    y = 2.85 - i * 0.68
    ax.text(X_LAB, y, name, fontsize=13, color=INK, va="center")
    for x, v in zip(XS, vals):
        ax.add_patch(FancyBboxPatch((x - 0.45, y - 0.22), 0.9, 0.44, boxstyle="round,pad=0,rounding_size=0.08", fc=TILE, ec="none"))
        ax.text(x, y, f"{v:.2f}", ha="center", va="center", fontsize=14, fontweight="bold", color=INK)
    if i < len(ROWS) - 1:
        ax.plot([X_LAB, 9.6], [y - 0.34, y - 0.34], color=LINE, lw=0.8)
fig.text(0.04, 0.035, "Paper values are adjusted R² on the data the model was fit to. XGBoost values are on held-out tournaments.",
         fontsize=10, color=MUTED)
fig.savefig(sys.argv[2], dpi=200, facecolor="white")
print("ok")
