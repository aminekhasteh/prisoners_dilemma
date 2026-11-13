"""How a zero-determinant (ZD) strategy picks its next move, drawn as a column sum in the visual language of the
payoff matrix (payoffs.py): circle = cooperate, square = defect, Player 1 filled, Player 2 in outline.
Each column is one outcome of the last round (CC, CD, DC, DD: Player 1's move first). Reading down a column gives
one entry of  q = (1, 1, 0, 0) + alpha (2, -1, 4, 0) + beta (2, 4, -1, 0):  start from Player 1's own last move, then
add alpha for every point Player 1 just scored above P = 1 and beta for every point Player 2 scored above 1.
Numbers on a tile are points; numbers with a bar under them are chances of cooperating (the blue share of the bar).
The recipe is the definition of a ZD strategy in Knight, Harper, Glynatsi & Gillard (2019, arXiv 1904.00973), eqs. 6-9.

Usage: python3 sse_math_recipe.py out.png [--dpi=200]"""
import sys, warnings, logging
from fractions import Fraction as Fr
warnings.filterwarnings("ignore"); logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch

# palette and inks shared with payoffs.py and sse_moves_circular.py
INK, INK2, MUTED, LINE = "#1b1b1b", "#3d3c39", "#6b6a66", "#c9c8c3"
COOP, DEFECT, TILE = "#2a78d6", "#eb6834", "#efeeea"
out = sys.argv[1]
DPI = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--dpi=")), 200))

plt.rcParams["font.family"] = ["DejaVu Sans"]
W, H = 100.0, 112.0                    # data units; 1 unit = 0.1 inch
fig = plt.figure(figsize=(W / 10, H / 10), facecolor="white")
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect("equal"); ax.axis("off")
PT = 10 / 72.0                         # one point in data units

OUTCOMES = ("CC", "CD", "DC", "DD")                # Player 1's move first
PAY1 = {"CC": 3, "CD": 0, "DC": 5, "DD": 1}        # Player 1's points
PAY2 = {"CC": 3, "CD": 5, "DC": 0, "DD": 1}        # Player 2's points
XC = {"CC": 40.5, "CD": 57.0, "DC": 73.5, "DD": 90.0}
XL, XR = 3.0, 97.5                     # left and right edge of the table
XOP = 30.5                             # the operators (+ alpha x, + beta x, =) are right-aligned here
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


def chance(cx, y, p, size=24):
    """A chance of cooperating: the number, and a bar whose blue share cooperates and whose orange share defects."""
    p = Fr(p)
    txt = str(p.numerator) if p.denominator == 1 else "%d/%d" % (p.numerator, p.denominator)
    ax.text(cx, y, txt, ha="center", va="center", fontsize=size, fontweight="bold", color=INK)
    w, h, yb = 10.4, 1.15, y - 3.7
    ax.add_patch(Rectangle((cx - w / 2, yb - h / 2), w, h, facecolor=DEFECT, edgecolor="none", zorder=2))
    if p > 0:
        ax.add_patch(Rectangle((cx - w / 2, yb - h / 2), w * float(p), h, facecolor=COOP, edgecolor="none", zorder=3))


