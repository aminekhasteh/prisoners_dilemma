#!/usr/bin/env bash
# Redraw every Article 2 figure into OUT_DIR (default: figures/). The optional RESULTS_DIR refreshes data/ first; use
# the final results, scripts/article2_llm_field/results_m3 (307 players: Knight's 272 and all 35 chatbot strategies),
# so every rank in the post comes from the same field.
# Usage: bash make_all.sh [OUT_DIR] [RESULTS_DIR]
# data/winners.csv is not refreshed here: it needs Knight et al.'s data (see prep_winners.py).
set -euo pipefail
cd "$(dirname "$0")"
OUT=${1:-figures}; PY=${PY:-python3}
mkdir -p "$OUT"
if [ -n "${2:-}" ]; then $PY prep_data.py "$2" data; $PY prep_m2.py "$2" data; $PY prep_new.py "$2" data; fi
# the cover shows all eleven chatbots of the post; the earlier five-chatbot layout is kept as an alternative
$PY cover.py data/llm_strategies.csv "$OUT/article2_cover.png" --new=data/new_llm_memory1.csv --dpi=180
$PY cover.py data/llm_strategies.csv "$OUT/article2_cover_five.png" --dpi=180
$PY llm_strategies.py data/llm_strategies.csv "$OUT/llm_strategies.png" --winners=data/winners.csv
$PY llm_strategies.py data/llm_strategies.csv "$OUT/new_llm_strategies.png" --new=data/new_llm_memory1.csv --winners=data/winners.csv
$PY llm_rank_63.py data/field_63.csv "$OUT/llm_rank_63.png"
$PY llm_rank_lines.py data/ranks_by_setting.csv noise "$OUT/llm_rank_noise.png"
$PY llm_rank_lines.py data/ranks_by_setting.csv length "$OUT/llm_rank_by_length.png"
$PY llm_m1_vs_m2.py data/m2_ranks.csv "$OUT/llm_m1_vs_m2.png"
# the same lines with Pal et al.'s memory-2 strategies in front
$PY llm_rank_lines.py data/ranks_by_setting.csv noise "$OUT/llm_rank_noise_m2.png" --m2
$PY llm_rank_lines.py data/ranks_by_setting.csv length "$OUT/llm_rank_by_length_m2.png" --m2
# New models: needs data/new_ranks.csv (prep_new.py RESULTS_DIR data)
if [ -f data/new_ranks.csv ]; then
  $PY llm_new_rank.py data/new_ranks.csv "$OUT/llm_new_rank.png"
  $PY llm_new_rank_lines.py data/new_ranks.csv noise "$OUT/new_llm_rank_noise.png"
  # the by-length chart needs the longer games (standard_per_tournament.csv in RESULTS_DIR)
  if grep -q '^s308,' data/new_ranks.csv; then
    $PY llm_new_rank_lines.py data/new_ranks.csv length "$OUT/new_llm_rank_by_length.png"
  fi
fi
# SSE of every chatbot strategy next to classic ones (needs data/sse_llm.csv and data/sse_field.csv from prep_sse.py)
if [ -f data/sse_llm.csv ]; then $PY llm_sse.py data/sse_llm.csv data/sse_field.csv "$OUT/llm_sse.png"; fi
