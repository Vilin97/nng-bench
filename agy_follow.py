"""Follow an Antigravity conversation's transcript while it runs and write it into the run directory in the same
event format the Claude runs use (so score.py, levels_timeline.py, vision_mistakes.py and make_fast.py work unchanged):
  agent.jsonl  {"type":"assistant","timestamp":..,"message":{"content":[thinking/text/tool_use]}} and
               {"type":"user","timestamp":..,"message":{"content":[tool_result]}}
  agent.ts     "<epoch>\tevent" per agent.jsonl line
  agent_raw.jsonl  the Antigravity transcript lines as they were
  agy_idle     present (with the epoch) while the model's turn has ended: its last response had no tool calls
Antigravity reaches MCP tools in two steps: read_file on ~/.gemini/antigravity/mcp/<server>/<tool>.json (the tool's
schema), then call_mcp_tool. The schema read is logged as tool "read_tool_schema"; call_mcp_tool as the MCP tool itself
(mcp__playwright__browser_click, ...); reading a long tool result Antigravity saved to a file is
"read_tool_output" (with the line-number prefixes removed, so it reads like the page snapshot it is). Any other tool keeps its Antigravity name (run_command, browser_subagent, ...).
usage: python3 agy_follow.py <conversation_id> <run_dir>   (runs until killed)"""
import json, re, sys, time
from datetime import datetime
from pathlib import Path

cid, out = sys.argv[1], Path(sys.argv[2])
src = Path.home() / ".gemini/antigravity/brain" / cid / ".system_generated/logs/transcript_full.jsonl"
jl, ts, raw = open(out / "agent.jsonl", "a"), open(out / "agent.ts", "a"), open(out / "agent_raw.jsonl", "a")
idle = out / "agy_idle"

def iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()

def emit(o):
    jl.write(json.dumps(o) + "\n"); jl.flush()
    ts.write(f"{time.time():.2f}\tevent\n"); ts.flush()

def tool_name(c):
    a = c.get("args") or {}
    if c["name"] == "call_mcp_tool":
        return f"mcp__{a.get('ServerName', '?')}__{a.get('ToolName', '?')}", a.get("Arguments") or {}
    if c["name"] == "read_file" and re.search(r"/\.gemini/antigravity/mcp/[^/]+/[^/]+\.json$", str(a.get("Path", ""))):
        return "read_tool_schema", a
    if c["name"] == "read_file" and f"/.gemini/antigravity/brain/{cid}/" in str(a.get("Path", "")):
        return "read_tool_output", a   # a long tool result that Antigravity saved to a file instead of showing it
    return c["name"], a

pending, n, seen = [], 0, 0
while True:
    lines = src.read_text().splitlines() if src.exists() else []
    for line in lines[seen:]:
        raw.write(line + "\n"); raw.flush()
        try: o = json.loads(line)
        except ValueError: continue
        t = o.get("created_at")
        if o.get("type") == "PLANNER_RESPONSE":
            content = []
            if o.get("thinking"): content.append({"type": "thinking", "thinking": o["thinking"]})
            if o.get("content"): content.append({"type": "text", "text": o["content"]})
            for c in o.get("tool_calls") or []:
                n += 1
                name, args = tool_name(c)
                content.append({"type": "tool_use", "id": f"agy{n}", "name": name, "input": args})
                pending.append((f"agy{n}", name))
            emit({"type": "assistant", "timestamp": t, "model": o.get("model"), "status": o.get("status"),
                  "usage": {k: o.get(k) for k in ("input_tokens", "cache_read_tokens", "output_tokens")}, "message": {"content": content}})
            if o.get("tool_calls"): idle.unlink(missing_ok=True)
            elif o.get("status") == "DONE": idle.write_text(f"{time.time():.0f}")
        elif o.get("source") == "MODEL" and pending:
            # a tool's result; its text starts with "Created At: ..." / "Completed At: ..." lines
            text = o.get("content") or ""
            done = re.findall(r"Completed At: (\S+)", text)
            body = re.sub(r"^(?:(?:Created|Completed) At: \S+\n)+", "", text)
            failed = o.get("status") not in ("DONE", None) or bool(o.get("error"))
            uid, name = pending.pop(0)
            if name == "read_tool_output":   # drop the "Showing lines a-b of n" header and the "<line>: " prefixes
                body = re.sub(r"^Showing lines \d+-\d+ of \d+\n", "", body)
                body = re.sub(r"(?m)^\d+: ?", "", body)
            emit({"type": "user", "timestamp": done[-1] if done else t, "message": {"content": [
                {"type": "tool_result", "tool_use_id": uid, "content": body or str(o.get("error") or ""), "is_error": failed}]}})
        else:
            emit({"type": "system", "timestamp": t, "agy_type": o.get("type"), "status": o.get("status"),
                  "content": (o.get("content") or "")[:2000]})
    seen = len(lines)
    time.sleep(0.5)
