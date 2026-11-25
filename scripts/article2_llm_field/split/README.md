# Splitting tournament runs across two servers

boo-server-big runs the tournaments in order (`run_new_big.sh`, then `run_m3_big.sh`). boo-smol, about 6.5 times slower,
takes whole tournaments from the **end** of that order, so the two machines meet in the middle and nothing running on
big has to be stopped.

Results are unchanged by where a pair is played: every match is seeded with
`SeedSequence([seed, turns, noise, i, j, repetition])`, so it depends only on the tournament and the two players.
Checked on 2026-11-25 by replaying 48 of big's pairs on boo-smol (memory-1, memory-2 and memory-3 players): scores and
cooperation rates were identical; only the `seconds` timing field differed.

| File | Runs on | What it does |
|---|---|---|
| `run_tail.sh` | boo-smol, tmux `split` | Plays the tournaments in `queue.txt` one at a time, skipping (or abandoning) any that big has started, according to `big_has.txt`. Finished, complete pair files go to `done/<results dir>/`. |
| `sync_big.sh` | boo-server-big, tmux `split` | Every 5 minutes, pushes the list of big's pair files to boo-smol as `big_has.txt`, and moves boo-smol's finished files into `results_new/pairs` or `results_m3/pairs` if big has not started them. When big reaches such a tournament it finds every pair done and skips it. |
| `queue.txt` | boo-smol | `<script> <results dir> <condition> <turns> <seed> <expected pairs>`, from the end of big's order backwards. |

Deployment: both scripts and the queue live in `~/projects/pd_split` on each machine. On boo-smol that folder also holds
a copy of `scripts/knight272` and the `article2_llm_field` code and CSVs (no results) under `scripts/`; the Knight data
and `libstrategies.so` come from boo-smol's main checkout. When the code changes, copy the changed files there and
check them against the commit (md5).

Logs: `~/projects/pd_split/run_tail.log` (boo-smol) and `~/projects/pd_split/sync_big.log` (big). Stop both tmux
`split` sessions when all runs are done.
