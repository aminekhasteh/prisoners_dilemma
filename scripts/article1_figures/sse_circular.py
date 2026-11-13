"""Circular plot of SSE for every strategy (or the top N with --top N) in the standard tournaments, grouped nice / nasty / other.
Layout follows Tanigawa et al. 2019 (Nat Commun 10:4064), Fig. 3b; sketch style matches sse_explained.py.

Niceness (Axelrod): a strategy is nice if it is never the first to defect. Per tournament we call it nice when it
opened with cooperation in every match (Initial_C_rate == 1) and never defected right after mutual cooperation
(CC_to_C_rate == 1). Across tournaments: nice = held in every one, nasty = failed in at least 95%, other = in between.
Only tournaments of 10+ turns are used: in 1-turn games no transitions exist, and in very short games a strategy
that springs its trap later never gets the chance to.

Usage: python sse_circular.py Data/combined_dataset.parquet out.png [out.csv] [--top N|all]"""
import sys, warnings, logging
warnings.filterwarnings("ignore"); logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import numpy as np
import polars as pl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COOP, DEFECT, OTHER = "#2a78d6", "#eb6834", "#9a9893"
INK, INK2, MUTED, LINE = "#1b1b1b", "#3d3c39", "#6b6a66", "#c9c8c3"
args = [a for a in sys.argv[1:] if not a.startswith("--top")]
top_arg = sys.argv[sys.argv.index("--top") + 1] if "--top" in sys.argv else "all"
if "--top" in sys.argv: args.remove(top_arg)
TOP = 10_000 if top_arg == "all" else int(top_arg)
MIN_TURNS, NASTY_CUT = 10, 0.05

df = (pl.scan_parquet(args[0])
      .filter((pl.col("dataset") == "standard") & (pl.col("turns") >= MIN_TURNS))
      .select("Name", "Normalized_Rank", "SSE", "Initial_C_rate", "CC_to_C_rate")
      .with_columns(((pl.col("Initial_C_rate") >= 1 - 1e-9) & (pl.col("CC_to_C_rate") >= 1 - 1e-9)).alias("nice"))
      .group_by("Name").agg(
          pl.len().alias("tournaments"),
          pl.col("Normalized_Rank").mean().alias("mean_norm_rank"),
          pl.col("SSE").median().alias("sse_median"),
          pl.col("SSE").quantile(0.25).alias("sse_q25"),
          pl.col("SSE").quantile(0.75).alias("sse_q75"),
          pl.col("nice").mean().alias("share_nice"))
      .sort("mean_norm_rank").head(TOP).collect()
      .with_row_index("place", offset=1)
      .with_columns(pl.when(pl.col("share_nice") == 1).then(pl.lit("nice"))
                    .when(pl.col("share_nice") <= NASTY_CUT).then(pl.lit("nasty"))
                    .otherwise(pl.lit("other")).alias("group")))
N = df.height
ALL = N < TOP or top_arg == "all"
BIG, HUGE = N > 40, N > 120               # many bars: thinner strokes, smaller labels
LABEL = f"All {N}" if ALL else f"Top {N}"
if len(args) > 2: df.write_csv(args[2])
print(df.group_by("group").len()); print(df.select("place", "Name", "group", "share_nice", "sse_median"))

GROUPS = [("nice", COOP, "Nice", "never the first\nto defect"),
          ("nasty", DEFECT, "Nasty", "defects first"),
          ("other", OTHER, "Other", "defects first\nonly sometimes")]
GROUPS = [g for g in GROUPS if (df["group"] == g[0]).any()]
GAP = 4 if HUGE else 2.5 if BIG else 1.2                                  # empty slots between groups
n_slots = N + GAP * len(GROUPS)
step = 2 * np.pi / n_slots
CAP = 1.6                                   # longer bars are cut here and their value written on the tip
rmax = min(CAP, max(0.75, float(df["sse_q75"].max()) * 1.05))
HOLE = 0.5 * rmax                           # empty middle, as in the Nature figure

plt.xkcd(scale=0.6, length=120, randomness=2)
plt.rcParams["font.family"] = ["Humor Sans", "Comic Neue", "DejaVu Sans"]
plt.rcParams["path.effects"] = []
FW, FH = (21, 22) if HUGE else (16, 17) if BIG else (12, 13)
AX = [0.19, 0.16, 0.62, 0.62 * FW / FH] if BIG else [0.22, 0.17, 0.56, 0.56]
fig = plt.figure(figsize=(FW, FH))
ax = fig.add_axes(AX, projection="polar")
ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
ax.set_ylim(-HOLE, rmax)
ax.axis("off")

