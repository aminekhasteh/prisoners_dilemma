# Article 2 figures

Scripts that draw the figures and cover for "How Nice Are Chatbots, According to Game Theory?". They only draw: the
tournament numbers come from `scripts/article2_llm_field/` (branch `article2-llm-field`), and the LLM strategies from
Pal et al. 2026 (arXiv 2601.09849), Table S12. Every rank comes from one field, the final 307 players (Knight et al.'s 272 and all 35 chatbot strategies,
`scripts/article2_llm_field/results_m3`). Small inputs are kept in `data/` so every figure redraws in seconds.

```
bash make_all.sh OUT_DIR                 # redraw everything from data/
bash make_all.sh OUT_DIR RESULTS_DIR     # refresh data/ from the final results (results_m3, 307 players), then redraw
```

| Script | Output | Inputs |
|---|---|---|
| `cover.py ... --new=data/new_llm_memory1.csv` | `article2_cover.png` (wide cover, same format as Article 1's: key on the left, the eleven chatbots' strategies as chance bars on the right, grouped by maker) | `data/llm_strategies.csv`, `data/new_llm_memory1.csv` |
| `cover.py` | `article2_cover_five.png` (the earlier layout: Pal et al.'s five chatbots, each with its closest classic) | `data/llm_strategies.csv` |
| `llm_strategies.py` | `llm_strategies.png` (the five strategies as numbers with chance bars, laid out like Article 1's `sse_math_p.png`) | `data/llm_strategies.csv` |
| `llm_strategies.py ... --new=data/new_llm_memory1.csv` | `new_llm_strategies.png` (the six newer models, grouped by maker under their Pal et al. predecessors) | `data/llm_strategies.csv`, `data/new_llm_memory1.csv` (copied from branch `claude/project-thread-xnwceg`, `scripts/article2_llm_field/new_llm_memory1.csv`) |
| `llm_strategies.py ... --winners=data/winners.csv` | adds a "Tournament winners" group to either strategy figure: the winner of each setting (no noise, 1% and 5% noise), with its chances measured from play and a line saying what it won | `data/winners.csv` |
| `llm_sse.py` | `llm_sse.png` (every chatbot strategy in the 307-player field, best first, with its SSE and nice / nasty label; classic strategies slotted in at their rank) | `data/sse_llm.csv`, `data/sse_field.csv` |
| `prep_sse.py LLM_SSE_CSV KNIGHT_DATA_DIR KNIGHT_SSE_CSV RANKS_CSV data` | `data/sse_llm.csv` (from `results_m3/llm_sse.csv`, PR #22: SSE from play, nice rule), `data/sse_field.csv` (Knight's 272 at 63 turns: median SSE, Article 1's nice / nasty group, rank in the 307 field) | see the script's docstring |
| `prep_winners.py KNIGHT_DATA_DIR data [RESULTS_DIR ...]` | `data/winners.csv` (Initial_C_rate and CC/CD/DC/DD_to_C_rate of each winner, averaged over Knight et al.'s 63-turn summaries, plus the label drawn under its name). With results folders it recounts each winner's first places and stops if a label is no longer true | `Data/knight2026/src/data/full_tournament*/full_63_turns_*_summary.csv`, `results*/*_per_tournament.csv` |
| `llm_rank_63.py` | `llm_rank_63.png` (all 307 players, mean rank vs mean score per turn, 63 turns, no noise; Pal et al.'s five as coloured diamonds, the other chatbot strategies as grey ones, zoom on GPT-5 and Gemini) | `data/field_63.csv` |
| `llm_rank_lines.py ... noise` | `llm_rank_noise.png` (mean rank at 0, 1 and 5% noise, 63 turns) | `data/ranks_by_setting.csv` |
| `llm_rank_lines.py ... length` | `llm_rank_by_length.png` (mean rank at 63, 77, 151, 156 and 308 turns, no noise) | `data/ranks_by_setting.csv` |
| `llm_m1_vs_m2.py` | `llm_m1_vs_m2.png` (one dumbbell per model: rank out of 307 as memory-1 vs memory-2; one panel per setting in the data: 63 turns, mean over the five lengths, 1% and 5% noise; where the two ranks are within five places, the filled diamond is drawn small inside the hollow one) | `data/m2_ranks.csv` |
| `llm_rank_lines.py data/ranks_by_setting.csv noise\|length --m2` | `llm_rank_noise_m2.png`, `llm_rank_by_length_m2.png` (memory-2 players as bold lines with hollow diamonds, memory-1 faded behind) | `data/ranks_by_setting.csv` |
| `llm_new_rank.py` | `llm_new_rank.png` (one row per model grouped by maker, a line through its memory-1, memory-2 and memory-3 ranks; one panel per setting in the data, two by two: 63 turns, mean over the five lengths, 1% and 5% noise) | `data/new_ranks.csv` |
| `llm_new_rank_lines.py ... noise\|length` | `new_llm_rank_noise.png`, `new_llm_rank_by_length.png` (the new models that mostly cooperate as lines, Claude Opus 5.5's memory-2 and memory-3 strategies in bold ink, GPT-5 and Claude Sonnet 4 memory-2 in their colours, Tit for Tat dashed; the two models that mostly defect are named in a note) | `data/new_ranks.csv` |
| `prep_new.py RESULTS_DIR data` | `data/new_ranks.csv` (one setting per game length, the mean over the lengths, and the two noise levels) | `results_m3/*_per_tournament.csv` |
| `prep_m2.py RESULTS_DIR data` | `data/m2_ranks.csv` | `results_m3/*_per_tournament.csv` |
| `prep_data.py RESULTS_DIR data [_m2]` | `data/field_63.csv`, `data/ranks_by_setting.csv` | `results/{standard,noise1,noise5}_per_tournament.csv` |

`data/llm_strategies.csv` is Table S12 of Pal et al. (also `pal2026_memory1_treatments.csv` on the run branch).
If a setting has fewer tournaments than planned (for example 308 turns while the run is still going), the length chart
says so under its x label.

Claims are checked before they are drawn: `prep_winners.py` recounts the winners' first places, and
`llm_new_rank_lines.py` checks what its two titles say against `data/new_ranks.csv`. Either stops with a message if
the data no longer supports the wording.

Visual code (`style.py`), shared with Article 1: DejaVu Sans, blue = cooperate, orange = defect, circle = cooperate,
square = defect, filled = the player, outline = the other player, a bar's blue share = chance of cooperating.
Strategies are diamonds. Each chatbot keeps one colour in every figure (never blue or orange); the set passes the
dataviz skill's `validate_palette.js --pairs all` with direct labels, so every chatbot mark is also labelled by name.
