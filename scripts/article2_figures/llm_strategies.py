"""The five LLM strategies of Pal et al. 2026 (Table S12) as five chances each: cooperating on the first move, and
cooperating after each outcome of the last round (CC, CD, DC, DD: the LLM's own move first). Same layout and marks as
Article 1's sse_math_p.py: a bar under each number, the blue share cooperates, the orange share defects.
The diamond next to each name is that model's colour in the rank charts.

With --new=data/new_llm_memory1.csv it draws the newer models instead (new_llm_strategies.png), grouped by maker,
each group opening with its Pal et al. models as a reference (those keep their diamond; new models get none, since
they have no colour in the rank charts yet). new_llm_memory1.csv comes from branch claude/project-thread-xnwceg
(scripts/article2_llm_field/): pooled over two prompt wordings, 50 calls each.

Usage: python3 llm_strategies.py data/llm_strategies.csv out.png [--new=data/new_llm_memory1.csv] [--dpi=200]"""
import sys
import pandas as pd
from style import setup, plt, INK, MUTED, LINE, COOP, DEFECT, LLMS, diamond, move
from matplotlib.patches import Rectangle

d = pd.read_csv(sys.argv[1]).set_index("Name")
out = sys.argv[2]
DPI = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--dpi=")), 200))
NEW = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--new=")), None)
COLS = ("p0", "CC", "CD", "DC", "DD")
old = lambda n, sub=None: (LLMS[n][0], sub or LLMS[n][1], LLMS[n][2], {c: float(d.loc[n, c]) for c in COLS})
if NEW:
    nw = pd.read_csv(NEW).set_index("model")
    CLASSIC = {"claude-opus-5-5": "Forgiver", "claude-sonnet-5-5": "close to Always Defect (default)", "claude-haiku-5-5": "GRIM",
               "gpt-6.1-sol": "between Tit for Tat and GRIM", "gpt-6.1-terra": "close to GRIM",
               "gpt-6-luna": "close to Always Defect"}
    new = lambda m: (nw.loc[m, "label"], CLASSIC[m], None, {c: float(nw.loc[m, c]) for c in COLS})
    ROWS = [("group", "Anthropic"), old("LLM: Claude Sonnet 4", "Forgiver (in Pal et al.)"),
            new("claude-opus-5-5"), new("claude-sonnet-5-5"),
            # the same model pushed to think (effort xhigh: it thought in 80% of calls), one wording, 50 calls
            # (claude/project-thread-xnwceg 92fb974); at default effort it almost never thinks
            ("Sonnet 5.5, thinking", "GRIM (effort xhigh, 50 calls)", None,
             dict(p0=1.00, CC=1.00, CD=0.00, DC=0.00, DD=0.08)),
            new("claude-haiku-5-5"),
            ("group", "OpenAI"), old("LLM: GPT-4o", "GRIM (in Pal et al.)"),
            old("LLM: GPT-5", "WSLS / Forgiver (in Pal et al.)"),
            new("gpt-6.1-sol"), new("gpt-6.1-terra"), new("gpt-6-luna")]
    TITLE = "Newer chatbots, different personalities"
    FOOT = ("Bars show a chance: the blue share cooperates, the orange share defects.\n"
            "New models: 100 calls per question, two wordings pooled. Older ones: Pal et al. 2026, Table S12.")
else:
    ROWS = [old(n) for n in ["LLM: Claude Sonnet 4", "LLM: Gemini 2.5 Pro", "LLM: GPT-4o", "LLM: GPT-5", "LLM: Llama 3.3 70B"]]
    TITLE = "Five chatbots, five strategies"
    FOOT = "Bars show a chance: the blue share cooperates, the orange share defects.   Data: Pal et al. 2026, Table S12."
NROW = sum(1 for r in ROWS if r[0] != "group"); NGRP = len(ROWS) - NROW

setup()
W, H = 112.0, 98.0 + 10.3 * (NROW - 5) + 4.5 * NGRP + (3.0 if NEW else 0)   # data units; 1 unit = 0.1 inch
fig = plt.figure(figsize=(W / 10, H / 10))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect("equal"); ax.axis("off")
PT = 10 / 72.0
XL, XR = 3.0, 109.0
XC = {"p0": 44.0, "CC": 61.0, "CD": 75.0, "DC": 89.0, "DD": 103.0}


