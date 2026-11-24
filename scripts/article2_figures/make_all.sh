#!/usr/bin/env bash
# Redraw every Article 2 figure into OUT_DIR (default: figures/). Optional RESULTS_DIR refreshes data/ first.
# Usage: bash make_all.sh [OUT_DIR] [RESULTS_DIR] [RESULTS_M2_DIR]
set -euo pipefail
cd "$(dirname "$0")"
OUT=${1:-figures}; PY=${PY:-python3}
mkdir -p "$OUT"
if [ -n "${2:-}" ]; then $PY prep_data.py "$2" data; fi
if [ -n "${3:-}" ]; then $PY prep_m2.py "$3" data; $PY prep_data.py "$3" data _m2; fi
$PY cover.py data/llm_strategies.csv "$OUT/article2_cover.png" --dpi=180
$PY llm_strategies.py data/llm_strategies.csv "$OUT/llm_strategies.png"
$PY llm_strategies.py data/llm_strategies.csv "$OUT/new_llm_strategies.png" --new=data/new_llm_memory1.csv
$PY llm_rank_63.py data/field_63.csv "$OUT/llm_rank_63.png"
$PY llm_rank_lines.py data/ranks_by_setting.csv noise "$OUT/llm_rank_noise.png"
$PY llm_rank_lines.py data/ranks_by_setting.csv length "$OUT/llm_rank_by_length.png"
$PY llm_m1_vs_m2.py data/m2_ranks.csv "$OUT/llm_m1_vs_m2.png"
# 282-player versions with the memory-2 players (need data/ranks_by_setting_m2.csv: prep_data.py RESULTS_M2_DIR data _m2)
if [ -f data/ranks_by_setting_m2.csv ]; then
  $PY llm_rank_lines.py data/ranks_by_setting_m2.csv noise "$OUT/llm_rank_noise_m2.png"
  $PY llm_rank_lines.py data/ranks_by_setting_m2.csv length "$OUT/llm_rank_by_length_m2.png"
fi
