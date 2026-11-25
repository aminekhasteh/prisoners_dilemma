"""How each setting's tournament winner actually plays, as the same five chances as the LLM strategies.
The winners are not memory-one strategies, so these are measured averages: Knight et al.'s per-tournament summary
columns Initial_C_rate and CC/CD/DC/DD_to_C_rate (chance of cooperating after each outcome, own move first), averaged
over that setting's tournaments in their 272-player field (63 turns). The winners are the rank-1 players in our
297-player results (the same player won every tournament of each setting).
Usage: python3 prep_winners.py KNIGHT_DATA_DIR data   (KNIGHT_DATA_DIR = Data/knight2026/src/data)"""
import sys, glob
from pathlib import Path
import pandas as pd

K, OUT = Path(sys.argv[1]), Path(sys.argv[2])
WIN = [("s63", "full_tournament", "EvolvedLookerUp2_2_2", "no noise"),
       ("n1", "full_tournament_1_percent_noise", "Evolved FSM 16 Noise 05", "1% noise"),
       ("n5", "full_tournament_5_percent_noise", "DBS: 0.75, 3, 4, 3, 5", "5% noise")]
rows = []
for key, folder, name, label in WIN:
    fs = [f for f in glob.glob(str(K / folder / "full_63_turns_*_summary.csv")) if "/._" not in f]
    x = pd.concat([pd.read_csv(f) for f in fs])
    r = x[x.Name == name]
    rows.append(dict(setting=key, setting_label=label, Name=name, tournaments=len(r),
                     p0=r.Initial_C_rate.mean(), CC=r.CC_to_C_rate.mean(), CD=r.CD_to_C_rate.mean(),
                     DC=r.DC_to_C_rate.mean(), DD=r.DD_to_C_rate.mean()))
w = pd.DataFrame(rows)
w.to_csv(OUT / "winners.csv", index=False, float_format="%.4f")
print(w.round(3).to_string(index=False))