def chance(cx, y, p, size=19):
    txt = "1" if p >= 0.995 else ("0" if p <= 0.005 else "%.2f" % p)
    ax.text(cx, y, txt, ha="center", va="center", fontsize=size, fontweight="bold", color=INK)
    w, h, yb = 10.4, 1.15, y - 3.6
    ax.add_patch(Rectangle((cx - w / 2, yb - h / 2), w, h, facecolor=DEFECT, edgecolor="none", zorder=2))
    if p > 0:
        ax.add_patch(Rectangle((cx - w / 2, yb - h / 2), w * p, h, facecolor=COOP, edgecolor="none", zorder=3))


def label(y, head, sub, x=XL):
    ax.text(x, y + 1.4, head, ha="left", va="center", fontsize=13, fontweight="bold", color=INK)
    ax.text(x, y - 1.7, sub, ha="left", va="center", fontsize=11.5, color=MUTED)


ax.text(W / 2, H - 2.8, TITLE, ha="center", va="top", fontsize=21, fontweight="bold", color=INK)
ax.text(W / 2, H - 7.5, "How likely each model is to cooperate on its first move, and after each thing that can happen in a round.\n"
        "Circle = cooperate, square = defect. Filled = the chatbot, outline = the other player.",
        ha="center", va="top", fontsize=12.5, color=MUTED, linespacing=1.45)

# header
Y0 = H - 21.5
label(Y0 - 0.9, "Last round", "chatbot, other player")
ax.text(XC["p0"], Y0 + 0.4, "Round 1", ha="center", va="center", fontsize=12.5, fontweight="bold", color=INK)
ax.text(XC["p0"], Y0 - 4.3, "first move", ha="center", va="center", fontsize=11.5, fontweight="bold", color=MUTED)
for o in ("CC", "CD", "DC", "DD"):
    move(ax, XC[o] - 3.0, Y0 + 0.4, o[0], 2.2, 1, PT); move(ax, XC[o] + 3.0, Y0 + 0.4, o[1], 2.2, 2, PT)
    ax.text(XC[o], Y0 - 4.3, o, ha="center", va="center", fontsize=11.5, fontweight="bold", color=MUTED)
ax.plot([XL, XR], [Y0 - 7.4, Y0 - 7.4], color=LINE, lw=1.0, zorder=1)
Y1 = Y0 - 11.9
label(Y1, "Chance the chatbot", "cooperates next")
ax.text(XC["p0"], Y1, "p₀", ha="center", va="center", fontsize=14.5, fontweight="bold", color=INK)
for i, o in enumerate(("CC", "CD", "DC", "DD")):
    ax.text(XC[o], Y1, "p" + "₁₂₃₄"[i], ha="center", va="center", fontsize=14.5, fontweight="bold", color=INK)
ax.plot([XL, XR], [Y1 - 4.6, Y1 - 4.6], color=INK, lw=1.3, zorder=1)
xm = (XC["p0"] + XC["CC"]) / 2
ax.plot([xm, xm], [9.0 + (3.0 if NEW else 0), Y0 + 3.5], color=LINE, lw=1.0, zorder=1)

y = Y1 - 10.6
for row in ROWS:
    if row[0] == "group":
        y += 2.0
        ax.text(XL, y, row[1].upper(), ha="left", va="center", fontsize=11, fontweight="bold", color=MUTED)
        ax.plot([XL + 14, xm - 2], [y, y], color=LINE, lw=1.0)
        y -= 6.5
        continue
    short, classic, col, vals = row
    if col:
        diamond(ax, XL + 1.3, y + 0.5, 1.3, col)
    label(y - 0.9, short, classic, x=XL + 4.0)
    for o in COLS:
        chance(XC[o], y + 0.6, vals[o])
    y -= 10.3

ax.text(W / 2, 4.0 + (1.6 if NEW else 0), FOOT,
        ha="center", va="center", fontsize=11.5, color=MUTED, linespacing=1.45)
fig.savefig(out, dpi=DPI)
print("ok", out)
