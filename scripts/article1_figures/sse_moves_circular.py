"""The all-195 SSE ring, with every bar built from the strategy's own moves against one shared opponent.
Circle = cooperate, square = defect (defections a shade darker). Bar length = median SSE, as in sse_circular.py;
each move takes the same length, so a longer bar shows more of the game. Labels: final nice / nasty / end-game.
Usage: python3 sse_moves_circular.py sse_all_circular.csv cover_moves_140.csv OPP_SEQ out.png [--full]
  --full: every bar shows the full MAXM moves (pure pattern, SSE not shown)."""
import sys, warnings, logging
warnings.filterwarnings("ignore"); logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.colors as mc
from matplotlib.patches import Circle, RegularPolygon
from matplotlib.collections import PatchCollection

INK, INK2, MUTED, LINE = "#1b1b1b", "#3d3c39", "#6b6a66", "#c9c8c3"
COOP, DEFECT, OTHER = "#2a78d6", "#eb6834", "#9a9893"
sse = pd.read_csv(sys.argv[1])[["place", "Name", "sse_median"]].rename(columns={"Name": "name"})
mv = pd.read_csv(sys.argv[2])[["name", "moves", "label"]]
df = sse.merge(mv, on="name", how="inner")
assert len(df) == len(sse) == len(mv), (len(df), len(sse), len(mv))
opp, out, FULL = sys.argv[3], sys.argv[4], "--full" in sys.argv
GROUPS = [("nice", "Blues", COOP, "Nice"), ("nasty", "Oranges", DEFECT, "Nasty"), ("end-game", "Greys", OTHER, "End-game")]
CAP, MAXM, GAP, DARKEN = 1.6, 60, 4, 0.35
d = CAP / MAXM                     # radial length of one move
HOLE = 0.5 * CAP
n_slots = len(df) + GAP * len(GROUPS)
step = 2 * np.pi / n_slots
c = 0.42 * d

plt.rcParams["font.family"] = ["Humor Sans", "Comic Neue", "DejaVu Sans"]
LAND, INTRO = "--landscape" in sys.argv, "--intro" in sys.argv
if LAND:
    FULL = True
    fig = plt.figure(figsize=(22, 12.4), facecolor="white")
    ax = fig.add_axes([0.385, 0.0, 0.615, 1.0])
else:
    fig = plt.figure(figsize=(21, 22), facecolor="white")
    ax = fig.add_axes([0.04, 0.085, 0.92, 0.92 * 21 / 22])
ax.set_aspect("equal"); ax.axis("off")
R = HOLE + CAP
ax.set_xlim(-R * 1.5, R * 1.5); ax.set_ylim(-R * 1.5, R * 1.5)
xy = lambda th, rr: (rr * np.sin(th), rr * np.cos(th))

tt = np.linspace(0, 2 * np.pi, 600)
if not FULL:
    for r in (0.5, 1.0, 1.5):
        ax.plot(*xy(tt, HOLE + r), color=LINE, lw=0.9, ls=(0, (2, 3)), zorder=0)
        ax.text(*xy(-GAP * step / 2, HOLE + r), f"{r:g}", ha="center", va="center", fontsize=12, color=MUTED)
    ax.text(*xy(-GAP * step / 2, HOLE + CAP + 0.07), "SSE", ha="center", va="center", fontsize=11, color=MUTED, fontweight="bold")
ax.plot(*xy(tt, HOLE - 0.01), color=INK, lw=1.4, zorder=2)

circles, cc, squares, sc = [], [], [], []
slot = 0.0
for key, cmap, col, title in GROUPS:
    sub = df[df.label == key].sort_values("place")
    start, n = slot, len(sub)
    for k, (_, row) in enumerate(sub.iterrows()):
        th = (slot + 0.5) * step
        base = np.array(matplotlib.colormaps[cmap]((0.35 + 0.3 * k / max(n - 1, 1)) if key == "end-game" else (0.45 + 0.45 * k / max(n - 1, 1)))[:3])
        nm = MAXM if FULL else max(1, int(round(min(row.sse_median, CAP) / d)))
        for t, a in enumerate(row.moves[:nm]):
            p = xy(th, HOLE + (t + 0.5) * d)
            if a == "C":
                circles.append(Circle(p, c)); cc.append(base)
            else:
                squares.append(RegularPolygon(p, 4, radius=c * 1.22, orientation=np.pi / 4 - th)); sc.append(base * (1 - DARKEN))
        if not FULL and row.sse_median > CAP:
            ax.text(*xy(th, HOLE + CAP + 0.035), f"{row.sse_median:.2f}", ha="center", va="center", fontsize=9, fontweight="bold",
                    color=INK, rotation=-np.degrees(th), bbox=dict(fc="white", ec="none", pad=0.6), zorder=6)
        deg = np.degrees(th); flip = 180 < deg < 360
        ax.text(*xy(th, R + 0.09), f"{int(row.place)}. {row['name']}", rotation=90 - deg + (180 if flip else 0), rotation_mode="anchor",
                ha="right" if flip else "left", va="center", fontsize=7.6, color=INK,
                fontweight="bold" if row["name"] == "Tit For Tat" else "normal")
        slot += 1
    arc = np.linspace((start + 0.08) * step, (slot - 0.08) * step, 80)
    ax.plot(*xy(arc, HOLE - 0.08), color=col, lw=7, solid_capstyle="round", zorder=2)
    slot += GAP
ax.add_collection(PatchCollection(circles, facecolors=cc, edgecolors="none", zorder=3))
ax.add_collection(PatchCollection(squares, facecolors=sc, edgecolors="none", zorder=3))

