# Article 2 figures

Scripts that draw the figures and cover for "How Nice Are Chatbots, According to Game Theory?". They only draw: the
tournament numbers come from `scripts/article2_llm_field/` (branch `article2-llm-field`), and the LLM strategies from
Pal et al. 2026 (arXiv 2601.09849), Table S12. Small inputs are kept in `data/` so every figure redraws in seconds.

```
bash make_all.sh OUT_DIR                 # redraw everything from data/
bash make_all.sh OUT_DIR RESULTS_DIR [RESULTS_M2_DIR] [RESULTS_NEW_DIR]   # refresh data/ from the runs' results first, then redraw
```

| Script | Output | Inputs |
|---|---|---|
| `cover.py` | `article2_cover.png` (wide cover, same format as Article 1's: key on the left, the five strategies as chance bars on the right) | `data/llm_strategies.csv` |
| `cover.py ... --new=data/new_llm_memory1.csv` | `article2_cover_eleven.png` (the same cover with all eleven chatbots of the post, grouped by maker) | `data/llm_strategies.csv`, `data/new_llm_memory1.csv` |
| `llm_strategies.py` | `llm_strategies.png` (the five strategies as numbers with chance bars, laid out like Article 1's `sse_math_p.png`) | `data/llm_strategies.csv` |
| `llm_strategies.py ... --new=data/new_llm_memory1.csv` | `new_llm_strategies.png` (the six newer models, grouped by maker under their Pal et al. predecessors) | `data/llm_strategies.csv`, `data/new_llm_memory1.csv` (copied from branch `claude/project-thread-xnwceg`, `scripts/article2_llm_field/new_llm_memory1.csv`) |
| `llm_strategies.py ... --winners=data/winners.csv` | adds a "Tournament winners" group to either strategy figure: the winner of each setting (no noise, 1% and 5% noise), with its chances measured from play and a line saying what it won | `data/winners.csv` |
| `prep_winners.py KNIGHT_DATA_DIR data [RESULTS_DIR ...]` | `data/winners.csv` (Initial_C_rate and CC/CD/DC/DD_to_C_rate of each winner, averaged over Knight et al.'s 63-turn summaries, plus the label drawn under its name). With results folders it recounts each winner's first places and stops if a label is no longer true | `Data/knight2026/src/data/full_tournament*/full_63_turns_*_summary.csv`, `results*/*_per_tournament.csv` |
| `llm_rank_63.py` | `llm_rank_63.png` (all 277 players, mean rank vs mean score per turn, 63 turns, no noise; LLMs as diamonds, zoom on GPT-5 and Gemini) | `data/field_63.csv` |
| `llm_rank_lines.py ... noise` | `llm_rank_noise.png` (mean rank at 0, 1 and 5% noise, 63 turns) | `data/ranks_by_setting.csv` |
| `llm_rank_lines.py ... length` | `llm_rank_by_length.png` (mean rank at 63, 77, 151, 156 and 308 turns, no noise) | `data/ranks_by_setting.csv` |
| `llm_m1_vs_m2.py` | `llm_m1_vs_m2.png` (one dumbbell per model: rank out of 282 as memory-1 vs memory-2; one panel per setting in the data: 63 turns, mean over the five lengths, 1% and 5% noise) | `data/m2_ranks.csv` |
| `llm_rank_lines.py data/ranks_by_setting_m2.csv noise\|length` | `llm_rank_noise_m2.png`, `llm_rank_by_length_m2.png` (282-player field: memory-2 players as bold lines with hollow diamonds, memory-1 faded behind) | `data/ranks_by_setting_m2.csv` |
| `llm_new_rank.py` | `llm_new_rank.png` (297-player field with the new models: one row per model grouped by maker, memory-1 vs memory-2 dumbbells; one panel per setting in the data, two by two: 63 turns, mean over the five lengths, 1% and 5% noise) | `data/new_ranks.csv` |
| `llm_new_rank_lines.py ... noise\|length` | `new_llm_rank_noise.png`, `new_llm_rank_by_length.png` (297-player field: the new models that mostly cooperate as lines, Claude Opus 5.5's memory-2 strategy in bold ink, GPT-5 and Claude Sonnet 4 memory-2 in their colours, Tit for Tat dashed; the two models that mostly defect are named in a note) | `data/new_ranks.csv` |
| `prep_new.py RESULTS_NEW_DIR data` | `data/new_ranks.csv` (one setting per game length, the mean over the lengths, and the two noise levels) | `results_new/*_per_tournament.csv` (297-player field) |
| `prep_m2.py RESULTS_M2_DIR data` | `data/m2_ranks.csv` | `results_m2/*_per_tournament.csv` (282-player field) |
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
