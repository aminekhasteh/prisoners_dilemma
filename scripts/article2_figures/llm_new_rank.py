"""The newer models' rank among all players, next to the Pal et al. models and Tit for Tat (dashed line).
One row per model, grouped by maker; a dumbbell joins its memory-1 rank (filled diamond) and memory-2 rank (hollow
diamond). Where the two ranks are less than five places apart, the filled diamond is drawn small inside the hollow
one. Pal et al.'s models keep their colours from the other charts, our 2026 reruns of Gemini and Llama use the same
colour as the original, and the six new models are dark grey (they get no identity colour, to keep the palette at
five). One panel per setting found in data/new_ranks.csv, in this order: 63 turns; mean over the five lengths;
1% noise; 5% noise. Three or four panels are laid out two by two, so the text stays readable at article width.
Usage: python3 llm_new_rank.py data/new_ranks.csv out.png [--dpi=200]"""
import sys
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patheffects import withStroke
from style import setup, plt, INK, INK2, MUTED, LINE, LLMS, TFT, axes_style, titles

r = pd.read_csv(sys.argv[1]); out = sys.argv[2]
DPI = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--dpi=")), 200))
SETTINGS = [(k, t) for k, t in (("s63", "63 turns, no noise"), ("slen", "All lengths, no noise"),
                                ("n1", "63 turns, 1% noise"), ("n5", "63 turns, 5% noise"))
            if (r.setting == k).any()]
NEWC = "#3d3c39"
COL = {LLMS["LLM: " + m][0]: LLMS["LLM: " + m][2] for m in
       ("Claude Sonnet 4", "GPT-4o", "GPT-5", "Gemini 2.5 Pro", "Llama 3.3 70B")}
# (group, model as in the data, label, sub-label, colour)
ROWS = [("ANTHROPIC", "Claude Sonnet 4", "Claude Sonnet 4", "Pal et al.", COL["Claude Sonnet 4"]),
        ("ANTHROPIC", "Claude Opus 5.5", "Claude Opus 5.5", "new", NEWC),
        ("ANTHROPIC", "Claude Sonnet 5.5", "Claude Sonnet 5.5", "new", NEWC),
        ("ANTHROPIC", "Claude Haiku 5.5", "Claude Haiku 5.5", "new", NEWC),
        ("OPENAI", "GPT-4o", "GPT-4o", "Pal et al.", COL["GPT-4o"]),
        ("OPENAI", "GPT-5", "GPT-5", "Pal et al.", COL["GPT-5"]),
        ("OPENAI", "GPT-6.1 Sol", "GPT-6.1 Sol", "new", NEWC),
        ("OPENAI", "GPT-6.1 Terra", "GPT-6.1 Terra", "new", NEWC),
        ("OPENAI", "GPT-6 Luna", "GPT-6 Luna", "new", NEWC),
        ("GOOGLE AND META", "Gemini 2.5 Pro", "Gemini 2.5 Pro", "Pal et al.", COL["Gemini 2.5 Pro"]),
        ("GOOGLE AND META", "Gemini 2.5 Pro (2026 rerun)", "Gemini 2.5 Pro", "our rerun", COL["Gemini 2.5 Pro"]),
        ("GOOGLE AND META", "Llama 3.3 70B", "Llama 3.3 70B", "Pal et al.", COL["Llama 3.3 70B"]),
        ("GOOGLE AND META", "Llama 3.3 70B (2026 rerun)", "Llama 3.3 70B", "our rerun", COL["Llama 3.3 70B"])]
rk = lambda v: "%d" % int(v + 0.5)
HALO = [withStroke(linewidth=2.6, foreground="white")]   # keeps a number readable where the dashed line runs behind it
TIE = 5   # ranks: closer than this, the hollow diamond covers the filled one, so a small filled one is drawn inside it

# y positions with a gap before each group
ys, groups, y = [], [], 0.0
for i, row in enumerate(ROWS):
    if i == 0 or row[0] != ROWS[i - 1][0]:
        groups.append((y, row[0])); y += 0.9
    ys.append(y); y += 1.0
N = int(r.players.max())