LAND_ = "--landscape" in sys.argv
lines = [(f"All {len(df)}", INK, 17 if LAND_ else 22)] + [(f"{t}: {(df.label == k).sum()}", col, 14 if LAND_ else 18) for k, _, col, t in GROUPS]
for i, (txt, col, fs) in enumerate(lines):
    ax.text(0, (0.15 if LAND_ else 0.11) * ((len(lines) - 1) / 2 - i), txt, ha="center", va="center", fontsize=fs, fontweight="bold", color=col)

if LAND:
    import textwrap
    X = 0.045
    def shape(axx, x, y, a, size, face, edge, lw=0.9):
        if a == "C": axx.add_patch(Circle((x, y), size, facecolor=face, edgecolor=edge, lw=lw))
        else: axx.add_patch(RegularPolygon((x, y), 4, radius=size * 1.25, orientation=np.pi / 4, facecolor=face, edgecolor=edge, lw=lw))
    y = 0.90
    if INTRO:
        fig.text(X - 0.008, y + 0.035, "\u201c", ha="left", va="top", fontsize=130, color="#b9c9e0", family="DejaVu Serif")
        fig.text(X + 0.035, y - 0.035, "195 strategies.\nOne opponent.\n%d rounds." % MAXM, ha="left", va="top", fontsize=36,
                 fontweight="bold", style="italic", color=INK, linespacing=1.25, family="DejaVu Serif")
        fig.text(X + 0.035, y - 0.228, "Here's how every single one of them played.\u201d", ha="left", va="top", fontsize=20,
                 style="italic", color=INK2, family="DejaVu Serif")
        y -= 0.40
    else:
        y = 0.5 + 0.36 / 2
    KW, KH = 0.33, 0.36
    kax = fig.add_axes([X, y - KH, KW, KH]); YL = 10 * (KH * 12.4) / (KW * 22)
    kax.set_xlim(0, 10); kax.set_ylim(0, YL); kax.axis("off"); kax.set_aspect("equal")
    rows = [("Nice", "never the first to defect", "Blues"), ("Nasty", "defects first", "Oranges"),
            ("End-game", "defects first only at the end", "Greys")]
    for i, (nm, desc, cm) in enumerate(rows):
        yy = YL - 0.35 - 0.75 * i
        base = np.array(matplotlib.colormaps[cm](0.5 if cm == "Greys" else 0.68)[:3])
        shape(kax, 0.25, yy, "C", 0.22, base, "none"); shape(kax, 0.85, yy, "D", 0.22, base * (1 - DARKEN), "none")
        kax.text(1.35, yy, nm, ha="left", va="center", fontsize=16, fontweight="bold", color=INK)
        kax.text(3.4, yy, desc, ha="left", va="center", fontsize=15, color=INK2)
    kax.text(0.0, YL - 2.75, "The opponent everyone plays (first %d moves):" % MAXM, ha="left", va="center", fontsize=15, color=INK2)
    per = 30; sz = 9.8 / per
    for t, a in enumerate(opp[:MAXM]):
        shape(kax, 0.05 + (t % per) * sz + sz / 2, YL - 3.35 - (t // per) * sz * 1.3, a, sz * 0.38, "white", INK, 0.9)
    kax.text(0.0, YL - 4.55, "circle = cooperate, square = defect", ha="left", va="center", fontsize=14, color=MUTED)
    fig.savefig(out, dpi=180, facecolor="white")
    print("ok landscape", len(circles) + len(squares), "moves drawn"); sys.exit()
fig.text(0.5, 0.985, "All 195 strategies: how ZD-like, how nice, and how they play", ha="center", va="top", fontsize=26, fontweight="bold", color=INK)
fig.text(0.5, 0.95, ("Every bar is made of the strategy's own moves against the same opponent, starting at the inner ring:\n"
                     "circle = cooperate, square = defect. " +
                     ("Each bar shows the first %d moves." % MAXM if FULL else
                      "Bar length = median SSE in standard tournaments, so a longer bar\nshows more of the game. Shorter bar = closer to a zero-determinant strategy.")),
         ha="center", va="top", fontsize=15, color=MUTED, linespacing=1.45)

# the shared opponent, as a strip at the bottom
oax = fig.add_axes([0.25, 0.07, 0.5, 0.016]); oax.set_aspect("equal"); oax.axis("off")
oax.set_xlim(-0.6, MAXM - 0.4); oax.set_ylim(-0.6, 0.6)
for t, a in enumerate(opp[:MAXM]):
    if a == "C": oax.add_patch(Circle((t, 0), 0.4, facecolor="white", edgecolor=INK, lw=0.8))
    else: oax.add_patch(RegularPolygon((t, 0), 4, radius=0.5, orientation=np.pi / 4, facecolor="white", edgecolor=INK, lw=0.8))
fig.text(0.5, 0.091, "The opponent everyone plays (first %d moves, cooperates about 70%% of the time at random):" % MAXM,
         ha="center", va="bottom", fontsize=13, color=INK2)
fig.text(0.5, 0.015, "Nice: never the first to defect.  Nasty: defects first.  End-game: defects first only in the last few rounds.\n"
         "Numbers give the order by average rank. Shades vary by strategy; defections are drawn a shade darker." +
         ("" if FULL else "\nHopeless has an SSE of 2.47; its bar stops at 1.6 and the value is written on it."),
         ha="center", va="bottom", fontsize=13, color=MUTED, linespacing=1.45)
fig.savefig(out, dpi=180, facecolor="white")
print("ok", len(circles) + len(squares), "moves drawn")
