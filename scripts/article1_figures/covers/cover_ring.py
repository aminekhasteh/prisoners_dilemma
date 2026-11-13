"""Cover idea 3: the all-195 SSE ring as art, no labels, title on the left. 14:10.
Bars and grouping follow sse_circular.py (nice, nasty, other; median SSE, capped at 1.6).
Usage: python3 cover_ring.py sse_all_circular.csv out.png ["title with \n breaks"] ["subtitle"] ["kicker under the title"]
Pass "-" as the title for a text-free cover (ring centred, small colour key only)."""
import sys, warnings, logging
warnings.filterwarnings("ignore"); logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COOP, DEFECT, OTHER, INK, INK2, MUTED, PAPER = "#2a78d6", "#eb6834", "#9a9893", "#1b1b1b", "#3d3c39", "#6b6a66", "#fbfaf6"
df = pd.read_csv(sys.argv[1])
CAP, GAP = 1.6, 4
groups = [("nice", COOP), ("nasty", DEFECT), ("other", OTHER)]
n_slots = len(df) + GAP * len(groups)
step = 2 * np.pi / n_slots
HOLE = 0.5 * CAP

plt.xkcd(scale=0.5, length=120, randomness=2)
plt.rcParams["font.family"] = ["Humor Sans", "Comic Neue", "DejaVu Sans"]
plt.rcParams["path.effects"] = []
fig = plt.figure(figsize=(14, 10), facecolor=PAPER)

NO_TEXT = len(sys.argv) > 3 and sys.argv[3] == "-"
# ring on the right, or centred when there is no title block
ax = fig.add_axes([0.205, 0.07, 0.59, 0.86] if NO_TEXT else [0.405, 0.07, 0.59, 0.86], projection="polar")
ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
ax.set_ylim(-HOLE, CAP); ax.axis("off"); ax.set_facecolor(PAPER)
th = np.linspace(0, 2 * np.pi, 400)
for r in (0.5, 1.0, 1.5):
    ax.plot(th, np.full_like(th, r), color="#d9d7d0", lw=0.9, ls=(0, (2, 3)), zorder=0)
ax.plot(th, np.zeros_like(th), color=INK, lw=1.6, zorder=2)
slot = 0.0
for key, col in groups:
    sub = df[df.group == key].sort_values("place")
    start = slot
    for _, row in sub.iterrows():
        t = (slot + 0.5) * step
        ax.bar(t, min(row.sse_median, CAP), width=step * 0.72, bottom=0, color=col, edgecolor=INK, lw=0.6, zorder=3, alpha=0.95)
        slot += 1
    arc = np.linspace((start + 0.3) * step, (slot - 0.3) * step, 80)
    ax.plot(arc, np.full_like(arc, -0.08 * CAP), color=col, lw=9, solid_capstyle="round", zorder=2)
    slot += GAP

# title block on the left
TITLE = sys.argv[3].replace("\\n", "\n") if len(sys.argv) > 3 else "Is Tit for Tat\nstill the best\nstrategy?"
SUB = sys.argv[4].replace("\\n", "\n") if len(sys.argv) > 4 else "195 strategies, 45,000 tournaments.\nWho wins now, and how they play."
if NO_TEXT:
    for i, (lab, col) in enumerate((("nice", COOP), ("nasty", DEFECT), ("sometimes nice", OTHER))):
        y = 0.165 - 0.05 * i
        fig.patches.append(plt.Rectangle((0.80, y - 0.012), 0.019, 0.024, transform=fig.transFigure,
                                         facecolor=col, edgecolor=INK, lw=1.1))
        fig.text(0.828, y, lab, ha="left", va="center", fontsize=15, color=INK2)
    fig.savefig(sys.argv[2], dpi=150, facecolor=PAPER)
    print("ok"); sys.exit()
KICKER = sys.argv[5].replace("\\n", "\n") if len(sys.argv) > 5 else ""
fig.text(0.055, 0.76 if KICKER else 0.70, TITLE, ha="left", va="center", fontsize=46,
         fontweight="bold", color=INK, linespacing=1.15)
if KICKER:
    fig.text(0.057, 0.585, KICKER, ha="left", va="center", fontsize=27, color=INK2, linespacing=1.25)
fig.text(0.057, 0.43, SUB,
         ha="left", va="center", fontsize=18, color=INK2, linespacing=1.5)
for i, (lab, col, n) in enumerate((("nice", COOP, (df.group == "nice").sum()),
                                   ("nasty", DEFECT, (df.group == "nasty").sum()),
                                   ("sometimes nice", OTHER, (df.group == "other").sum()))):
    y = 0.27 - 0.055 * i
    fig.patches.append(plt.Rectangle((0.058, y - 0.014), 0.022, 0.028, transform=fig.transFigure,
                                     facecolor=col, edgecolor=INK, lw=1.2))
    fig.text(0.092, y, f"{lab}", ha="left", va="center", fontsize=17, color=INK)
fig.savefig(sys.argv[2], dpi=150, facecolor=PAPER)
print("ok")