# radial guide rings, Nature-style ticks along the gap before the first group
for r in np.arange(0.5 if rmax > 1.5 else 0.25, rmax + 1e-9, 0.5 if rmax > 1.5 else 0.25):
    th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(th, np.full_like(th, r), color=LINE, lw=0.9, ls=(0, (2, 3)), zorder=0)
    ax.text(-GAP * step / 2, r, f"{r:g}", ha="center", va="center", fontsize=12 if HUGE else 10, color=MUTED)
ax.text(-GAP * step / 2, rmax + 0.06 * rmax, "SSE", ha="center", va="bottom", fontsize=10.5, color=MUTED, fontweight="bold")
ax.plot(np.linspace(0, 2 * np.pi, 400), np.zeros(400), color=INK, lw=1.4, zorder=2)

slot = 0.0
for key, col, title, blurb in GROUPS:
    sub = df.filter(pl.col("group") == key).sort("place")
    start = slot
    for row in sub.iter_rows(named=True):
        th = (slot + 0.5) * step
        cut = row["sse_median"] > rmax
        ax.bar(th, min(row["sse_median"], rmax), width=step * 0.72, bottom=0, color=col, edgecolor=INK, lw=0.5 if HUGE else 0.7 if BIG else 1.4, zorder=3,
               alpha=0.92)
        if cut:
            ax.text(th, rmax * 0.97, f"{row['sse_median']:.2f}", ha="center", va="center", fontsize=9, fontweight="bold",
                    color=INK, rotation=90 - np.degrees(th), bbox=dict(fc="white", ec="none", pad=0.6), zorder=6)
        ax.plot([th, th], [min(row["sse_q25"], rmax), min(row["sse_q75"], rmax)], color=INK, lw=0.6 if HUGE else 0.8 if BIG else 1.3, zorder=4)
        # label outside the ring, rotated to read outward
        deg = np.degrees(th)
        flip = 180 < deg < 360
        rot = 90 - deg + (180 if flip else 0)
        ax.text(th, rmax + 0.04 * rmax, f"{row['place']}. {row['Name']}", rotation=rot, rotation_mode="anchor",
                ha="right" if flip else "left", va="center", fontsize=7.6 if HUGE else 8.2 if BIG else 11.5, color=INK,
                fontweight="bold" if row["Name"] == "Tit For Tat" else "normal")  # the article's subject
        slot += 1
    # group arc on the inside of the ring, with its name
    th0, th1 = (start + 0.08) * step, (slot - 0.08) * step
    arc = np.linspace(th0, th1, 80)
    r_arc = -0.07 * rmax
    ax.plot(arc, np.full_like(arc, r_arc), color=col, lw=7, solid_capstyle="round", zorder=2)
    slot += GAP

# middle of the ring: total, then the colour key (like the Nature figure's legend), centred as one block
lines = [(LABEL, INK, 22 if HUGE else 18 if BIG else 15)] + \
        [(f"{title}: {int((df['group'] == key).sum())}", col, 18 if HUGE else 15 if BIG else 12.5) for key, col, title, _ in GROUPS]
cy, dy = AX[1] + AX[3] / 2, (0.021 if HUGE else 0.024 if BIG else 0.03)
for i, (txt, col, fs) in enumerate(lines):
    fig.text(0.5, cy + dy * ((len(lines) - 1) / 2 - i), txt, ha="center", va="center", fontsize=fs, fontweight="bold", color=col)

fig.text(0.5, 0.985, (f"All {N} strategies" if ALL else f"The top {N} strategies") + ": how ZD-like, and how nice", ha="center", va="top",
         fontsize=26 if HUGE else 21,
         fontweight="bold", color=INK)
fig.text(0.5, 0.947,
         "Standard tournaments (no noise, fixed length). Bar = median SSE across tournaments; the line\n"
         "inside it spans the middle half. Shorter bar = closer to a zero-determinant strategy.",
         ha="center", va="top", fontsize=15 if HUGE else 12.5, color=MUTED, linespacing=1.45)
fig.text(0.5, 0.018,
         "Nice: never the first to defect.  Nasty: defects first in nearly every tournament.  "
         "Other: defects first in some.\nNumbers give the order by average rank. Tournaments with fewer than "
         f"{MIN_TURNS} turns are left out." + "".join(
             f"\n{r['Name']} has an SSE of {r['sse_median']:.2f}. Drawn to scale it squashed everything else into the middle, "
             f"so the axis stops at {rmax:g} and its value is written on the bar."
             for r in df.filter(pl.col("sse_median") > rmax).iter_rows(named=True)),
         ha="center", va="bottom", fontsize=13 if HUGE else 10.5, color=MUTED, linespacing=1.45)
fig.savefig(args[1], dpi=180, facecolor="white")
print("ok")
