"""How the tournament winners actually play, as the same five chances as the LLM strategies.
The winners are not memory-one strategies, so these are measured averages: Knight et al.'s per-tournament summary
columns Initial_C_rate and CC/CD/DC/DD_to_C_rate (chance of cooperating after each outcome, own move first), averaged
over that setting's 63-turn tournaments in their 272-player field.

One winner per setting, the same in every field we ran (277, 282, 297 and the final 307 players):
  no noise  EvolvedLookerUp2_2_2 has the best mean rank over the 100 no-noise tournaments. In the final 307-player
            field it finishes first in all 100 (in the smaller fields: 62, 63 and 100, and in every one with games of
            151 turns or more; Evolved FSM 16 took the others, all at 63 and 77 turns).
  1% noise  Evolved FSM 16 Noise 05 finishes first in all 13 tournaments.
  5% noise  DBS finishes first in all 7 tournaments.
The figure's labels (label, label2 in data/winners.csv) say exactly this. Pass the results folders to re-check the
counts: the script stops if a label no longer holds.

Usage: python3 prep_winners.py KNIGHT_DATA_DIR data [RESULTS_DIR ...]
       KNIGHT_DATA_DIR = Data/knight2026/src/data; RESULTS_DIR = scripts/article2_llm_field/results, results_m2, ..."""
import sys, glob
from pathlib import Path
import pandas as pd

K, OUT = Path(sys.argv[1]), Path(sys.argv[2])
# (setting, Knight folder, player, setting label, label line 1, label line 2)
WIN = [("s63", "full_tournament", "EvolvedLookerUp2_2_2", "no noise",
        "won every tournament without noise", ""),
       ("n1", "full_tournament_1_percent_noise", "Evolved FSM 16 Noise 05", "1% noise",
        "won every tournament at 1% noise", ""),
       ("n5", "full_tournament_5_percent_noise", "DBS: 0.75, 3, 4, 3, 5", "5% noise",
        "won every tournament at 5% noise", "")]


def check(res):
    """First places of the three winners in one results folder; stops if a figure label is not true there."""
    std = res / "standard_per_tournament.csv"
    std = pd.read_csv(std if std.exists() else res / "standard63_per_tournament.csv")
    first = lambda d, name: d[(d["rank"] == 1) & (d.Name == name)].groupby("turns").size()
    played = lambda d: d.groupby("turns").seed.nunique()
    out = []
    for key, _, name, label, *_ in WIN:
        if key == "s63":
            d = std
        elif (res / ("noise%s_per_tournament.csv" % key[1])).exists():
            d = pd.read_csv(res / ("noise%s_per_tournament.csv" % key[1]))
        else:
            continue
        won, n = first(d, name).reindex(played(d).index, fill_value=0), played(d)
        ok = (won == n).all()                                      # every label says "won every tournament"
        out.append("%s: %d of %d" % (label, won.sum(), n.sum()))
        if not ok:
            sys.exit("%s: the label for %s (%s) does not hold: first in %s of %s tournaments by game length"
                     % (res, name, label, won.to_dict(), n.to_dict()))
    print("%s  first places  %s" % (res, "; ".join(out)))


rows = []
for key, folder, name, label, line1, line2 in WIN:
    fs = [f for f in glob.glob(str(K / folder / "full_63_turns_*_summary.csv")) if "/._" not in f]
    x = pd.concat([pd.read_csv(f) for f in fs])
    r = x[x.Name == name]
    rows.append(dict(setting=key, setting_label=label, Name=name, tournaments=len(r),
                     p0=r.Initial_C_rate.mean(), CC=r.CC_to_C_rate.mean(), CD=r.CD_to_C_rate.mean(),
                     DC=r.DC_to_C_rate.mean(), DD=r.DD_to_C_rate.mean(), label=line1, label2=line2))
for res in sys.argv[3:]:
    check(Path(res))
w = pd.DataFrame(rows)
w.to_csv(OUT / "winners.csv", index=False, float_format="%.4f")
print(w.round(3).to_string(index=False))
