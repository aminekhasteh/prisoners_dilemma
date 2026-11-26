"""Article 2 cover: the chatbots' memory-1 strategies as five chance bars each (first move, then after CC, CD, DC, DD),
drawn large in the series' visual code. Same wide format as Article 1's cover (sse_moves_circular.py --landscape):
a key on the left, the picture on the right, no title (Substack puts the title under the image).
Without --new it shows Pal et al.'s five, each with its closest classic. With --new it shows all eleven chatbots of
the post, grouped by maker (Anthropic, OpenAI, then Google and Meta): the five keep their colours and the six newer
models are dark grey diamonds, as in the other figures.
Usage: python3 cover.py data/llm_strategies.csv out.png [--new=data/new_llm_memory1.csv] [--dpi=150]"""
import sys
import pandas as pd
from style import setup, plt, INK, INK2, MUTED, LINE, COOP, DEFECT, LLMS, diamond, move
from matplotlib.patches import Rectangle, FancyBboxPatch

d = pd.read_csv(sys.argv[1]).set_index("Name")
out = sys.argv[2]
DPI = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--dpi=")), 150))
NEW = next((a.split("=")[1] for a in sys.argv if a.startswith("--new=")), None)
ORDER = ["LLM: Claude Sonnet 4", "LLM: Gemini 2.5 Pro", "LLM: GPT-4o", "LLM: GPT-5", "LLM: Llama 3.3 70B"]
SHORT = {"LLM: Claude Sonnet 4": "Forgiver", "LLM: Gemini 2.5 Pro": "~ Win-Stay Lose-Shift", "LLM: GPT-4o": "GRIM",
         "LLM: GPT-5": "~ WSLS / Forgiver", "LLM: Llama 3.3 70B": "~ Generous Tit for Tat"}
NEWC = "#3d3c39"   # the newer models get no identity colour
OUTCOMES = ["p0", "CC", "CD", "DC", "DD"]
if NEW:   # all eleven, one group per maker, a model's predecessor first
    nw = pd.read_csv(NEW).set_index("label")
    old = lambda m: (LLMS["LLM: " + m][0], None, LLMS["LLM: " + m][2], d.loc["LLM: " + m, OUTCOMES])
    new = lambda m: (m, None, NEWC, nw.loc[m, OUTCOMES])
    GROUPS = [[old("Claude Sonnet 4"), new("Claude Opus 5.5"), new("Claude Sonnet 5.5"), new("Claude Haiku 5.5")],
              [old("GPT-4o"), old("GPT-5"), new("GPT-6.1 Sol"), new("GPT-6.1 Terra"), new("GPT-6 Luna")],
              [old("Gemini 2.5 Pro"), old("Llama 3.3 70B")]]
    COUNT, PITCH, GROUP_GAP, BH, NAME_PT, DIAMOND_R, Y_FIRST = "Eleven chatbots", 6.9, 3.4, 4.4, 21, 2.1, 91.5
else:
    GROUPS = [[(LLMS[n][0], SHORT[n], LLMS[n][2], d.loc[n, OUTCOMES]) for n in ORDER]]
    COUNT, PITCH, GROUP_GAP, BH, NAME_PT, DIAMOND_R, Y_FIRST = "Chatbots", 17.5, 0.0, 7.0, 22, 2.6, 87.0

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
ax.text(KX, 47, COUNT + " said how they'd play.\nThen they played 272 strategies.",
        ha="left", va="center", fontsize=18, color=MUTED, linespacing=1.5)

# the grid of bars on the right
XC = {"p0": 118, "CC": 145, "CD": 166, "DC": 187, "DD": 208}
BW = 16.5
Y0 = 104
ax.text(XC["p0"], Y0, "first\nmove", ha="center", va="center", fontsize=19, fontweight="bold", color=MUTED, linespacing=1.1)
for o in ("CC", "CD", "DC", "DD"):
    move(ax, XC[o] - 4.0, Y0, o[0], 3.0, 1, PT, lw=2.6); move(ax, XC[o] + 4.0, Y0, o[1], 3.0, 2, PT, lw=2.6)
ax.text((XC["CC"] + XC["DD"]) / 2, Y0 + 7.5, "after the last round", ha="center", va="center", fontsize=17, color=MUTED)
xm = (XC["p0"] + XC["CC"]) / 2
ax.plot([xm, xm], [12, Y0 + 5], color=LINE, lw=1.4)
y = Y_FIRST
for group in GROUPS:
    for short, classic, col, chance in group:
        diamond(ax, 70, y, DIAMOND_R, col)
        if classic:   # two lines: the name, then its closest classic
            ax.text(75, y + 1.6, short, ha="left", va="center", fontsize=NAME_PT, fontweight="bold", color=INK)
            ax.text(75, y - 2.9, classic, ha="left", va="center", fontsize=15, color=MUTED)
        else:
            ax.text(75, y, short, ha="left", va="center", fontsize=NAME_PT, fontweight="bold", color=INK)
        for o in XC:
            p = float(chance[o]); x0 = XC[o] - BW / 2
            ax.add_patch(FancyBboxPatch((x0, y - BH / 2), BW, BH, boxstyle="square,pad=0", facecolor=DEFECT, edgecolor="none"))
            if p > 0:
                ax.add_patch(Rectangle((x0, y - BH / 2), BW * p, BH, facecolor=COOP, edgecolor="none"))
        y -= PITCH
    y -= GROUP_GAP
fig.savefig(out, dpi=DPI)
print("ok", out)
