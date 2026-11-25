#!/usr/bin/env bash
# Runs on boo-server-big (tmux `split`). Every 5 minutes: tells boo-smol which tournaments big has started, and moves
# boo-smol's finished pair files into big's pairs folders when big has not started them. Big's runs read a pair file
# when they reach that tournament, find every pair done and skip it. Pair seeds depend only on (seed, turns, noise,
# i, j, repetition), so the results are the same as if big had played them.
set -uo pipefail
SMOL=aminekhasteh@100.121.18.5
F=~/projects/prisoners_dilemma/scripts/article2_llm_field
L=~/projects/pd_split
ts() { TZ=America/New_York date '+%F %I:%M %p %Z'; }
while true; do
    (cd "$F" && for d in results_new results_m3; do ls "$d/pairs" 2>/dev/null | sed "s|^|$d/|"; done) > "$L/big_has.txt"
    rsync -a --timeout=60 "$L/big_has.txt" "$SMOL:projects/pd_split/big_has.txt" || echo "=== $(ts) push failed"
    for d in results_new results_m3; do
        mkdir -p "$L/incoming/$d" "$F/$d/pairs"
        rsync -a --timeout=300 "$SMOL:projects/pd_split/done/$d/" "$L/incoming/$d/" 2>/dev/null
        for p in "$L/incoming/$d"/*.jsonl; do
            [[ -e "$p" ]] || continue
            b=$(basename "$p")
            [[ -e "$F/$d/pairs/$b" || -e "$L/merged/$d/$b" ]] && continue
            cp "$p" "$F/$d/pairs/.$b.tmp" && mv "$F/$d/pairs/.$b.tmp" "$F/$d/pairs/$b"
            mkdir -p "$L/merged/$d"; touch "$L/merged/$d/$b"
            echo "=== $(ts) merged from boo-smol: $d/$b"
        done
    done
    sleep 300
done
