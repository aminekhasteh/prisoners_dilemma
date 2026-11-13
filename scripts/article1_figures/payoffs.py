"""One round of the Prisoner's Dilemma as a payoff matrix, drawn in the same visual language as the cover and
the SSE ring (sse_moves_circular.py): circle = cooperate, square = defect, same palette and typeface.
Player 1 is drawn filled, Player 2 in outline, the way the shared opponent is drawn on the cover and the ring.
Each outcome carries its two-letter code (CC, CD, DC, DD: Player 1's move first), which the rest of the post uses.

Usage: python3 payoffs.py out.png [--filled] [--dpi=200]
  --filled: draw Player 2 filled as well (colour by move); the subtitle then says who is on the left and right."""
import sys, warnings, logging
warnings.filterwarnings("ignore"); logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

# palette and inks shared with sse_moves_circular.py
INK, INK2, MUTED, LINE = "#1b1b1b", "#3d3c39", "#6b6a66", "#c9c8c3"
COOP, DEFECT = "#2a78d6", "#eb6834"
out = sys.argv[1]
FILLED = "--filled" in sys.argv
DPI = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--dpi=")), 200))

plt.rcParams["font.family"] = ["DejaVu Sans"]
W, H = 100.0, 89.0                     # data units; 1 unit = 0.1 inch
fig = plt.figure(figsize=(W / 10, H / 10), facecolor="white")
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect("equal"); ax.axis("off")
PT = 10 / 72.0                         # one point in data units
WORD = {"C": "cooperates", "D": "defects"}


def mark(x, y, move, r, player, lw=2.0):
    """Circle = cooperate, square = defect. Player 1 is filled, Player 2 is an ink outline (unless --filled)."""
    col = COOP if move == "C" else DEFECT
    if player == 2 and not FILLED:
        r -= lw * PT / 2               # keep the outer size equal to the filled marks
        kw = dict(facecolor="white", edgecolor=INK, lw=lw, zorder=3)
    else:
        kw = dict(facecolor=col, edgecolor="none", zorder=3)
    if move == "C":
        ax.add_patch(Circle((x, y), r, **kw))
    else:
        s = 0.88 * r                   # same circle-to-square ratio as the ring
        ax.add_patch(Rectangle((x - s, y - s), 2 * s, 2 * s, joinstyle="miter", **kw))


def band(x0, y0, x1, y1, col):
    """Thick round-capped band marking the span of a move, like the arcs inside the ring."""
    ax.plot([x0, x1], [y0, y1], color=col, lw=5.5, solid_capstyle="round", zorder=2)


def two_weight(cx, y, plain, bold, size):
    """Centre 'plain bold' on cx, with the second word in bold."""
    t1 = ax.text(0, y, plain + " ", fontsize=size, color=INK2, va="center")
    t2 = ax.text(0, y, bold, fontsize=size, fontweight="bold", color=INK, va="center")
    fig.canvas.draw()
    inv = ax.transData.inverted()
    w1, w2 = (t.get_window_extent().transformed(inv).width for t in (t1, t2))
    t1.set_x(cx - (w1 + w2) / 2); t2.set_x(cx - (w1 + w2) / 2 + w1)


XL, XM, XR = 21.0, 59.0, 97.0          # left edge, middle and right edge of the four outcomes
YT, YM, YB = 63.0, 38.0, 13.0          # top, middle and bottom
CW, CH = XM - XL, YT - YM

# title block, as on the SSE ring
ax.text(W / 2, H - 2.8, "One round of the Prisoner's Dilemma", ha="center", va="top", fontsize=21, fontweight="bold", color=INK)
ax.text(W / 2, H - 7.5, "Both players move at the same time. Circle = cooperate, square = defect.\n" +
        ("In each box, Player 1 is on the left and Player 2 on the right." if FILLED else "Filled = Player 1, outline = Player 2."),
        ha="center", va="top", fontsize=12.5, color=MUTED, linespacing=1.45)

# hairlines between the four outcomes
ax.plot([XM, XM], [YB + 1.2, YT - 0.4], color=LINE, lw=1.0, zorder=1)
ax.plot([XL + 0.4, XR - 1.2], [YM, YM], color=LINE, lw=1.0, zorder=1)

# coloured bands along the top (Player 2's move) and the left (Player 1's move)
g, off = 1.6, 1.4
band(XL + g, YT + off, XM - g, YT + off, COOP); band(XM + g, YT + off, XR - g, YT + off, DEFECT)
band(XL - off, YT - g, XL - off, YM + g, COOP); band(XL - off, YM - g, XL - off, YB + g, DEFECT)

# column headers: Player 2
for cx, mv in ((XL + CW / 2, "C"), (XM + CW / 2, "D")):
    mark(cx, YT + 8.9, mv, 1.5, 2, lw=1.6)
    two_weight(cx, YT + 4.7, "Player 2", WORD[mv], 13)

# row headers: Player 1
hx = (3.0 + XL - off) / 2
for cy, mv in ((YT - CH / 2, "C"), (YM - CH / 2, "D")):
    mark(hx, cy + 4.6, mv, 1.5, 1)
    ax.text(hx, cy + 0.4, "Player 1", ha="center", va="center", fontsize=13, color=INK2)
    ax.text(hx, cy - 3.0, WORD[mv], ha="center", va="center", fontsize=13, fontweight="bold", color=INK)

# the four outcomes: (Player 1's move, Player 2's move) -> (Player 1's points, Player 2's points)
NAMES = {3: "Reward (R)", 0: "Sucker's payoff (S)", 5: "Temptation (T)", 1: "Punishment (P)"}
PAY = {("C", "C"): (3, 3), ("C", "D"): (0, 5), ("D", "C"): (5, 0), ("D", "D"): (1, 1)}
DX = 8.6
for (m1, m2), (p1, p2) in PAY.items():
    x0, y1 = (XL if m2 == "C" else XM), (YT if m1 == "C" else YM)
    cx, cy = x0 + CW / 2, y1 - CH / 2 + 0.5
    for x, mv, pts, who in ((cx - DX, m1, p1, 1), (cx + DX, m2, p2, 2)):
        mark(x, cy + 4.8, mv, 3.0, who)
        ax.text(x, cy - 3.2, str(pts), ha="center", va="center", fontsize=30, fontweight="bold", color=INK)
    if p1 == p2:
        ax.text(cx, cy - 8.8, NAMES[p1] + " for both", ha="center", va="center", fontsize=11.5, color=INK2)
    else:
        ax.text(cx - DX, cy - 8.8, NAMES[p1], ha="center", va="center", fontsize=11.5, color=INK2)
        ax.text(cx + DX, cy - 8.8, NAMES[p2], ha="center", va="center", fontsize=11.5, color=INK2)
    ax.text(x0 + 2.4, y1 - 2.9, m1 + m2, ha="left", va="center", fontsize=11.5, fontweight="bold", color=MUTED)

# notes, as under the SSE ring
ax.text(W / 2, 6.3, "Temptation (T = 5)  >  Reward (R = 3)  >  Punishment (P = 1)  >  Sucker's payoff (S = 0)\n"
        "CC, CD, DC, DD: Player 1's move first, then Player 2's.",
        ha="center", va="center", fontsize=12, color=MUTED, linespacing=1.5)
fig.savefig(out, dpi=DPI, facecolor="white")
print("ok", out)
