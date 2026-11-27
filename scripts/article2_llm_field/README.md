# Article 2: five LLM strategies in Knight et al.'s 272-player field

Adds five memory-one strategies fitted to LLM play (Pal et al. 2026, arXiv 2601.09849, Table S12) to the 272 players of
Knight et al. 2025 (arXiv 2510.15438, Zenodo 17250038), giving 277 players, and ranks everyone the way Knight did.

| Player | p0 | P(C) after CC | CD | DC | DD | Close to |
|---|---|---|---|---|---|---|
| LLM: Claude Sonnet 4 | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | Forgiver |
| LLM: Gemini 2.5 Pro | 0.82 | 1.00 | 0.00 | 0.02 | 0.42 | WSLS |
| LLM: GPT-4o | 1.00 | 1.00 | 0.00 | 0.00 | 0.00 | Grim |
| LLM: GPT-5 | 1.00 | 1.00 | 0.00 | 0.54 | 1.00 | Forgiver |
| LLM: Llama 3.3 70B | 1.00 | 1.00 | 0.26 | 0.98 | 0.56 | GTFT |

p0 is the chance of cooperating in round 1. CD means "I cooperated, they defected". `axl.MemoryOnePlayer` only takes a
fixed first move, so `StochasticStartMemoryOne` draws the first move from the player's own seeded RNG.

## Settings (copied from Knight's `run_full_tournament*.py`)

Default payoffs (3, 0, 5, 1); match lengths fixed but hidden from the players (`match_attributes={"length": inf}`);
250 repetitions per seed; self-interactions left out of the scores; ranked by the median over repetitions of each
player's mean score per turn (axelrod's `ResultSet.ranking`). Rank 1 is best; normalized rank = (rank - 1) / 276.

| Condition | Noise | Turns | Seeds (Knight's) | Knight tournaments |
|---|---|---|---|---|
| `standard` | 0 | 63, 77, 151, 156, 308 | 0 to 19 | 100 |
| `noise1` | 1% | 63 | 0, 2, 4-13, 19 | 13 |
| `noise5` | 5% | 63 | 2, 7, 10, 14, 15, 16, 18 | 7 |

These are the same 120 tournaments the knight272 rerun of Article 1 analysed.

## How it works

Only the new matches are played: each LLM player against the 272 and against the other four LLM players, 1,370 pairs
per tournament. The 272 x 272 part is read from Knight's files (`scores.gz`: each player's total in each repetition;
`cooperation_rates.gz`). For repetition r, a Knight player's new total is its Knight total plus what it scored in
repetition r against the five newcomers. Adding players to a round robin does not change the other matches, so this gives
the same ranking a full 277-player rerun would, without replaying the 37,000 old pairs. The script checks that
`scores.gz` reproduces Knight's `Median_score` before using it.

- The 63 original Fortran entries run from `libstrategies.so` (built from TourExec, see `../knight272/README.md`), with
  the same call as `../knight272/replay_moves.py`.
- Library players use axelrod 4.14 (Knight used 4.10). The Meta* players' teams are cut back to the strategies 4.10 had,
  which gives exactly Knight's team sizes (213, 146, 134, 79, 67, 36); every player's name is checked against
  `players.index`.
- `--validate N` replays N random pairs from Knight's field and compares them with Knight's payoff matrix. Against the
  standard 63-turn seed-0 file, 21 of 40 pairs matched exactly (deterministic ones) and none differed by more than 3
  standard errors; at 5% noise, 1 of 40 was just past 3 SE (k36r vs Appeaser, +0.04).
