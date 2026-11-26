"""Write codex_catalog_direct.json: the Codex model catalog (~/.codex/models_cache.json, written by Codex itself) with every
model switched to direct tool calls. Codex >= 0.160 runs GPT 6.x in "code_mode_only": every tool is reached through an `exec`
tool that runs JavaScript, so the model can script the browser, which the benchmark forbids. run.sh passes this file to
Codex with -c model_catalog_json=... (the tool_mode config key itself is ignored).
usage: python3 make_codex_catalog.py   (run Codex once first so the cache exists)"""
import json
from pathlib import Path

cache = json.loads((Path.home() / ".codex/models_cache.json").read_text())
for m in cache["models"]:
    m.update(tool_mode="direct",              # browser tools called one at a time, no JavaScript `exec`
             supports_search_tool=False,      # tool search breaks with direct tools ("unsupported call: tool_search_tool")
             experimental_supported_tools=[], multi_agent_version=None, apply_patch_tool_type=None)  # no sub-agents, no file edits
out = Path(__file__).parent / "codex_catalog_direct.json"
out.write_text(json.dumps({"models": cache["models"]}, indent=1))
print(f"{len(cache['models'])} models -> {out}")
