#!/usr/bin/env bash
# New LLM strategies (run_new_field.py, 297 players) on boo-server-big. 63-turn conditions first (standard, noise5,
# noise1), then standard at all five lengths, reusing the 63-turn pairs. Needs results/pairs and results_m2/pairs.
# Resumable: rerun the same command after a stop. Usage: ./run_new_big.sh [processes]   (log: results_new/run_new_big.log)
set -uo pipefail
cd "$(dirname "$0")"
PY=~/.local/share/axelrod-probe-venv/bin/python
P=${1:-16}
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
mkdir -p results_new
ts() { TZ=America/New_York date '+%F %I:%M %p %Z'; }
# $? must be saved before the echo: "$(ts)" in the same line resets it, so the old logs always said "exit 0".
FAILED=()
step() {
    echo "=== $(ts) start: $*"
    nice -n 10 "$PY" run_new_field.py "$@" --processes "$P"
    local rc=$?
    echo "=== $(ts) exit $rc: $*"
    ((rc == 0)) || FAILED+=("[$*]")
    return $rc
}
step standard --turns 63 && cp results_new/standard_per_tournament.csv results_new/standard63_per_tournament.csv && cp results_new/standard_summary.csv results_new/standard63_summary.csv
step noise5
step noise1
step standard
if ((${#FAILED[@]})); then
    echo "=== $(ts) FAILED (rerun the same command to resume): ${FAILED[*]}"
    exit 1
fi
echo "=== $(ts) all done"