def tile(cx, y, raw):
    """Points scored last round, minus P = 1, on a scoreboard tile; the subtraction is spelled out on the tile."""
    w, h, pts = 10.4, 7.6, raw - 1
    ax.add_patch(FancyBboxPatch((cx - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=1.2",
                                facecolor=TILE, edgecolor="none", zorder=2))
    s = ("+%d" % pts) if pts > 0 else ("−%d" % -pts if pts < 0 else "0")
    ax.text(cx, y + 0.9, s, ha="center", va="center", fontsize=20, fontweight="bold", color=INK, zorder=3)
    ax.text(cx, y - 2.3, "%d − 1" % raw, ha="center", va="center", fontsize=10.5, color=MUTED, zorder=3)


def label(y, head, sub, op=None):
    ax.text(XL, y + 1.4, head, ha="left", va="center", fontsize=13, fontweight="bold", color=INK)
    ax.text(XL, y - 1.7, sub, ha="left", va="center", fontsize=11.5, color=MUTED)
    if op:
        ax.text(XOP, y, op, ha="right", va="center", fontsize=19, fontweight="bold", color=INK)


# title block, as on the payoff matrix
ax.text(W / 2, H - 2.8, "How a ZD strategy picks its next move", ha="center", va="top", fontsize=21, fontweight="bold", color=INK)
ax.text(W / 2, H - 7.5, "It starts from its own last move, then adjusts for the points each player just scored.\n"
        "Circle = cooperate, square = defect. Filled = Player 1 (the ZD player), outline = Player 2.",
        ha="center", va="top", fontsize=12.5, color=MUTED, linespacing=1.45)

# header: the four things that can have happened in the last round
Y0 = H - 21.5
label(Y0 - 0.9, "Last round", "Player 1, Player 2")
for o in OUTCOMES:
    mark(XC[o] - 3.0, Y0 + 0.4, o[0], 2.2, 1); mark(XC[o] + 3.0, Y0 + 0.4, o[1], 2.2, 2)
    ax.text(XC[o], Y0 - 4.3, o, ha="center", va="center", fontsize=11.5, fontweight="bold", color=MUTED)
ax.plot([XL, XR], [Y0 - 7.4, Y0 - 7.4], color=LINE, lw=1.0, zorder=1)

# the column sum
Y1 = Y0 - 13.6
label(Y1 - 0.9, "Start", "its own last move")
for o in OUTCOMES:
    chance(XC[o], Y1 + 0.6, 1 if o[0] == "C" else 0)

Y2 = Y1 - 12.3
label(Y2, "Player 1's points", "last round, minus 1", "+ α ×")
Y3 = Y2 - 10.4
label(Y3, "Player 2's points", "last round, minus 1", "+ β ×")
for o in OUTCOMES:
    tile(XC[o], Y2, PAY1[o]); tile(XC[o], Y3, PAY2[o])

YR = Y3 - 6.2
ax.plot([XL, XR], [YR, YR], color=INK, lw=1.3, zorder=1)
Y4 = YR - 5.6
label(Y4, "Chance Player 1", "cooperates next", "=")
FORM = {"CC": "1 + 2α + 2β", "CD": "1 − α + 4β", "DC": "4α − β", "DD": "0"}
for i, o in enumerate(OUTCOMES):
    ax.text(XC[o], Y4 + 2.0, "q" + SUB[i], ha="center", va="center", fontsize=12, color=MUTED)
    ax.text(XC[o], Y4 - 1.4, FORM[o], ha="center", va="center", fontsize=14.5, fontweight="bold", color=INK)

# two settings of the dials, with the sum spelled out under each chance
def term(v, decimal, first=False):
    """One term of the sum, with its sign; fractions are written as decimals when the dials are given as decimals."""
    v = Fr(v)
    if v.denominator == 1:
        t = str(abs(v.numerator))
    else:
        t = "%g" % abs(float(v)) if decimal else "%d/%d" % (abs(v.numerator), v.denominator)
    return t if first else ("\u2212 " if v < 0 else "+ ") + t


YE = Y4 - 5.9
ax.plot([XL, XR], [YE, YE], color=LINE, lw=1.0, zorder=1)
y = YE - 6.3
for name, dials, a, b, dec in (("Tit for Tat", "\u03b1 = 0.2, \u03b2 = \u22120.2", Fr(1, 5), Fr(-1, 5), True),
                               ("Extort-2", "\u03b1 = 1/18, \u03b2 = \u22121/9", Fr(1, 18), Fr(-1, 9), False)):
    label(y - 0.9, name, dials)
    for o in OUTCOMES:
        s0, t1, t2 = (1 if o[0] == "C" else 0), a * (PAY1[o] - 1), b * (PAY2[o] - 1)
        chance(XC[o], y + 0.6, s0 + t1 + t2, size=22)
        ax.text(XC[o], y - 5.6, "%s %s %s" % (term(s0, dec, first=True), term(t1, dec), term(t2, dec)),
                ha="center", va="center", fontsize=10.5, color=MUTED)
    y -= 13.0

# notes, as under the payoff matrix
ax.text(W / 2, 5.4, "Tiles hold points. Bars show a chance: the blue share cooperates, the orange share defects.\n"
        "The dials α and β turn one into the other: they say how much chance of cooperating a point is worth.",
        ha="center", va="center", fontsize=12, color=MUTED, linespacing=1.5)
fig.savefig(out, dpi=DPI, facecolor="white")
print("ok", out)
