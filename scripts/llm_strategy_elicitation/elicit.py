"""Ask a model the Pal et al. prompts N times per scenario and append every reply to a JSONL file.

Each trial is one fresh, stateless call. A reply that is not a bare L or R is logged as invalid and the trial is
re-asked (up to --attempts times). Re-running the same command resumes: trials already in the file are skipped.

  python elicit.py --provider fake --model fake --tag fake_test
  python elicit.py --provider gemini --model gemini-3.1-flash-lite --temperature 0 --seed 42 \
      --experiments memory1,memory2 --trials 50 --max-usd 2 --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import sys
import time
from collections import Counter
from pathlib import Path

from prompts import EXPERIMENTS, SYSTEM_PROMPT, build_prompt, parse_answer, scenarios
from providers import PRICES, make_provider

HERE = Path(__file__).resolve().parent


def read_done(path: Path):
    valid, spent = Counter(), 0.0
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            spent += r.get("cost_usd", 0.0)
            if r["choice"] is not None:
                valid[(r["key"], r["trial"])] += 1
    return valid, spent


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", required=True, choices=["anthropic", "openai", "openrouter", "gemini", "fake"])
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", help="name of the run (default: model name)")
    ap.add_argument("--experiments", default="memory1,memory2")
    ap.add_argument("--trials", type=int, default=50)
    ap.add_argument("--attempts", type=int, default=3, help="tries per trial when the reply is not L or R")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--max-usd", type=float, default=1.0, help="stop when this run's spend reaches this")
    ap.add_argument("--limit", type=int, help="stop after this many new calls (for timing/cost probes)")
    ap.add_argument("--temperature", type=float)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--top-p", type=float)
    ap.add_argument("--max-tokens", type=int, help="override the provider's max output tokens (reasoning models need room)")
    ap.add_argument("--host", help="OpenRouter: pin one serving provider, e.g. deepinfra")
    ap.add_argument("--effort", help="Anthropic effort or OpenAI reasoning effort (e.g. none, low, high)")
    ap.add_argument("--thinking", help="Anthropic thinking type, e.g. adaptive or between_tools")
    ap.add_argument("--thinking-budget", type=int, help="Gemini thinking budget (0 = off where allowed)")
    ap.add_argument("--est-in", type=int, default=300, help="dry run: assumed input tokens per call")
    ap.add_argument("--est-out", type=int, default=2, help="dry run: assumed output (+thinking) tokens per call")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    exps = args.experiments.split(",")
    for e in exps:
        if e not in EXPERIMENTS:
            sys.exit(f"unknown experiment {e}; choose from {EXPERIMENTS}")
    scen = [s for e in exps for s in scenarios(e)]
    tag = args.tag or args.model
    out = HERE / "results" / "raw" / f"{tag}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    valid, spent = read_done(out)
    todo = [(s, t) for s in scen for t in range(args.trials) if not valid[(s.key, t)]]
    if args.limit:
        todo = todo[: args.limit]

    pin, pout = PRICES.get(args.model, (float("nan"), float("nan")))
    est = len(todo) * (args.est_in * pin + args.est_out * pout) / 1e6
    print(f"{tag}: {len(scen)} scenarios x {args.trials} trials; {len(todo)} calls to make; "
          f"spent so far ${spent:.4f}; estimate for the rest ${est:.2f} "
          f"(at {args.est_in} in / {args.est_out} out tokens per call)")
    if args.dry_run or not todo:
        return

    prov = make_provider(args)
    from prompts import VARIANT
    settings = {**prov.settings(), "prompt_variant": VARIANT}
    lock, sem = asyncio.Lock(), asyncio.Semaphore(args.concurrency)
    stats = Counter()
    stop = asyncio.Event()
    t0 = time.time()
    fh = out.open("a")

    async def one(s, trial):
        nonlocal spent
        prompt = build_prompt(s)
        for attempt in range(args.attempts):
            if stop.is_set():
                return
            async with sem:
                try:
                    r = await prov.ask(SYSTEM_PROMPT, prompt)
                except Exception as e:  # SDKs already retry 429/5xx; anything left is logged and skipped
                    stats["errors"] += 1
                    print(f"error on {s.key} trial {trial}: {type(e).__name__}: {str(e)[:200]}", file=sys.stderr)
                    if stats["errors"] >= 20:
                        stop.set()
                    return
            choice = parse_answer(r.text)
            c = prov.cost(r)
            rec = {"time": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "tag": tag,
                   "key": s.key, "experiment": s.experiment, "treatment": s.treatment, "kind": s.kind,
                   "prev3": s.prev3, "prev2": s.prev2, "prev1": s.prev1, "trial": trial, "attempt": attempt,
                   "text": r.text[:200], "choice": choice, "input_tokens": r.input_tokens,
                   "output_tokens": r.output_tokens, "thinking_tokens": r.thinking_tokens,
                   "stop_reason": r.stop_reason, "cost_usd": c, "settings": settings}
            async with lock:
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                spent += c
                stats["calls"] += 1
                stats["valid" if choice else "invalid"] += 1
                if spent >= args.max_usd and not stop.is_set():
                    print(f"spend cap ${args.max_usd} reached; stopping", file=sys.stderr)
                    stop.set()
                if stats["calls"] % 100 == 0:
                    print(f"  {stats['calls']} calls, {stats['invalid']} invalid, ${spent:.4f}, "
                          f"{time.time() - t0:.0f} s", flush=True)
            if choice:
                return

    await asyncio.gather(*(one(s, t) for s, t in todo))
    fh.close()
    print(f"done: {dict(stats)}; total spent ${spent:.4f}; {time.time() - t0:.0f} s; results in {out}")


if __name__ == "__main__":
    asyncio.run(main())
