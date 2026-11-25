<!--
REVIEW NOTES (delete before publishing)

What changed from the Medium version:
- New intro and a "What I got wrong the first time" section with the ablation table.
- "My Analysis" rewritten around the corrected v2 results (normalized rank, seed-grouped
  split, no scaler, bootstrap intervals). The old SHAP interpretations are replaced; several
  flipped direction (notably DC to C rate and C_r / C_min).
- New headline finding: the effect of cooperating more than the median player flips sign
  when noise is added.
- New closing section teasing the LLM follow-up.
- Background kept mostly as-is, with small fixes:
  * One-shot PD: rewrote the "defect pays double" argument as dominance (whatever the other
    player does, defecting pays more). The old version relied on equation images that assumed
    a 50/50 opponent.
  * "strategies that take advantage of reinforcement learning such as finite state automata
    and hidden Markov models": the top Axelrod strategies (Evolved FSM, Evolved HMM,
    EvolvedLookerUp) were *trained* with evolutionary / optimisation algorithms. Reworded;
    double-check against the paper if you want a more precise phrasing.
  * "SSE = 0 ... full potential for extortionate behaviour": ZD strategies include generous
    ones too, so softened to "ZD-like (can enforce a linear payoff relationship)".
  * Kept the paper's image placeholders; re-upload those from the original post.

Things for you to check:
- [IMAGE] markers: upload the files listed. Paths are relative to this file.
- The voice: I tried to keep yours (first person, casual). Edit freely.
- The Substack "originally published on Medium" line at the top: keep or drop.
-->

# Is Tit for Tat the Best Strategy for the Iterated Prisoner's Dilemma? (Revisited)

