"""Results table of the 10-minute runs: levels solved, Lean mistakes, computer-use mistakes, seconds per browser action and
API-equivalent cost, per model and input mode. Writes results.csv and prints a Markdown table (both modes side by side).
Counts only what happened before the clock stopped (600 s of play). Lean mistakes come from the screen recording
(vision_mistakes.py) when available, else from the logs.
usage: python3 results.py"""
import csv, json, subprocess, sys
from pathlib import Path
from cost import cost

B = Path(__file__).parent
MODELS = {  # run name suffix -> display name, in table order
    "claude-fable-5-2": "Claude Fable 5.2", "claude-opus-5-5": "Claude Opus 5.5", "gpt-6.1-terra": "GPT 6.1 Terra",
    "claude-sonnet-5-5": "Claude Sonnet 5.5", "gpt-6.1-sol": "GPT 6.1 Sol", "gpt-6.2-sol": "GPT 6.2 Sol",
    "gemini-4-hydrogen": "Gemini 4 Hydrogen", "gemini-4-neon": "Gemini 4 Neon", "claude-haiku-5-5": "Claude Haiku 5.5",
    "gpt-6.2-astra": "GPT 6.2 Astra", "gemini-4-carbon": "Gemini 4 Carbon",
}

def metrics(run):
    tl = json.loads(subprocess.run([sys.executable, str(B / "levels_timeline.py"), run], capture_output=True, text=True, check=True).stdout)
    s = tl["start"]
    levels = sum(1 for t, _ in tl["solved"] if t - s <= 600)
    v = B / "runs" / run / "vision_mistakes.json"
    lean_src = json.loads(v.read_text())["lean_mistakes"] if v.exists() else tl["lean_mistakes"]
    lean = sum(1 for m in lean_src if m[0] - s <= 600)
    cu = sum(1 for c in tl["cu_mistakes"] if c[0] - s <= 600)
    calls = 0
    for line in (B / "runs" / run / "agent.jsonl").read_text().splitlines():
        try: o = json.loads(line)
        except ValueError: continue
        if o.get("type") == "assistant":
            calls += sum(1 for b in o["message"].get("content", []) if b.get("type") == "tool_use"
                         and b["name"].split("__")[-1].startswith("browser_"))
        if o.get("type") == "item.started" and o.get("item", {}).get("type") == "mcp_tool_call":
            calls += 1
    usd, u = cost(run)
    return {"run": run, "levels": levels, "lean_mistakes": lean, "cu_mistakes": cu, "browser_actions": calls,
            "sec_per_action": round(600 / max(calls, 1), 1), "cost_usd": round(usd, 2),
            **{f"tokens_{k}": v for k, v in u.items()}}

rows = {}
for m in MODELS:
    for mode in ("editor", "typewriter"):
        run = f"{mode}-{m}"
        if (B / "runs" / run / "final_state.json").exists():
            rows[run] = {"model": MODELS[m], "mode": mode, **metrics(run)}

with open(B / "results.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["model", "mode", "run", "levels", "lean_mistakes", "cu_mistakes", "browser_actions", "sec_per_action", "cost_usd",
                                      "tokens_input", "tokens_cache_write", "tokens_cache_read", "tokens_output"])
    w.writeheader(); w.writerows(rows.values())

print("| Model | Levels, editor | Levels, typewriter | Lean mistakes (ed / tw) | Computer-use mistakes (ed / tw) | Sec per action (ed) | Cost (ed / tw) |")
print("|---|---|---|---|---|---|---|")
for m, name in sorted(MODELS.items(), key=lambda kv: -rows.get(f"editor-{kv[0]}", {}).get("levels", 0)):
    e, t = rows.get(f"editor-{m}"), rows.get(f"typewriter-{m}")
    if not e or not t: continue
    print(f"| {name} | {e['levels']} | {t['levels']} | {e['lean_mistakes']} / {t['lean_mistakes']} | {e['cu_mistakes']} / {t['cu_mistakes']} "
          f"| {e['sec_per_action']} | ${e['cost_usd']:.2f} / ${t['cost_usd']:.2f} |")
