"""API-equivalent cost of each run (the runs used subscriptions, so nothing was billed per token): token_usage.py totals x list
prices, $ per million tokens, as of 2026-11-26. Claude: Anthropic's model table (cache writes 1.25x input). OpenAI and Google:
third-party summaries of their pricing pages (GPT 6.2 Sol cache writes $2.50 not applied: Codex reports none; Gemini 4 Carbon at its
introductory rate, which rises to $4/$20 on 2026-12-01). Long-prompt surcharges (>272K input on GPT) do not apply: prompts stayed below.
Price sources: Claude: Anthropic's models table (claude-api docs, cached 2026-11-03); GPT 6.2: lindy.ai/blog/gpt-6-2-astra,
requesty.ai/blog/gpt-6-2-sol-astra-pricing-benchmarks; GPT 6 Luna: eesel.ai/blog/gpt-6-luna-pricing, apidog.com/blog/gpt-6-luna-high-volume-api-workloads;
GPT 6.1: eesel.ai/blog/gpt-6-1-terra-pricing, reflektlab.ai/blog/openai-api-pricing;
DeepSeek V4.1 Flash on Nebius Token Factory: getmaxim.ai/bifrost/llm-cost-calculator/provider/nebius/model/deepseek-v4.1-flash
(cached input billed as input: nebius.com/prices-ai-studio lists no cache discount);
Gemini 4: techjacksolutions.com/ai-tools/google-gemini/gemini-4-pricing-and-api, cloudinsight.cc/en/blog/gemini-4-carbon-neon-hydrogen-guide.
usage: python3 cost.py <run> ...  -> run, $ cost, token totals"""
import json, sys
from token_usage import usage

PRICES = {  # input, cache write, cache read, output
    "claude-fable-5-2": (8, 10, 0.20, 40), "claude-opus-5-5": (4, 5, 0.20, 20), "claude-sonnet-5-5": (2, 2.5, 0.10, 10),
    "claude-haiku-5-5": (0.10, 0.125, 0.01, 0.50),
    "gpt-6-luna": (0.10, 0, 0.01, 0.50),
    "deepseek-4.1-flash": (0.30, 0, 0.30, 1.20),   # Nebius Token Factory; no cached-input discount listed
    "gpt-6.1-terra": (1, 0, 0.05, 5), "gpt-6.1-sol": (2, 0, 0.10, 10), "gpt-6.2-sol": (2, 0, 0.10, 10), "gpt-6.2-astra": (8, 0, 0.40, 40),
    "gemini-4-hydrogen": (1.50, 0, 0.075, 7.50), "gemini-4-neon": (3, 0, 0.15, 15), "gemini-4-carbon": (2, 0, 0.10, 10),
}

def cost(run):
    model = run.split("-", 1)[1].removeprefix("editor-")
    pi, pw, pr, po = PRICES[model]
    u = usage(run)
    return (u["input"] * pi + u["cache_write"] * pw + u["cache_read"] * pr + u["output"] * po) / 1e6, u

if __name__ == "__main__":
    for r in sys.argv[1:]:
        c, u = cost(r)
        print(f"{r:32s} ${c:6.2f}  in {u['input']:>9,}  cache_w {u['cache_write']:>9,}  cache_r {u['cache_read']:>11,}  out {u['output']:>8,}")
