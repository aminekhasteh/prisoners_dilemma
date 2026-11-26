---
name: "self-eval"
description: "Grade finished work honestly on two axes with a devil's-advocate pass against inflation. Use whenever the user asks how well a task went, to rate the work or for an honest self-review."
license: "MIT"
---

# Self-Eval: Honest Work Evaluation

ultrathink

AI self-assessment converges to "everything is a 4" because a single-axis score conflates task difficulty with execution quality. This skill separates the two axes, combines them through a fixed matrix, runs a devil's-advocate pass, and checks the score history for clustering.

## Examples

### Example 1: Feature Implementation

```
/self-eval added pagination to the user list API
```

Output:
```
## Self-Evaluation

**Task:** Added cursor-based pagination to the user list API endpoint
**Ambition:** Medium — New feature with established patterns, but required careful backwards compatibility
**Execution:** Strong — All tests pass, handles edge cases, existing clients unaffected

**Devil's Advocate:**
- Lower: Pagination is well-documented. The pattern was copied from another endpoint with minor changes. Could argue Low ambition.
- Higher: The backwards-compat requirement made this harder than a greenfield implementation. Had to support both offset and cursor modes.
- Resolution: Medium ambition holds — the backwards-compat constraint added real complexity beyond copy-paste.

**Score: 4** — Solid execution on meaningful work with real constraints.
```

### Example 2: Bug Fix

```
/self-eval
```

Output:
```
## Self-Evaluation

**Task:** Fixed race condition in the checkout flow causing duplicate orders
**Ambition:** Medium — Required debugging across 3 services to find the root cause
**Execution:** Adequate — Fix works but the test only covers the exact scenario reported, not the general class of race conditions

**Devil's Advocate:**
- Lower: The fix was a single line (adding a mutex). Once found, it was trivial.
- Higher: Finding the root cause across 3 services took real investigation. The mutex placement required understanding the full flow.
- Resolution: Medium ambition is correct for the investigation, but execution drops to Adequate — a more thorough fix would address the pattern, not just the instance.

**Score: 3** — Good debugging work but the fix is narrow.
```

---

## What to Evaluate

$ARGUMENTS

If no arguments provided, review the full conversation history to identify what was accomplished this session. Summarize the work in one sentence before scoring.

## How to Score — Two-Axis Model

Score on two independent axes, then combine using the matrix. Do NOT pick a number first and rationalize it — rate each axis separately, then read the matrix.

### Axis 1: Task Ambition (what was attempted)

Rate the difficulty and risk of what was worked on. NOT how well it was done.

- **Low (1)** — Safe, familiar, routine. No real risk of failure. Examples: minor config changes, simple refactors, copy-paste with small modifications, tasks you were confident you'd complete before starting.
- **Medium (2)** — Meaningful work with novelty or challenge. Partial failure was possible. Examples: new feature implementation, integrating an unfamiliar API, architectural changes, debugging a tricky issue.
- **High (3)** — Ambitious, unfamiliar, or high-stakes. Real risk of complete failure. Examples: building something from scratch in an unfamiliar domain, complex system redesign, performance-critical optimization, shipping to production under pressure.

**Self-check:** If you were confident of success before starting, ambition is Low or Medium, not High.

### Axis 2: Execution Quality (how well it was done)

Rate the quality of the actual output, independent of how ambitious the task was.

- **Poor (1)** — Major failures, incomplete, wrong output, or abandoned mid-task. The deliverable doesn't meet its own stated criteria.
- **Adequate (2)** — Completed but with gaps, shortcuts, or missing rigor. Did the thing but left obvious improvements on the table.
- **Strong (3)** — Well-executed, thorough, quality output. No obvious improvements left undone given the scope.

### Composite Score Matrix

|                        | Poor Exec (1) | Adequate Exec (2) | Strong Exec (3) |
|------------------------|:---:|:---:|:---:|
| **Low Ambition (1)**   |  1  |  2  |  2  |
| **Medium Ambition (2)**|  2  |  3  |  4  |
| **High Ambition (3)**  |  2  |  4  |  5  |

**Read the matrix, don't override it.** The composite is your score. The devil's advocate below can cause you to re-rate an axis — but you cannot directly override the matrix result.

Key properties:
- Low ambition caps at 2. Safe work done perfectly is still safe work.
- A 5 requires BOTH high ambition AND strong execution. It should be rare.
- High ambition + poor execution = 2. Bold failure hurts.
- The most common honest score for solid work is 3 (medium ambition, adequate execution).

## Devil's Advocate

Before writing your final score, write all three of these:

1. **Case for LOWER:** Why might this work deserve a lower score? What was easy, what was avoided, what was less ambitious than it appears? Would a skeptical reviewer agree with your axis ratings?
2. **Case for HIGHER:** Why might this work deserve a higher score? What was genuinely challenging, surprising, or exceeded the original plan?
3. **Resolution:** If either case reveals you mis-rated an axis, re-rate it and recompute the matrix result. Then state your final score with a 1-2 sentence justification that addresses at least one point from each case.

Each case names concrete points from the work itself; a case that could apply to any task isn't doing its job.

## Anti-Inflation Check

Check for a score history file at `.self-eval-scores.jsonl` in the current working directory.

If the file exists, read it and check the last 5 scores. If 4+ of the last 5 are the same number, flag it:
> **Warning: Score clustering detected.** Last 5 scores: [list]. Consider whether you're anchoring to a default.

If the file doesn't exist, ask yourself: "Would an outside observer rate this the same way I am?"

## Score Persistence

After presenting your evaluation, append one line to `.self-eval-scores.jsonl` in the current working directory:

```json
{"date":"YYYY-MM-DD","score":N,"ambition":"Low|Medium|High","execution":"Poor|Adequate|Strong","task":"1-sentence summary"}
```

This enables the anti-inflation check to work across sessions. If the file doesn't exist, create it.

## Output Format

Present your evaluation as:

## Self-Evaluation

**Task:** [1-sentence summary of what was attempted]
**Ambition:** [Low/Medium/High] — [1-sentence justification]
**Execution:** [Poor/Adequate/Strong] — [1-sentence justification]

**Devil's Advocate:**
- Lower: [why it might deserve less]
- Higher: [why it might deserve more]
- Resolution: [final reasoning]

**Score: [1-5]** — [1-sentence final justification]
