"""Where the five LLM strategies of Pal et al. land among all players (the final field: 307), 63-turn games, no noise,
20 tournaments. The other chatbot strategies in the field are small grey diamonds.
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
N = len(f)
field = f[f.llm == 0]
ax.scatter(field.mean_rank, field.mean_score, s=16, color=FIELD, lw=0, zorder=2)
others = f[(f.llm == 1) & ~f.Name.isin(list(LLMS))]
ax.scatter(others.mean_rank, others.mean_score, s=30, marker="D", color="#a9a8a3", lw=0, zorder=2)
# label positions in data units (rank, score), placed by hand in the empty space around the curve: Llama, Claude and
# Tit for Tat above it, so that no label or leader line touches the zoom box and its two connector lines. The third
# value is where the leader line meets the label (0.5, 0.5 = its centre; 0, 0.5 = the middle of its left edge).
POS = {"LLM: GPT-4o": (40, 2.50, (0.5, 0.5)), "LLM: Llama 3.3 70B": (110, 2.735, (0, 0.5)),
       "LLM: Claude Sonnet 4": (164, 2.682, (0, 0.5))}
PAIR = ("LLM: GPT-5", "LLM: Gemini 2.5 Pro")   # 149th and 150th: drawn apart in the zoom
for name, (short, classic, col) in LLMS.items():
    r = f[f.Name == name].iloc[0]
    ax.scatter([r.mean_rank], [r.mean_score], s=150, marker="D", color=col, edgecolor="white", lw=1.6, zorder=4)
    if name in PAIR: continue
    ax.annotate(f"{short}\n{nth(r.mean_rank)}", (r.mean_rank, r.mean_score), xytext=POS[name][:2], textcoords="data",
                ha="center", va="center", fontsize=10.5, color=INK, fontweight="bold", linespacing=1.15,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8, shrinkA=4, shrinkB=9, relpos=POS[name][2]))
t = f[f.Name == TFT].iloc[0]
ax.scatter([t.mean_rank], [t.mean_score], s=130, facecolor="none", edgecolor=INK, lw=1.3, zorder=3)
ax.annotate(f"Tit for Tat\n{nth(t.mean_rank)}", (t.mean_rank, t.mean_score), xytext=(90, 2.52), textcoords="data",
            ha="center", va="center", fontsize=10.5, color=INK2, linespacing=1.15,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8, shrinkA=4, shrinkB=9))
top = f.iloc[0]
ax.annotate(f"{top.Name}, 1st", (top.mean_rank, top.mean_score), xytext=(10, 4), textcoords="offset points",
            ha="left", va="center", fontsize=10.5, color=INK2)
# zoom on ranks 140 to 158, where GPT-5 and Gemini sit next to each other (and next to Win-Stay Lose-Shift)
pair = f[f.Name.isin(PAIR)]
X0, X1 = pair.mean_rank.min() - 8.5, pair.mean_rank.max() + 5.5
Y0, Y1 = pair.mean_score.min() - 0.03, pair.mean_score.max() + 0.03
ax.set_xlim(-4, N + 4); ax.set_ylim(1.73, 2.875)
(fx0, fy0), (fx1, fy1) = fig.transFigure.inverted().transform(ax.transData.transform([(22, 1.80), (127, 2.32)]))
ins = fig.add_axes([fx0, fy0, fx1 - fx0, fy1 - fy0])   # a sibling axes, so the main grid stays behind it
z = f[(f.mean_rank >= X0) & (f.mean_rank <= X1) & (f.mean_score >= Y0) & (f.mean_score <= Y1)]
ins.scatter(z[z.llm == 0].mean_rank, z[z.llm == 0].mean_score, s=40, color=FIELD, lw=0, zorder=2)
for name, xy, ha in ((PAIR[0], (-34, 16), "right"), (PAIR[1], (-34, -20), "right")):
    short, _, col = LLMS[name]; r = f[f.Name == name].iloc[0]
    ins.scatter([r.mean_rank], [r.mean_score], s=150, marker="D", color=col, edgecolor="white", lw=1.6, zorder=4)
    ins.annotate(f"{short}\n{nth(r.mean_rank)}", (r.mean_rank, r.mean_score), xytext=xy, textcoords="offset points", ha=ha,
                 va="center", fontsize=10.5, color=INK, fontweight="bold", linespacing=1.15,
                 arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8, shrinkA=3, shrinkB=7))
w = f[f.Name == "Win-Stay Lose-Shift"].iloc[0]
ins.annotate(f"Win-Stay Lose-Shift, {nth(w.mean_rank)}", (w.mean_rank, w.mean_score), xytext=(12, 16), textcoords="offset points",
             ha="left", va="center", fontsize=10, color=INK2,
             arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8, shrinkA=3, shrinkB=5))
ins.set_xlim(X0, X1); ins.set_ylim(Y0, Y1)
ins.locator_params(nbins=4)
axes_style(ins); ins.grid(False); ins.tick_params(labelsize=9.5)
for s_ in ins.spines.values(): s_.set_visible(True); s_.set_color(MUTED)
ax.indicate_inset_zoom(ins, edgecolor=MUTED, alpha=0.8, lw=0.8)
ax.set_xticks([1, 50, 100, 150, 200, 250, N])
ax.set_xlabel(f"Mean rank out of {N} (1 = best)", fontsize=12, color=INK2)
ax.set_ylabel("Mean score per turn", fontsize=12, color=INK2)
axes_style(ax)
five = f[f.Name.isin(list(LLMS))].sort_values("mean_rank")
assert five.Name.iloc[0] == "LLM: GPT-4o", "title no longer true: GPT-4o is not the best of Pal et al.'s five"
titles(fig, 0.09, 0.925, "In short games, the grudge-holder is the best of Pal et al.'s five",
       f"63-turn games, no noise: each point is one of {N} players, averaged over 20 tournaments. Coloured diamonds:\n"
       f"Pal et al.'s five. Grey dots: Knight et al.'s 272 strategies. Grey diamonds: the other {N - 277} chatbot strategies.")
fig.savefig(out, dpi=DPI)
print("ok", out)
