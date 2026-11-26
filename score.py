"""Summarise each run: levels the game marks completed, furthest level reached, timeline, API errors."""
import json, re, sys
from pathlib import Path

RUNS = Path(__file__).parent / "runs"
BLOCKED = {"browser_evaluate", "browser_file_upload", "browser_install", "browser_close", "browser_console_messages",
           "browser_network_requests", "browser_run_code"}
MODELS = ["gemini-4-hydrogen", "gemini-4-neon", "gemini-4-carbon", "claude-fable-5-2", "claude-sonnet-5-5", "claude-opus-5-5", "claude-haiku-5-5", "gpt-6-luna", "gpt-6.1-terra", "gpt-6.1-sol", "gpt-6.2-astra", "gpt-6.2-sol"]
names = sys.argv[1:] or [f"{mode}-{m}" for mode in ("typewriter", "editor") for m in MODELS]

for name in names:
    d = RUNS / name
    if not (d / "final_state.json").exists():
        print(f"== {name}: no final state yet"); continue
    st = json.loads((d / "final_state.json").read_text())
    prog = json.loads(st["localStorage"].get("game_progress", "{}"))
    game = prog.get("games", {}).get("g/leanprover-community/nng4", {})
    data = game.get("data", {})
    solved = {w: sorted(int(k) for k, v in lv.items() if isinstance(v, dict) and v.get("completed"))
              for w, lv in data.items()}
    total = sum(len(v) for v in solved.values())

    first_seen, seen = [], set()
    for line in (d / "progress.jsonl").read_text().splitlines():
        r = json.loads(line)
        m = re.search(r"/world/([^/]+)/level/(\d+)", r["url"])
        if m and m.groups() not in seen:
            seen.add(m.groups()); first_seen.append((r["t"], f"{m[1]} {m[2]}"))

    agent = (d / "agent.jsonl").read_text()
    errs = len(re.findall(r'"turn\.failed"|overloaded_error|rate_limit_error|"is_error":true', agent))
    capacity = agent.count("at capacity")
    runner = (d / "runner.log").read_text().splitlines()
    invocations = sum(1 for l in runner if l.startswith("agent invocation"))

    print(f"== {name}: {total} levels solved")
    for w, ks in solved.items():
        print(f"   {w}: {ks}")
    print(f"   final page: {st['url'].split('/nng4/')[-1]}, game mode at end: {'typewriter' if game.get('typewriterMode', True) else 'editor'}")
    print(f"   first reached: " + ", ".join(f"{lvl} @{t//60}:{t%60:02d}" for t, lvl in first_seen))
    tools, violations, bad = {}, 0, {}
    for line in agent.splitlines():
        try: o = json.loads(line)
        except ValueError: continue
        calls = []
        if o.get("type") == "assistant":
            calls = [(b["name"].split("__")[-1], b.get("input")) for b in o["message"].get("content", []) if b.get("type") == "tool_use"]
        it = o.get("item", {})
        if o.get("type") == "item.started" and it.get("type") == "mcp_tool_call":
            calls = [(it["tool"], it.get("arguments"))]
        for n, args in calls:
            tools[n] = tools.get(n, 0) + 1
            # browser tools only; Antigravity's reads of an MCP tool's schema or of a long tool result it saved to a
            # file are part of calling the browser tools (agy_follow.py); anything else (run_command, its own browser...) breaks the rule
            if n in BLOCKED or not (n.startswith("browser_") or n in ("read_tool_schema", "read_tool_output")) \
                    or "javascript:" in json.dumps(args or {}).lower():
                violations += 1; bad[n] = bad.get(n, 0) + 1
    # Codex: its JSON events show MCP calls even when the model reached them through code mode's `exec` tool
    # (JavaScript that calls the browser tools); the session rollout records the actual calls the model made
    code_exec = 0
    for tid in sorted(set(re.findall(r'"thread_id":"([^"]+)"', agent))):
        for f in list(Path.home().glob(f".codex/sessions/*/*/*/*{tid}.jsonl")) + list(Path.home().glob(f".codex/archived_sessions/*{tid}.jsonl")):
            for line in f.read_text().splitlines():
                p = json.loads(line).get("payload", {})
                if p.get("type") == "custom_tool_call" and p.get("name") == "exec": code_exec += 1
    if code_exec: violations += code_exec
    print(f"   tool calls: {dict(sorted(tools.items(), key=lambda x: -x[1]))}")
    print(f"   RULE CHECK: {'VIOLATION x%d' % violations if violations else 'clean (no scripts)'}"
          + (f" ({code_exec} Codex code-mode exec calls: browser tools driven by JavaScript)" if code_exec else "")
          + (f" (non-browser or blocked tools: {bad})" if bad else ""))
    print(f"   agent restarts: {invocations - 1}, failed turns/errors: {errs}, 'at capacity' msgs: {capacity}")
