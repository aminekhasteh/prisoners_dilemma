# Article 2 figures

Scripts that draw the figures and cover for "How Nice Are Chatbots, According to Game Theory?". They only draw: the
tournament numbers come from `scripts/article2_llm_field/` (branch `article2-llm-field`), and the LLM strategies from
Pal et al. 2026 (arXiv 2601.09849), Table S12. Small inputs are kept in `data/` so every figure redraws in seconds.

```
bash make_all.sh OUT_DIR                 # redraw everything from data/
bash make_all.sh OUT_DIR RESULTS_DIR     # refresh data/ from the run's results/ first, then redraw
```

| Script | Output | Inputs |
|---|---|---|
| `cover.py` | `article2_cover.png` (wide cover, same format as Article 1's: key on the left, the five strategies as chance bars on the right) | `data/llm_strategies.csv` |
| `llm_strategies.py` | `llm_strategies.png` (the five strategies as numbers with chance bars, laid out like Article 1's `sse_math_p.png`) | `data/llm_strategies.csv` |
| `llm_strategies.py ... --new=data/new_llm_memory1.csv` | `new_llm_strategies.png` (the six newer models, grouped by maker under their Pal et al. predecessors) | `data/llm_strategies.csv`, `data/new_llm_memory1.csv` (copied from branch `claude/project-thread-xnwceg`, `scripts/article2_llm_field/new_llm_memory1.csv`) |
| `llm_rank_63.py` | `llm_rank_63.png` (all 277 players, mean rank vs mean score per turn, 63 turns, no noise; LLMs as diamonds, zoom on GPT-5 and Gemini) | `data/field_63.csv` |
| `llm_rank_lines.py ... noise` | `llm_rank_noise.png` (mean rank at 0, 1 and 5% noise, 63 turns) | `data/ranks_by_setting.csv` |
| `llm_rank_lines.py ... length` | `llm_rank_by_length.png` (mean rank at 63, 77, 151, 156 and 308 turns, no noise) | `data/ranks_by_setting.csv` |
| `prep_data.py RESULTS_DIR data` | `data/field_63.csv`, `data/ranks_by_setting.csv` | `results/{standard,noise1,noise5}_per_tournament.csv` |

`data/llm_strategies.csv` is Table S12 of Pal et al. (also `pal2026_memory1_treatments.csv` on the run branch).
If a setting has fewer tournaments than planned (for example 308 turns while the run is still going), the length chart
says so under its x label.

Visual code (`style.py`), shared with Article 1: DejaVu Sans, blue = cooperate, orange = defect, circle = cooperate,
square = defect, filled = the player, outline = the other player, a bar's blue share = chance of cooperating.
Strategies are diamonds. Each chatbot keeps one colour in every figure (never blue or orange); the set passes the
dataviz skill's `validate_palette.js --pairs all` with direct labels, so every chatbot mark is also labelled by name.
