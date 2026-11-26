"""Where the five LLM strategies land among all 277 players: 63-turn games, no noise, 20 tournaments.
One point per player: its mean rank (x, 1 = best) and its mean score per turn (y, the median over repetitions,
which is what the ranking uses). The field is grey; the LLMs are diamonds in their own colours, labelled in ink;
Tit for Tat (k92r) gets an ink ring.
Usage: python3 llm_rank_63.py data/field_63.csv out.png [--dpi=200]"""
import sys
import pandas as pd
from style import setup, plt, INK, INK2, MUTED, FIELD, LLMS, TFT, axes_style, titles

f = pd.read_csv(sys.argv[1]); out = sys.argv[2]
DPI = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--dpi=")), 200))


def nth(v):
    """Rank as an ordinal (53rd, 64th), halves rounded up as in the article's tables."""
    n = int(v + 0.5)
    return "%d%s" % (n, "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))


setup()
fig, ax = plt.subplots(figsize=(10, 6.6))
fig.subplots_adjust(left=0.09, right=0.97, bottom=0.1, top=0.83)
field = f[f.llm == 0]
ax.scatter(field.mean_rank, field.mean_score, s=16, color=FIELD, lw=0, zorder=2)
# label positions in data units (rank, score), placed by hand in the empty space around the curve: Llama, Claude and
# Tit for Tat above it, so that no label or leader line touches the zoom box and its two connector lines
POS = {"LLM: GPT-4o": (40, 2.50), "LLM: Llama 3.3 70B": (110, 2.735), "LLM: Claude Sonnet 4": (158, 2.675)}
PAIR = ("LLM: GPT-5", "LLM: Gemini 2.5 Pro")   # 149th and 150th: drawn apart in the zoom
for name, (short, classic, col) in LLMS.items():
    r = f[f.Name == name].iloc[0]
    ax.scatter([r.mean_rank], [r.mean_score], s=150, marker="D", color=col, edgecolor="white", lw=1.6, zorder=4)
    if name in PAIR: continue
    ax.annotate(f"{short}\n{nth(r.mean_rank)}", (r.mean_rank, r.mean_score), xytext=POS[name], textcoords="data",
                ha="center", va="center", fontsize=10.5, color=INK, fontweight="bold", linespacing=1.15,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8, shrinkA=14, shrinkB=7))
t = f[f.Name == TFT].iloc[0]
ax.scatter([t.mean_rank], [t.mean_score], s=130, facecolor="none", edgecolor=INK, lw=1.3, zorder=3)
ax.annotate(f"Tit for Tat\n{nth(t.mean_rank)}", (t.mean_rank, t.mean_score), xytext=(74, 2.805), textcoords="data",
            ha="center", va="center", fontsize=10.5, color=INK2, linespacing=1.15,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8, shrinkA=14, shrinkB=7))
top = f.iloc[0]
ax.annotate(f"{top.Name}, 1st", (top.mean_rank, top.mean_score), xytext=(10, 4), textcoords="offset points",
            ha="left", va="center", fontsize=10.5, color=INK2)
# zoom on ranks 140 to 158, where GPT-5 and Gemini sit next to each other (and next to Win-Stay Lose-Shift)
X0, X1, Y0, Y1 = 141.5, 155.5, 2.530, 2.590
ax.set_xlim(-4, 281); ax.set_ylim(1.73, 2.875)
(fx0, fy0), (fx1, fy1) = fig.transFigure.inverted().transform(ax.transData.transform([(22, 1.80), (127, 2.32)]))
ins = fig.add_axes([fx0, fy0, fx1 - fx0, fy1 - fy0])   # a sibling axes, so the main grid stays behind it
z = f[(f.mean_rank >= X0) & (f.mean_rank <= X1)]
ins.scatter(z[z.llm == 0].mean_rank, z[z.llm == 0].mean_score, s=40, color=FIELD, lw=0, zorder=2)
for name, xy, ha in ((PAIR[0], (147.6, 2.566), "right"), (PAIR[1], (148.8, 2.541), "right")):
    short, _, col = LLMS[name]; r = f[f.Name == name].iloc[0]
    ins.scatter([r.mean_rank], [r.mean_score], s=150, marker="D", color=col, edgecolor="white", lw=1.6, zorder=4)
    ins.annotate(f"{short}\n{nth(r.mean_rank)}", (r.mean_rank, r.mean_score), xytext=xy, textcoords="data", ha=ha,
                 va="center", fontsize=10.5, color=INK, fontweight="bold", linespacing=1.15,
                 arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8, shrinkA=3, shrinkB=7))
w = f[f.Name == "Win-Stay Lose-Shift"].iloc[0]
ins.annotate(f"Win-Stay Lose-Shift, {nth(w.mean_rank)}", (w.mean_rank, w.mean_score), xytext=(147.0, 2.587), textcoords="data",
             ha="left", va="center", fontsize=10, color=INK2,
             arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8, shrinkA=3, shrinkB=5))
ins.set_xlim(X0, X1); ins.set_ylim(Y0, Y1)
ins.set_xticks([142, 146, 150, 154]); ins.set_yticks([2.54, 2.56, 2.58])
axes_style(ins); ins.grid(False); ins.tick_params(labelsize=9.5)
for s_ in ins.spines.values(): s_.set_visible(True); s_.set_color(MUTED)
ax.indicate_inset_zoom(ins, edgecolor=MUTED, alpha=0.8, lw=0.8)
ax.set_xticks([1, 50, 100, 150, 200, 250, 277])
ax.set_xlabel("Mean rank out of 277 (1 = best)", fontsize=12, color=INK2)
ax.set_ylabel("Mean score per turn", fontsize=12, color=INK2)
axes_style(ax)
titles(fig, 0.09, 0.925, "In short games, the grudge-holder is the best chatbot",
       "63-turn games, no noise: each point is one of 277 players, averaged over 20 tournaments.\n"
       "Grey = Knight et al.'s 272 strategies, diamonds = the five chatbot strategies.")
fig.savefig(out, dpi=DPI)
print("ok", out)
