# Eliciting an LLM's repeated-game strategy (Pal et al. 2026 replication)

Asks a model the prompts of Pal et al. (arXiv 2601.09849, SI section 4) many times per scenario and turns the
answers into a memory-1 strategy (p0 and P(C) after CC, CD, DC, DD, own move first) and a memory-2 strategy
(21 probabilities). The output CSVs have the same columns as `../article2_llm_field/pal2026_*.csv`, so the new
strategies can join the tournament the same way the paper's five did.

| File | What it does |
|---|---|
| `prompts.py` | Prompt templates and scenarios: `memory1` (5), `memory2` (21), `framing` (9 x 5), `stopping` (w, 4 x 5), `gains` (x = 0..10, 11 x 5) |
| `providers.py` | Async adapters for Anthropic, OpenAI (Responses API), OpenRouter (open-weight models such as Llama) and Gemini, a `fake` model for free testing, and the price table |
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
OPENROUTER_API_KEY=...
```

## Running

Use the repo `.venv` (it has `anthropic`, `openai` and `google-genai`). Always do a `--dry-run` first.

```
python elicit.py --provider fake --model fake --tag fake_test                      # free end-to-end test
python elicit.py --provider gemini --model gemini-3.1-flash-lite --temperature 0 --seed 42 --trials 50 --max-usd 1
python elicit.py --provider anthropic --model claude-opus-5-5 --effort low --limit 20 --max-usd 1   # cost probe
python elicit.py --provider openrouter --model meta-llama/llama-3.3-70b-instruct --tag llama-3.3-70b \
    --temperature 0 --top-p 1e-8 --experiments memory1,memory2,framing,stopping,gains --max-usd 3   # paper settings
