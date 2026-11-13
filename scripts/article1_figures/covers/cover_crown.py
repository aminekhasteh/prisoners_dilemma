"""Cover idea 1: Tit for Tat's crown slides onto a trained strategy. 14:10, sketch style. Usage: python3 cover_crown.py out.png"""
import sys, warnings, logging
warnings.filterwarnings("ignore"); logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Arc, FancyBboxPatch, Polygon, Rectangle
from matplotlib.transforms import Affine2D

COOP, DEFECT, INK, MUTED, INK2, GOLD, PAPER = "#2a78d6", "#eb6834", "#1b1b1b", "#6b6a66", "#3d3c39", "#f2b51d", "#fbfaf6"

def crown(ax, cx, cy, s, angle):
    pts = np.array([[-1, 0], [1, 0], [1.05, 0.95], [0.5, 0.45], [0, 1.15], [-0.5, 0.45], [-1.05, 0.95]]) * s
    t = Affine2D().rotate_deg(angle).translate(cx, cy)
    ax.add_patch(Polygon(t.transform(pts), closed=True, facecolor=GOLD, edgecolor=INK, lw=2.6, zorder=6))
    for px, py in ([-1.05, 0.95], [0, 1.15], [1.05, 0.95]):
        x, y = t.transform([[px * s, py * s]])[0]
        ax.add_patch(Circle((x, y), 0.09 * s, facecolor=GOLD, edgecolor=INK, lw=2, zorder=7))
    x, y = t.transform([[0, 0.28 * s]])[0]
    ax.add_patch(Circle((x, y), 0.13 * s, facecolor=DEFECT, edgecolor=INK, lw=1.6, zorder=7))

fig = plt.figure(figsize=(14, 10))
plt.xkcd(scale=0.7, length=120, randomness=2)
plt.rcParams["font.family"] = ["Humor Sans", "Comic Neue", "DejaVu Sans"]
plt.rcParams["path.effects"] = []
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 14); ax.set_ylim(0, 10); ax.set_aspect("equal"); ax.axis("off")
ax.add_patch(Rectangle((0, 0), 14, 10, facecolor=PAPER, edgecolor="none", zorder=0))

ax.text(7, 8.85, "Is Tit for Tat still the best strategy?", ha="center", va="center", fontsize=38, fontweight="bold", color=INK)
ax.text(7, 8.0, "195 strategies, 45,000 tournaments, one new champion", ha="center", va="center", fontsize=21, color=INK2)

ground = 1.55
ax.plot([0.8, 13.2], [ground, ground], color=INK, lw=2.2)

# Tit for Tat: Player 1's circle, a little stunned
tx, ty, r = 3.7, 3.75, 1.75
ax.add_patch(Circle((tx, ty), r, facecolor=COOP, edgecolor=INK, lw=3, zorder=3))
for dx in (-0.32, 0.32):
    ax.add_patch(Circle((tx + dx * r, ty + 0.2 * r), 0.075 * r, color=INK, zorder=4))
    ax.plot([tx + dx * r - 0.16 * r, tx + dx * r + 0.12 * r], [ty + 0.42 * r, ty + 0.36 * r + (0.05 * r if dx > 0 else 0)],
            color=INK, lw=2.4, zorder=4)
ax.add_patch(Circle((tx, ty - 0.38 * r), 0.13 * r, facecolor=INK, edgecolor=INK, zorder=4))   # small "oh"
ax.text(tx, ground - 0.55, "Tit for Tat", ha="center", va="center", fontsize=24, fontweight="bold", color=COOP)
ax.text(tx, ground - 1.05, "champion since 1980", ha="center", va="center", fontsize=15, color=MUTED)

# a trained strategy: Player 2's rounded square, with a robot antenna, grinning
rx, ry, h = 10.3, 3.75, 1.65
ax.add_patch(FancyBboxPatch((rx - h, ry - h), 2 * h, 2 * h, boxstyle="round,pad=0,rounding_size=0.4",
                            facecolor=DEFECT, edgecolor=INK, lw=3, zorder=3))
ax.plot([rx, rx], [ry + h, ry + h + 0.55], color=INK, lw=3, zorder=2)
ax.add_patch(Circle((rx, ry + h + 0.66), 0.14, facecolor=GOLD, edgecolor=INK, lw=2, zorder=3))
for dx in (-0.55, 0.55):
    ax.add_patch(Rectangle((rx + dx - 0.2, ry + 0.25), 0.4, 0.42, facecolor="white", edgecolor=INK, lw=2.2, zorder=4))
    ax.add_patch(Rectangle((rx + dx - 0.07, ry + 0.3), 0.15, 0.2, facecolor=INK, edgecolor=INK, lw=0, zorder=5))
ax.add_patch(Arc((rx, ry - 0.35), 1.6, 0.9, theta1=195, theta2=345, lw=3, color=INK, zorder=4))
ax.text(rx, ground - 0.55, "a trained strategy", ha="center", va="center", fontsize=24, fontweight="bold", color=DEFECT)
ax.text(rx, ground - 1.05, "tuned by evolution", ha="center", va="center", fontsize=15, color=MUTED)

# the crown, mid-flight from one head to the other
crown(ax, 8.75, 6.45, 0.75, -20)
th = np.linspace(np.radians(160), np.radians(35), 60)
cx0, cy0, R = 6.95, 4.9, 2.05
ax.plot(cx0 + R * np.cos(th), cy0 + R * np.sin(th), color=MUTED, lw=2.2, ls=(0, (5, 4)), zorder=1)
for k, (x0, y0) in enumerate(((7.95, 7.15), (7.75, 6.85), (7.65, 6.5))):
    ax.plot([x0 - 0.55 + 0.1 * k, x0 - 0.05], [y0, y0 - 0.05], color=INK2, lw=1.8, zorder=1)
ax.text(tx + 0.15, ty + r + 0.45, "hey!", ha="center", va="center", fontsize=19, color=INK2, rotation=8)

fig.savefig(sys.argv[1], dpi=150, facecolor=PAPER)
print("ok")
