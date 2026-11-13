"""Cover idea: every strategy's moves against the same fixed opponent, as rows of shapes.
Circle = cooperate, square = defect. Each strategy gets its own shade: blues for nice, oranges for nasty, greys for other.
Moves are simulated on the server (cover_moves.csv: name, moves, label); this script only draws.

Usage: python3 cover_moves.py cover_moves.csv groups.csv out.png OPP_SEQ [--sample] [--labels] [--rotate]
  --rotate: strategies as columns, turns running down, no text (the cover layout).
  groups.csv: sse_all_circular.csv (place, Name, group) used for ordering and as fallback labels."""
import sys, warnings, logging
warnings.filterwarnings("ignore"); logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.patches import Circle, Rectangle

PAPER, INK, INK2, MUTED = "#fbfaf6", "#1b1b1b", "#3d3c39", "#6b6a66"
SAMPLE = ["Tit For Tat", "Grudger", "Win-Stay Lose-Shift", "Cooperator", "Tit For 2 Tats", "GTFT", "Fool Me Once",
          "Spiteful Tit For Tat", "Hard Tit For Tat", "Grofman", "PSO Gambler 1_1_1", "Davis",
          "Evolved FSM 16", "Evolved HMM 5", "EvolvedLookerUp2_2_2", "Evolved ANN", "BackStabber", "DoubleCrosser",
          "ZD-Extort-2", "Suspicious Tit For Tat", "Defector", "Alternator", "Bully", "Prober", "Random",
          "Joss", "Calculator", "Handshake", "Omega TFT", "Meta Majority"]

moves = pd.read_csv(sys.argv[1])
groups = pd.read_csv(sys.argv[2])[["place", "Name", "group"]].rename(columns={"Name": "name"})
df = moves.drop(columns=[c for c in ("group", "place") if c in moves]).merge(groups, on="name", how="left")
df["place"] = df["place"].fillna(999)
if "label" in df and df["label"].notna().any():
    df["group"] = df["label"].fillna(df["group"])
df = df[df["moves"].notna() & df["group"].notna()]
opp = sys.argv[4]
sample = "--sample" in sys.argv
labels = "--labels" in sys.argv
if sample:
    df = df[df["name"].isin(SAMPLE)]
OTHER_NAME = "end-game" if df["group"].isin(["end-game", "endgame"]).any() else "other"
df["group"] = df["group"].replace({"end-game": "other", "endgame": "other"})
order = {"nice": 0, "other": 1, "nasty": 2}
df = df.sort_values(["group", "place"], key=lambda s: s.map(order) if s.name == "group" else s).reset_index(drop=True)

# one shade per strategy inside its colour family
fam = {"nice": matplotlib.colormaps.get_cmap("Blues"), "nasty": matplotlib.colormaps.get_cmap("Oranges"), "other": matplotlib.colormaps.get_cmap("Greys")}
cols = []
for g, sub in df.groupby("group", sort=False):
    n = len(sub)
    for k in range(n):
        lo, hi = (0.35, 0.65) if g == "other" else (0.45, 0.9)
        cols.append((sub.index[k], fam[g](lo + (hi - lo) * (k / max(n - 1, 1)))))
df["colour"] = pd.Series(dict(cols))

T = min(len(opp), df["moves"].str.len().max())
rows = len(df) + 1

if "--rotate" in sys.argv:
    # strategies become columns (opponent first, in white), turns run top to bottom; no text, cover-ready
    gap = 0.8                                   # small gap between the opponent column and the rest
    x0, x1, y0, y1 = -0.5, len(df) + gap + 0.5, -0.5, T - 0.5
    W = 14.0                                    # full bleed: the figure is exactly the grid, no margin
    fig = plt.figure(figsize=(W, W * (y1 - y0) / (x1 - x0)), facecolor=PAPER)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_aspect("equal")
    ax.set_xlim(x0, x1); ax.set_ylim(y1, y0)
    c = 0.38
    def put(x, y, a, col, edge):
        if a == "C":
            ax.add_patch(Circle((x, y), c, facecolor=col, edgecolor=edge, lw=0.35))
        else:
            ax.add_patch(Rectangle((x - c * 0.88, y - c * 0.88), 1.76 * c, 1.76 * c, facecolor=col, edgecolor=edge, lw=0.35))
    for t, a in enumerate(opp[:T]):
        put(0, t, a, "#ffffff", INK)
    import matplotlib.colors as mc
    DARKEN = float(next((a.split("=")[1] for a in sys.argv if a.startswith("--darken=")), 0.35))
    for i, r in df.iterrows():
        base = np.array(mc.to_rgb(r["colour"]))
        dark = tuple(base * (1 - DARKEN))       # defections a shade darker, so streaks show at cover size
        for t, a in enumerate(r["moves"][:T]):
            put(i + 1 + gap, t, a, r["colour"] if a == "C" else dark, "none")
    fig.savefig(sys.argv[3], dpi=200, facecolor=PAPER)
    print("ok rotated", len(df), "strategies,", T, "turns"); sys.exit()

fig = plt.figure(figsize=(14, 10), facecolor=PAPER)
left = 0.2 if labels else 0.04
ax = fig.add_axes([left, 0.04, 0.96 - left, 0.92]); ax.axis("off")
ax.set_xlim(-0.6, T - 0.4); ax.set_ylim(rows - 0.4 + (0.6 if labels else 0), -0.6 - (1.0 if labels else 0))
cell = 0.36

def shape(x, y, a, col, edge):
    if a == "C":
        ax.add_patch(Circle((x, y), cell, facecolor=col, edgecolor=edge, lw=0.6))
    else:
        ax.add_patch(Rectangle((x - cell * 0.9, y - cell * 0.9), 1.8 * cell * 0.9, 1.8 * cell * 0.9,
                               facecolor=col, edgecolor=edge, lw=0.6))

for t, a in enumerate(opp[:T]):            # the shared opponent on top
    shape(t, 0, a, "#ffffff", INK)
if labels:
    ax.text(-1.0, 0, "the opponent", ha="right", va="center", fontsize=9.5, color=INK, fontweight="bold")
for i, r in df.iterrows():
    y = i + 1.0 + (0.4 if labels else 0.25)
    for t, a in enumerate(r["moves"][:T]):
        shape(t, y, a, r["colour"], "none")
    if labels:
        ax.text(-1.0, y, r["name"], ha="right", va="center", fontsize=8.5, color=INK2)
if labels:
    ax.text((T - 1) / 2, -1.25, "turn 1  →  turn %d.   circle = cooperate,  square = defect.   "
            "blues = nice,  oranges = nasty,  greys = %s" % (T, OTHER_NAME), ha="center", va="center", fontsize=10, color=MUTED)
fig.savefig(sys.argv[3], dpi=150, facecolor=PAPER)
print("ok", len(df), "strategies,", T, "turns")
