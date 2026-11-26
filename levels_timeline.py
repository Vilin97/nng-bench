"""When was each level solved? Scans the browser tool results the agent received: each carries the page URL
and a snapshot of the page; a snapshot showing the game's "Level completed" message marks that level solved.
Checked against the final game state (the set of levels marked completed).
Also counts two kinds of mistakes:
- Lean mistakes: each distinct error the game showed on a level (editor mode: error box at a position; typewriter
  mode: a "Failed command"), counted once, when the agent first saw it. "unsolved goals" (unfinished proof) is not one.
- Computer-use mistakes: each browser action that failed (stale element reference, click/type timeout, typing into
  something that isn't a text field, calling a tool that doesn't exist, ...). A wait_for timeout is not one: it is a
  check that some text has not appeared yet.
usage: python3 levels_timeline.py <run_name>
  -> JSON {"t0": recorder start epoch, "start": clock start epoch, "solved": [[epoch, "World L"], ...], "lean_mistakes": [[epoch, level, where, message], ...],
      "cu_mistakes": [[epoch, tool, error], ...]}"""
import json, re, sys, os
from pathlib import Path

run = Path(__file__).parent / "runs" / sys.argv[1]

calls = {}   # Claude tool_use id -> (tool, args)
def results(o):
    """yield (tool, args, text, failed) for each tool result contained in one agent event"""
    if o.get("type") == "assistant":
        for b in o.get("message", {}).get("content", []):
            if b.get("type") == "tool_use": calls[b["id"]] = (b["name"].split("__")[-1], b.get("input") or {})
    if o.get("type") == "user":
        for b in o.get("message", {}).get("content", []):
            if isinstance(b, dict) and b.get("type") == "tool_result":
                c = b.get("content")
                tool, args = calls.get(b.get("tool_use_id"), ("?", {}))
                yield tool, args, c if isinstance(c, str) else " ".join(x.get("text", "") for x in c if isinstance(x, dict)), bool(b.get("is_error"))
    it = o.get("item", {})
    if o.get("type") == "item.completed" and it.get("type") == "mcp_tool_call":
        res = it.get("result") or {}
        c = res.get("content", [])
        failed = bool(res.get("isError") or res.get("is_error") or it.get("error") or it.get("status") == "failed")
        yield it["tool"], it.get("arguments") or {}, "\n".join(x.get("text", "") for x in c if isinstance(x, dict)) or str(it.get("error") or ""), failed

# Game messages that are not mistakes: an unfinished proof, or a placeholder
NOT_MISTAKES = ("unsolved goals", "declaration uses 'sorry'")
def errors(snap):
    """(position, message) of each error box in a page snapshot"""
    out = []
    for m in re.finditer(r"Line (\d+), Character (\d+)\s*\n((?:.*\n){0,4})", snap):
        msg = re.search(r"(?:- text|- generic \[ref=\w+\]|- paragraph \[ref=\w+\]): (.+)", m[3])
        if msg:
            text = msg[1].strip().strip('"')
            if not text.startswith(NOT_MISTAKES) and not re.match(r"Line \d+, Character", text):
                out.append((f"{m[1]}:{m[2]}", text))
    # typewriter mode: a rejected tactic shows as "Failed command: <tactic>" followed by the error
    for m in re.finditer(r"Failed command\s*\n\s*- text: (.+)\n((?:.*\n){0,3})", snap):
        cmd = m[1].strip().strip('"').lstrip(": ").strip()
        msg = re.search(r"- text: (.+)", m[2])
        out.append(("cmd:" + re.sub(r"[\W_]+", "", cmd), msg[1].strip().strip('"') if msg else "failed"))
    return out

def solved_set():
    st = json.loads((run / "final_state.json").read_text())
    data = json.loads(st["localStorage"]["game_progress"])["games"]["g/leanprover-community/nng4"]["data"]
    return {f"{w} {k}" for w, lv in data.items() if isinstance(lv, dict) for k, v in lv.items() if isinstance(v, dict) and v.get("completed")}

from datetime import datetime
lines = (run / "agent.jsonl").read_text().split("\n")
tsfile = run / "agent.ts"   # arrival times; older runs lack it, then Claude's own event timestamps are used
stamps = [float(l.split("\t")[0]) for l in tsfile.read_text().split("\n") if l] if tsfile.exists() else [None] * len(lines)
first, last_event, mistakes, cu = {}, 0, {}, []
for line, t in zip(lines, stamps):
    try: o = json.loads(line)
    except ValueError: continue
    if o.get("timestamp"): t = datetime.fromisoformat(o["timestamp"].replace("Z", "+00:00")).timestamp()
    if t is None: continue
    last_event = max(last_event, t)
    for tool, args, text, failed in results(o):
        if failed:
            if not (tool == "browser_wait_for" and "Timeout" in text):
                cu.append([t, tool, re.sub(r"\s+", " ", text.split("Error:", 1)[-1]).strip()[:120]])
            continue
        m = re.search(r"Page URL: \S*/world/(\w+)/level/(\d+)", text)
        snap = text.split("Page Snapshot", 1)[-1] if "Page Snapshot" in text else ""
        if not m: continue
        level = f"{m[1]} {m[2]}"
        if re.search(r"Level completed", snap):
            first.setdefault(level, t)
        # mistakes: each distinct error the game shows on a level, counted once, when the agent first sees it;
        # skipped while the agent types a word one key at a time (half-typed words show passing errors)
        if tool == "browser_press_key" and len(str(args.get("key", ""))) == 1: continue
        for pos, msg in errors(snap):
            # typewriter: one mistake per rejected tactic (its error text may still be loading in an early snapshot)
            key = (level, pos) if pos.startswith("cmd:") else (level, pos, msg)
            if key not in mistakes: mistakes[key] = (t, msg)

final = solved_set()
# recorder start: progress.jsonl logs seconds since recorder start; its last line was written ~when the file was last modified
prog = (run / "progress.jsonl").read_text().split("\n")
last_t = json.loads([l for l in prog if l][-1])["t"]
t0 = os.path.getmtime(run / "progress.jsonl") - last_t - 0.5
start = json.loads((run / "meta.json").read_text())["start"]
# fallback for solved levels no snapshot showed as completed: the end of the first visit to that level
# (the agent moves on right after solving); on the final page, the agent's last event
visits, prev = {}, None
for l in prog:
    if not l: continue
    r = json.loads(l)
    m = re.search(r"/world/(\w+)/level/(\d+)", r["url"])
    cur = f"{m[1]} {m[2]}" if m else None
    if cur != prev and prev and prev not in visits: visits[prev] = t0 + r["t"]
    prev = cur
missing = sorted(final - set(first))
for l in missing:
    first[l] = visits.get(l, last_event)
extra = sorted(set(first) - final)
print(json.dumps({"t0": t0, "start": start, "solved": sorted([[t, l] for l, t in first.items() if l in final]),
                  "fallback": missing,
                  "lean_mistakes": sorted([t, k[0], k[1], msg] for k, (t, msg) in mistakes.items()), "cu_mistakes": sorted(cu), "not_in_final": extra}))
