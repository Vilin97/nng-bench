"""Token usage of a run, summed over the model's API requests (for the API-equivalent cost; the runs used subscriptions).
Claude: final message.usage of each distinct assistant message in the Claude Code session log
(~/.claude/projects/*/<session_id>.jsonl; the stream in agent.jsonl only has usage as of each message's start). Codex: the last cumulative total_token_usage in each
session rollout (~/.codex/sessions). Antigravity (Gemini): input/cache_read/output tokens of each model step (agy_follow.py).
usage: python3 token_usage.py <run> ...  -> JSON per run {"input": uncached input, "cache_write", "cache_read", "output"}"""
import json, re, sys
from pathlib import Path

def usage(run):
    d = Path(__file__).parent / "runs" / run
    tot = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0}
    text = (d / "agent.jsonl").read_text()
    seen = set()
    for line in text.splitlines():
        try: o = json.loads(line)
        except ValueError: continue
        if o.get("type") != "assistant": continue
        if "usage" in o and o.get("model", "").startswith("gemini"):          # Antigravity step
            u = o["usage"]
            tot["input"] += u.get("input_tokens") or 0; tot["cache_read"] += u.get("cache_read_tokens") or 0
            tot["output"] += u.get("output_tokens") or 0
            continue
    final = {}
    for sid in sorted(set(re.findall(r'"session_id":"([^"]+)"', text))):    # Claude
        for f in Path.home().glob(f".claude/projects/*/{sid}.jsonl"):
            for line in f.read_text().splitlines():
                try: o = json.loads(line)
                except ValueError: continue
                m = o.get("message") or {}
                if o.get("type") == "assistant" and m.get("usage"): final[m.get("id")] = m["usage"]   # last entry per message wins
    for u in final.values():
        tot["input"] += u.get("input_tokens", 0); tot["cache_write"] += u.get("cache_creation_input_tokens", 0)
        tot["cache_read"] += u.get("cache_read_input_tokens", 0); tot["output"] += u.get("output_tokens", 0)
    for tid in sorted(set(re.findall(r'"thread_id":"([^"]+)"', text))):         # Codex
        for f in Path.home().glob(f".codex/sessions/*/*/*/*{tid}.jsonl"):
            last = None
            for line in f.read_text().splitlines():
                p = json.loads(line).get("payload", {})
                if p.get("type") == "token_count" and p.get("info"): last = p["info"]["total_token_usage"]
            if last:
                c = last.get("cached_input_tokens", 0)
                tot["input"] += last["input_tokens"] - c; tot["cache_read"] += c; tot["output"] += last["output_tokens"]
    return tot

if __name__ == "__main__":
    print(json.dumps({r: usage(r) for r in sys.argv[1:]}, indent=1))
