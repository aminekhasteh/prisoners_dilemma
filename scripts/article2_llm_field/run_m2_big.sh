#!/usr/bin/env bash
# Memory-2 runs on boo-server-big (16 threads): no noise first (standard at 63 turns, then all five lengths, reusing the
# 63-turn pairs), then noise5 and noise1. Needs the memory-1 pairs in results/pairs (copied from boo-smol).
# Resumable: rerun the same command after a stop. Usage: ./run_m2_big.sh [processes]   (log: results_m2/run_m2_big.log)
set -uo pipefail
cd "$(dirname "$0")"
PY=~/.local/share/axelrod-probe-venv/bin/python
P=${1:-16}
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
mkdir -p results_m2
ts() { TZ=America/New_York date '+%F %I:%M %p %Z'; }
step() {
    echo "=== $(ts) start: $*"
    nice -n 10 "$PY" run_m2_field.py "$@" --processes "$P"
    echo "=== $(ts) exit $?: $*"
}
step standard --turns 63
cp results_m2/standard_per_tournament.csv results_m2/standard63_per_tournament.csv
cp results_m2/standard_summary.csv results_m2/standard63_summary.csv
step standard
step noise5
step noise1
echo "=== $(ts) all done"
