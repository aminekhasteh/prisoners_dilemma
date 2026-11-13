"""Every zero-determinant (ZD) strategy lies on one flat sheet, and SSE is the squared distance from a strategy to it.
A strategy's chances of cooperating after CC, CD and DC make it a point in a cube. The recipe
q = (1, 1, 0, 0) + alpha (2, -1, 4, 0) + beta (2, 4, -1, 0) has only two dials, so it can only reach the plane
3 q1 - 2 q2 - 2 q3 = 1; inside the cube that plane is a triangle. Grudger, p = (1, 0, 0, 0), sits off the sheet, and
the dashed line is its gap to the closest ZD strategy q* = (11/17, 4/17, 4/17, 0): SSE = 4/17.
The two arrows on the sheet are the recipe's two directions (more alpha, more beta); the white weave follows them.
Same marks, palette and typeface as payoffs.py: circle = cooperate, square = defect, Player 1 filled, Player 2 in
outline. Strategies are drawn as diamonds so they are not mistaken for moves.
Source: Knight, Harper, Glynatsi & Gillard (2019, arXiv 1904.00973): eqs. 12-14 for the plane and its triangle,
eqs. 17-21 for SSE.

Usage: python3 sse_math_sheet.py out.png [--dpi=200] [--az=-62] [--el=21] [--sheet=#e4e3de] [--legs]
  --az, --el: viewing angle of the cube in degrees; the labels are placed for the default view.
  --legs: also draw the three per-outcome gaps (6/17, 4/17, 4/17) that make up Grudger's dashed line."""
import sys, itertools, warnings, logging
warnings.filterwarnings("ignore"); logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Circle, Rectangle, Polygon, FancyArrowPatch

# palette and inks shared with payoffs.py and sse_moves_circular.py
INK, INK2, MUTED = "#1b1b1b", "#3d3c39", "#6b6a66"
COOP, DEFECT, MESH = "#2a78d6", "#eb6834", "#ffffff"
EDGE, EDGE_HIDDEN = "#b4b3ae", "#d3d2cd"   # the cube's visible and hidden edges
out = sys.argv[1]
opt = lambda k, dflt: type(dflt)(next((a.split("=")[1] for a in sys.argv if a.startswith("--%s=" % k)), dflt))
DPI, AZ, EL, SHEET = opt("dpi", 200), opt("az", -62.0), opt("el", 21.0), opt("sheet", "#e4e3de")
LEGS = "--legs" in sys.argv

plt.rcParams["font.family"] = ["DejaVu Sans"]
W, H = 100.0, 102.0                    # data units; 1 unit = 0.1 inch
fig = plt.figure(figsize=(W / 10, H / 10), facecolor="white")
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect("equal"); ax.axis("off")
PT = 10 / 72.0

# orthographic view of the cube: d points to the camera, r is screen-right, u is screen-up
az, el = np.radians(AZ), np.radians(EL)
d = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
r = np.array([-np.sin(az), np.cos(az), 0.0])
u = np.cross(d, r)
S, OX, OY = 43.5, 16.5, 30.0           # scale, and where the cube's origin sits on the page
P = lambda p: np.array([OX + S * float(np.dot(p, r)), OY + S * float(np.dot(p, u))])
V = lambda *c: np.array(c, float)


def mark(x, y, move, rad, player, lw=1.5):
    """Circle = cooperate, square = defect. Player 1 is filled, Player 2 is an ink outline."""
    if player == 2:
        rad -= lw * PT / 2
        kw = dict(facecolor="white", edgecolor=INK, lw=lw, zorder=9)
    else:
        kw = dict(facecolor=COOP if move == "C" else DEFECT, edgecolor="none", zorder=9)
    if move == "C":
        ax.add_patch(Circle((x, y), rad, **kw))
    else:
        s = 0.88 * rad
        ax.add_patch(Rectangle((x - s, y - s), 2 * s, 2 * s, joinstyle="miter", **kw))


def seg(a, b, **kw):
    (xa, ya), (xb, yb) = P(a), P(b)
    return ax.plot([xa, xb], [ya, yb], **kw)[0]


def diamond(p, size=1.25, hollow=False):
    x, y = P(p)
    ax.add_patch(Polygon([(x, y + size), (x + size, y), (x, y - size), (x - size, y)], closed=True,
                         facecolor="white" if hollow else INK, edgecolor=INK if hollow else "white",
                         lw=1.7 if hollow else 1.3, joinstyle="miter", zorder=8))