setup()
n = len(SETTINGS)
nr = 1 if n <= 2 else 2; nc = -(-n // nr)
# the layout is set in inches, so the header and the row height stay the same whatever the number of panels
W, LEFT, RIGHT, WGAP = 10.0, 2.45, 0.3, 0.3
TOP, HGAP, BOTTOM = 1.85, 0.55, 0.75
PH = (0.37 if nr == 1 else 0.29) * (y + 1.1)            # one panel: the y axis runs from -1.5 to y - 0.4
H = TOP + nr * PH + (nr - 1) * HGAP + BOTTOM
PW = (W - LEFT - RIGHT - (nc - 1) * WGAP) / nc
fig, axes = plt.subplots(nr, nc, figsize=(W, H), sharey=True, sharex=True, squeeze=False)
fig.subplots_adjust(left=LEFT / W, right=1 - RIGHT / W, bottom=BOTTOM / H, top=1 - TOP / H,
                    wspace=WGAP / PW, hspace=HGAP / PH)
for ax in axes.ravel()[n:]: ax.set_visible(False)
for i, (ax, (key, head)) in enumerate(zip(axes.ravel(), SETTINGS)):
    s = r[r.setting == key].set_index(["model", "memory"]).mean_rank
    t = s.get((TFT, 1))
    ax.axvline(t, color=MUTED, lw=1.3, ls=(0, (4, 3)), zorder=1)
    ax.text(t, -0.9, "Tit for Tat " + rk(t), ha="center", va="center", fontsize=9.5, color=INK2,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5), zorder=3)
    for yy, (_, m, _, _, col) in zip(ys, ROWS):
        a, b = s.get((m, 1)), s.get((m, 2))
        pts = [v for v in (a, b) if v is not None and v == v]
        if len(pts) == 2:
            ax.plot([a, b], [yy, yy], color=LINE, lw=3, zorder=2, solid_capstyle="round")
        if a is not None and a == a:
            ax.scatter([a], [yy], s=95, marker="D", color=col, edgecolor="white", lw=1.3, zorder=4)
        if b is not None and b == b:
            ax.scatter([b], [yy], s=85, marker="D", facecolor="white", edgecolor=col, lw=2.0, zorder=5)
        if len(pts) == 2 and abs(a - b) < TIE:
            ax.scatter([a], [yy], s=20, marker="D", color=col, lw=0, zorder=6)
        # numbers on the outside of the dumbbell, a fixed distance from the diamonds' tips
        lo, hi = min(pts), max(pts)
        for v, dx, ha in ((lo, -11, "right"), (hi, 11, "left")):
            if len(pts) == 1 and ha == "right": continue
            m2 = b is not None and v == b and (a is None or a != b)
            ax.annotate(rk(v), (v, yy), xytext=(dx, 0), textcoords="offset points", ha=ha, va="center", fontsize=9,
                        color=INK if m2 else INK2, fontweight="bold" if m2 else "normal", path_effects=HALO, zorder=6)
    ax.set_xlim(-38, N + 36); ax.set_xticks([1, 100, 200, N])
    ax.set_ylim(y - 0.4, -1.5)
    ax.set_title(head, fontsize=12, color=INK, fontweight="bold", loc="left", pad=8)
    ax.set_title("%d tournaments" % r[r.setting == key].tournaments.max(), fontsize=10, color=MUTED, loc="right", pad=8)
    axes_style(ax); ax.grid(axis="y", visible=False); ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    if i + nc >= n: ax.tick_params(axis="x", labelbottom=True)      # no panel below this one
axes[0, 0].set_yticks(ys, ["%s  ·  %s" % (lab, sub) for _, _, lab, sub, _ in ROWS])
for ax in axes[:, 0]:                                               # first column: model names and group headers
    ax.tick_params(axis="y", labelleft=True, labelsize=10.5)
    for lab, (_, _, _, sub, _) in zip(ax.get_yticklabels(), ROWS):
        lab.set_color(INK if sub == "new" else INK2); lab.set_fontweight("bold" if sub == "new" else "normal")
    for gy, g in groups:
        ax.text(-0.02, gy, g, transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=10,
                fontweight="bold", color=MUTED)
fig.supxlabel(f"Mean rank out of {N} (1 = best)", fontsize=12, color=INK2, y=0.12 / H,
              x=(LEFT + (W - RIGHT)) / 2 / W)
key = [Line2D([], [], ls="", marker="D", ms=9, color=MUTED, mec="white", label="memory-1: looks at the last round"),
       Line2D([], [], ls="", marker="D", ms=9, mfc="white", mec=MUTED, mew=2, label="memory-2: last two rounds (bold number)")]
fig.legend(handles=key, loc="upper left", bbox_to_anchor=(0.012, 1 - 1.03 / H), ncol=2, frameon=False, fontsize=10.5,
           handletextpad=0.3, columnspacing=1.6)
TITLE = ("Memory-2 lifts Opus 5.5 and both GPT-6.1 models in every setting" if n > 1
         else "The newer chatbots: some climb, some fall to the bottom")
titles(fig, 0.02, 1 - 0.5 / H, TITLE,
       f"All memory-1 and memory-2 strategies in one {N}-player field: Knight et al.'s 272 plus {N - 272} chatbot strategies.\n"
       "Bold names = new models. Pal et al. = the paper's numbers. Our rerun = the same model asked again in 2026.",
       gap=0.08 / H)
fig.savefig(out, dpi=DPI)
print("ok", out, [k for k, _ in SETTINGS])
