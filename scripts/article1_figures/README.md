# Article 1 figures

Scripts that draw the figures and cover for the Substack post "How Nice Should You Be? Game Theory Has Some Thoughts".
They only draw: the numbers come from the analysis in `scripts/` (and, for the move sequences, a server-side replay).
Small inputs are kept in `data/` so every figure can be redrawn without rerunning the analysis.

| Script | Output | Inputs |
|---|---|---|
| `make_figures.py data OUT_DIR` | `noise_flip_by_level.png`, `r2_by_setting.png`, `importance_all.png` | `data/noise_flip_summary.csv`, `data/holdout_r2.csv`, `data/shap_importance_ci.csv` (copied from `Results/` on branches `revisit-normalized-rank` and `claude/project-thread-s27dmu`) |
| `payoffs.py out.png [--filled]` | `payoffs.png` (payoff matrix for one round, drawn with the same marks, palette and typeface as the ring: circle = cooperate, square = defect, Player 1 filled, Player 2 in outline; `--filled` fills both) | none |
| `sse_explained.py out.png` | `sse_explained.png` (SSE vs closest ZD twin) | none (Knight et al. 2019, eqs. 17-21) |
| `sse_circular.py Data/combined_dataset.parquet out.png [out.csv] [--top N\|all]` | `sse_all_circular.png`, `sse_top100_circular.png`, `sse_top20_circular.png` and the matching CSVs in `data/` | `Data/combined_dataset.parquet` from `scripts/prepare_data.py` |
| `sse_moves_circular.py data/sse_all_circular.csv data/cover_moves_140.csv OPP_SEQ out.png [--full] [--landscape]` | `sse_moves_circular.png`; `--landscape` gives `sse_moves_landscape.png` (the cover) | `data/sse_all_circular.csv`, `data/cover_moves_140.csv`; `OPP_SEQ` = contents of `data/cover_opponent_140.txt` |
| `covers/cover_moves.py data/cover_moves.csv data/sse_all_circular.csv out.png OPP_SEQ [--sample] [--labels] [--rotate]` | cover drafts (`cover_moves_*.png`) | `data/cover_moves.csv` (moves simulated on the server), `data/sse_all_circular.csv` |
| `covers/cover_ring.py data/sse_all_circular.csv out.png [title] [subtitle] [kicker]` | ring cover drafts (`cover_ring*.png`) | `data/sse_all_circular.csv` |
| `covers/cover_crown.py out.png` | crown cover draft | none |

`data/cover_moves*.csv` hold each strategy's moves against one fixed opponent (`label` = nice / nasty / end-game from the replay-based
"never defects first" check). They were made on the server; the replay script is not part of this folder.