- `--figure-s1` checks the five S12 players against Pal et al.'s own tournament (SI Figure S1 B, p. 41): the
  game ends with probability w = 0.01 after every round, payoffs (3, 0, 5, 1), and self-play is included (each row
  sum covers all five opponents, a copy of itself among them). It compares the 25 pairwise payoffs first, then row
  sums and ranks. Each pair gets an exact Markov-chain value (E[total payoff] / E[length]) and `--reps` simulated
  matches from our engine (`axl.Match(prob_end=w)`). With `--reps 2000`: exact vs printed agrees in all 25 cells to
  one unit in the last printed digit (the table mixes rounding and truncation, e.g. 2.97916 is printed 2.9791), the
  simulated payoffs are within 3 SE of the exact ones in all 25, and the exact row sums and ranks equal the paper's.
  Output: `results/figure_s1_check.csv`. The two checks answer different questions: `--validate` tests the engine and
  the 272 against Knight's fixed-length tournament; `--figure-s1` tests that the LLM vectors are read and played the
  way Pal et al. meant them (orientation of CD/DC, first move, self-play convention).

## Running

Use the axelrod venv (`~/.local/share/axelrod-probe-venv/bin/python`); the repo's `.venv` has no axelrod. Set
`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`. Data and the Fortran library default to the main checkout
(`~/projects/prisoners_dilemma/Data/knight2026/src/data`, `article1/knight2026/lib/libstrategies.so`); override with
`--knight` and `--lib`.

```
python run_llm_field.py noise5                          # one condition, all its seeds, 250 reps
python run_llm_field.py standard --turns 63             # standard, 63 turns only
python run_llm_field.py standard --seeds 0 --turns 63 --reps 10 --out results/timing_runs   # quick check
python run_llm_field.py standard --validate 40 --reps 250
```

Raw new matches are appended to `results/pairs/*.jsonl` as each pair finishes (not in git), so a stopped run resumes
where it left off. At the end the script writes `results/<condition>_per_tournament.csv` (one row per player per
tournament: median and mean score per turn, rank, normalized rank, cooperation rate), `results/<condition>_summary.csv`
(means over tournaments, sorted by normalized rank) and `results/timing_<condition>.csv` (seconds per pair).
Runs with fewer than 250 repetitions get a `_<n>reps` suffix; with fewer repetitions, Knight's repetition r is paired
with new repetition r mod n.

## Timing on boo-server-smol (4 processes)

Small runs are in `results/timing_runs/`. Cost is linear in turns x repetitions: about 0.39 CPU-seconds, or 0.097
wall-seconds, per repetition-turn for all 1,370 new pairs. The 22 Meta*/NMWE* opponents take about 90% of it.

| Small run | Wall time |
|---|---|
| standard, 63 turns, seed 0, 10 reps | 62 s |
| standard, 308 turns, seed 0, 3 reps | 86 s |
| noise5, 63 turns, seed 10, 10 reps | 64 s |

| Full run (250 reps) | Estimated wall time |
|---|---|
| `noise5` (7 tournaments) | about 3 h |
| `noise1` (13 tournaments) | about 5.5 h |
| `standard`, 63 turns only (20 tournaments) | about 8.5 h |
| `standard`, all five lengths (100 tournaments) | about 100 h (4 days) |

Per standard length (20 seeds): 63 turns 8.5 h, 77 turns 10.5 h, 151 turns 20 h, 156 turns 21 h, 308 turns 41.5 h.

## Pal et al. 2026 tables beyond S12 (memory-2, framings, w, x)

Source: arXiv 2601.09849v1 (101-page PDF with the supplement; kept untracked at `Studies/2601.09849v1.pdf` in the main
checkout). `extract_pal2026.py` reads it with pypdf and writes the two CSVs below. In the paper L = cooperate and
R = defect, and an outcome "LR" means the LLM played L and the other agent played R; the CSVs write C/D with the
LLM's own move first (LR = CD).

| Paper table | PDF page (printed SI page) | What it is |
|---|---|---|
| S11 | 45 (23) | Memory-2 raw counts: times L was chosen out of 50, in 21 scenarios |
| S25 | 55-56 (33-34) | The same 21 numbers as means with Wilson intervals (the inferred memory-2 strategies) |
| S12 | 47 (25) | Memory-1, no framing (the five players already in the tournament) |
| S13-S21 | 47-50 (25-28) | Memory-1 under nine framing sentences; S22 (p. 50) summarises the strategy labels |
| S23 | 51 (29) | Memory-1 with a stated stopping probability w = 0.01, 0.1, 0.2, 0.5 |
| S24 | 51-54 (29-32) | Memory-1 in the equal-gains games, x = 0 to 10 |

