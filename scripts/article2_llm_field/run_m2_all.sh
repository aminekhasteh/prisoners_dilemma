#!/usr/bin/env bash
# Memory-2 runs for the three 63-turn conditions. Waits until run_all.sh has finished (it needs the memory-1 pairs and
# all 4 cores), then runs noise5, noise1 and standard at 63 turns. Resumable: rerun the same command after a stop.
# Usage: ./run_m2_all.sh [processes]   (log: results_m2/run_m2_all.log)
set -uo pipefail
cd "$(dirname "$0")"
PY=~/.local/share/axelrod-probe-venv/bin/python
P=${1:-4}
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
mkdir -p results_m2
ts() { TZ=America/New_York date '+%F %I:%M %p %Z'; }
if pgrep -f "run_all.sh" >/dev/null; then
    echo "=== $(ts) waiting for run_all.sh to finish"
    while pgrep -f "run_all.sh" >/dev/null; do sleep 600; done
fi
step() {
    echo "=== $(ts) start: $*"
    nice -n 10 "$PY" run_m2_field.py "$@" --processes "$P"
    echo "=== $(ts) exit $?: $*"
}
step noise5
step noise1
step standard --turns 63
echo "=== all done"
