"""Memory-1 vs memory-2: one dumbbell per model, its rank (out of the field size) when it remembers only the last round (filled
diamond) and the last two rounds (hollow diamond); where the two ranks are less than five places apart, the filled
diamond is drawn small inside the hollow one. One panel per setting found in data/m2_ranks.csv, in this order:
63 turns; mean over the five lengths; 1% noise; 5% noise. The dashed line is Tit for Tat in the same field.
Usage: python3 llm_m1_vs_m2.py data/m2_ranks.csv out.png [--dpi=200]"""
import sys
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patheffects import withStroke
from style import setup, plt, INK, INK2, MUTED, LINE, LLMS, TFT, axes_style, titles

r = pd.read_csv(sys.argv[1]); out = sys.argv[2]
DPI = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--dpi=")), 200))
SETTINGS = [("s63", "63 turns, no noise"), ("slen", "All lengths, no noise"),
            ("n1", "63 turns, 1% noise"), ("n5", "63 turns, 5% noise")]
SETTINGS = [(k, t) for k, t in SETTINGS if (r.setting == k).any()]
MODELS = list(LLMS)                    # same order as the other charts
N = int(r.players.max()) if "players" in r else 282
rk = lambda v: "%d" % int(v + 0.5)     # halves rounded up, as in the article's tables
HALO = [withStroke(linewidth=2.6, foreground="white")]   # keeps a number readable where the dashed line runs behind it
TIE = 5   # ranks: closer than this, the hollow diamond covers the filled one, so a small filled one is drawn inside it

setup()
n = len(SETTINGS)
nr = 1 if n <= 2 else 2; nc = -(-n // nr)          # 2 x 2 for four panels, so it still reads on a phone
fig, axes = plt.subplots(nr, nc, figsize=(10, 5.4 + 3.4 * (nr - 1)), sharey=True, sharex=True, squeeze=False)
axes = axes.ravel()
for ax in axes[n:]: ax.set_visible(False)
top = 0.68 if nr == 1 else 0.80
fig.subplots_adjust(left=0.17, right=0.97, bottom=0.12 if nr == 1 else 0.08, top=top, wspace=0.1, hspace=0.32)
for ax, (key, head) in zip(axes, SETTINGS):
    s = r[r.setting == key].set_index(["model", "memory"]).mean_rank
    t = s.get((TFT, 1))
    if t is not None:
        ax.axvline(t, color=MUTED, lw=1.3, ls=(0, (4, 3)), zorder=1)
        ax.text(t, -0.85, "Tit for Tat " + rk(t), ha="center", va="center", fontsize=9.5, color=INK2,
                bbox=dict(facecolor="white", edgecolor="none", pad=1.5), zorder=3)
    for i, m in enumerate(MODELS):
        col = LLMS[m][2]; a, b = s.get((m, 1)), s.get((m, 2))
        ax.plot([a, b], [i, i], color=LINE, lw=3, zorder=2, solid_capstyle="round")
        ax.scatter([a], [i], s=110, marker="D", color=col, edgecolor="white", lw=1.4, zorder=4)
        ax.scatter([b], [i], s=100, marker="D", facecolor="white", edgecolor=col, lw=2.2, zorder=5)
        if abs(a - b) < TIE:
            ax.scatter([a], [i], s=22, marker="D", color=col, lw=0, zorder=6)
        # numbers beside each end, on the outside of the dumbbell so they never sit on the bar
        lo, hi = (a, b) if a <= b else (b, a)
        ax.text(lo - 9, i, rk(lo), ha="right", va="center", fontsize=9.5, color=INK2 if lo == a else INK,
                fontweight="normal" if lo == a else "bold", path_effects=HALO)
        ax.text(hi + 9, i, rk(hi), ha="left", va="center", fontsize=9.5, color=INK2 if hi == a else INK,
                fontweight="normal" if hi == a else "bold", path_effects=HALO)
    ax.set_xlim(-30, N + 18); ax.set_xticks([1, 100, 200, N])
    ax.set_ylim(len(MODELS) - 0.5, -1.0)
    head += " (%d tournaments)" % r[r.setting == key].tournaments.max()
    ax.set_title(head, fontsize=12, color=INK, fontweight="bold", loc="left", pad=8)
    axes_style(ax); ax.grid(axis="y", visible=False); ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
axes[0].set_yticks(range(len(MODELS)), [LLMS[m][0] for m in MODELS], fontsize=11.5, color=INK)
for ax in axes[:n]:
    ax.tick_params(axis="y", labelleft=True, labelsize=11.5, labelcolor=INK) if ax.get_subplotspec().colspan.start == 0 else None
fig.supxlabel(f"Mean rank out of {N} (1 = best)", fontsize=12, color=INK2, y=0.01, x=0.57)
key = [Line2D([], [], ls="", marker="D", ms=9, color=MUTED, mec="white", label="memory-1: looks at the last round"),
       Line2D([], [], ls="", marker="D", ms=9, mfc="white", mec=MUTED, mew=2, label="memory-2: looks at the last two rounds (bold number)")]
fig.legend(handles=key, loc="upper left", bbox_to_anchor=(0.012, top + (0.12 if nr == 1 else 0.075)), ncol=2, frameon=False,
           fontsize=10.5, handletextpad=0.3, columnspacing=1.6)
titles(fig, 0.02, 0.945 if nr == 1 else 0.965, "Give the chatbots a second round of memory, and some jump to the top",
       "Each model's strategy, asked for twice: from the last round only, and from the last two rounds (Pal et al. 2026).\n"
       f"Both versions play in one {N}-player field: Knight et al.'s 272 strategies plus {N - 272} chatbot strategies. Dashed line = Tit for Tat.")
fig.savefig(out, dpi=DPI)
print("ok", out, [k for k, _ in SETTINGS])
