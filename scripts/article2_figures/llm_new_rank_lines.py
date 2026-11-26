"""The newer models' mean rank (out of 297, 1 = best) across settings, one line per strategy, in the same layout as
llm_rank_lines.py.
  noise:  63-turn games at 0, 1 and 5% noise (20, 13 and 7 tournaments)  -> new_llm_rank_noise.png
  length: no noise, games of 63, 77, 151, 156 and 308 turns (20 each)     -> new_llm_rank_by_length.png
Lines: the memory-2 strategies of the four new models that mostly cooperate (hollow diamonds; Claude Opus 5.5 in bold
ink, the others grey, because new models get no identity colour), the memory-1 strategies of Opus 5.5 and Haiku 5.5
(thin, small filled diamonds), the two best strategies of Pal et al. in their own colours (GPT-5 and Claude Sonnet 4,
memory-2), and Tit for Tat (k92r) as a dashed grey reference. Claude Sonnet 5.5 and GPT-6 Luna mostly defect and rank
below 250th in every setting, so they are left off the 1-to-200 axis and named in a note (llm_new_rank.py shows them).
What the titles claim is checked against the data first.
Usage: python3 llm_new_rank_lines.py data/new_ranks.csv noise|length out.png [--dpi=200]"""
import sys
import pandas as pd
from style import setup, plt, INK, INK2, MUTED, LINE, LLMS, TFT, axes_style, titles

r = pd.read_csv(sys.argv[1]); mode = sys.argv[2]; out = sys.argv[3]
DPI = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--dpi=")), 200))
N = int(r.players.max())
s = r.set_index(["setting", "model", "memory"]).mean_rank
HERO = "Claude Opus 5.5"
# (model as in the data, memory, label, style)
SERIES = [(HERO, 2, "Opus 5.5", "hero"),
          ("GPT-6.1 Sol", 2, "GPT-6.1 Sol", "new"),
          ("GPT-6.1 Terra", 2, "GPT-6.1 Terra", "new"),
          ("Claude Haiku 5.5", 2, "Haiku 5.5", "new"),
          (HERO, 1, "Opus 5.5, memory-1", "m1"),
          ("Claude Haiku 5.5", 1, "Haiku 5.5, memory-1", "m1"),
          ("GPT-5", 2, "GPT-5", "pal"),
          ("Claude Sonnet 4", 2, "Claude Sonnet 4", "pal")]
HIDDEN = ("Claude Sonnet 5.5", "GPT-6 Luna")
if mode == "noise":
    keys = ["s63", "n1", "n5"]
    ticks = ["No noise", "1% noise", "5% noise"]
    planned = [20, 13, 7]
    xlabel = "Chance that any single move gets flipped (63-turn games)"
    title = "At 5% noise, only Opus 5.5's memory-2 strategy still beats Tit for Tat"
    sub = f"Mean rank out of {N} (1 = best) in 63-turn games: 20 tournaments without noise, 13 at 1% and 7 at 5%.\n"
    last = r[(r.setting == "n5") & (r.Name != TFT)]
    ahead = last[last.mean_rank < s[("n5", TFT, 1)]].Name.tolist()
    assert ahead == ["LLM-m2: " + HERO], f"title no longer true, ahead of Tit for Tat at 5% noise: {ahead}"
else:
    keys = ["s63", "s77", "s151", "s156", "s308"]
    ticks = ["63", "77", "151", "156", "308"]
    planned = [20] * 5
    xlabel = "Game length (turns per match), no noise"
    title = "In longer games, Opus 5.5 climbs and the GPT-6.1 models slip"
    sub = f"Mean rank out of {N} (1 = best) over 20 tournaments at each of the five game lengths, no noise.\n"
    move = lambda m: s[(keys[-1], m, 2)] - s[(keys[0], m, 2)]
    assert move(HERO) < 0 < min(move("GPT-6.1 Sol"), move("GPT-6.1 Terra")), "title no longer true"
sub += "Hollow diamonds: memory-2 strategies. Small filled diamonds: memory-1. Dashed grey: Tit for Tat."
for m in HIDDEN:   # the note under the lines says so
    assert min(s[(k, m, mem)] for k in keys for mem in (1, 2)) > 250, f"{m} is no longer below 250th"

