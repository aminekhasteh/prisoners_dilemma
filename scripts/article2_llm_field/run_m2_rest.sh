#!/usr/bin/env bash
# Memory-2 runs at the remaining standard lengths (77, 151, 156, 308). Waits until both run_all.sh (memory-1 pairs)
# and run_m2_all.sh (the 63-turn memory-2 runs) have finished, then runs standard at all five lengths; the saved
# 63-turn pairs are reused. Resumable: rerun the same command after a stop.
# Usage: ./run_m2_rest.sh [processes]   (log: results_m2/run_m2_rest.log)
set -uo pipefail
cd "$(dirname "$0")"
PY=~/.local/share/axelrod-probe-venv/bin/python
P=${1:-4}
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
mkdir -p results_m2
ts() { TZ=America/New_York date '+%F %I:%M %p %Z'; }
busy() { pgrep -f "run_all.sh" >/dev/null || pgrep -f "run_m2_all.sh" >/dev/null; }
if busy; then
    echo "=== $(ts) waiting for run_all.sh and run_m2_all.sh to finish"
    while busy; do sleep 600; done
fi
echo "=== $(ts) start: standard (all lengths)"
nice -n 10 "$PY" run_m2_field.py standard --processes "$P"
echo "=== $(ts) exit $?: standard (all lengths)"
echo "=== all done"