def note(xy, text, ha="left", va="center", size=11.5, color=MUTED, weight="normal", on_sheet=False):
    halo = [pe.withStroke(linewidth=3.4, foreground=SHEET if on_sheet else "white")]
    return ax.text(xy[0], xy[1], text, ha=ha, va=va, fontsize=size, color=color, fontweight=weight, linespacing=1.35,
                   zorder=10, path_effects=halo)


def name(xy, text, ha="left", on_sheet=False):
    return note(xy, text, ha=ha, size=13, color=INK, weight="bold", on_sheet=on_sheet)


def leader(a, b):
    """Thin line from a label to the thing it names."""
    ax.plot([a[0], b[0]], [a[1], b[1]], color=MUTED, lw=0.9, zorder=7, solid_capstyle="round")


# the cube: the three edges that meet the far corner are hidden
corners = [V(*c) for c in itertools.product((0, 1), repeat=3)]
far = min(corners, key=lambda c: np.dot(c, d))
for a, b in itertools.combinations(corners, 2):
    if np.abs(a - b).sum() == 1:
        hidden = (a == far).all() or (b == far).all()
        seg(a, b, color=EDGE_HIDDEN if hidden else EDGE, lw=1.0, ls=(0, (2.5, 2.5)) if hidden else "-",
            zorder=1 if hidden else 6, solid_capstyle="round")

# the sheet: the part of the plane 3 q1 - 2 q2 - 2 q3 = 1 that lies inside the cube
A, B, C = V(1, 1, 0), V(1, 0, 1), V(1 / 3, 0, 0)
q = lambda a, b: V(1, 1, 0) + a * V(2, -1, 4) + b * V(2, 4, -1)
tri = Polygon([P(A), P(B), P(C)], closed=True, facecolor=SHEET, edgecolor="none", zorder=2)
ax.add_patch(tri)
for k in range(-12, 13):               # the weave: lines of constant alpha and lines of constant beta
    t = k / 30.0
    for a0, a1 in (((t, -0.4), (t, 0.1)), ((-0.2, t), (0.3, t))):
        seg(q(*a0), q(*a1), color=MESH, lw=0.9, zorder=3).set_clip_path(tri)
ax.add_patch(Polygon([P(A), P(B), P(C)], closed=True, facecolor="none", edgecolor=INK, lw=1.5, joinstyle="round", zorder=4))

# the two dials, as directions on the sheet
D0 = (0.09, -0.19)
for da, db, txt, off in ((0.05, 0, "\u03b1", (-1.5, 0.6)), (0, 0.05, "\u03b2", (1.6, 0.0))):
    p0, p1 = P(q(*D0)), P(q(D0[0] + da, D0[1] + db))
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=11, color=INK2, lw=1.3, shrinkA=0, shrinkB=0, zorder=7))
    note((p1[0] + off[0], p1[1] + off[1]), txt, ha="center", size=13.5, color=INK2, weight="bold", on_sheet=True)

# Grudger (p) and its closest ZD strategy (q*)
G, Q, E = V(1, 0, 0), V(11 / 17, 4 / 17, 4 / 17), V(8 / 9, 1 / 2, 1 / 3)
if LEGS:                               # the three per-outcome gaps: 6/17 after CC, 4/17 after CD, 4/17 after DC
    L1, L2 = V(11 / 17, 0, 0), V(11 / 17, 4 / 17, 0)
    for a, b in ((G, L1), (L1, L2), (L2, Q)):
        seg(a, b, color=INK2, lw=1.0, zorder=7, solid_capstyle="round")
seg(G, Q, color=INK, lw=1.9, ls=(0, (2.2, 1.8)), zorder=7)
nh, th, k = V(3, -2, -2) / 17 ** 0.5, (C - Q) / np.linalg.norm(C - Q), 0.06      # right-angle mark at the foot of the gap
c1, c2, c3 = P(Q + k * th), P(Q + k * th + k * nh), P(Q + k * nh)
ax.plot([c1[0], c2[0], c3[0]], [c1[1], c2[1], c3[1]], color=INK, lw=1.0, zorder=7, solid_joinstyle="miter")
for p in (A, B, E):
    diamond(p)
diamond(Q, hollow=True); diamond(G, size=1.55)