GREY, GREY1 = MUTED, "#8d8c87"
PAL = {short: col for short, _, col in LLMS.values()}
STYLE = {"hero": (dict(color=INK, lw=3.0, zorder=6), dict(s=90, facecolor="white", edgecolor=INK, lw=2.4, zorder=7)),
         "new": (dict(color=GREY, lw=2.0, zorder=4), dict(s=55, facecolor="white", edgecolor=GREY, lw=1.8, zorder=5)),
         "m1": (dict(color=GREY1, lw=1.2, zorder=3), dict(s=26, facecolor=GREY1, edgecolor=GREY1, lw=0.5, zorder=3))}
TEXT = {"hero": dict(fontsize=11.5, color=INK, fontweight="bold"), "new": dict(fontsize=11, color=INK),
        "pal": dict(fontsize=11, color=INK2), "m1": dict(fontsize=10, color=MUTED), "tft": dict(fontsize=11, color=INK2)}

setup()
fig, ax = plt.subplots(figsize=(10.8, 6.6))
fig.subplots_adjust(left=0.09, right=0.76, bottom=0.12, top=0.83)
xs = list(range(len(keys)))
counts = [int(r[r.setting == k].tournaments.max()) for k in keys]
ticks = [t if c >= p else f"{t}\n({c} of {p} tournaments)" for t, c, p in zip(ticks, counts, planned)]
tft = [float(s[(k, TFT, 1)]) for k in keys]
ax.plot(xs, tft, color=MUTED, lw=1.6, ls=(0, (4, 3)), zorder=2)
ends = [(tft[-1], "Tit for Tat", "tft")]
top = 0.0
for model, mem, lab, kind in SERIES:
    v = [float(s[(k, model, mem)]) for k in keys]
    if kind == "pal":   # Pal et al.'s models keep their colour from the other charts
        line = dict(color=PAL[model], lw=1.8, zorder=4)
        mark = dict(s=50, facecolor="white", edgecolor=PAL[model], lw=1.8, zorder=5)
    else:
        line, mark = STYLE[kind]
    ax.plot(xs, v, solid_capstyle="round", **line)
    ax.scatter(xs, v, marker="D", **mark)
    ends.append((v[-1], lab, kind)); top = max(top, max(v))
    if kind == "hero":   # where the highlighted line starts, so it can be read without the table
        ax.annotate("%d" % int(v[0] + 0.5), (xs[0], v[0]), xytext=(-13, 0), textcoords="offset points", ha="right",
                    va="center", fontsize=10.5, color=INK, fontweight="bold")


def rk(v):
    """Rank as a whole number, halves rounded up (100.5 -> 101), as in the article's tables."""
    return "%d" % int(v + 0.5)


GAP = 11   # rank units between label centres, so no two labels overlap


def spread(vals):
    """Label positions for values sorted top to bottom, pushed down until GAP apart."""
    placed = []
    for y in vals:
        placed.append(max(y, placed[-1] + GAP) if placed else y)
    return placed


ends.sort()
for (y, lab, kind), y_lab in zip(ends, spread([e[0] for e in ends])):
    ax.annotate(f"{lab}, {rk(y)}", (xs[-1], y), xytext=(xs[-1] + 0.18, y_lab), textcoords="data", ha="left",
                va="center", annotation_clip=False, **TEXT[kind],
                arrowprops=dict(arrowstyle="-", color=LINE, lw=0.8, shrinkA=0, shrinkB=6) if abs(y_lab - y) > 2 else None)

lo = max(200, top + 8)
ax.set_ylim(lo, 1); ax.set_yticks([1, 50, 100, 150, 200] + ([250] if lo > 250 else []))
ax.set_xlim(-0.35, xs[-1] + 0.12); ax.set_xticks(xs, ticks)
ax.text(0.012, 0.025, "Not shown: %s and %s, which stay below 250th." % HIDDEN, transform=ax.transAxes, ha="left",
        va="bottom", fontsize=10, color=MUTED)
ax.set_xlabel(xlabel, fontsize=12, color=INK2)
ax.set_ylabel(f"Mean rank out of {N} (1 = best)", fontsize=12, color=INK2)
axes_style(ax); ax.grid(axis="x", visible=False)
titles(fig, 0.09, 0.925, title, sub)
fig.savefig(out, dpi=DPI)
print("ok", out, counts)
