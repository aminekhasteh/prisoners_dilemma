"""Check each API key without printing it: list models, show credit where the API exposes it, send one tiny call."""
import asyncio, json, urllib.request
import anthropic, openai
from providers import load_key, AnthropicProvider, OpenAIProvider, OpenRouterProvider
from prompts import SYSTEM_PROMPT, build_prompt, scenarios

WANT = {"anthropic": ["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"],
        "openai": ["gpt-6-luna", "gpt-6.1-terra", "gpt-6.1-sol"]}


def get(url, key):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    return json.load(urllib.request.urlopen(req, timeout=30))


async def main():
    ids = [m.id for m in anthropic.Anthropic(api_key=load_key("ANTHROPIC_API_KEY")).models.list()]
    print("Anthropic models available:", {m: m in ids for m in WANT["anthropic"]})
    oids = [m.id for m in openai.OpenAI(api_key=load_key("OPENAI_API_KEY")).models.list()]
    print("OpenAI models available:", {m: m in oids for m in WANT["openai"]})
    print("  OpenAI gpt-6* ids seen:", sorted(i for i in oids if i.startswith("gpt-6")))
    ork = load_key("OPENROUTER_API_KEY")
    k = get("https://openrouter.ai/api/v1/key", ork)["data"]
    print("OpenRouter key: limit", k.get("limit"), "limit_remaining", k.get("limit_remaining"), "usage", k.get("usage"))
    try:
        c = get("https://openrouter.ai/api/v1/credits", ork)["data"]
        print("OpenRouter credits: total", c.get("total_credits"), "used", c.get("total_usage"))
    except Exception as e:
        print("OpenRouter credits endpoint:", type(e).__name__, str(e)[:120])

    prompt = build_prompt(scenarios("memory1")[0])
    provs = [AnthropicProvider(m) for m in WANT["anthropic"]] + [OpenAIProvider(m) for m in WANT["openai"]] + \
            [OpenRouterProvider("meta-llama/llama-3.3-70b-instruct", temperature=0, top_p=1e-8)]
    total = 0.0
    for p in provs:
        try:
            r = await p.ask(SYSTEM_PROMPT, prompt)
            c = p.cost(r)
            total += c
            print(f"  call OK  {p.model:36s} answer={r.text.strip()[:10]!r:8s} in={r.input_tokens} out={r.output_tokens} "
                  f"reasoning={r.thinking_tokens} ${c:.5f}")
        except Exception as e:
            print(f"  call FAIL {p.model:35s} {type(e).__name__}: {str(e)[:300]}")
    print(f"total test spend ${total:.4f}")

asyncio.run(main())