# axes: three visible edges, each one a chance of cooperating that runs from 0 to 1
def axis(a, b, title, code, off0, off1, toff, moff):
    pa, pb = P(a), P(b)
    e = (pb - pa) / np.linalg.norm(pb - pa)
    ax.text(pa[0] + off0[0], pa[1] + off0[1], "0", ha="center", va="center", fontsize=11.5, color=MUTED)
    ax.text(pb[0] + off1[0], pb[1] + off1[1], "1", ha="center", va="center", fontsize=11.5, color=MUTED)
    m = (pa + pb) / 2 + np.array(toff)
    ax.text(m[0], m[1], title, ha="center", va="center", fontsize=12.5, color=INK2,
            rotation=np.degrees(np.arctan2(e[1], e[0])), rotation_mode="anchor")
    c = m + e * moff                    # the outcome's two marks, set along the edge after the title
    mark(*(c - 1.6 * e), code[0], 1.15, 1); mark(*(c + 1.6 * e), code[1], 1.15, 2)


axis(V(0, 0, 0), V(1, 0, 0), "after CC", "CC", (-0.9, -1.9), (-1.6, -2.1), (-1.5, -3.9), 8.4)
axis(V(1, 0, 0), V(1, 1, 0), "after CD", "CD", (1.9, -1.4), (0.9, -2.6), (1.2, -4.0), 8.4)
axis(V(0, 0, 0), V(0, 0, 1), "after DC", "DC", (-2.0, 0.2), (-2.0, 0), (-4.2, -2.0), 8.4)
pc = P(C); ax.text(pc[0] - 0.6, pc[1] - 2.2, "1/3", ha="center", va="center", fontsize=11.5, color=MUTED)

# labels
pa, pb, pg, pq, pe_ = P(A), P(B), P(G), P(Q), P(E)
name((pb[0] + 2.2, pb[1] + 3.6), "Tit for Tat"); note((pb[0] + 2.2, pb[1] + 0.9), "(1, 0, 1)")
name((pe_[0] - 3.4, pe_[1] - 3.6), "Extort-2", on_sheet=True)
note((pe_[0] - 3.4, pe_[1] - 6.2), "(8/9, 1/2, 1/3)", on_sheet=True)
name((pa[0] + 2.6, pa[1] + 2.0), "The recipe's start"); note((pa[0] + 2.6, pa[1] - 0.8), "(1, 1, 0), \u03b1 = \u03b2 = 0")
name((pg[0] + 0.5, pg[1] - 5.8), "Grudger", ha="center"); note((pg[0] + 0.5, pg[1] - 8.5), "p = (1, 0, 0)", ha="center")
note((pg[0] + 0.5, pg[1] - 11.1), "SSE = gap\u00b2 = 4/17 \u2248 0.24", ha="center")
name((20.0, pq[1] + 11.2), "q*"); note((20.0, pq[1] + 8.5), "closest ZD strategy"); note((20.0, pq[1] + 5.9), "(0.65, 0.24, 0.24)")
leader((33.4, pq[1] + 6.6), (pq[0] - 1.8, pq[1] + 0.8))
mid = pg + 0.33 * (pq - pg)
note((mid[0] - 1.6, mid[1] + 0.2), "gap", ha="right", size=12.5, color=INK, weight="bold")
pz = P(V(0, 0, 1))                     # the sheet's equation, in the empty part of the cube
name((pz[0] + 4.5, pz[1] - 8.0), "The ZD sheet"); note((pz[0] + 4.5, pz[1] - 11.0), "3q\u2081 \u2212 2q\u2082 \u2212 2q\u2083 = 1", size=13, color=INK2)
ps = P(C) + (P(B) - P(C)) * 0.66
leader((pz[0] + 23.6, pz[1] - 11.4), (ps[0] + 1.0, ps[1] - 0.2))

# title block and notes, as on the payoff matrix
ax.text(W / 2, H - 2.8, "Every ZD strategy lies on one flat sheet", ha="center", va="top", fontsize=21, fontweight="bold", color=INK)
ax.text(W / 2, H - 7.5, "Any strategy p is a point in this cube: its chances of cooperating after CC, after CD and after DC.\n"
        "A ZD strategy q can only sit on the grey triangle. Turning α and β (the arrows) slides it around the sheet.\n"
        "SSE is the squared distance from p to that sheet.",
        ha="center", va="top", fontsize=12.5, color=MUTED, linespacing=1.45)
ax.text(W / 2, 5.6, "The fourth number (after DD) has no room in a cube. Every ZD strategy has 0 there, so it adds p₄² to SSE:\n"
        "nothing for Grudger, a full 1 for Win-Stay-Lose-Shift, which shares Grudger's corner.",
        ha="center", va="center", fontsize=12, color=MUTED, linespacing=1.5)
fig.savefig(out, dpi=DPI, facecolor="white")
print("ok", out)
