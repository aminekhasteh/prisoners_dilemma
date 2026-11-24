# Eliciting an LLM's repeated-game strategy (Pal et al. 2026 replication)

Asks a model the prompts of Pal et al. (arXiv 2601.09849, SI section 4) many times per scenario and turns the
answers into a memory-1 strategy (p0 and P(C) after CC, CD, DC, DD, own move first) and a memory-2 strategy
(21 probabilities). The output CSVs have the same columns as `../article2_llm_field/pal2026_*.csv`, so the new
strategies can join the tournament the same way the paper's five did.

| File | What it does |
|---|---|
| `prompts.py` | Prompt templates and scenarios: `memory1` (5), `memory2` (21), `framing` (9 x 5), `stopping` (w, 4 x 5), `gains` (x = 0..10, 11 x 5) |
| `providers.py` | Async adapters for Anthropic, OpenAI (Responses API) and Gemini, a `fake` model for free testing, and the price table |
| `elicit.py` | Runs the calls, appends every reply to `results/raw/<tag>.jsonl`, resumes, enforces `--max-usd` |
| `estimate.py` | Counts, Wilson intervals, strategy labels, CSVs, and `--compare` against the paper's numbers |

## Choices that differ from, or fill gaps in, the paper

- Each trial is one stateless call with system prompt "Follow specified goals". Only a bare `L` or `R` counts; any
  other reply is logged as invalid and the same trial is asked again (up to 3 times).
- The SI writes "you got [a] point(s)". We write "1 point" / "N points". The payoff table lines keep the SI's
  wording ("both of you get 1 points").
- In the memory-2 later-round prompt the SI gives the other agent the focal player's payoff for the previous round
  (an apparent typo); we use the other agent's actual payoff.
- Current Claude models do not accept `temperature` or `top_p`, and Claude Opus 5.5 always thinks, so Claude runs
  at default sampling (settings are saved with every reply). The paper used temperature 0 throughout.

## API keys

Keys live outside the repo in `~/.config/pd-llm/keys.env` (mode 600, checked at start-up):

```
ANTHROPIC_API_KEY=...
GEMINI_API_KEY=...
OPENAI_API_KEY=...
```

## Running

Use the repo `.venv` (it has `anthropic`, `openai` and `google-genai`). Always do a `--dry-run` first.

```
python elicit.py --provider fake --model fake --tag fake_test                      # free end-to-end test
python elicit.py --provider gemini --model gemini-3.1-flash-lite --temperature 0 --seed 42 --trials 50 --max-usd 1
python elicit.py --provider anthropic --model claude-opus-5-5 --effort low --limit 20 --max-usd 1   # cost probe
python estimate.py gemini-2.5-pro --compare gemini-2.5-pro
```
