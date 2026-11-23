"""Article 2 cover: the five LLM strategies as five chance bars each (first move, then after CC, CD, DC, DD), drawn
large in the series' visual code. Same wide format as Article 1's cover (sse_moves_circular.py --landscape):
a key on the left, the picture on the right, no title (Substack puts the title under the image).
Usage: python3 cover.py data/llm_strategies.csv out.png [--dpi=150]"""
import sys
import pandas as pd
from style import setup, plt, INK, INK2, MUTED, LINE, COOP, DEFECT, LLMS, diamond, move
from matplotlib.patches import Rectangle, FancyBboxPatch

d = pd.read_csv(sys.argv[1]).set_index("Name")
out = sys.argv[2]
DPI = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--dpi=")), 150))
ORDER = ["LLM: Claude Sonnet 4", "LLM: Gemini 2.5 Pro", "LLM: GPT-4o", "LLM: GPT-5", "LLM: Llama 3.3 70B"]

setup()
W, H = 220.0, 124.0
fig = plt.figure(figsize=(W / 10, H / 10))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect("equal"); ax.axis("off")
PT = 10 / 72.0

# key on the left, as on Article 1's cover
KX = 9
move(ax, KX + 2.4, 72, "C", 2.4, 1, PT); move(ax, KX + 8.6, 72, "D", 2.4, 1, PT)
ax.text(KX + 15, 72, "cooperate, defect", ha="left", va="center", fontsize=21, color=INK2)
bw = 11
ax.add_patch(Rectangle((KX, 60.2), bw, 3.2, facecolor=DEFECT, edgecolor="none"))
ax.add_patch(Rectangle((KX, 60.2), bw * 0.7, 3.2, facecolor=COOP, edgecolor="none"))
ax.text(KX + 15, 61.8, "chance of cooperating", ha="left", va="center", fontsize=21, color=INK2)
ax.text(KX, 47, "Five chatbots said how they'd play.\nThen they played 272 strategies.",
        ha="left", va="center", fontsize=18, color=MUTED, linespacing=1.5)

# the grid of bars on the right
XC = {"p0": 118, "CC": 145, "CD": 166, "DC": 187, "DD": 208}
BW, BH = 16.5, 7.0
SHORT = {"LLM: Claude Sonnet 4": "Forgiver", "LLM: Gemini 2.5 Pro": "~ Win-Stay Lose-Shift", "LLM: GPT-4o": "GRIM",
         "LLM: GPT-5": "~ WSLS / Forgiver", "LLM: Llama 3.3 70B": "~ Generous Tit for Tat"}
Y0 = 104
ax.text(XC["p0"], Y0, "first\nmove", ha="center", va="center", fontsize=19, fontweight="bold", color=MUTED, linespacing=1.1)
for o in ("CC", "CD", "DC", "DD"):
    move(ax, XC[o] - 4.0, Y0, o[0], 3.0, 1, PT, lw=2.6); move(ax, XC[o] + 4.0, Y0, o[1], 3.0, 2, PT, lw=2.6)
ax.text((XC["CC"] + XC["DD"]) / 2, Y0 + 7.5, "after the last round", ha="center", va="center", fontsize=17, color=MUTED)
xm = (XC["p0"] + XC["CC"]) / 2
ax.plot([xm, xm], [12, Y0 + 5], color=LINE, lw=1.4)
y = Y0 - 17
for name in ORDER:
    short, classic, col = LLMS[name]
    diamond(ax, 70, y, 2.6, col)
    ax.text(75, y + 1.6, short, ha="left", va="center", fontsize=22, fontweight="bold", color=INK)
    ax.text(75, y - 2.9, SHORT[name], ha="left", va="center", fontsize=15, color=MUTED)
    for o in XC:
        p = float(d.loc[name, o]); x0 = XC[o] - BW / 2
        ax.add_patch(FancyBboxPatch((x0, y - BH / 2), BW, BH, boxstyle="square,pad=0", facecolor=DEFECT, edgecolor="none"))
        if p > 0:
            ax.add_patch(Rectangle((x0, y - BH / 2), BW * p, BH, facecolor=COOP, edgecolor="none"))
    y -= 17.5
fig.savefig(out, dpi=DPI)
print("ok", out)
