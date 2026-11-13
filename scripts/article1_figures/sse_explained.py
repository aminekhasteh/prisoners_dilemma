"""Sketch-style explainer of SSE: a strategy's four cooperation rates vs its closest ZD twin.
Method: Knight, Harper, Glynatsi & Gillard (2019), eqs. 17-21. Usage: python3 sse_explained.py out.png"""
import sys, warnings, logging
warnings.filterwarnings("ignore"); logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch

COOP, GAP, INK, MUTED, INK2 = "#2a78d6", "#eb6834", "#1b1b1b", "#6b6a66", "#3d3c39"
R, S, T, P = 3, 0, 5, 1
C = np.array([[R - P, R - P], [S - P, T - P], [T - P, S - P], [0, 0]], float)

def zd_twin(p):
    """Closest extortion-type ZD strategy to p (least squares), and the SSE."""
    p = np.asarray(p, float); shift = np.array([1, 1, 0, 0])
    x, *_ = np.linalg.lstsq(C, p - shift, rcond=None)
    twin = C @ x + shift
    return twin, float(((p - twin) ** 2).sum())

def panel(ax, name, blurb, p):
    twin, sse = zd_twin(p)
    ax.set_xlim(0, 10); ax.set_ylim(0, 5.2); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.15, 0.15), 9.7, 4.9, boxstyle="round,pad=0.05,rounding_size=0.4",
                                facecolor="white", edgecolor="#c9c8c3", lw=1.5))
    ax.text(0.55, 4.6, name, ha="left", va="center", fontsize=16, fontweight="bold", color=INK)
    ax.text(0.55, 4.05, blurb, ha="left", va="center", fontsize=11.5, color=INK2)
    base, H, w = 1.35, 2.0, 0.78
    xs = [1.45, 2.65, 3.85, 5.05]
    ax.plot([0.85, 5.65], [base, base], color=INK, lw=1.5)
    ax.plot([0.85, 5.65], [base + H, base + H], color="#c9c8c3", lw=1, ls=(0, (2, 3)))
    ax.text(0.75, base + H, "always", ha="right", va="center", fontsize=9.5, color=MUTED)
    ax.text(0.75, base, "never", ha="right", va="center", fontsize=9.5, color=MUTED)
    for x, lab, pv, tv in zip(xs, ("CC", "CD", "DC", "DD"), p, twin):
        lo, hi = sorted((pv, tv))
        if lo > 0:  # the part where strategy and twin agree
            ax.add_patch(Rectangle((x - w / 2, base), w, lo * H, facecolor=COOP, edgecolor="none", alpha=0.9, zorder=2))
        if hi - lo > 1e-6:  # the gap
            ax.add_patch(Rectangle((x - w / 2, base + lo * H), w, (hi - lo) * H, facecolor="#fbd9c6",
                                   edgecolor=GAP, lw=0, hatch="///", zorder=2))
        if pv > 0:  # the strategy's own bar, solid outline
            ax.add_patch(Rectangle((x - w / 2, base), w, pv * H, facecolor="none", edgecolor=INK, lw=1.8, zorder=3))
        # the ZD twin: dashed outline
        ax.plot([x - w / 2 - 0.08, x + w / 2 + 0.08], [base + tv * H] * 2, color=INK, lw=2.4, ls=(0, (3, 2)), zorder=4)
        if tv > 0.01:
            for sx in (x - w / 2, x + w / 2):
                ax.plot([sx, sx], [base, base + tv * H], color=INK, lw=1.2, ls=(0, (3, 2)), zorder=4)
        ax.text(x, base - 0.3, f"after {lab}", ha="center", va="center", fontsize=11, color=INK)
        g2 = (pv - tv) ** 2
        ax.text(x, base - 0.75, f"gap² {g2:.2f}", ha="center", va="center", fontsize=10.5,
                color=GAP if g2 > 1e-6 else MUTED, fontweight="bold" if g2 > 1e-6 else "normal")
    gaps = [(a - b) ** 2 for a, b in zip(p, twin)]
    ax.add_patch(FancyBboxPatch((6.35, 0.75), 3.1, 2.75, boxstyle="round,pad=0.1,rounding_size=0.3",
                                facecolor="#f6f5f2", edgecolor="#c9c8c3", lw=1.2))
    ax.text(7.9, 3.0, "add up the gaps²", ha="center", va="center", fontsize=10.5, color=INK2)
    ax.text(7.9, 2.45, " + ".join(f"{g:.2f}" for g in gaps), ha="center", va="center", fontsize=10.5, color=INK2)
    ax.text(7.9, 1.5, f"SSE = {sse:.2f}", ha="center", va="center", fontsize=19, fontweight="bold", color=INK)

plt.xkcd(scale=0.6, length=120, randomness=2)
plt.rcParams["font.family"] = ["Humor Sans", "Comic Neue", "DejaVu Sans"]
plt.rcParams["path.effects"] = []
fig, axes = plt.subplots(3, 1, figsize=(10, 12.4))
panel(axes[0], "Extort-2", "A ZD strategy by design, so the bars match the dashed lines exactly.", [8 / 9, 1 / 2, 1 / 3, 0])
panel(axes[1], "Grudger", "Cooperates until the other player defects once, then never forgives.", [1, 0, 0, 0])
panel(axes[2], "Win-Stay-Lose-Shift", "Like Grudger, except it tries to make peace after both players defect.", [1, 0, 0, 1])
fig.text(0.5, 0.995, "How SSE is measured", ha="center", va="top", fontsize=20, fontweight="bold", color=INK)
fig.text(0.5, 0.962, "Solid bars: how often a strategy cooperates after each kind of round.\n"
         "Dashed lines: its closest ZD strategy. Orange: the gaps between the two.",
         ha="center", va="top", fontsize=12.5, color=MUTED, linespacing=1.4)
fig.text(0.5, 0.012, "CC: both cooperated.  CD: it cooperated, the other player defected.  DC: the reverse.  DD: both defected.",
         ha="center", va="bottom", fontsize=10.5, color=MUTED)
fig.subplots_adjust(left=0.02, right=0.98, bottom=0.04, top=0.905, hspace=0.07)
fig.savefig(sys.argv[1], dpi=180, facecolor="white")
print("ok")
