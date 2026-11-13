# Article 1 figures

Scripts that draw the figures and cover for the Substack post "How Nice Should You Be? Game Theory Has Some Thoughts".
They only draw: the numbers come from the analysis in `scripts/` (and, for the move sequences, a server-side replay).
Small inputs are kept in `data/` so every figure can be redrawn without rerunning the analysis.

| Script | Output | Inputs |
|---|---|---|
| `make_figures.py data OUT_DIR` | `noise_flip_by_level.png`, `r2_by_setting.png`, `importance_all.png` | `data/noise_flip_summary.csv`, `data/holdout_r2.csv`, `data/shap_importance_ci.csv` (copied from `Results/` on branches `revisit-normalized-rank` and `claude/project-thread-s27dmu`) |
| `old_model_on_new.py data/old_model_on_272.csv out.png` | `old_model_on_new_strategies.png` (predicted vs actual rank for the 272 strategies of Knight et al. 2025 (arXiv 2510.15438), from the model trained on the 195-strategy no-noise tournaments; strategies it never saw are highlighted) | `data/old_model_on_272.csv` |
| `payoffs.py out.png [--filled]` | `payoffs.png` (payoff matrix for one round, drawn with the same marks, palette and typeface as the ring: circle = cooperate, square = defect, Player 1 filled, Player 2 in outline; `--filled` fills both) | none |
| `sse_math_p.py out.png` | `sse_math_p.png` (a strategy as four numbers: its chance of cooperating after CC, CD, DC and DD, shown for Tit for Tat, Grudger, Win-Stay-Lose-Shift and RANDOM) | none |
| `sse_math_recipe.py out.png` | `sse_math_recipe.png` (how a zero-determinant strategy picks its next move: one column per outcome, points on tiles turned into a chance by the dials α and β; worked for Tit for Tat and Extort-2) | none (Knight et al. 2019, eqs. 6-9) |
| `sse_math_sheet.py out.png [--legs] [--az=-62] [--el=21]` | `sse_math_sheet.png` (every ZD strategy lies on the plane 3q₁ − 2q₂ − 2q₃ = 1, a triangle inside the cube of strategies; SSE is the squared distance to it, drawn for Grudger; `--legs` adds the three per-outcome gaps) | none (Knight et al. 2019, eqs. 12-14 and 17-21) |
| `sse_explained.py out.png` | `sse_explained.png` (SSE vs closest ZD twin) | none (Knight et al. 2019, eqs. 17-21) |
| `sse_circular.py Data/combined_dataset.parquet out.png [out.csv] [--top N\|all]` | `sse_all_circular.png`, `sse_top100_circular.png`, `sse_top20_circular.png` and the matching CSVs in `data/` | `Data/combined_dataset.parquet` from `scripts/prepare_data.py` |
| `sse_moves_circular.py data/sse_all_circular.csv data/cover_moves_140.csv OPP_SEQ out.png [--full] [--landscape]` | `sse_moves_circular.png`; `--landscape` gives `sse_moves_landscape.png` (the cover) | `data/sse_all_circular.csv`, `data/cover_moves_140.csv`; `OPP_SEQ` = contents of `data/cover_opponent_140.txt` |
| `covers/cover_moves.py data/cover_moves.csv data/sse_all_circular.csv out.png OPP_SEQ [--sample] [--labels] [--rotate]` | cover drafts (`cover_moves_*.png`) | `data/cover_moves.csv` (moves simulated on the server), `data/sse_all_circular.csv` |
| `covers/cover_ring.py data/sse_all_circular.csv out.png [title] [subtitle] [kicker]` | ring cover drafts (`cover_ring*.png`) | `data/sse_all_circular.csv` |
| `covers/cover_crown.py out.png` | crown cover draft | none |

`data/cover_moves*.csv` hold each strategy's moves against one fixed opponent (`label` = nice / nasty / end-game from the replay-based
"never defects first" check). They were made on the server; the replay script is not part of this folder.

`data/old_model_on_272.csv` has one row per strategy: its mean normalized rank in the 100 no-noise tournaments of Knight et al. 2025
(`actual`), the rank predicted by `Models/v2/model_no_noise_no_probend.json` (`pred`), and whether the model saw the strategy in
training (`group`). It was made on the server by the 272-strategy rerun; that script is not part of this folder.

The three `sse_math_*.py` figures use the payoff matrix's marks (circle = cooperate, square = defect, Player 1 filled, Player 2 in
outline) and add two conventions: a number on a grey tile is points, a number with a bar under it is a chance of cooperating
(the blue share of the bar). Strategies in the cube are drawn as diamonds, so they are not read as moves.