python estimate.py llama-3.3-70b --compare llama-3.3-70b
```

## First result: Llama 3.3 70B does not reproduce the paper (2026-11-24)

Llama 3.3 70B via OpenRouter, 50 trials per scenario, memory-1 and memory-2 (1,300 calls; about $0.23 per run as actually billed by OpenRouter, $1.16 for all five, although the price table at the time said $0.04).
Memory-1 P(C), own move first; paper = Table S12.

| Run | p0 | CC | CD | DC | DD | Label |
|---|---|---|---|---|---|---|
| Paper (temperature 0, top_p 1e-8) | 1.00 | 1.00 | 0.26 | 0.98 | 0.56 | ~GTFT |
| `llama-3.3-70b`: our clean wording, temperature 0 | 1.00 | 1.00 | 0.00 | 0.04 | 1.00 | WSLS |
| `_si`: SI wording verbatim ("point(s)"), temperature 0 | 1.00 | 1.00 | 0.00 | 0.88 | 1.00 | ~Forgiver |
| `_si_space`: SI wording as one paragraph, temperature 0 | 1.00 | 1.00 | 0.00 | 0.18 | 1.00 | ~WSLS |
| `_si_t07`: SI wording, temperature 0.7 | 1.00 | 1.00 | 0.00 | 0.72 | 1.00 | ~Forgiver |
| `_t1`: clean wording, default temperature | 1.00 | 1.00 | 0.00 | 0.04 | 1.00 | WSLS |

All runs agree with the paper on the first move and after mutual cooperation, and all disagree after being exploited
(never forgives, paper 26%) and after mutual defection (always cooperates, paper 56%). Whether Llama cooperates after
exploiting the other agent swings from 4% to 88% with the wording ("1 point" vs "point(s)", line breaks). OpenRouter
spread the calls over six hosts, and hosts sometimes answered the same prompt differently (`stop_reason` records the
host). 16 to 18 of the 26 scenarios differ from the paper at p < 0.05 in every run.

## Llama follow-up: one host at a time, and the treatment tables (2026-11-24)

Paper wording verbatim (`PD_PROMPT_VARIANT=si`), temperature 0, top_p 1e-8, each run pinned to one OpenRouter host
(`--host`, no fallback). Cloudflare rejects these settings (HTTP 400). Memory-1 P(C), own move first:

| Host (weights) | p0 | CC | CD | DC | DD | Label | memory-2 scenarios that differ from the paper (p < 0.05) |
|---|---|---|---|---|---|---|---|
| Paper | 1.00 | 1.00 | 0.26 | 0.98 | 0.56 | ~GTFT | |
| DeepInfra (fp8) | 1.00 | 1.00 | 0.00 | 0.00 | 1.00 | WSLS | 14 of 21 |
| AkashML (fp8) | 1.00 | 1.00 | 0.00 | 0.38 | 1.00 | ~WSLS | 15 of 21 |
| Parasail (fp8) | 1.00 | 1.00 | 0.00 | 0.50 | 1.00 | ~WSLS | 11 of 21 |
| Amazon Bedrock | 1.00 | 1.00 | 0.00 | 0.72 | 1.00 | ~Forgiver | 15 of 21 |
| Groq | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | Forgiver | 16 of 21 |
| CoreWeave (fp16) | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | Forgiver | 11 of 21 |

- Every host gives CD = 0 and DD = 1 (paper 0.26 and 0.56). DC, cooperating after exploiting the other agent, goes
  from 0 to 1 depending on the host, so for this model it is a knife-edge choice.
- Temperature 0 is not deterministic on these hosts: 2 to 10 of the 26 scenarios get mixed answers within one host.

Treatment tables on Amazon Bedrock (`llama_si_bedrock_treatments`, 6,000 calls; full listing in
`logs/bedrock_treat_compare.txt`): framings differ from the paper in 12 of 45 cells, stopping probabilities in 8 of
20, payoff costs x in 23 of 55. The cooperative framings match almost cell for cell ("Think about fair outcomes"
5 of 5, "Accumulate many points, but do not exploit" 5 of 5, "keep in mind the other's welfare" 4 of 5), and
"Exploit the other agent as much as possible" gives ALLD in both. That pins down the answer coding (L = cooperate,
own move first): with the coding reversed those cells could not match. The differences are in the competitive
framings (ours defect from round 1, the paper's Llama opens with cooperation and then plays GRIM) and in the
stopping-probability prompts (paper GRIM, ours Forgiver).

## New models: core runs and the strategies for the tournament (2026-11-24)

Six models, memory-1 and memory-2, 50 trials per scenario in each of the two wordings (`clean` and `si`), default
API settings (Claude: no sampling parameters, default effort and thinking; GPT-6: default reasoning). 15,600 calls,
$14.24 in total (Opus 5.5 $8.56). `combine.py` adds the two wordings' counts (100 trials per scenario) and writes
`../article2_llm_field/new_llm_memory1.csv` and `new_llm_memory2.csv` (same columns as `pal2026_memory2.csv`);
`results/wording_comparison.csv` tests clean against si for every scenario.

| Model | p0 | CC | CD | DC | DD | Label | Scenarios where the wordings differ (p < 0.05) |
|---|---|---|---|---|---|---|---|
| Claude Opus 5.5 | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | Forgiver | 0 of 26 |
| Claude Sonnet 5.5 | 0.00 | 0.11 | 0.00 | 0.00 | 0.00 | ~ALLD | 3 of 26 |
| Claude Haiku 5.5 | 1.00 | 1.00 | 0.00 | 0.00 | 0.00 | GRIM | 3 of 26 |
| GPT-6.1 Sol | 1.00 | 1.00 | 0.00 | 0.51 | 0.00 | between TFT and GRIM | 2 of 26 |
| GPT-6.1 Terra | 1.00 | 1.00 | 0.00 | 0.25 | 0.00 | ~GRIM | 1 of 26 |
| GPT-6 Luna | 0.12 | 0.55 | 0.01 | 0.09 | 0.18 | ~ALLD | 3 of 26 |

Unlike Llama 3.3 70B, the new models barely move between the two wordings: the memory-1 vectors differ by at most
0.22 (Sonnet after CC), and Opus gives identical answers in all 26 scenarios.

## Gemini 2.5 Pro check, memory-1 only (2026-11-24)

Paper wording verbatim, temperature 0, seed 42, default thinking (median 1,170 reasoning tokens per answer), via
OpenRouter (all calls served by Google AI Studio), 250 calls, $4.30. OpenRouter limits new accounts to 20 requests a
minute for this model, so use `--concurrency 3`.

| Run | p0 | CC | CD | DC | DD | Label |
|---|---|---|---|---|---|---|
| Paper (Table S12) | 0.82 [0.69, 0.90] | 1.00 | 0.00 | 0.02 [0.00, 0.10] | 0.42 [0.29, 0.56] | ~WSLS |
| Ours (`gemini-2.5-pro_si`) | 1.00 [0.93, 1.00] | 1.00 | 0.00 | 0.72 [0.58, 0.83] | 0.70 [0.56, 0.81] | ~Forgiver |

Same after CC and after being exploited; different on the first move (p = 0.003), after exploiting the other agent
(p < 0.001) and after mutual defection (p = 0.008). As with Llama, the gaps are in the cells that decide between
WSLS/Grim-like and Forgiver-like play.
