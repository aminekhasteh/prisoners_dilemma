"""How ZD-like are the chatbot strategies, are they nice, and where do they finish? One row per player, sorted by mean
rank in the 307-player field (63-turn games, no noise); a few classic strategies from Knight et al.'s field are
slotted in at their own rank for reference.

x = SSE (Article 1: squared distance of the strategy's CC/CD/DC/DD -> C rates, measured in play, from the plane of
zero-determinant strategies; 0 = exactly ZD). Colour = Article 1's niceness (nice = never the first to defect):
blue nice, orange nasty, orange ringed in blue = nasty but only just (defects first in under 5% of games against
Always Cooperate). Chatbots are diamonds: filled = memory-1, hollow = memory-2, hollow with a dot = memory-3.
Classics are circles with italic names.
Usage: python3 llm_sse.py data/sse_llm.csv data/sse_field.csv out.png [--dpi=200]"""
import sys
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from style import setup, plt, INK, INK2, MUTED, LINE, GRID, COOP, DEFECT, titles

llm = pd.read_csv(sys.argv[1]); field = pd.read_csv(sys.argv[2]); out = sys.argv[3]
DPI = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--dpi=")), 200))
N, XMAX = 307, 1.6

CLASSICS = [("EvolvedLookerUp2_2_2", "Evolved Lookup table (winner)"), ("DBS", "DBS"), ("k92r", "Tit for Tat"),
            ("GTFT", "Generous Tit for Tat"), ("Forgiver", "Forgiver (library version)"),
            ("Two Tits For Tat", "Two Tits for Tat"), ("Win-Stay Lose-Shift", "Win-Stay Lose-Shift"),
            ("Cooperator", "Always Cooperate"), ("Suspicious Tit For Tat", "Suspicious Tit for Tat"),
            ("ZD-Extort-2:", "ZD-Extort-2"), ("Alternator", "Alternator"), ("krandomc", "RANDOM (1980 entry)"),
            ("Defector", "Always Defect")]
SHORT = {"Claude Sonnet 5.5 (effort xhigh)": "Claude Sonnet 5.5, thinking", "Gemini 2.5 Pro (2026 rerun)": "Gemini 2.5 Pro, our rerun",
         "Llama 3.3 70B (2026 rerun)": "Llama 3.3 70B, our rerun"}

rows = []
for r in llm.itertuples():
    model = r.Name.split(": ", 1)[1]
    kind = "nice" if r.nice_rule == "nice" else ("nearly" if r.p_never_first_63 >= 0.95 else "nasty")
    rows.append(dict(label=SHORT.get(model, model), mem=int(r.memory), rank=r.mean_rank, sse=r.sse_played, kind=kind,
                     classic=False))
for pre, lab in CLASSICS:
    r = field[field.Name.str.startswith(pre)].iloc[0]
    rows.append(dict(label=lab, mem=0, rank=r.mean_rank, sse=r.sse, kind=r.group, classic=True))
rows = sorted(rows, key=lambda d: d["rank"])
rk = lambda v: "%d" % int(v + 0.5)

setup()
H = 0.215 * len(rows) + 2.65
fig = plt.figure(figsize=(10.5, H))
top, bot = 1 - 2.1 / H, 0.35 / H
ax = fig.add_axes([0.43, bot, 0.54, top - bot])
n = len(rows)
ys = np.arange(n)
for y, d in zip(ys, rows):
    col = COOP if d["kind"] == "nice" else DEFECT
    x = min(d["sse"], XMAX)
    ax.plot([0, XMAX], [y, y], color=GRID, lw=0.6, zorder=0)
    if d["classic"]:
        ax.scatter([x], [y], s=55, facecolor="white", edgecolor=col, lw=1.7, zorder=3)
    elif d["mem"] == 1:
        ax.scatter([x], [y], s=95, marker="D", facecolor=col, edgecolor=COOP if d["kind"] == "nearly" else "white",
                   lw=2.0 if d["kind"] == "nearly" else 1.0, zorder=4)
    else:
        ax.scatter([x], [y], s=85, marker="D", facecolor="white", edgecolor=col, lw=2.0, zorder=4)
        if d["kind"] == "nearly":
            ax.scatter([x], [y], s=30, marker="D", facecolor="white", edgecolor=COOP, lw=1.4, zorder=5)
        if d["mem"] == 3:
            ax.scatter([x], [y], s=10, color=col, lw=0, zorder=6)
    # name and rank in the left margin, in axes-fraction x so they line up
    tag = "" if d["classic"] else "   m%d" % d["mem"]
    ax.text(-0.04, y, d["label"], transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=9.6,
            color=INK2 if d["classic"] else INK, style="italic" if d["classic"] else "normal",
            fontweight="normal" if d["classic"] else "bold")
    if tag:
        ax.text(-0.025, y, "m%d" % d["mem"], transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=8.5,
                color=MUTED)
    ax.text(-0.56, y, rk(d["rank"]), transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=9.6,
            color=INK2 if d["classic"] else INK)
ax.text(-0.56, -1.6, "rank", transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=9.5, color=MUTED,
        fontweight="bold")
ax.text(-0.04, -1.6, "strategy", transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=9.5, color=MUTED,
        fontweight="bold")
ax.set_ylim(n - 0.4, -2.3); ax.set_yticks([])
ax.set_xlim(-0.05, XMAX + 0.05); ax.set_xticks([0, 0.4, 0.8, 1.2, 1.6])
ax.xaxis.tick_top(); ax.xaxis.set_label_position("top")
ax.tick_params(axis="x", colors=MUTED, labelsize=10, length=0)
for s in ax.spines.values(): s.set_visible(False)
for xv in (0, 0.4, 0.8, 1.2, 1.6):
    ax.axvline(xv, color=GRID, lw=0.8, zorder=0)
ax.set_xlabel("SSE: distance from a zero-determinant strategy (0 = exactly ZD)", fontsize=10.5, color=INK2, labelpad=6)

key = [Line2D([], [], ls="", marker="D", ms=8, color=COOP, mec="white", label="nice (never defects first)"),
       Line2D([], [], ls="", marker="D", ms=8, color=DEFECT, mec="white", label="nasty"),
       Line2D([], [], ls="", marker="D", ms=8, color=DEFECT, mec=COOP, mew=2, label="nasty, but only just"),
       Line2D([], [], ls="", marker="D", ms=8, color=MUTED, mec="white", label="m1 = memory-1"),
       Line2D([], [], ls="", marker="D", ms=8, mfc="white", mec=MUTED, mew=2, label="m2 = memory-2 (m3: with a dot)"),
       Line2D([], [], ls="", marker="o", ms=8, mfc="white", mec=MUTED, mew=1.6, label="classic strategy, for reference")]
fig.legend(handles=key, loc="upper left", bbox_to_anchor=(0.03, 1 - 0.95 / H), ncol=3, frameon=False, fontsize=9.8,
           handletextpad=0.3, columnspacing=1.3)
n_nice = sum(d["kind"] == "nice" for d in rows if not d["classic"])
titles(fig, 0.03, 1 - 0.42 / H, f"{n_nice} of {len(llm)} chatbot strategies are nice, and SSE says little about who wins",
       f"Every chatbot strategy in the {N}-player field, best first (63-turn games, no noise),\nwith classic strategies from Knight et al.'s field slotted in at their own rank for reference.",
       gap=0.06 / H)
fig.savefig(out, dpi=DPI)
print("ok", out, n, "rows")
