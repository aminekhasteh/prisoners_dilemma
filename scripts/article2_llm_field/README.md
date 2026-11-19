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