Section 4.4 (p. 37, printed 15) has the memory-2 prompts. The memory-2 experiment re-asks round 1 and round 2 rather
than reusing S12, so its first-move numbers differ a little (Gemini cooperates first 45/50 times here, 41/50 in S12).
S11 counts / 50 match the S25 means in all 105 cells.

`pal2026_memory2.csv`: one row per model and scenario.
- `scenario`: `round1` (first move), `round2` (second move, given round 1's outcome in `prev1`), or `later` (any
  round from 3 on, given the outcome two rounds ago `prev2` and last round `prev1`).
- `count_C` out of `n` = 50 trials; `p_C` = count_C / n, the probability of cooperating.

`pal2026_memory1_treatments.csv`: one row per model and treatment, with `p0` and P(C) after `CC`, `CD`, `DC`, `DD`
(own move first) and the paper's label in `note`. `treatment` is `framing` (value = the added sentence, worded as in
Table S22), `stopping_w` or `equal_gains_x`.

### Memory-2 players (planned, not yet in run_llm_field.py)

A `MemoryTwoLLM(axl.Player)` with p0, four round-2 probabilities and sixteen later-round probabilities: move 1 uses
p0; move 2 looks up (own, opponent) in round 1; from move 3 on it looks up (round t-2 outcome, round t-1 outcome). Like
`StochasticStartMemoryOne`, it draws from its own seeded RNG and returns C/D directly when a probability is 0 or 1
(deterministic players are not seeded by `axl.Match`). Memory depth 2. Names like "LLM-m2: Claude Sonnet 4".

The natural design is a 282-player field: Knight's 272, the five memory-1 players and the five memory-2 players. Only
the memory-2 players' pairs are new (5 x 272 + 5 x 5 against memory-1 + 10 among themselves = 1,395 pairs). The
memory-1 pairs already played are reused, which needs `combine` to read two pair files per tournament.

`run_m2_field.py` now implements this (`MemoryTwoLLM`, players named "LLM-m2: ..."), importing `run_llm_field.py`
and writing to `results_m2/`. `run_m2_all.sh` waits for `run_all.sh` to finish, then runs the three 63-turn conditions
(about 17 h on 4 cores). A 2-repetition test at 5% noise ran end to end (1,395 new pairs merged with the memory-1 pairs
into a 282-player ranking).

## Pooled vs wording-specific players (memory-depth comparisons)

The newly elicited players in `run_new_field.py` and `run_m3_field.py` ("LLM: <model>", "LLM-m2: <model>") pool the
clean and SI wordings (100 trials per scenario). They are an explicitly labeled extension (`player_type` in
`new_llm_memory1.csv`), not a single prompt, and the two wordings can disagree: Llama 3.3 70B cooperates after DC
with probability 0.04 clean, 0.88 SI, 0.46 pooled. In memory-2 the clean prompt also corrects the SI's misprinted
opponent payoff, so the two wordings give different game information. The memory-3 players are clean only, and the
Sonnet 5.5 effort-xhigh variant has an SI memory-1 and clean memory-2/3, so neither the pooled field nor that
variant supports a claim about memory depth.

`../llm_strategy_elicitation/combine.py` also writes `new_llm_memory1_by_wording.csv` and
`new_llm_memory2_by_wording.csv` (one strategy per model and wording, from the saved replies; no API calls).
`run_wording_field.py --wording clean` puts clean memory-1, memory-2 and memory-3 players of the same seven models
in one field (272 + 21 = 293 players, 5,922 new pairs per tournament, all played by the script), so depth is the only
thing that changes between a model's three players. Output: `results_clean/`. A 2-repetition noise5 test ran end to
end. Expected time on boo-server-big at 16 processes, scaled from the 297-player run: about 16 min per 63-turn
tournament, so about 5.5 h for standard 63 turns, 2 h for noise5, 3.5 h for noise1, and about 2.5 days for all five
standard lengths.
