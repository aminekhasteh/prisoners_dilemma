"""Rankings, niceness and SSE results for the 272-strategy standard tournaments (the article's "Checking nice" section).
Usage: python results_niceness_sse.py data/knight272.parquet data/niceness_matrix.csv results/"""
import sys
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

df = pd.read_parquet(sys.argv[1]); lab = pd.read_csv(sys.argv[2]); out = sys.argv[3]
s = df[df.noise == 0]
r = (s.groupby("Name").agg(mean_norm_rank=("Normalized_Rank", "mean"), median_norm_rank=("Normalized_Rank", "median"),
                           sse_median=("SSE", "median"), dd_to_c=("DD_to_C_rate", "median"), coop=("Cooperation_rating", "mean"),
                           score=("Median_score", "mean"), fortran=("fortran", "first"), python_class=("python_class", "first"))
     .sort_values("mean_norm_rank").reset_index())
r["place"] = np.arange(1, len(r) + 1)
r["place_by_median"] = r.median_norm_rank.rank(method="min").astype(int)
r = r.merge(lab[["Name", "label_matrix"]].rename(columns={"label_matrix": "label"}), on="Name")
r.to_csv(out + "ranking_standard.csv", index=False)
r[["Name", "label"]].to_csv(out + "../data/niceness.csv", index=False)
r[["place", "Name", "sse_median", "label"]].to_csv(out + "sse_ranking_fullnames.csv", index=False)   # input for sse_moves_circular.py

def cliff(a, b):
    u = mannwhitneyu(a, b).statistic
    return 2 * u / (len(a) * len(b)) - 1

lines = []
P = lambda *a: lines.append(" ".join(str(x) for x in a))
P("strategies:", len(r), "| nice", (r.label == "nice").sum(), "| nasty", (r.label == "nasty").sum())
for n in (15, 20, 50, 100):
    P(f"top {n}: nice {(r.head(n).label == 'nice').sum()}, nasty {(r.head(n).label == 'nasty').sum()}",
      "| nasty in it:", r.head(n)[r.head(n).label == "nasty"].Name.tolist() if n <= 20 else "")
P("bottom 50: nice", (r.tail(50).label == "nice").sum())
P("mean normalized rank: nice %.3f, nasty %.3f" % (r[r.label == "nice"].mean_norm_rank.mean(), r[r.label == "nasty"].mean_norm_rank.mean()))
for k in ["k92r", "k42r", "k61r", "Spiteful Tit For Tat", "Cooperator", "Defector", "Win-Stay Lose-Shift: C", "Grudger"]:
    x = r[r.Name == k]
    if len(x): P(f"{k}: place {int(x.place.iloc[0])} of {len(r)} by mean rank, {int(x.place_by_median.iloc[0])} by median; SSE {x.sse_median.iloc[0]:.3f}; {x.label.iloc[0]}")
P("best original (Fortran) entries:", r[r.fortran == 1].head(5)[["Name", "place"]].values.tolist())
P("Fortran entries in top 20/50/100:", [(r.head(n).fortran == 1).sum() for n in (20, 50, 100)])
a, b = r[r.label == "nasty"].sse_median, r[r.label == "nice"].sse_median
P("median SSE: nice %.3f, nasty %.3f; Mann-Whitney p=%.2g; Cliff's delta %.2f" % (b.median(), a.median(), mannwhitneyu(a, b).pvalue, cliff(a, b)))
q = r[r.dd_to_c <= 0.5]; a, b = q[q.label == "nasty"].sse_median, q[q.label == "nice"].sse_median
P("without DD->C > 0.5 (%d dropped: %d nasty, %d nice): nice %.3f, nasty %.3f; p=%.2g" % (
    len(r) - len(q), ((r.dd_to_c > 0.5) & (r.label == "nasty")).sum(), ((r.dd_to_c > 0.5) & (r.label == "nice")).sum(), b.median(), a.median(), mannwhitneyu(a, b).pvalue))
P("spearman SSE vs mean rank: all %.2f; top 100 %.2f" % (r.sse_median.corr(r.mean_norm_rank, method="spearman"),
                                                          r.head(100).sse_median.corr(r.head(100).mean_norm_rank, method="spearman")))
P("\ntop 20:\n" + r.head(20)[["place", "Name", "label", "sse_median", "coop", "score"]].round(3).to_string(index=False))
open(out + "niceness_sse.txt", "w").write("\n".join(lines)); print("\n".join(lines))
