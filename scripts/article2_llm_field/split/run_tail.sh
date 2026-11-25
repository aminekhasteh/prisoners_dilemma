#!/usr/bin/env bash
# Runs on boo-smol. Works through queue.txt (taken from the END of boo-server-big's run order), one tournament at a
# time, and skips or abandons any tournament boo-server-big has started (big_has.txt, pushed by sync_big.sh).
# Finished pair files go to done/<results dir>/, which sync_big.sh pulls into big's pairs folders.
# queue.txt lines: <script> <results dir> <condition> <turns> <seed> <expected pairs>
set -uo pipefail
cd "$(dirname "$0")"; B=$PWD
PY=~/.local/share/axelrod-probe-venv/bin/python
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
ts() { TZ=America/New_York date '+%F %I:%M %p %Z'; }
big_has() { grep -qx "$1/$2" big_has.txt 2>/dev/null; }
while read -r script rdir cond turns seed want; do
    [[ -z "$script" || "$script" == \#* ]] && continue
    f="${cond}_${turns}t_seed${seed}_250reps.jsonl"
    if [[ -f "done/$rdir/$f" ]]; then continue; fi
    if big_has "$rdir" "$f"; then echo "=== $(ts) skip (big has it): $rdir/$f"; continue; fi
    echo "=== $(ts) start: $rdir/$f"
    mkdir -p "out/$rdir" "done/$rdir"
    (cd scripts/article2_llm_field && exec nice -n 10 "$PY" "$script" "$cond" --turns "$turns" --seeds "$seed" \
        --processes 4 --out "$B/out/$rdir") > "out/$rdir/${f%.jsonl}.log" 2>&1 &
    pid=$!
    while kill -0 "$pid" 2>/dev/null; do
        sleep 60
        if big_has "$rdir" "$f"; then
            echo "=== $(ts) big started $rdir/$f, abandoning it"; pkill -P "$pid"; kill "$pid"; wait "$pid"; continue 2
        fi
    done
    wait "$pid"
    n=$(python3 -c "import json,sys; print(len({(d['i'],d['j']) for d in map(json.loads, open(sys.argv[1])) if 'scores' in d}))" "out/$rdir/pairs/$f")
    if [[ "$n" == "$want" ]]; then
        cp "out/$rdir/pairs/$f" "done/$rdir/.$f.tmp" && mv "done/$rdir/.$f.tmp" "done/$rdir/$f"
        echo "=== $(ts) done: $rdir/$f ($n pairs, $(grep -o 'done in [0-9]* s' "out/$rdir/${f%.jsonl}.log"))"
    else
        echo "=== $(ts) INCOMPLETE: $rdir/$f has $n of $want pairs"
    fi
done < queue.txt
echo "=== $(ts) queue finished"
