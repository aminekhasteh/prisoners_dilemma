#!/usr/bin/env bash
# Redraw every Article 2 figure into OUT_DIR (default: figures/). Optional RESULTS_DIR refreshes data/ first.
# Usage: bash make_all.sh [OUT_DIR] [RESULTS_DIR]
set -euo pipefail
cd "$(dirname "$0")"
OUT=${1:-figures}; PY=${PY:-python3}
mkdir -p "$OUT"
if [ -n "${2:-}" ]; then $PY prep_data.py "$2" data; fi
$PY cover.py data/llm_strategies.csv "$OUT/article2_cover.png" --dpi=180
$PY llm_strategies.py data/llm_strategies.csv "$OUT/llm_strategies.png"
$PY llm_rank_63.py data/field_63.csv "$OUT/llm_rank_63.png"
$PY llm_rank_lines.py data/ranks_by_setting.csv noise "$OUT/llm_rank_noise.png"
$PY llm_rank_lines.py data/ranks_by_setting.csv length "$OUT/llm_rank_by_length.png"
