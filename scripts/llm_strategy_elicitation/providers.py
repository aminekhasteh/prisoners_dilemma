"""Thin async adapters around the model APIs. Each call returns the raw text, token usage and settings.

Keys are read from ~/.config/pd-llm/keys.env (KEY=VALUE lines, mode 600) and passed to the clients directly,
never printed or written to the results.
"""
from __future__ import annotations

import os
import random
import stat
from dataclasses import dataclass
from pathlib import Path

KEYS_FILE = Path(os.environ.get("PD_LLM_KEYS", "~/.config/pd-llm/keys.env")).expanduser()

# USD per million tokens (input, output). Output includes thinking tokens. Check before large runs.
PRICES = {
    "claude-opus-5-5": (4.0, 20.0),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-fable-5-1": (10.0, 50.0),
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-2.5-pro": (1.25, 10.0),
    "gpt-6-luna": (0.10, 0.50),
    "gpt-6.1-terra": (1.0, 5.0),
    "gpt-6.1-sol": (2.0, 10.0),
    "fake": (0.0, 0.0),
}


def load_key(name: str) -> str:
    if not KEYS_FILE.exists():
        raise SystemExit(f"{KEYS_FILE} not found; see README (API keys)")
    if KEYS_FILE.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise SystemExit(f"{KEYS_FILE} is readable by others; run: chmod 600 {KEYS_FILE}")
    for line in KEYS_FILE.read_text().splitlines():
        k, _, v = line.strip().partition("=")
        if k.strip() == name and v.strip():
            return v.strip().strip('"').strip("'")
    raise SystemExit(f"{name} is not set in {KEYS_FILE}")


@dataclass
class Reply:
    text: str
    input_tokens: int
    output_tokens: int     # includes thinking tokens
    thinking_tokens: int | None = None
    stop_reason: str | None = None


class Provider:
    name = "base"
    model = ""

    def settings(self) -> dict:
        raise NotImplementedError

    async def ask(self, system: str, prompt: str) -> Reply:
        raise NotImplementedError

    def cost(self, r: Reply) -> float:
        pin, pout = PRICES.get(self.model, (None, None))
        if pin is None:
            raise SystemExit(f"no price for {self.model}; add it to PRICES in providers.py")
        return (r.input_tokens * pin + r.output_tokens * pout) / 1e6


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, model, effort=None, thinking=None, max_tokens=4000):
        import anthropic
        self.model, self.effort, self.thinking, self.max_tokens = model, effort, thinking, max_tokens
        self.client = anthropic.AsyncAnthropic(api_key=load_key("ANTHROPIC_API_KEY"), max_retries=6)

    def settings(self):
        return {"provider": self.name, "model": self.model, "effort": self.effort, "thinking": self.thinking,
                "max_tokens": self.max_tokens, "temperature": "default (not settable)"}

    async def ask(self, system, prompt):
        kw = dict(model=self.model, max_tokens=self.max_tokens, system=system,
                  messages=[{"role": "user", "content": prompt}])
        if self.effort:
            kw["output_config"] = {"effort": self.effort}
        if self.thinking:
            kw["thinking"] = {"type": self.thinking}
        m = await self.client.messages.create(**kw)
        text = "".join(b.text for b in m.content if b.type == "text")
        return Reply(text, m.usage.input_tokens, m.usage.output_tokens, None, m.stop_reason)


class GeminiProvider(Provider):
    name = "gemini"

    def __init__(self, model, temperature=None, seed=None, thinking_budget=None, max_tokens=4000):
        from google import genai
        self.model, self.temperature, self.seed = model, temperature, seed
        self.thinking_budget, self.max_tokens = thinking_budget, max_tokens
        self.client = genai.Client(api_key=load_key("GEMINI_API_KEY"))

    def settings(self):
        return {"provider": self.name, "model": self.model, "temperature": self.temperature, "seed": self.seed,
                "thinking_budget": self.thinking_budget, "max_tokens": self.max_tokens}

    async def ask(self, system, prompt):
        from google.genai import types
        cfg = dict(system_instruction=system, max_output_tokens=self.max_tokens)
        if self.temperature is not None:
            cfg["temperature"] = self.temperature
        if self.seed is not None:
            cfg["seed"] = self.seed
        if self.thinking_budget is not None:
            cfg["thinking_config"] = types.ThinkingConfig(thinking_budget=self.thinking_budget)
        r = await self.client.aio.models.generate_content(
            model=self.model, contents=prompt, config=types.GenerateContentConfig(**cfg))
        u = r.usage_metadata
        thoughts = u.thoughts_token_count or 0
        out = (u.candidates_token_count or 0) + thoughts
        stop = r.candidates[0].finish_reason.name if r.candidates and r.candidates[0].finish_reason else None
        return Reply(r.text or "", u.prompt_token_count or 0, out, thoughts, stop)


class OpenAIProvider(Provider):
    name = "openai"

    def __init__(self, model, effort=None, temperature=None, max_tokens=4000):
        import openai
        self.model, self.effort, self.temperature, self.max_tokens = model, effort, temperature, max_tokens
        self.client = openai.AsyncOpenAI(api_key=load_key("OPENAI_API_KEY"), max_retries=6)

    def settings(self):
        return {"provider": self.name, "model": self.model, "reasoning_effort": self.effort,
                "temperature": self.temperature, "max_tokens": self.max_tokens}

    async def ask(self, system, prompt):
        kw = dict(model=self.model, instructions=system, input=prompt, max_output_tokens=self.max_tokens)
        if self.effort:
            kw["reasoning"] = {"effort": self.effort}
        if self.temperature is not None:
            kw["temperature"] = self.temperature
        r = await self.client.responses.create(**kw)
        u = r.usage
        rt = getattr(getattr(u, "output_tokens_details", None), "reasoning_tokens", None)
        return Reply(r.output_text or "", u.input_tokens, u.output_tokens, rt, r.status)


class FakeProvider(Provider):
    """Offline stand-in: answers L with a fixed probability per outcome, for testing the pipeline at no cost."""
    name = "fake"
    model = "fake"
    P = {"round1": 0.9, "CC": 1.0, "CD": 0.1, "DC": 0.6, "DD": 0.3}

    def __init__(self, seed=0, invalid_rate=0.05):
        self.rng, self.invalid_rate = random.Random(seed), invalid_rate

    def settings(self):
        return {"provider": "fake", "model": "fake", "p": self.P, "invalid_rate": self.invalid_rate}

    async def ask(self, system, prompt):
        if self.rng.random() < self.invalid_rate:
            return Reply("I would choose L because...", 250, 8)
        if "This is the first round." in prompt:
            p = self.P["round1"]
        else:
            last = [l for l in prompt.splitlines() if "you chose" in l][-1]
            own, other = last.split("you chose ")[1][0], last.split("chose ")[-1][0]
            p = self.P[{"L": "C", "R": "D"}[own] + {"L": "C", "R": "D"}[other]]
        return Reply("L" if self.rng.random() < p else "R", 250, 1)


def make_provider(args) -> Provider:
    if args.provider == "fake":
        return FakeProvider(seed=args.seed or 0)
    if args.provider == "anthropic":
        return AnthropicProvider(args.model, effort=args.effort, thinking=args.thinking)
    if args.provider == "openai":
        return OpenAIProvider(args.model, effort=args.effort, temperature=args.temperature)
    if args.provider == "gemini":
        return GeminiProvider(args.model, temperature=args.temperature, seed=args.seed,
                              thinking_budget=args.thinking_budget)
    raise SystemExit(f"unknown provider {args.provider}")
