# Article 1 rerun on the 272 strategies of Knight et al. 2025

Data: Zenodo 17250038, unpacked to `Data/knight2026/` (not in git; see README.md). 272 players = 209 Axelrod-Python library strategies + the 63 original
Fortran entries of Axelrod's second tournament. 100 no-noise round robins (lengths 63, 77, 151, 156, 308; 20 seeds each;
250 repetitions) and 20 noisy ones at 63 turns (13 at 1% noise, 7 at 5%).

Run order: see README.md.

| Result | Article today (195 strategies, Glynatsi 2024 data) | Rerun (272 strategies, Knight 2025 data) |
|---|---|---|
| Tournaments | ~45,600, random subsets of 3 to 195 players | 120, always all 272 players |
| Winner, no noise (mean normalized rank) | Evolved FSM 16 | EvolvedLookerUp2_2_2 |
| Tit for Tat, no noise | 66th of 195 | 58th of 272 (the original Fortran entry, k92r) |
| Nice / nasty / end-game | 96 / 93 / 6 | 145 / 127 / 0 (match length is hidden, so end-game strategies never get to defect) |
| Nice in the top 20 | 18 (other 2 are end-game) | 20 |
| Nice in the top 100 | 91 | 96 |
| Median SSE, nice vs nasty | 0.09 vs 0.16, p < 0.001 | 0.05 vs 0.14, p < 0.001 |
| Same, without strategies that cooperate after mutual defection | gap gone, p = 0.37 | gap gone, p = 0.21 |
| R², unseen tournaments, no noise | 0.96 | 1.00 (same 272 players every time, so this test is trivial here) |
| R², unseen strategies, no noise | 0.75 | 0.76 |
| R², unseen strategies, noisy | 0.51 (noise up to 10%) | 0.64 (1% and 5% noise) |
| Top SHAP features, no noise | CC to C, then CD to C, SSE, DC to C | Cr / C_mean, CD to C, Cr / C_median, SSE, DC to C |
| Dropping Cr / C_median from the model | R² 0.882 to 0.879 | R² unchanged to three decimals |
| Rank gap, above vs below median cooperators, no noise | -0.12 | -0.24 (63 turns), -0.26 (all lengths) |
| Same at about 1% noise | -0.09 | -0.23 |
| Same at about 5% noise | +0.09 (2 to 5%), +0.24 (5 to 10%) | -0.10 |

Directions of the SHAP effects in the no-noise model are the same as in the article: high CC to C better, high CD to C
worse, low SSE better, low DC to C better, more memory better, stochastic worse.

Not reproducible from this data: probabilistic-ending settings, noise above 5%, random-subset tournaments, and the
figures built from move-by-move play for the 38 Fortran entries that have no Python version (needs gfortran).

Nice / nasty labels: read from the pairwise cooperation matrices (`niceness_from_matrix.py`). They agree with the old
replay-based labels on 184 of 185 strategies that have both; the exception is Knowledgeable Worse and Worse, which needs
to know the match length to defect.

## The 195-strategy model on strategies it never saw (`test_old_model.py`)

The XGBoost model trained on Glynatsi et al.'s no-noise tournaments (`Models/v2/model_no_noise_no_probend.json`, 195
strategies) predicts each strategy's normalized rank in Knight et al.'s 100 no-noise round robins. "New" = the 63 Fortran
entries plus 23 library strategies that are not among the 195. One point per strategy (mean over 100 tournaments).

| Strategies | n | R² | Spearman | Mean error |
|---|---|---|---|---|
| Seen (in the 195) | 186 | 0.84 | 0.94 | about 25 places |
| New, all | 86 | 0.63 | 0.81 | about 33 places |
| New, 1980 Fortran entries | 63 | 0.61 | 0.77 | about 31 places |
| New, library | 23 | 0.54 | 0.83 | about 38 places |

Worst misses: Bush Mosteller (actual 261st, predicted 174th), k53r (104th vs 16th), k57r (116th vs 29th),
UsuallyCooperates (153rd vs 270th), k52r (165th vs 83rd), k32r (28th vs 132nd). The model is a bit optimistic across the board
(mean error -0.07 for seen strategies, -0.06 for new ones); the new ones just scatter more. The 38 Fortran entries without a Python twin get memory depth inf and no use of game or length
(they keep their own state and only see the turn number and scores); leaving these unknown dropped new-strategy R² to 0.45.
Knight's runs are outside the training range: 63 to 308 turns (trained on 1 to 200), 250 repetitions (10 to 100), 272 players (3 to 195).
