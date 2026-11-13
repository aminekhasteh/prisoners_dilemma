"""Sketch-style infographic of the four Prisoner's Dilemma outcomes. Usage: python3 payoffs.py out.png"""
import sys, warnings, logging
warnings.filterwarnings("ignore"); logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Arc, FancyBboxPatch

COOP, DEFECT, INK, MUTED, INK2 = "#2a78d6", "#eb6834", "#1b1b1b", "#6b6a66", "#3d3c39"
FACE = {5: "grin", 3: "smile", 1: "meh", 0: "sad"}

def face(ax, x, y, r, color, pts, square=False):
    if square:
        ax.add_patch(FancyBboxPatch((x - 0.9 * r, y - 0.9 * r), 1.8 * r, 1.8 * r, boxstyle="round,pad=0,rounding_size=0.25",
                                    facecolor=color, edgecolor=INK, lw=2, alpha=0.9, zorder=2))
    else:
        ax.add_patch(Circle((x, y), r, facecolor=color, edgecolor=INK, lw=2, alpha=0.9, zorder=2))
    for dx in (-0.32, 0.32):
        ax.add_patch(Circle((x + dx * r, y + 0.22 * r), 0.07 * r, color=INK, zorder=3))
    m = FACE[pts]
    if m == "grin":
        ax.add_patch(Arc((x, y - 0.12 * r), 1.0 * r, 0.8 * r, theta1=200, theta2=340, lw=2.5, color=INK, zorder=3))
    elif m == "smile":
        ax.add_patch(Arc((x, y - 0.1 * r), 0.7 * r, 0.45 * r, theta1=200, theta2=340, lw=2.5, color=INK, zorder=3))
    elif m == "meh":
        ax.plot([x - 0.3 * r, x + 0.3 * r], [y - 0.35 * r, y - 0.35 * r], lw=2.5, color=INK, zorder=3)
    else:
        ax.add_patch(Arc((x, y - 0.55 * r), 0.7 * r, 0.45 * r, theta1=20, theta2=160, lw=2.5, color=INK, zorder=3))

def panel(ax, you, them, py, pt, title, sub):
    ax.set_xlim(0, 10); ax.set_ylim(1, 10); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.2, 1.2), 9.6, 8.6, boxstyle="round,pad=0.1,rounding_size=0.6",
                                facecolor="white", edgecolor="#c9c8c3", lw=1.5))
    ax.text(5, 9.15, title, ha="center", va="center", fontsize=15 if len(title) < 20 else 12.5, fontweight="bold", color=INK)
    ax.plot([1.0, 9.0], [8.6, 8.6], color=INK, lw=1.5)
    ax.text(5, 7.75, sub, ha="center", va="center", fontsize=10.5, color=INK2, linespacing=1.3,
            bbox=dict(boxstyle="round,pad=0.45,rounding_size=0.3", facecolor="#f6f5f2", edgecolor="#c9c8c3", lw=1.2))
    for x, who, move, pts, sq in ((2.6, "Player 1", you, py, False), (7.4, "Player 2", them, pt, True)):
        col = COOP if move == "C" else DEFECT
        face(ax, x, 4.55, 1.15, col, pts, sq)
        ax.text(x, 2.85, who, ha="center", fontsize=12.5, color=INK)
        ax.text(x, 1.95, "cooperates" if move == "C" else "defects", ha="center", fontsize=12.5, color=col, fontweight="bold")
        ax.text(x, 6.3, f"+{pts}", ha="center", va="center", fontsize=22, fontweight="bold", color=INK)
    ax.plot([5, 5], [1.7, 6.8], color=MUTED, lw=1.5, ls=(0, (4, 3)))

plt.xkcd(scale=0.6, length=120, randomness=2)
plt.rcParams["font.family"] = ["Humor Sans", "Comic Neue", "DejaVu Sans"]
plt.rcParams["path.effects"] = []
fig, axes = plt.subplots(2, 2, figsize=(10, 9.2))
panel(axes[0, 0], "C", "C", 3, 3, "Both cooperate", "Reward (R) for both")
panel(axes[0, 1], "C", "D", 0, 5, "Player 1 cooperates, Player 2 defects", "Player 1 gets the Sucker's payoff (S),\nPlayer 2 gets the Temptation (T)")
panel(axes[1, 0], "D", "C", 5, 0, "Player 1 defects, Player 2 cooperates", "Player 1 gets the Temptation (T),\nPlayer 2 gets the Sucker's payoff (S)")
panel(axes[1, 1], "D", "D", 1, 1, "Both defect", "Punishment (P) for both")
fig.text(0.5, 0.995, "One round of the Prisoner's Dilemma", ha="center", va="top", fontsize=19, fontweight="bold", color=INK)
fig.text(0.5, 0.955, "Player 1 is the circle, Player 2 is the square. One move each, at the same time.", ha="center", va="top", fontsize=12.5, color=MUTED)
fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.92, wspace=0.06, hspace=0.06)
fig.savefig(sys.argv[1], dpi=180, facecolor="white")
print("ok")