*Originally published on Medium in August 2024. This version fixes two mistakes in my analysis and adds new results. If you read the first one, skip to [What I got wrong the first time](#what-i-got-wrong-the-first-time).*

The goals of this post:

1. Explain the prisoner's dilemma and the iterated prisoner's dilemma
2. Walk through the results of the most recent large iterated prisoner's dilemma study
3. Share my own analysis of that data, now corrected, and what it says about how winning strategies behave
4. Set up what's next: putting LLMs into the tournament

[IMAGE: cover photo by Raúl Gómez on Unsplash]

## Background

The Prisoner's Dilemma (PD) is a classic game theory problem, formulated by Merrill Flood and Melvin Dresher in 1950. Albert W. Tucker later framed the rewards as prison sentences and gave it its name (1). In its simplest form, two players each choose to **cooperate** or **defect**, independently and at the same time, knowing the payoffs:

|                   | Cooperate (C) | Defect (D) |
|-------------------|:-------------:|:----------:|
| **Cooperate (C)** | R, R          | S, T       |
| **Defect (D)**    | T, S          | P, P       |

where T > R > P > S and 2R > T + S (2). A common choice of values is:

- **T = 5**: temptation to defect
- **R = 3**: reward for mutual cooperation
- **P = 1**: punishment for mutual defection
- **S = 0**: sucker's payoff

If you only play once, defecting is always the better move. If the other player cooperates, defecting gets you 5 instead of 3. If they defect, defecting gets you 1 instead of 0. Whatever they do, you're better off defecting. The catch is that when both players reason this way, both get 1, when they could have had 3 each by cooperating. That's the dilemma.

The **Iterated Prisoner's Dilemma (IPD)** repeats the game many times between the same two players, adding up points across rounds. Now the math changes: what you do today affects what your opponent does tomorrow, so each player can adopt a *strategy*.

In 1980, Robert Axelrod ran the second round of his famous IPD computer tournament (3). It was the largest of its time, with 63 submitted strategies from research labs and independent contestants. Each pair played five matches, with lengths of 63, 77, 151 and 308 moves (151 on average), and a random player was included as a benchmark.

The winner was **Tit for Tat (TFT)**: cooperate on the first move, then copy whatever your opponent did last. It was simple, nice and forgiving. Axelrod distilled its success into four suggestions:

1. Don't be envious: don't strive for a bigger payoff than your opponent.
2. Be nice: don't be the first to defect.
3. Reciprocate both cooperation and defection: be provokable, and be forgiving.
4. Don't be too clever: don't scheme to exploit your opponent.

Veritasium has a great video on this:

[EMBED: https://www.youtube.com/watch?v=mScpHTIi-kM]

I got really obsessed with this study, because it's rare to learn life lessons from math! I wish we'd learned this in school instead of more calculus.

## So why write about it?

In 2024, Glynatsi, Knight and Harper published *Properties of Winning Iterated Prisoner's Dilemma Strategies* (4). They simulated 45,686 IPD tournaments using the ~200 strategies in the open-source Axelrod-Python library (5, 6).

Turns out, **Tit for Tat isn't the winner anymore.** Sorry Veritasium! The strategies at the top were trained ones, such as evolved finite state machines, evolved lookup tables and evolved hidden Markov models. TFT didn't make the top 15, though Spiteful TFT came 5th in tournaments with a probabilistic ending, both with and without noise. So maybe being clever *does* pay off, contrary to Axelrod's fourth suggestion.

## How the data was generated

The authors simulated tournaments with this procedure:

[IMAGE: ../Simulated_data_algo.png (Algorithm 1 from the paper)]

Each random draw picks a number of players N (3 to 195), the players themselves, the number of repetitions k, the number of turns n, a noise probability pₙ (each move gets flipped with probability pₙ) and a probability of ending pₑ (the match ends after each turn with probability pₑ). The same draw is run in four settings: standard, noisy, probabilistic ending, and noisy with probabilistic ending. That comes to about **4 million rows**, one per strategy per tournament.

Each row describes how a strategy behaved in that tournament:

- **stochastic**: whether the strategy uses randomness
- **makes use of game / length**: whether it uses the game's payoffs or the match length
- **memory usage**: the strategy's memory size divided by the number of turns
- **SSE**: how far the strategy is from zero-determinant behaviour (more on this below)
- **Cᵣ**: the strategy's cooperation rate
- **C_max, C_min, C_median, C_mean**: the max, min, median and mean cooperation rate across everyone in the tournament
- **Cᵣ / C_max, Cᵣ / C_min, Cᵣ / C_median, Cᵣ / C_mean**: how the strategy's cooperation compares to the rest of the field
- **CC to C rate**: probability of cooperating after both cooperated
- **CD to C rate**: probability of cooperating after *being* betrayed
- **DC to C rate**: probability of cooperating after *betraying* the opponent
- **DD to C rate**: probability of cooperating after both defected
- **pₙ, pₑ, n, N, k**: the tournament settings

The authors kindly shared all the data on Zenodo (record 10246247).

### Zero-determinant strategies and SSE

Zero-determinant (ZD) strategies can single-handedly enforce a linear relationship between their own score and their opponent's, no matter what the opponent does (8). Some flavours:

- **Extortionate ZD**: guarantees "my score is always a fixed multiple of yours, and higher."
- **Generous ZD**: pushes towards cooperation, but keeps a slight edge.
- **Equalizer ZD**: pins the opponent's score to a fixed value.

**SSE** measures how close a strategy's behaviour is to a ZD strategy (9), on a 0 to 1 scale:

- **SSE = 0**: behaves exactly like a ZD strategy
- **SSE = 1**: no resemblance to ZD behaviour
- In between: some ZD-like behaviour; lower means closer

[IMAGE: ../Plots/sse_counts_top_20_strategies.png]

## What the paper found

The authors fit a linear regression in each of the four settings, predicting a strategy's **normalized rank**, r = R / (N − 1). Here r = 0 means first place and r = 1 means last. (**Lower is better.** Hold on to that, it matters in a moment.)

[IMAGE: ../simulated_data_results_reg.png (regression table from the paper)]

Their conclusions, in short:

1. Be nice in non-noisy environments or when games are long.
2. Be provokable in tournaments with short matches, and generous in tournaments with noise.
3. Be a little bit envious.
4. Be clever.
5. Adapt to the environment, including the population: adjust to the mean cooperation around you.

## What I got wrong the first time

In the original post, I trained an XGBoost model on the same data and used SHAP values (10) to "verify" the paper's findings. When I came back to extend the project, I found two mistakes.

**Mistake 1: I predicted the wrong thing.** The paper predicts *normalized* rank. I predicted *raw* rank, meaning 0 for first place and 194 for last place in a 195-player tournament. Tournament size ranges from 3 to 195, so a big chunk of what my model learned was just "how many players were there?" That meant I wasn't checking the paper's results at all. I was answering a different question.

**Mistake 2: my SHAP plots explained a model that didn't exist.** I standardized the features before training (subtract the mean, divide by the standard deviation), but then computed SHAP values on the *raw* features. The model was being asked about inputs on a completely different scale from anything it saw in training. That's why the old plots had those strange blocky clusters, and why some of my interpretations pointed the wrong way.

While I was at it, I made two more changes:

- **Split train and test by tournament.** Originally, rows were split at random, so the same tournament could appear in both training and test data.
- **Added 95% bootstrap intervals** to the feature importances. In the original post I complained that the paper didn't report confidence intervals, so it was only fair to include my own.

Here's what each fix did to the model's accuracy on the full dataset (R² is the share of the variation in rank the model explains; 1 is perfect):

| Setup | R² |
|---|---|
| Original: raw rank, random split, scaled features | 0.72 |
| + predict normalized rank | **0.88** |
| + split by tournament | 0.88 |
| + no scaling (final) | 0.88 |

Two honest takeaways:

- **The target was the big one.** Once tournament size is out of the picture, the model explains much more.
- **Splitting by tournament barely mattered.** I expected leakage between training and test data to be inflating my numbers, and it wasn't. That's good news! Not every fix changes the answer, and it's worth reporting the ones that don't.

Dropping the scaler doesn't change accuracy (tree models don't care about scale), but it's what makes the SHAP plots below trustworthy.

Here's the corrected model in each setting, next to my old numbers and the paper's linear regressions:

| Setting | Paper (linear, adj. R²) | My original (raw rank) | Revisited (normalized rank) |
|---|---|---|---|
| Standard | 0.54 | 0.90 | **0.96** |
| Noisy | 0.37 | 0.81 | **0.94** |
| Probabilistic ending | 0.46 | 0.82 | **0.91** |
| Noisy + probabilistic ending | 0.54 | 0.65 | **0.78** |

The non-linear model explains much more than a linear one, and the pattern holds: the noisier and less predictable the tournament, the harder it is to explain who wins.

One caveat I missed last time: these features (cooperation rates, CC to C and so on) are measured *in the same tournament* as the rank. So the model **describes how winners behave**. It doesn't predict who will win before the tournament starts. That's the same framing as the paper, and it's the right one here. Just read the results below as "winners tend to…", not "doing X causes you to win."

## The corrected analysis

A quick guide to reading SHAP plots:

- Each dot is one strategy in one tournament.
- **Left of zero = pushes toward a better (lower) rank. Right of zero = worse.**
- Colour is the feature's value: red is high, blue is low.
- Features are sorted by overall importance.

### The standard tournament (no noise, fixed length)

[IMAGE: ../Plots/v2/SHAP_no_noise_no_probend.png]

- **Be nice.** A high CC to C rate (keep cooperating while things are going well) goes with a better rank. This is the most important feature.
- **Be provokable.** A high CD to C rate, meaning cooperating again right after being betrayed, is one of the clearest predictors of a *worse* rank. Don't be a pushover.
- **Be a little envious.** Low SSE (behaving more like a zero-determinant strategy) goes with a better rank. Strategies that quietly keep an edge over their opponent do well.
- **Don't apologise too fast.** A low DC to C rate goes with a better rank: after defecting on a cooperator, winners tend to *keep* defecting rather than immediately going back to cooperating. This is the opposite of what I wrote last time, when my interpretation said "be forgiving" here.
- **Cooperate at least as much as the crowd.** High Cᵣ / C_median goes with a better rank.
- **Be clever.** Higher memory usage and using the match length both go with a better rank. Being stochastic goes with a worse one.

That's a remarkably close match to the paper's conclusions: nice, provokable, a little envious, and clever.

### The twist: noise flips the story

Here's the result I didn't see the first time. Look at the top feature, Cᵣ / C_median (how much you cooperate compared to the median player), in the noisy setting:

[IMAGE: ../Plots/v2/SHAP_has_noise_no_probend.png]

In the standard tournament, cooperating **more** than the median player goes with a better rank. With noise, it goes with a **worse** one. The red dots moved from the left side to the right.

But being the *least* cooperative player doesn't win either: a high Cᵣ / C_min (cooperating well above the least cooperative player) still goes with a better rank.

So in noisy tournaments, the winners sit **in the middle of the pack**: they cooperate less than the typical player, but they're not the most hostile one in the room.

Intuitively: when moves randomly flip, a very cooperative strategy keeps getting "betrayed" by accidents and exploited by opportunists, while a very hostile one drags everyone into mutual defection. The winners **calibrate to the population**. That's the paper's fifth lesson, "adjust to the mean population cooperation," showing up clearly in the data.

With all four settings pooled together, Cᵣ / C_median is by far the most important feature:

[IMAGE: ../Plots/v2/importance_all.png]

The bars are mean |SHAP| (how much a feature moves the prediction on average), and the black lines are 95% bootstrap intervals over tournaments. The intervals are tight, because with 4 million rows the uncertainty is small. Two honest caveats:

- These intervals capture variation across *tournaments*, not what would happen if I retrained the model.
- Many of these features are strongly correlated (all the Cᵣ ratios move together). SHAP splits credit between correlated features somewhat arbitrarily, so read *groups* of related features together rather than over-interpreting any single bar.

The plots for the other settings are in the repo: `Plots/v2/`.

## So, is Tit for Tat the best strategy?

Not anymore. But its spirit survives. The winners in the standard setting are still **nice and provokable**, like TFT. What changed is that they're also **a little envious and a little clever**, and in noisy worlds they **read the room**: they match their cooperation to the population instead of following a fixed rule.

If I had to sum up the lessons for humans: be nice, don't be a pushover, keep a slight edge, and when the world is noisy, calibrate to the people around you.

## What's next: what happens when an LLM enters the tournament?

Everything above describes *how winning strategies behave*: how often they cooperate, how they respond to betrayal, how they compare to the crowd. That gives us a behavioural fingerprint we can apply to **any** player.

Including a large language model.

In the next post, I'll give LLMs a seat in Axelrod's tournament. They'll play against classic strategies like Tit for Tat, Grudger and Win-Stay-Lose-Shift, as well as the evolved champions. Then I'll measure them with the same features. Does an LLM play like Tit for Tat? Like a Grudger? Is it a pushover? Does it read the room when noise is added? And does it act differently when the game is called a "prisoner's dilemma" versus a neutral business scenario?

I'll start with small open models running on my laptop, and share the code so you can run it yourself. Subscribe if you want to see how they do. 🙂

## Code and data

- Code: https://github.com/aminekhasteh/prisoners_dilemma (the revisited analysis is in `scripts/`)
- Data: Glynatsi, Knight & Harper, Zenodo record 10246247

## References

1. Flood, M. & Dresher, M. (1950); Tucker, A. W. Prisoner's Dilemma. https://en.wikipedia.org/wiki/Prisoner's_dilemma
2. Stanford Encyclopedia of Philosophy: Prisoner's Dilemma. https://plato.stanford.edu/entries/prisoner-dilemma/
3. Axelrod, R. (1980). More Effective Choice in the Prisoner's Dilemma. *Journal of Conflict Resolution*.
4. Glynatsi, N., Knight, V. & Harper, M. (2024). Properties of Winning Iterated Prisoner's Dilemma Strategies. https://pmc.ncbi.nlm.nih.gov/articles/PMC11670945/
5. Axelrod-Python library. https://github.com/Axelrod-Python/Axelrod
6. Axelrod-Python strategy index. https://axelrod.readthedocs.io/en/latest/reference/strategy_index.html
7. Glynatsi, Knight & Harper tournament data. https://zenodo.org/records/10246247
8. Press, W. H. & Dyson, F. J. (2012). Iterated Prisoner's Dilemma contains strategies that dominate any evolutionary opponent. *PNAS*.
9. SSE as a measure of distance from ZD behaviour: see (4).
10. Lundberg, S. & Lee, S.-I. (2017). A Unified Approach to Interpreting Model Predictions. *NeurIPS*.
