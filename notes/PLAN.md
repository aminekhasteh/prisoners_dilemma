# Project plan: from IPD tournaments to LLM evals

**Goal:** rebuild my portfolio with an educational Substack series. It starts from my 2024
Iterated Prisoner's Dilemma analysis and extends it into evaluating LLMs as IPD players.

**Constraints:** 3 to 5 hours a week. At least 3 to 4 articles. Local models through Ollama
first; up to $200 for API models later, more if it's worth it.

**Audience and tone:** Substack readers, educational. Each article answers one question,
explains one idea and has about 3 charts.

**Machine:** M2 MacBook Air, 16 GB RAM. Fits quantized ~3 to 8B models. Expect about 0.5 to
1 s per LLM move.

---

## Article 1: Revisit, fix and repost (weeks 1 to 3) — in progress

Repost the Medium article on Substack with a corrected analysis and a teaser for the LLM work.

- [x] Clone the repo to `~/Desktop/prisoners_dilemma`, branch `revisit-normalized-rank`
- [x] Python 3.12 venv, pinned `requirements.txt` (macOS needs `brew install libomp`)
- [x] `scripts/download_data.py`: Zenodo record 10246247 (~1.75 GB, 45,686 tournaments)
- [x] `scripts/prepare_data.py`: combine the 4 datasets into a parquet file (4,011,653 rows)
- [x] `scripts/train_and_explain.py`:
  - [x] Target: `Normalized_Rank` = Rank / (N − 1), the paper's target (was raw `Rank`)
  - [x] Train/test split grouped by tournament seed
  - [x] Remove `StandardScaler` (the old SHAP values were computed on unscaled inputs for a
        model trained on scaled ones)
  - [x] 95% bootstrap intervals for mean |SHAP|
  - [x] Ablation table (`Results/ablation.csv`)
- [x] Push the branch
- [x] Draft the revised article: `article/tit_for_tat_revisited.md`
- [ ] Review and edit the draft in my own voice
- [ ] Optional: one clean side-by-side chart of the noise flip (Cᵣ / C_median)
- [ ] Commit the final draft, merge the branch (PR)
- [ ] Publish on Substack (upload images, add the "originally published on Medium" note)

**Key results so far**
- R² (all data): 0.72 → **0.88** from switching the target. Splitting by seed barely mattered
  (0.884 → 0.882).
- R² by setting (v2): 0.96 standard, 0.94 noise, 0.91 probabilistic ending, 0.78 both.
  The paper's linear models: 0.37 to 0.54.
- Standard setting: be nice (CC→C high), be provokable (CD→C low), be a little envious
  (low SSE), keep defecting after exploiting (DC→C low), be clever (memory, uses length).
- **Headline:** with noise, cooperating more than the median player goes with a *worse*
  rank. Winners sit in the middle of the pack.
- Caveats: the model describes how winners behave and doesn't predict who will win;
  the Cᵣ ratio features are correlated; the intervals only cover variation across tournaments.

---

## Article 2: An LLM joins the tournament (weeks 4 to 7)

Question: *How do LLMs play the IPD, and which classic strategy do they look like?*

- [ ] Install Ollama; pull 2 to 3 small models from different families
- [ ] Check that the Axelrod library (v4.14.0) installs on Python 3.12
- [ ] `LLMPlayer(axl.Player)`:
  - [ ] Creates the client lazily inside `strategy()` (Axelrod clones players and runs
        matches in separate processes, so a stored client breaks both)
  - [ ] Strict C/D parsing with a fallback; count parse failures
  - [ ] Cache responses keyed by (model, prompt, history)
  - [ ] Freeze the prompt template, model tags, temperature and seeds
- [ ] Pilot: about 20 representative opponents (TFT, Grudger, WSLS, Random, Defector,
      Cooperator, the evolved FSM/HMM/LookerUp strategies), standard setting, short matches
- [ ] Compute the behavioral profile for each LLM: CC/CD/DC/DD→C rates, Cᵣ, SSE
- [ ] Find the nearest classic strategies by behavioral profile ("plays like Grudger")
- [ ] **Decision point:** if the small models play badly (always C, always D or
      unparseable), write that up as a finding and consider a bigger model

**Estimated cost:** about 20 opponents × 50 turns × 3 repeats ≈ 3,000 calls, roughly
30 to 60 minutes per model per condition, run locally. Free.

---

## Article 3: Stress tests (weeks 8 to 10)

Question: *Do LLMs adapt like winning strategies do?*

- [ ] Noise (pₙ) and probabilistic ending (pₑ) conditions
- [ ] Framing: named "prisoner's dilemma" vs. a neutral business scenario
      (does the model rely on memorized game theory?)
- [ ] Use the Article 1 SHAP models to explain *why* each LLM's rank shifts
- [ ] Check: does the LLM "read the room" under noise, like the winners do?

---

## Article 4: Pick one (weeks 11 to 14)

- **Option A: does thinking make it meaner?** Reasoning on vs. off, testing CoopEval's
  finding (2026) that stronger reasoners cooperate less.
- **Option B: LLM as strategy designer.** Have an LLM write a strategy from the paper's five
  lessons, test it in the tournament, and submit it to Axelrod-Python (the original
  article's "future work").

Budget: this is where to add 1 or 2 frontier models via API. Estimate the cost from the
pilot's real call counts before spending anything.

---

## Guardrails

- Freeze everything for each article (model tags, seeds, prompts) so readers can reproduce it.
- If a week's work doesn't produce a chart, cut scope rather than stretch the timeline.
- Report negative and null results (like the seed split not mattering).
- Frame results as description ("winners tend to…"), not causation.

## Related work to cite or position against

- Glynatsi, Knight & Harper (2024), *Properties of Winning IPD Strategies*: the dataset and baseline
- γ-Bench / GAMA-Bench (ICLR 2025): aggregate game-theory scores for LLMs
- CoopEval (arXiv 2604.15267, 2026): LLM vs. LLM cooperation mechanisms; reasoning lowers cooperation
- SPARC: LLMs predicting the behavior of Axelrod strategies from their code
- Evaluating LLMs in Open-Source Games (NeurIPS 2025)

**Where this series differs:** it puts LLMs in the classic ~240-strategy Axelrod tournament
and describes them with the same behavioral profile used to explain winning strategies,
so you see how a model plays, not just a single score.

## Open questions

- Which models to compare first (local), and which frontier models later?
- Article 4: Option A or B?
- Package the harness for reuse (e.g., as an Inspect task) or keep it as scripts?
