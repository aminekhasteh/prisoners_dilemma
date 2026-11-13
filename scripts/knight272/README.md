# Article 1 rerun on the 272 strategies of Knight et al. 2025

Redoes the Article 1 analysis on the tournament data from Knight, Campbell, Harper, Gaffney and Glynatsi (2025),
"Reviving, reproducing, and revisiting Axelrod's second tournament" (arXiv 2510.15438). Their 272 players are 209
Axelrod-Python strategies plus the 63 original Fortran entries of Axelrod's 1980 second tournament (k31r to k92r and
krandomc; k92r is Tit for Tat). Old-vs-new numbers are in `RESULTS.md`.

## Data (not in git)

Download `archive.tar.gz` (4.1 GB, md5 e89a21713394fc5834ad29edff8e6bd3) from Zenodo record 17250038
(https://zenodo.org/records/17250038) and unpack it to `Data/knight2026/` at the repo root. Unpacked it is 22 GB; only
`src/data/full_tournament*/` is used here. The parquet that `build_dataset.py` makes (`data/knight272.parquet`, 4 MB) is
not committed either; rerun step 2 to get it.

## Run order

All commands from this folder. Steps 1 and 9 need the axelrod library (4.14); the rest use the repo's `requirements.txt`.
Set `OPENBLAS_NUM_THREADS=1` on the 4-core server.

| Step | Command | Output |
|---|---|---|
| 1 | `python strategy_traits.py ../../Data/knight2026/src/data data/strategy_traits.csv` | traits for each of the 272 players |
| 2 | `python build_dataset.py ../../Data/knight2026/src/data data/strategy_traits.csv data/knight272.parquet` | one row per strategy per tournament, same columns as `Data/combined_dataset.parquet` (adds SSE and the cooperation ratios) |
| 3 | `python niceness_from_matrix.py ../../Data/knight2026/src/data data/niceness_matrix.csv` | nice / nasty from the pairwise cooperation matrices |
| 4 | `python results_niceness_sse.py data/knight272.parquet data/niceness_matrix.csv results/` | `results/ranking_standard.csv`, `results/niceness_sse.txt`, `results/sse_ranking_fullnames.csv`, `data/niceness.csv` |
| 5 | `python sse_circular.py data/knight272.parquet figures/sse_top20_circular.png results/sse_top20_circular.csv --top 20 --labels data/niceness.csv` (also `--top 100`, `--top all`) | the bar-style SSE rings |
| 6 | `python model_and_flip.py data/knight272.parquet results/ figures/` | XGBoost + SHAP and the noise flip: `results/holdout_r2.csv`, `shap_importance_ci.csv`, `noise_flip_summary.csv`, `figures/shap_standard.png` |
| 7 | `python make_figures.py results/ figures/` | `noise_flip_by_level.png`, `r2_by_setting.png`, `importance_all.png`, `importance_standard.png` |
| 8 | `python test_old_model.py data/knight272.parquet ../../Models/v2/model_no_noise_no_probend.json data/strategy_names_195.txt results/ figures/` | the 195-strategy model tested on the 86 strategies it never saw: `results/old_model_on_272.csv`, `figures/old_model_on_new_strategies.png` |
| 9 | `python replay_moves.py data/strategy_traits.csv data/niceness.csv data/cover_opponent_140.txt data/cover_moves_140.csv` | every player's 140 moves against the cover opponent |
| 10 | `python sse_moves_circular.py results/sse_ranking_fullnames.csv data/cover_moves_140.csv "$(cat data/cover_opponent_140.txt)" figures/sse_moves_circular.png` (add `--full`, or `--landscape --intro` for the cover) | the move ring and the cover |

Step 8 needs `Models/v2/model_no_noise_no_probend.json` from `scripts/train_and_explain.py`.

Step 9 calls the original Fortran. Build it once with gfortran (`sudo apt install gfortran`):
`git clone https://github.com/Axelrod-Python/TourExec && make -C TourExec && mkdir -p lib && cp TourExec/bin/libstrategies.so lib/`.
The script loads `lib/libstrategies.so` directly, so the axelrod-fortran package is not needed. As a check, k92r plays
exactly like Tit for Tat.

## Notes

- The archive's `*_cooperation_rates.gz` matrices are stored transposed (rows are the column player), and its folders
  contain macOS `._*` files, so the scripts glob `full_*`.
- 38 Fortran entries have no Python version. They get memory depth inf and no use of game or length: each function keeps
  its own state between calls and only sees the turn number and both scores.
- `sse_moves_circular.py` is the 272 copy of `scripts/article1_figures/sse_moves_circular.py`: smaller labels,
  parameter suffixes dropped, k92r bold as Tit for Tat, and legend rows only for groups that exist (there is no
  end-game group here, because match length is hidden from players).
