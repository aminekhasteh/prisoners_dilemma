"""A memory-one strategy as four numbers: its chance of cooperating after each outcome of the last round
(CC, CD, DC, DD: Player 1's move first). Drawn in the visual language of the payoff matrix (payoffs.py):
circle = cooperate, square = defect, Player 1 filled, Player 2 in outline. A bar under a number shows the chance:
the blue share cooperates, the orange share defects. sse_math_recipe.py draws ZD strategies the same way.

Usage: python3 sse_math_p.py out.png [--dpi=200]"""
import sys, warnings, logging
from fractions import Fraction as Fr
warnings.filterwarnings("ignore"); logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

# palette and inks shared with payoffs.py and sse_moves_circular.py
INK, INK2, MUTED, LINE = "#1b1b1b", "#3d3c39", "#6b6a66", "#c9c8c3"
COOP, DEFECT = "#2a78d6", "#eb6834"
out = sys.argv[1]
DPI = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--dpi=")), 200))

plt.rcParams["font.family"] = ["DejaVu Sans"]
W, H = 100.0, 87.0                     # data units; 1 unit = 0.1 inch
fig = plt.figure(figsize=(W / 10, H / 10), facecolor="white")
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect("equal"); ax.axis("off")
PT = 10 / 72.0                         # one point in data units

OUTCOMES = ("CC", "CD", "DC", "DD")                # Player 1's move first
XC = {"CC": 40.5, "CD": 57.0, "DC": 73.5, "DD": 90.0}
XL, XR = 3.0, 97.5                     # left and right edge of the table
SUB = "₁₂₃₄"


def mark(x, y, move, r, player, lw=1.8):
    """Circle = cooperate, square = defect. Player 1 is filled, Player 2 is an ink outline."""
    if player == 2:
        r -= lw * PT / 2
        kw = dict(facecolor="white", edgecolor=INK, lw=lw, zorder=3)
    else:
        kw = dict(facecolor=COOP if move == "C" else DEFECT, edgecolor="none", zorder=3)
    if move == "C":
        ax.add_patch(Circle((x, y), r, **kw))
    else:
        s = 0.88 * r
        ax.add_patch(Rectangle((x - s, y - s), 2 * s, 2 * s, joinstyle="miter", **kw))


def chance(cx, y, p, size=22):
    """A chance of cooperating: the number, and a bar whose blue share cooperates and whose orange share defects."""
    p = Fr(p)
    txt = str(p.numerator) if p.denominator == 1 else "%d/%d" % (p.numerator, p.denominator)
    ax.text(cx, y, txt, ha="center", va="center", fontsize=size, fontweight="bold", color=INK)
    w, h, yb = 10.4, 1.15, y - 3.7
    ax.add_patch(Rectangle((cx - w / 2, yb - h / 2), w, h, facecolor=DEFECT, edgecolor="none", zorder=2))
    if p > 0:
        ax.add_patch(Rectangle((cx - w / 2, yb - h / 2), w * float(p), h, facecolor=COOP, edgecolor="none", zorder=3))


def label(y, head, sub):
    ax.text(XL, y + 1.4, head, ha="left", va="center", fontsize=13, fontweight="bold", color=INK)
    ax.text(XL, y - 1.7, sub, ha="left", va="center", fontsize=11.5, color=MUTED)


# title block, as on the payoff matrix
ax.text(W / 2, H - 2.8, "A strategy in four numbers", ha="center", va="top", fontsize=21, fontweight="bold", color=INK)
ax.text(W / 2, H - 7.5, "After each thing that can happen in a round, how likely is Player 1 to cooperate next?\n"
        "Circle = cooperate, square = defect. Filled = Player 1, outline = Player 2.",
        ha="center", va="top", fontsize=12.5, color=MUTED, linespacing=1.45)

# header: the four things that can have happened in the last round
Y0 = H - 21.5
label(Y0 - 0.9, "Last round", "Player 1, Player 2")
for o in OUTCOMES:
    mark(XC[o] - 3.0, Y0 + 0.4, o[0], 2.2, 1); mark(XC[o] + 3.0, Y0 + 0.4, o[1], 2.2, 2)
    ax.text(XC[o], Y0 - 4.3, o, ha="center", va="center", fontsize=11.5, fontweight="bold", color=MUTED)
ax.plot([XL, XR], [Y0 - 7.4, Y0 - 7.4], color=LINE, lw=1.0, zorder=1)

# the four numbers
Y1 = Y0 - 11.9
label(Y1, "Chance Player 1", "cooperates next")
for i, o in enumerate(OUTCOMES):
    ax.text(XC[o], Y1, "p" + SUB[i], ha="center", va="center", fontsize=14.5, fontweight="bold", color=INK)
ax.plot([XL, XR], [Y1 - 4.6, Y1 - 4.6], color=INK, lw=1.3, zorder=1)

# four strategies
y = Y1 - 10.6
for name, what, p in (("Tit for Tat", "copies Player 2's last move", (1, 0, 1, 0)),
                      ("Grudger", "never forgives a defection", (1, 0, 0, 0)),
                      ("Win-Stay-Lose-Shift", "repeats a move that paid off", (1, 0, 0, 1)),
                      ("RANDOM", "flips a coin every turn", (Fr(1, 2),) * 4)):
    label(y - 0.9, name, what)
    for o, v in zip(OUTCOMES, p):
        chance(XC[o], y + 0.6, v)
    y -= 10.3

# note, as under the payoff matrix
ax.text(W / 2, 4.2, "Bars show a chance: the blue share cooperates, the orange share defects.",
        ha="center", va="center", fontsize=12, color=MUTED)
fig.savefig(out, dpi=DPI, facecolor="white")
print("ok", out)
