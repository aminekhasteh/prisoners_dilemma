"""Mean rank of the five LLM strategies (out of 277, 1 = best) across settings, one line per model, with Tit for Tat
(k92r) as a dashed grey reference.
  noise:  63-turn games at 0, 1 and 5% noise (20, 13 and 7 tournaments)  -> llm_rank_noise.png
  length: no noise, games of 63, 77, 151, 156 and 308 turns (20 each)     -> llm_rank_by_length.png
Lengths are spaced evenly (they are the five fixed lengths of Axelrod's second tournament, not a scale).
If a setting has fewer tournaments than planned, the x label says so.
Usage: python3 llm_rank_lines.py data/ranks_by_setting.csv noise|length out.png [--dpi=200]"""
import sys
import pandas as pd
from style import setup, plt, INK, INK2, MUTED, LINE, LLMS, TFT, axes_style, titles

r = pd.read_csv(sys.argv[1]); mode = sys.argv[2]; out = sys.argv[3]
DPI = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--dpi=")), 200))
if mode == "noise":
    r = r[r.turns == 63]
    keys = [("standard", 0.0), ("noise1", 0.01), ("noise5", 0.05)]
    sel = lambda c, n: r[(r.condition == c) & (r.noise == n)]
    ticks = ["No noise", "1% noise", "5% noise"]
    planned = [20, 13, 7]
    xlabel = "Chance that any single move gets flipped (63-turn games)"
    title = "Add a little noise, and the grudge falls apart"
    sub = ("Mean rank out of 277 (1 = best) in 63-turn games: 20 tournaments without noise, 13 at 1% and 7 at 5%.\n"
           "One line per chatbot strategy. Dashed grey = Tit for Tat.")
else:
    r = r[r.condition == "standard"]
    keys = [("standard", t) for t in (63, 77, 151, 156, 308)]
    sel = lambda c, t: r[r.turns == t]
    ticks = ["63", "77", "151", "156", "308"]
    planned = [20] * 5
    xlabel = "Game length (turns per match), no noise"
    title = "In longer games, the forgivers climb and the grudge slides"
    sub = ("Mean rank out of 277 (1 = best) over 20 tournaments at each of the five game lengths, no noise.\n"
           "One line per chatbot strategy. Dashed grey = Tit for Tat.")

setup()
fig, ax = plt.subplots(figsize=(10.8, 6.6))
fig.subplots_adjust(left=0.09, right=0.76, bottom=0.12, top=0.83)
xs = list(range(len(keys)))
series = {}
for name in list(LLMS) + [TFT]:
    series[name] = [float(sel(*k).set_index("Name").loc[name, "mean_rank"]) for k in keys]
counts = [int(sel(*k).tournaments.max()) for k in keys]
ticks = [t if c >= p else f"{t}\n({c} of {p} tournaments)" for t, c, p in zip(ticks, counts, planned)]

ax.plot(xs, series[TFT], color=MUTED, lw=1.6, ls=(0, (4, 3)), zorder=2)
for name, (short, _, col) in LLMS.items():
    ax.plot(xs, series[name], color=col, lw=2.2, zorder=3, solid_capstyle="round")
    ax.scatter(xs, series[name], s=90, marker="D", color=col, edgecolor="white", lw=1.4, zorder=4)

GAP = 11   # rank units between label centres, so no two labels overlap


def spread(vals):
    """Label positions for values sorted top to bottom, pushed down until GAP apart."""
    placed = []
    for y in vals:
        placed.append(max(y, placed[-1] + GAP) if placed else y)
    return placed


ends = sorted([(series[n][-1], n) for n in list(LLMS) + [TFT]])
for (y, n), y_lab in zip(ends, spread([e[0] for e in ends])):
    short = "Tit for Tat" if n == TFT else LLMS[n][0]
    ax.annotate(f"{short}, {y:.0f}", (xs[-1], y), xytext=(xs[-1] + 0.18, y_lab), textcoords="data",
                ha="left", va="center", fontsize=11, color=INK2 if n == TFT else INK,
                fontweight="normal" if n == TFT else "bold", annotation_clip=False,
                arrowprops=dict(arrowstyle="-", color=LINE, lw=0.8, shrinkA=0, shrinkB=6) if abs(y_lab - y) > 2 else None)
# start values, small and muted, so the first column can be read without the table
starts = sorted([(series[n][0], n) for n in LLMS])
for (y, n), y_lab in zip(starts, spread([s_[0] for s_ in starts])):
    ax.text(xs[0] - 0.09, y_lab, f"{y:.0f}", ha="right", va="center", fontsize=9.5, color=MUTED)

ax.set_ylim(200, 1); ax.set_yticks([1, 50, 100, 150, 200])
ax.set_xlim(-0.35, xs[-1] + 0.12); ax.set_xticks(xs, ticks)
ax.set_xlabel(xlabel, fontsize=12, color=INK2)
ax.set_ylabel("Mean rank out of 277 (1 = best)", fontsize=12, color=INK2)
axes_style(ax); ax.grid(axis="x", visible=False)
titles(fig, 0.09, 0.925, title, sub)
fig.savefig(out, dpi=DPI)
print("ok", out, counts)
