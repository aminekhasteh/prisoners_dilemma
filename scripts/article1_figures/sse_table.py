"""Median SSE of nice vs nasty strategies, as a small table image for the Article 1 Substack post (Substack has no tables).
Numbers come from scripts/knight272/results/niceness_sse.txt (272 strategies, Knight et al. 2025 no-noise tournaments).
Usage: python3 sse_table.py out.png"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

INK, INK2, MUTED, LINE, TILE = "#1b1b1b", "#3d3c39", "#6b6a66", "#c9c8c3", "#efeeea"
NICE, NASTY = "#2a78d6", "#eb6834"
plt.rcParams["font.family"] = "DejaVu Sans"

ROWS = [("All 272 strategies", "145 nice, 127 nasty", "0.05", "0.14", "Yes", "p < 0.001"),
        ("Without the 48 that usually\ncooperate after a mutual defection", "133 nice, 91 nasty", "0.05", "0.06", "No", "p = 0.21")]

fig = plt.figure(figsize=(10, 4.4), facecolor="white")
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 10); ax.set_ylim(0, 4.4); ax.axis("off")
fig.text(0.04, 0.93, "Nasty strategies look less ZD-like, until you remove one habit", fontsize=17, fontweight="bold", color=INK, va="top")
fig.text(0.04, 0.84, "Median SSE of each group. Lower means closer to a zero-determinant strategy.", fontsize=12, color=MUTED, va="top")

X_LAB, X_NICE, X_NASTY, X_GAP = 0.4, 5.6, 7.0, 8.55
y_head = 3.25
ax.text(X_NICE, y_head, "Nice", ha="center", fontsize=14, fontweight="bold", color=NICE)
ax.text(X_NASTY, y_head, "Nasty", ha="center", fontsize=14, fontweight="bold", color=NASTY)
ax.text(X_GAP, y_head, "Real gap?", ha="center", fontsize=14, fontweight="bold", color=INK)
ax.plot([X_LAB, 9.6], [y_head - 0.22, y_head - 0.22], color=INK, lw=1.2)

for i, (label, counts, nice, nasty, gap, p) in enumerate(ROWS):
    y = 2.45 - i * 1.15
    ax.text(X_LAB, y + 0.08, label, fontsize=13, color=INK, va="center", linespacing=1.3)
    ax.text(X_LAB, y - (0.5 if "\n" in label else 0.32), counts, fontsize=10.5, color=MUTED, va="center")
    for x, v in ((X_NICE, nice), (X_NASTY, nasty)):
        ax.add_patch(FancyBboxPatch((x - 0.48, y - 0.24), 0.96, 0.48, boxstyle="round,pad=0,rounding_size=0.08", fc=TILE, ec="none"))
        ax.text(x, y, v, ha="center", va="center", fontsize=15, fontweight="bold", color=INK)
    ax.text(X_GAP, y + 0.08, gap, ha="center", va="center", fontsize=14, fontweight="bold", color=INK)
    ax.text(X_GAP, y - 0.24, p, ha="center", va="center", fontsize=10.5, color=MUTED)
    if i == 0:
        ax.plot([X_LAB, 9.6], [y - 0.68, y - 0.68], color=LINE, lw=0.9)

fig.text(0.04, 0.035, "Mann-Whitney test on each strategy's median SSE across Knight et al.'s 100 no-noise tournaments.",
         fontsize=10, color=MUTED)
fig.savefig(sys.argv[1], dpi=200, facecolor="white")
print("ok")
