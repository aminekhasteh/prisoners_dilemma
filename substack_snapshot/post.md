# How Nice Should You Be? Game Theory Has Some Thoughts

*Tit for Tat used to be the best strategy in the Prisoner's Dilemma. Here's what 45,000 simulated tournaments say about who wins now, and why a little noise changes everything.*

- Published: 2026-11-14T00:45:56.572Z
- Updated: 2026-11-19T03:49:53.506Z
- URL: https://upsidedownmonkeys.substack.com/p/how-nice-should-you-be-game-theory

---

![272 strategies, one opponent, 60 rounds: every strategy's moves as a ring of circles (cooperate) and squares (defect), coloured nice or nasty](https://substackcdn.com/image/fetch/$s_!Hprw!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F88db405f-5372-417b-8fff-7e95e2aebee7_3960x2232.png)

## First, the game

The Prisoner’s Dilemma (PD) is one of the classic puzzles of game theory. Merrill Flood and Melvin Dresher came up with it in 1950. Albert W. Tucker later turned the payoffs into prison sentences, and that’s where the name comes from (1). The setup is simple. Two players each choose to **cooperate** or **defect**, at the same time, without talking to each other. They both know the payoffs. There are only four ways a single round can play out.

![Payoff matrix for one round of the Prisoner's Dilemma: circle = cooperate, square = defect; Player 1 is filled, Player 2 is in outline](https://substackcdn.com/image/fetch/$s_!LH1O!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F3a6273ca-ff24-4e59-be0a-de498737574e_2000x1780.png)

In the original paper, **T** is the temptation to defect (5 points), **R** is the reward when both players cooperate (3), **P** is the punishment when both defect (1), and **S** is the sucker’s payoff (0). To count as a real dilemma, the payoffs need to follow:

- T > R > P > S
- 2R > T + S (2)

The second rule  means  taking turns and betraying each other still pays less than cooperating every time.

Now put yourself in Player 1’s shoes ***Whatever Player 2 does, you are better off defecting.*** If Player 2 cooperates, defecting wins you five points instead of three, and if Player 2 defects, defecting wins you one point instead of zero.  The catch is that Player 2 is doing the exact same math. The best outcome for both (3 and 3) is one where nobody has to lose.

The **Iterated Prisoner’s Dilemma (IPD)** is the same game played many times by the same two players, with points added up across rounds. What Player 1 does today affects what Player 2 does tomorrow. So instead of a single move, each player needs a *strategy*: a rule for what to do based on what has happened so far. One catch: the players don’t know which round is the last. If they did, the whole thing falls apart. Say both know the game ends after round 10. In round 10 there’s no future to protect, so both defect. Each player can see that coming, so there’s no reason to be nice in round 9 either. Then the same goes for round 8, and so on, until both defect from the very first round.

[Subscribe widget: Thanks for reading! Subscribe for free to receive new posts and support my work.]

## 1980: computers play the Prisoner’s Dilemma

In 1980, Robert Axelrod invited people to send in computer programs that would play the IPD against each other (3). For his second tournament, he got 62 entries from six countries, from a 10-year-old computer hobbyist to professors in seven different fields. He also threw in RANDOM, a program that just flips a coin every turn. Every strategy played every other one in five games, with game lengths drawn at random, about 151 moves on average. Nobody knew when the last move would come, so nobody could plan to stab their opponent in the back on the final turn.

### Enter Tit for Tat

The winner was **Tit for Tat (TFT)**, submitted by Anatol Rapoport, a psychology professor at the University of Toronto. It had also won the first tournament, and it was the simplest program in both. A professor won, but Axelrod was careful to point out that overall, “the professors did not do significantly better than the others.” Fun fact: the program that ran that tournament is lost, but the Fortran entries themselves survived. In 2025, Knight and colleagues got them running on modern computers and replayed the whole thing. Tit for Tat won again (11).

Good news for nerds like me who have no game theory background...

So what was special about Tit for Tat’s rule?

> **Cooperate on the first move, then copy whatever the other player did last.**
>
> Axelrod’s four lessons from it:
>
> 1. **Don’t be envious.** Don’t try to outscore your opponent.
> 2. **Be nice.** Never defect first.
> 3. **Reciprocate.** Hit back right away, forgive right away.
> 4. **Don’t be too clever.** Don’t scheme to exploit anyone.

There are a few words people use to describe Tit for Tat. It’s **nice**: it never defects first. It’s **retaliatory**: defect on it and it hits back right away, so it’s not a pushover. It’s **forgiving**: the moment you cooperate again, it lets it go. No grudges. And it’s **clear**: it’s so simple that the other player figures it out fast and learns that cooperating pays (3). Honestly, most people I know could use at least two of these.

The opposite of nice is **nasty**. On paper that’s easy: a nasty strategy defects first. In practice it gets messy. A strategy that betrays you once in a 200-round game and one that betrays you every single round are both “nasty”. Some play nice the whole game and only stab you in the back in the very last round. Are those the same thing? Not really. I’ll come back to this later, because it ended up mattering more than I expected. For now, the headline: in Axelrod’s tournaments, most of the top finishers were nice.

**Veritasium** has a great video on this:

https://www.youtube.com/watch?v=mScpHTIi-kM

## Forty years later, Tit for Tat lost its crown

In 2024, Nikoleta Glynatsi, Vincent Knight and Marc Harper published *Properties of Winning Iterated Prisoner’s Dilemma Strategies* (4). They took the 195 strategies in the open-source Axelrod-Python library (5, 6) and ran tournaments. A lot of tournaments.

Turns out, **Tit for Tat isn’t the winner anymore!**

The top spots went to *trained* strategies: finite state machines, lookup tables, neural networks and hidden Markov models whose settings were tuned by evolutionary and optimization algorithms. Tit for Tat comes 66th out of 195 by its typical finish in standard tournaments. Its cousin, Spiteful Tit for Tat, does better. It cooperates until you defect twice in a row. Then it never forgives you. Ever. That one makes the top 15 when there’s noise or the games end at random. So grudges have their uses, apparently.

So maybe being clever *does* pay off, which goes against Axelrod’s fourth piece of advice, and against being clear.

## 45,000 tournaments later

Here’s the setup. The authors put together 11,400 random tournament recipes. For each one, they rolled the dice on:

- **who’s playing**: anywhere from 3 to all 195 strategies (**N**)
- **how long each game lasts** (**n**), and how many times to replay the whole tournament (**k**)
- **noise** (**pₙ**): the chance that any single move gets flipped by accident. Player 1 means to cooperate, but it comes out as a defection. Think of a text message that reads way ruder than you meant it.
- **a random ending** (**pₑ**): after every turn, the game might just stop. A 10% chance means games last about 10 turns on average.

Then they played every recipe four ways: **standard** (no noise, fixed length), **noisy**, **random ending**, and **both**. That’s about 45,600 tournaments and 4 million rows of data, one row per strategy per tournament. And they put all of it on Zenodo for anyone to use (7).

So what’s actually in those 4 million rows? Each one follows a single strategy through a single tournament: how often it cooperated, how it reacted to the other player’s last move, and where it finished in the rankings. Here are the measurements this post leans on:

> 1. **Cᵣ**: the strategy’s cooperation rate, meaning the share of its moves that were “cooperate”
> 2. **Cᵣ / C_median**: its cooperation rate divided by the median player’s in that tournament. Above 1 means it cooperated more than the typical player. (There are also versions comparing it to the max, min and mean player.)
> 3. **CC to C rate**: how often it keeps cooperating after you both cooperated. This is niceness.
> 4. **CD to C rate**: how often it cooperates again right after being betrayed. High means forgiving, or a pushover, depending on your mood.
> 5. **DC to C rate**: how often it goes back to cooperating after *it* betrayed a cooperator
> 6. **DD to C rate**: how often it tries to restart cooperation after you both defected
> 7. **memory usage**: how many past turns it looks at, divided by the length of the game
> 8. **makes use of length**: whether it knows how long the game is
> 9. **stochastic**: whether it uses randomness
> 10. **SSE**: how much it behaves like a zero-determinant strategy (more on that below)

### How to measure envy?

Zero-determinant (ZD) strategies, found by Press and Dyson in 2012, can single-handedly force a straight-line relationship between their own score and their opponent’s, no matter what the opponent does (8). They come in a few flavours:

- **Extortionate ZD**: “my score is always a fixed multiple of yours, and higher.”
- **Generous ZD**: pushes towards cooperation, but keeps a slight edge.
- **Equalizer ZD**: pins the opponent’s score to a fixed value. Whatever you do, you get what it decided you get.

**SSE** measures how far a strategy’s actual behaviour is from the closest ZD strategy (9). An SSE of 0 means it behaves exactly like a ZD strategy, and the bigger the number, the less it does. The paper reads low SSE as being “a little envious”: quietly making sure you come out a bit ahead.

Here’s how it’s worked out. Take the four rates from earlier: how often a strategy cooperates after CC, CD, DC and DD. Then find the ZD strategy whose four rates are as close as possible to those. The gaps between the two are the errors. Square them, add them up, and you’ve got the SSE, the sum of squared errors. Yes, the name is literally the recipe.

Here’s the same recipe in math. It comes down to the distance from a point to a plane, which is about as friendly as linear algebra gets.

Two strategies show up in this math, p and q, and they’re easy to mix up. p is the strategy on trial: Tit for Tat, Grudger, whichever one we want an SSE for. Its numbers are whatever they are. q is a ZD strategy, and its numbers are ours to pick. We slide q around until it sits as close to p as it can get, and SSE measures the gap that’s left.

**The strategy.** Write it as its four cooperation rates, its own move first:

```latex
p = (p_1, p_2, p_3, p_4) = \big(\Pr(\mathrm{C} \mid \mathrm{CC}),\ \Pr(\mathrm{C} \mid \mathrm{CD}),\ \Pr(\mathrm{C} \mid \mathrm{DC}),\ \Pr(\mathrm{C} \mid \mathrm{DD})\big)
```

Each of the four is a probability, a number between 0 and 1. Tit for Tat copies Player 2’s last move, so it’s p = (1, 0, 1, 0): it cooperates for sure after CC and DC, and defects for sure after CD and DD. RANDOM, the coin flipper from Axelrod’s tournament, is (1/2, 1/2, 1/2, 1/2).

![A strategy written as four numbers: its chance of cooperating after CC, CD, DC and DD, shown for Tit for Tat, Grudger, Win-Stay-Lose-Shift and RANDOM](https://substackcdn.com/image/fetch/$s_!OxCu!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F29cef7c5-6239-4595-8549-b4c3f86bf64b_2000x1740.png)

**The ZD strategies.** A ZD strategy is also just four cooperation rates. I’ll call it q, so it doesn’t get mixed up with p, the strategy we’re measuring. Press and Dyson’s recipe builds every ZD strategy of the kind SSE uses from a starting point and two directions. Two dials, α and β, say how far to go along each:

```latex
q = (1, 1, 0, 0) + \alpha\,(2, -1, 4, 0) + \beta\,(2, 4, -1, 0)
```

The starting point (1, 1, 0, 0) just says whether Player 1 cooperated in CC, CD, DC and DD: yes, yes, no, no. The two directions are each player’s payoffs after CC, CD, DC and DD, minus P = 1: (3, 0, 5, 1) − 1 for Player 1 and (3, 5, 0, 1) − 1 for Player 2.

**Why minus 1?** It measures every score from the punishment P = 1, the score both players get if they just defect forever.

Every setting of the dials gives one ZD strategy, as long as its four rates stay between 0 and 1. Tit for Tat, for example, is α = 0.2 and β = −0.2:

```latex
(1, 1, 0, 0) + 0.2\,(2, -1, 4, 0) - 0.2\,(2, 4, -1, 0) = (1, 0, 1, 0)
```

![How a ZD strategy picks its next move: it starts from its own last move, then adds α times Player 1's points minus 1 and β times Player 2's points minus 1, worked out for Tit for Tat and Extort-2](https://substackcdn.com/image/fetch/$s_!kT5S!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F8ffcd43d-155a-408c-a226-41279ef386f4_2000x2240.png)

From the illustration above, let’s take CD: Player 1 cooperated and Player 2 defected. The ZD player starts from its own last move, so its chance of cooperating starts at 1. It scored 0, which is 1 point below P, so the chance moves by −α. Player 2 scored 5, which is 4 above P, so the chance moves by 4β. That’s q₂ = 1 − α + 4β. The payoffs never turn into probabilities. They’re what the ZD player looks at, and the dials do the converting: α is how much chance of cooperating one of its own points is worth, and β does the same for Player 2’s points.

So why build strategies this way? Because whatever Player 2 does, a player using q pins the two long-run average scores, s₁ and s₂, to a straight line:

```latex
s_1 - 1 = \chi\,(s_2 - 1), \qquad \chi = -\beta / \alpha
```

Tit for Tat has χ = 1, so the two scores always come out equal.

> #### Proof
>
> Let v hold how often CC, CD, DC and DD happen over a long game. Player 1 cooperates in a share v · (1, 1, 0, 0) of the rounds (the CC and CD ones), and its strategy has it cooperate in the following round a share v · q of the time. Over a long game those two shares are the same, so v · (q − (1, 1, 0, 0)) = 0. Now put the recipe in for q − (1, 1, 0, 0). Since v · (3, 0, 5, 1) = s₁, v · (3, 5, 0, 1) = s₂ and the four shares add up to 1, out comes α(s₁ − 1) + β(s₂ − 1) = 0, which is the line above.
>
> For SSE, though, the dial values don’t matter. All that matters is the set of points you can reach by turning them, which is a flat sheet. To see why it’s flat, write the recipe out one entry at a time:
>
> ```latex
> \begin{aligned}
> q_1 &= 1 + 2\alpha + 2\beta \\
> q_2 &= 1 - \alpha + 4\beta \\
> q_3 &= 4\alpha - \beta \\
> q_4 &= 0
> \end{aligned}
> ```
>
> That’s four numbers run by only two dials, so they can’t all move freely. Whatever α and β are, the four numbers have to obey two rules. The first is sitting right there: q₄ = 0. For the second, add the two middle lines, and put the result next to the first line:
>
> ```latex
> \begin{aligned}
> q_1 - 1 &= 2\alpha + 2\beta = 2\,(\alpha + \beta) \\
> q_2 + q_3 - 1 &= 3\alpha + 3\beta = 3\,(\alpha + \beta)
> \end{aligned}
> ```
>
> Both are a multiple of the same thing, α + β. So three times the first always equals two times the second, and the dials drop out: 3(q₁ − 1) = 2(q₂ + q₃ − 1). Tidy that up and you have the two rules every ZD strategy follows:
>
> ```latex
> q_4 = 0, \qquad 3q_1 - 2q_2 - 2q_3 = 1
> ```
>
> The 2 and the 3 are payoffs in disguise: after CC, each player is 2 points above P, and after CD and DC the two players are 4 above and 1 below, which adds up to 3. An equation like that one describes a flat sheet, a plane. Here it is, inside a cube that holds every possible strategy:
>
> ![A cube of all strategies: the ZD strategies lie on one grey triangle, and the dashed line is Grudger's gap to its closest ZD strategy](https://substackcdn.com/image/fetch/$s_!uLh_!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fb27c01d4-78b7-4e33-9f92-ba49c5c94d22_2000x2040.png)
>
> **The gaps.** Now bring back p. It can sit anywhere in the cube, on the sheet or off it. To find out which, put its numbers through the same rule: m = 3p₁ − 2p₂ − 2p₃ − 1. A ZD strategy gets m = 0. Anything else is off the sheet, and m says by how much. The closest ZD strategy, q*, is straight across from p, at the end of the dashed line in the picture (the orthogonal projection of p onto the plane), with q₄* = 0. Getting there means moving p along d = (3, −2, −2), the three numbers in the rule. Every step along d changes m by 9 + 4 + 4 = 17, so it takes m/17 of a step, and the gaps are:
>
> ```latex
> p - q^* = \Big(\tfrac{3m}{17},\ -\tfrac{2m}{17},\ -\tfrac{2m}{17},\ p_4\Big)
> ```
>
> and SSE is the sum of the four squared gaps:
>
> ```latex
> \mathrm{SSE}(p) = \Big(\tfrac{3m}{17}\Big)^2 + \Big(\tfrac{2m}{17}\Big)^2 + \Big(\tfrac{2m}{17}\Big)^2 + p_4^2 = \frac{m^2}{17} + p_4^2
> ```

**Let’s take a look at three example strategies:**

*Tit for Tat*, p = (1, 0, 1, 0):

```latex
\begin{aligned}
m &= 3 \cdot 1 - 2 \cdot 0 - 2 \cdot 1 - 1 = 0 \\
p - q^* &= (0,\ 0,\ 0,\ 0) \\
\mathrm{SSE} &= 0
\end{aligned}
```

*Grudger*, p = (1, 0, 0, 0):

```latex
\begin{aligned}
m &= 3 \cdot 1 - 2 \cdot 0 - 2 \cdot 0 - 1 = 2 \\
p - q^* &= \Big(\tfrac{6}{17},\ -\tfrac{4}{17},\ -\tfrac{4}{17},\ 0\Big) \approx (0.35,\ -0.24,\ -0.24,\ 0) \\
\mathrm{SSE} &= \frac{36 + 16 + 16}{289} + 0^2 = \frac{4}{17} \approx 0.24
\end{aligned}
```

*Win-Stay-Lose-Shift*, p = (1, 0, 0, 1):

```latex
\begin{aligned}
m &= 3 \cdot 1 - 2 \cdot 0 - 2 \cdot 0 - 1 = 2 \\
p - q^* &= \Big(\tfrac{6}{17},\ -\tfrac{4}{17},\ -\tfrac{4}{17},\ 1\Big) \\
\mathrm{SSE} &= \frac{36 + 16 + 16}{289} + 1^2 = \frac{21}{17} \approx 1.24
\end{aligned}
```

Here’s how SSE is spread out across an even bigger lineup than the paper’s. In Knight and colleagues’ rerun of Axelrod’s tournament (11), 272 strategies play: 209 from the Axelrod-Python library and all 63 original 1980 Fortran entries, the ones with names like k42r and k92r. I also sorted them into nice and nasty.

![All 272 strategies by SSE, each bar built from the strategy's own moves, sorted into nice and nasty](https://substackcdn.com/image/fetch/$s_!9pzn!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fff3530f7-9723-4d2f-9967-28a12ba22184_3780x3960.png)

Each bar is a strategy’s typical (median) SSE across tournaments, so a shorter bar means more ZD-like. If you noticed, the bars are built from the same moves as the cover, against the same opponent, starting from the middle. So a long bar shows more of how that strategy plays, and a short one only shows its first few moves. The longest bars mostly belong to nasty strategies near the bottom of the rankings, like Bully, Alternator and Anti Tit For Tat.

The colours sort the strategies into nice and nasty. But here is a question worth answering:

## Who is nice, and who is nasty?

When Axelrod said “be nice”, he meant something very specific: a nice strategy is never the first to defect. That’s it. It can hit back as hard as it likes, as long as it never throws the first punch. Glynatsi and colleagues (4) also end up telling winners to be nice, but they never check that rule. Their “nice” comes from the cooperation numbers instead: strategies with a high CC to C rate, and ones that cooperate more than the median player, tend to rank better. A strategy could cooperate 99% of the time and still be the one who defects first.

> Their recipe for a winning strategy:
>
> 1. Be nice when there’s no noise or when games are long.
> 2. Be provokable (retaliatory) when games are short, and generous (forgiving) when there’s noise.
> 3. Be a little bit envious.
> 4. Be clever.
> 5. Adapt to the environment, including how cooperative everyone else is.

Out of curiosity, I checked Axelrod’s rule directly. For each of the 272 strategies, I went through its games against every other strategy and checked whether it was ever the first to defect. Every strategy landed in one of two groups:

- **Nice**: never the first to defect.
- **Nasty**: defects first at some point, even if only once.

That gives 145 nice and 127 nasty strategies, which are the colours in the ring above. And it backs the paper’s first lesson (be nice when there’s no noise) more directly than its own numbers do: nice strategies take all of the top 20 spots and 96 of the top 100. What about the strategies that play nice and stab you in the last round? The paper calls DoubleCrosser and BackStabber “cheaters” for doing this. Here they sit at #23 and #32, and they count as nice: Knight and colleagues never tell the players how long a game is, so that last-round stab never comes. Axelrod’s lesson still holds 40 years later, with a twist. The very top isn’t Tit for Tat or its relatives, which sit in the middle (Tit for Tat is #58). It’s evolved and trained strategies, programs that a computer tuned to win these tournaments, and they came out nice too. The best of the 1980 entries, k42r, comes 18th.

What about SSE? Nasty strategies do sit a bit further from ZD behaviour: a typical SSE of 0.14, against 0.05 for nice ones, and that gap is too big to be luck (Mann-Whitney test, p < 0.001). But the whole gap comes from one kind of nasty strategy, the ones that cooperate right after both players defected, like Alternator and the cyclers. Remember the lonely p₄² at the end of the SSE formula? Those strategies pay for it every time. Take them out and the gap disappears (p = 0.21). This lines up with another finding in the paper: cooperating after a mutual defection goes with a worse rank. So being nice doesn’t make you more ZD-like. Some nasty strategies just make a move that SSE can’t fit, and it doesn’t do them any favours in the standings either.

One difference from the paper: my ring ranks strategies by their average rank over Knight and colleagues’ 100 no-noise tournaments, where all 272 strategies play each other every time. The paper has Evolved HMM 5 at #1. Here it’s EvolvedLookerUp2_2_2, but the same group of trained strategies sits at the top.

## My analysis

A linear regression assumes every feature pushes rank in one direction, by the same amount, everywhere. Strategies probably don’t work like that. Cooperating a lot might be great in one crowd and terrible in another. So I trained an XGBoost model to predict normalized rank from the same features, because when you get tabular data, why not just use XGBoost? Then I used SHAP values (10) to see what the model learned.

To keep myself honest, I tested the model on tournaments it never saw during training. If a tournament was in the test set, none of its rows were in training.

![R² by setting](https://substackcdn.com/image/fetch/$s_!CjWX!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fc997f2e5-8927-4bd0-b464-cb09d1458c52_1854x1080.png)

R² is the share of the differences in rank that the model explains, where 1 is perfect. Across all the data, the model explains 88% of the variation in rank in new tournaments. In every setting it does much better than the paper’s linear models.

There’s a tougher test, though: strategies the model has never seen. I held out a group of strategies entirely and tested on them. R² drops to 0.81 overall, and for noisy tournaments in the paper’s range it falls to 0.51 (the green bars). So the model is great at recognizing how familiar strategies do, and not so great at sizing up a stranger. Kinda like most people at a party.

One more thing to keep in mind. These features (cooperation rates, CC to C and so on) are measured *in the same tournament* as the rank. So the model **describes how winners behave**. It can’t tell you who will win before the tournament starts, and it doesn’t prove that doing X causes you to win. That’s the same framing as the paper. So read everything below as “winners tend to…”.

### Meeting strangers from 1980

Then I tried an even harder test. Knight and colleagues’ lineup has 86 strategies my model had never seen: 63 original 1980 Fortran entries and 23 newer library strategies. I took the version of my model trained on the paper’s standard tournaments (no noise, fixed length), exactly as it was, and asked it where each of the 272 strategies would finish in Knight’s 100 no-noise tournaments.

![Predicted vs actual rank for all 272 strategies: grey dots were seen in training, blue dots are new library strategies, green triangles are 1980 Fortran entries](https://substackcdn.com/image/fetch/$s_!Xm9t!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fe635b6fc-f515-41f8-a197-56a8c0ef30d9_1800x1720.png)

Each point is one strategy. On the dashed line, the model guessed its rank exactly. For the 186 strategies it had seen before, it does well: R² of 0.84, and its order matches the real one closely (Spearman correlation 0.94). For the 86 newcomers, R² drops to 0.63 (Spearman 0.81), and its typical miss grows from about 25 places to about 33, out of 272. The 1980 entries and the new library strategies are about equally hard to read (R² 0.61 and 0.54).

The misses are the fun part. The model thought k53r, a 1980 entry, would come 16th. It came 104th. Bush Mosteller, a strategy that learns as it plays, was predicted 174th and finished 261st. The one big miss in the other direction is UsuallyCooperates: the model expected it near the very bottom (270th), and it came 153rd. Even Tit for Tat, as k92r, gets underrated: predicted 128th, actual 58th.

Two caveats. 38 of the Fortran entries have no Python version, so some of their traits, like how much memory they use, had to be filled in by assumption. And Knight’s tournaments are bigger and longer than anything in the training data: 272 players and games of up to 308 turns. So an R² of 0.63 isn’t bad for a model meeting strangers in a room it has never been in.

### The standard tournament

No noise, fixed length: the closest thing to Axelrod’s world. Here’s what the model says winners tend to do, most important habit first:

> - **Be nice.** A high CC to C rate (keep cooperating while things are going well) goes with a better rank. It’s the most important feature by far. If things are going well, don’t be the one to ruin it.
> - **Be retaliatory.** A high CD to C rate, cooperating again right after being betrayed, is one of the clearest signs of a *worse* rank. Don’t be a pushover!
> - **Be a little envious.** A low SSE, meaning a strategy plays a bit like a zero-determinant one, goes with a better rank. Quietly keeping a small edge pays.
> - **Don’t apologise too fast.** A low DC to C rate goes with a better rank. After betraying a cooperator, winners tend to keep defecting for a bit instead of rushing back with flowers.
> - **Cooperate about as much as the crowd.** Strategies that cooperate about as much as the median player finish best. Cooperating much less is the worst place to be. Cooperating much more doesn’t help either: strategies above 1.25 times the median do noticeably worse than those near it.
> - **Be clever.** Remembering more of the game and knowing how long it lasts both go with a better rank. Flipping coins goes with a worse one.

That’s a close match to the paper: nice, retaliatory, a little envious, and clever. Tit for Tat gets the first two right, but it can’t keep an edge: it never scores more than the opponent it’s playing. Too polite. And that’s the funny part about a game that isn’t zero-sum. Tit for Tat won Axelrod’s tournaments without beating anyone head to head. It just racked up 3s with everyone willing to cooperate, while the nasty strategies won their matchups and lost the tournament.

Maybe foreign policy should take notes?! Anyway, I’ll leave that one to the reader.

### What matters most overall

With all four settings pooled, the most important features are about how your cooperation compares to everyone else’s:

![Feature importance, all settings pooled](https://substackcdn.com/image/fetch/$s_!uYPw!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F03a6972f-c9b0-4491-b64a-d20daf966451_1904x1146.png)

The bars are mean |SHAP|, how much a feature moves the predicted rank on average. The black lines are 95% bootstrap intervals across tournaments. (The paper didn’t report confidence intervals, and some 95% intervals are always nice, so here are mine.)

Cᵣ / C_median is on top, but I wouldn’t crown it on its own. The comparison features all carry nearly the same information. When I retrained the model without Cᵣ / C_median, R² barely moved, from 0.882 to 0.879, because the other comparisons picked up the slack. So the real lesson is about the group: **what matters is how cooperative you are compared with the people around you**, not exactly which yardstick you use.

## The twist: noise flips the story

This is the result that surprised me most.

In the standard tournament, cooperating more than the median player goes with a better rank. The paper noticed that in noisy tournaments this reverses: you don’t want to cooperate more than the median or mean player. I wanted to know *how much* noise it takes. So I split the noisy tournaments by noise level and compared strategies that cooperated more than the median player with those that cooperated less:

![The noise flip by noise level](https://substackcdn.com/image/fetch/$s_!Ax8M!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F0df7929a-8436-4c46-bee5-8d84bd38f05a_1828x1157.png)

Each dot is the average gap in normalized rank between the two groups. Below zero (blue), the more cooperative half finishes higher. Above zero (orange), it finishes lower.

- **No noise:** the more cooperative half finishes 0.12 higher. In a 100-player tournament, that’s about 12 places.
- **1–2% noise:** the advantage is basically gone.
- **2–5% noise:** it flips. Cooperating more than the median now goes with a worse rank.
- **5–10% noise:** the more cooperative half finishes 0.24 lower, about 24 places in a 100-player tournament.

So it doesn’t take much. Once about one move in 30 gets scrambled, being the friendliest player in the room starts to cost you.

Here’s my intuition. Noise is rough on everyone. Picture two Tit for Tats: one move gets flipped by accident, the other one hits back, the first one hits back for that, and now they’re stuck trading defections like an echo until another accident breaks the loop. The usual fix is to be more forgiving, like Generous Tit for Tat, which lets some defections slide. But forgive too much and you become an easy target. A very cooperative strategy keeps getting “betrayed” by accidents, and the opportunists happily take advantage. A strategy that holds back a little loses less to the chaos. The winners **read the room**, which is the paper’s fifth lesson showing up clearly in the data.

I stopped the chart at 50% noise on purpose. Past that point, more than half of every strategy’s moves get flipped, so a “cooperative” strategy actually defects most of the time, and the labels stop meaning much. That’s also why the paper focuses on 10% or less.

(Is splitting by the median the best way to look at this? Maybe not! If you have a better idea, please let me know in the comments.)

## So, is Tit for Tat the best strategy?

Not anymore. But its spirit survives! In the standard setting, winners are still **mostly nice and retaliatory**, like Tit for Tat. What changed is that they’re also **a little envious and a little clever**. And when the world gets noisy, even a little, they **cooperate a bit less than the crowd** instead of following a fixed rule.

If I had to sum it up for humans: be nice, don’t be a pushover, keep a slight edge, and when things get messy, pay attention to the people around you.

## What’s next: what happens when an AI model joins the tournament?

Everything above describes *how winning strategies behave*: how often they cooperate, how they respond to betrayal, how they compare to the crowd. That’s a behavioural fingerprint, and you can take it for **any** player.

Including a large language model.

In the next post, I’ll give LLMs a seat in Axelrod’s tournament. They’ll play against classics like Tit for Tat, Grudger and Win-Stay-Lose-Shift, and against the evolved champions. Then I’ll measure them with the same features. Does an LLM play like Tit for Tat? Is it nice or nasty? Does it forgive, or hold a grudge like Grudger? Is it a pushover? Does it read the room when noise is added? And does it play differently when the game is called a “prisoner’s dilemma” versus a neutral business deal?

I won’t be the first to try this. Pal, Hilbe, Nowak and colleagues recently put five big LLMs through the repeated prisoner’s dilemma, and found that none of them was fully consistent across all their tests (12). I want to see how that looks through the same lens as the strategies above.

I’ll start with small open models running on my laptop, and share the code so you can run it yourself.

Thanks for stopping by! Subscribe if you want to see how the robots do, and feel free to leave a comment if you have anything to add, or you just wanna holla at me 🙂

---

## Glossary of symbols

Every letter in this post, in one place. Watch out for the p’s: lowercase p is a chance (a number between 0 and 1), while capital P is a number of points.

**The game**

- **C, D** (moves): cooperate, defect
- **CC, CD, DC, DD** (outcomes): what happened in one round, Player 1’s move first. CD means Player 1 cooperated and Player 2 defected.
- **R = 3** (points): Reward, what each player gets when both cooperate
- **S = 0** (points): Sucker’s payoff, for cooperating while the other player defects
- **T = 5** (points): Temptation, for defecting while the other player cooperates
- **P = 1** (points): Punishment, what each player gets when both defect. The ZD math measures every score from here, which is where the “minus 1” comes from.
- **s₁, s₂** (points): Player 1’s and Player 2’s average score per round over a long game

**The tournaments**

- **N** (a count): number of strategies in a tournament (3 to 195 in the paper’s data, 272 in Knight and colleagues’)
- **n** (a count): number of turns in each game
- **k** (a count): number of times the whole tournament is replayed
- **pₙ** (a chance): noise, the chance that any single move gets flipped by accident
- **pₑ** (a chance): random ending, the chance that a game stops after any turn
- **Normalized rank** (0 to 1): finishing position divided by (N − 1). 0 is first place, 1 is last.

**Measuring a strategy**

- **Cᵣ** (a share): cooperation rate, the share of a strategy’s moves that were “cooperate”
- **Cᵣ / C_median** (a ratio): its cooperation rate divided by the median player’s in the same tournament. Above 1 means it cooperated more than the typical player.
- **CC to C, CD to C, DC to C, DD to C** (shares): how often a strategy cooperates right after each outcome
- **SSE** (a squared distance): sum of squared errors, how far a strategy’s behaviour is from the closest ZD strategy. 0 means it behaves exactly like one.

**The SSE math**

- **p = (p₁, p₂, p₃, p₄)** (four chances): the strategy we’re measuring, its chance of cooperating after CC, CD, DC and DD
- **q = (q₁, q₂, q₃, q₄)** (four chances): a zero-determinant (ZD) strategy, built from the recipe
- **q*** (four chances): the ZD strategy closest to p
- **α, alpha** (chance per point): how much the ZD player’s chance of cooperating moves for each point it scored above P
- **β, beta** (chance per point): the same, for each point the other player scored above P
- **χ, chi** (a ratio): the extortion factor, −β/α. The ZD player’s score above P is always χ times the other player’s. 1 is fair (Tit for Tat), 2 is Extort-2.
- **m** (a number): 3p₁ − 2p₂ − 2p₃ − 1, how far p is off the ZD sheet. 0 means it’s on it.
- **d = (3, −2, −2)** (a direction): straight off the ZD sheet. Every step along it changes m by 17.

**The model**

- **R²** (a share): the share of the differences in rank that the model explains. 1 is perfect. Not the same as R, the reward.
- **Spearman correlation** (−1 to 1): how well the predicted order of finish matches the real one. 1 is a perfect match.
- **SHAP value** (a change in rank): how much one feature pushed one strategy’s predicted rank up or down
- **p, as in p < 0.001** (a chance): the p-value, the chance of a gap this big if there were really no difference. Not a strategy.

## Code and data

- Code: https://github.com/aminekhasteh/prisoners_dilemma
- Data for the model, SHAP and noise sections (195 strategies, about 45,600 tournaments): Glynatsi, Knight & Harper, Zenodo record 10246247 (7)
- Data for the cover, the SSE ring, the nice/nasty section and “Meeting strangers from 1980” (272 strategies, including the 1980 Fortran entries): Knight, Campbell, Harper, Gaffney & Glynatsi, Zenodo record 17250038, https://zenodo.org/records/17250038 (11)

## References

1. Prisoner’s dilemma (Flood & Dresher, 1950; Tucker). https://en.wikipedia.org/wiki/Prisoner%27s_dilemma
2. Kuhn, S. Prisoner’s Dilemma. *Stanford Encyclopedia of Philosophy*. https://plato.stanford.edu/entries/prisoner-dilemma/
3. Axelrod, R. (1980). More Effective Choice in the Prisoner’s Dilemma. *Journal of Conflict Resolution*, 24(3), 379–403.
4. Glynatsi, N. E., Knight, V. & Harper, M. (2024). Properties of Winning Iterated Prisoner’s Dilemma Strategies. https://pmc.ncbi.nlm.nih.gov/articles/PMC11670945/
5. The Axelrod project developers. Axelrod-Python library. https://github.com/Axelrod-Python/Axelrod
6. Axelrod-Python strategy index. https://axelrod.readthedocs.io/en/latest/reference/strategy_index.html
7. Glynatsi, Knight & Harper. Tournament data. https://zenodo.org/records/10246247
8. Press, W. H. & Dyson, F. J. (2012). Iterated Prisoner’s Dilemma contains strategies that dominate any evolutionary opponent. *PNAS*, 109(26), 10409–10413.
9. Knight, V., Harper, M., Glynatsi, N. E. & Gillard, J. (2024). Recognising and evaluating the effectiveness of extortion in the Iterated Prisoner’s Dilemma. *PLOS ONE*. https://arxiv.org/abs/1904.00973
10. Lundberg, S. & Lee, S.-I. (2017). A Unified Approach to Interpreting Model Predictions. *NeurIPS*.
11. Knight, V., Campbell, O., Harper, M., Gaffney, T. J. & Glynatsi, N. E. (2025). Reviving, reproducing, and revisiting Axelrod’s second tournament. arXiv:2510.15438. https://arxiv.org/abs/2510.15438
12. Pal, S., Mallela, A., Hilbe, C., Pracher, L., Wei, C., Fu, F., Schnell, S. & Nowak, M. A. (2026). Strategies of cooperation and defection in five large language models. arXiv:2601.09849. https://arxiv.org/abs/2601.09849

[Subscribe widget: Thanks for reading! Subscribe for free to receive new posts and support my work.]
