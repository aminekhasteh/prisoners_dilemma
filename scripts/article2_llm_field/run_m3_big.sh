#!/usr/bin/env bash
# Memory-3 LLM strategies (run_m3_field.py, 304 players) on boo-server-big. Waits for run_new_big.sh to finish (it
# needs results_new/pairs and all cores), then runs the 63-turn conditions (standard, noise5, noise1) and standard at
# all five lengths. Resumable: rerun the same command after a stop.
# Usage: ./run_m3_big.sh [processes]   (log: results_m3/run_m3_big.log)
set -uo pipefail
cd "$(dirname "$0")"
PY=~/.local/share/axelrod-probe-venv/bin/python
P=${1:-16}
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
mkdir -p results_m3
ts() { TZ=America/New_York date '+%F %I:%M %p %Z'; }
if pgrep -f "run_new_big.sh" >/dev/null; then
    echo "=== $(ts) waiting for run_new_big.sh to finish"
    while pgrep -f "run_new_big.sh" >/dev/null; do sleep 300; done
fi
# $? must be saved before the echo: "$(ts)" in the same line resets it, so the old logs always said "exit 0".
FAILED=()
step() {
    echo "=== $(ts) start: $*"
    nice -n 10 "$PY" run_m3_field.py "$@" --processes "$P"
    local rc=$?
    echo "=== $(ts) exit $rc: $*"
    ((rc == 0)) || FAILED+=("[$*]")
    return $rc
}
step standard --turns 63 && cp results_m3/standard_per_tournament.csv results_m3/standard63_per_tournament.csv && cp results_m3/standard_summary.csv results_m3/standard63_summary.csv
step noise5
step noise1
step standard
if ((${#FAILED[@]})); then
    echo "=== $(ts) FAILED (rerun the same command to resume): ${FAILED[*]}"
    exit 1
fi
echo "=== $(ts) all done"
