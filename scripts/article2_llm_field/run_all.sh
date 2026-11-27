#!/usr/bin/env bash
# Full Article 2 runs, in order: noise5, noise1, standard at 63 turns, then standard at all five lengths
# (the 63-turn pairs are already saved by then, so that last step only plays 77, 151, 156 and 308).
# Usage: ./run_all.sh [processes]   (log: results/run_all.log)
set -uo pipefail
cd "$(dirname "$0")"
PY=~/.local/share/axelrod-probe-venv/bin/python
P=${1:-4}
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
mkdir -p results
ts() { TZ=America/New_York date '+%F %I:%M %p %Z'; }
# $? must be saved before the echo: "$(ts)" in the same line resets it, so the old logs always said "exit 0".
FAILED=()
step() {
    echo "=== $(ts) start: $*"
    nice -n 10 "$PY" run_llm_field.py "$@" --processes "$P"
    local rc=$?
    echo "=== $(ts) exit $rc: $*"
    ((rc == 0)) || FAILED+=("[$*]")
    return $rc
}
step noise5
step noise1
step standard --turns 63
step standard
if ((${#FAILED[@]})); then
    echo "=== $(ts) FAILED (rerun the same command to resume): ${FAILED[*]}"
    exit 1
fi
echo "=== $(ts) all done"
