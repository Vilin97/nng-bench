#!/bin/bash
# usage: run.sh <name> <claude|codex|agy> <model> [duration_s]
# agy: Gemini models through the running Antigravity app (agentapi; agy.sh/agy_rpc.sh/agy_follow.py); its Playwright MCP
#   server and tool grants are set in ~/.gemini/config (mcp_config.json, config.json globalPermissionGrants).
# INPUT_MODE=typewriter (default: one tactic at a time) or editor (whole proof in a multi-line editor)
# GOAL=timed (default: as many levels as possible in DURATION) or end (finish the whole game, in order; DURATION is only a safety cap).
#   GOAL=end also removes the URL/tab tools, so the agent moves only with the game's own buttons and the game's
#   level locks prevent skipping; the run stops as soon as the game marks all levels completed.
# Thinking is logged as summaries (Claude: --thinking-display summarized; Codex: model_reasoning_summary=detailed),
# so the video can show it. Earlier runs (before 2026-11-17) logged no thinking text.
# Fresh headless Chromium profile on NNG Tutorial level 1; 25 fps recorder + agent (browser tools only) for DURATION seconds.
set -um
NAME=$1; KIND=$2; MODEL=$3; DUR=${4:-600}
B=$HOME/Github/nng-bench
# tools that run code or are not needed to play; removed from both harnesses
BLOCKED=(browser_evaluate browser_file_upload browser_install browser_close browser_console_messages browser_network_requests)
OUT=$B/runs/$NAME; rm -rf "$OUT"; mkdir -p "$OUT/work"
PORT=${PORT:-9333}   # one Chromium per port; parallel runs use different ports
CHROME=$HOME/Library/Caches/ms-playwright/chromium-1194/chrome-mac/Chromium.app/Contents/MacOS/Chromium
URL='https://adam.math.hhu.de/#/g/leanprover-community/nng4/world/Tutorial/level/1'
unset CLAUDECODE

pkill -f "remote-debugging-port=$PORT"; sleep 1
"$CHROME" --headless=new --remote-debugging-port=$PORT --user-data-dir="$OUT/profile" \
  --window-size=1440,1090 --no-first-run --no-default-browser-check "$URL" >"$OUT/chrome.log" 2>&1 &
CHROME_PID=$!
for i in $(seq 30); do curl -s localhost:$PORT/json/version >/dev/null && break; sleep 1; done
sleep 12   # let the game page fully load before the clock starts
MODE=${INPUT_MODE:-typewriter}
if [ "$MODE" = editor ]; then
  node $B/setmode.mjs $PORT > "$OUT/setmode.log" 2>&1 || { echo "could not switch to editor mode" >> "$OUT/runner.log"; exit 1; }
fi

# Antigravity: one Playwright MCP server per port ("playwright" for 9333, else "playwright<port>"), all defined in
# ~/.gemini/config/mcp_config.json. RefreshMcpServers restarts ALL of them, so parallel runs refresh once beforehand
# and set AGY_NO_REFRESH=1.
AGY_SERVER=playwright; [ "$PORT" != 9333 ] && AGY_SERVER=playwright$PORT
if [ "$KIND" = agy ] && [ "${AGY_NO_REFRESH:-0}" != 1 ]; then
  $B/agy_rpc.sh RefreshMcpServers >/dev/null
  for i in $(seq 20); do $B/agy_rpc.sh GetMcpServerStates | grep -q MCP_SERVER_STATUS_READY && break; sleep 1; done
fi

GOAL=${GOAL:-timed}
TOTAL_LEVELS=79   # NNG4: 9 worlds (gamedata/game.json worldSize)
# Power World level 10 is Fermat's Last Theorem: unprovable in the game by design (its conclusion says
# "Either that, or you used magic"), so the game is finished when the other 78 levels are solved.
STOP_AT=$((TOTAL_LEVELS-1))
[ "$GOAL" = end ] && BLOCKED+=(browser_navigate browser_navigate_back browser_tabs)

MCP_BIN=$B/node_modules/.bin/mcp-server-playwright
cat > "$OUT/mcp.json" <<EOF
{"mcpServers":{"playwright":{"command":"$MCP_BIN","args":["--cdp-endpoint","http://127.0.0.1:$PORT","--output-dir","$OUT/mcp-out"]}}}
EOF

if [ "$MODE" = editor ]; then
  MODE_TEXT="The game is in Editor mode: each level has a multi-line code editor below the theorem statement, where you write the whole proof (one tactic per line, indented as usual in Lean). The game checks the proof as you edit it and shows the current goal and any errors below the editor; when the proof is complete you can go to the next level. Typing into the editor inserts text at the cursor; it does not replace what is already there. Stay in Editor mode (do not switch to Typewriter mode)."
else
  # typewriter runs before 2026-11-18 used the prompt without this sentence (GPT 6.2 Sol then switched itself to Editor mode)
  MODE_TEXT="Stay in Typewriter mode (do not switch to Editor mode)."
fi
if [ "$GOAL" = end ]; then
  GOAL_TEXT="Your goal: finish the whole game: solve every level of every world, in order, starting from Tutorial World Level 1. There is no time limit, but play efficiently. Do not skip levels: solve each level before you move on to the next one; when a world is finished, go back to the world map and continue with a world that has become available. The game is finished when every level of every world is solved. A level only counts if you actually solve it in the game. Play only through the browser: read the goal and messages on the page, enter tactics into the game's input, and move between levels and worlds with the game's own buttons and links (you cannot type URLs)."
  CONT="You are not done yet. Continue playing the Natural Number Game in the browser from wherever you are: solve the current level, then the next ones, in order, until every level of every world is solved."
else
  GOAL_TEXT="Your goal: solve as many levels as possible, in order, starting from Tutorial World Level 1, within a strict 10-minute time limit. A level only counts if you actually solve it in the game. Play only through the browser: read the goal and messages on the page, enter tactics into the game's input, submit them, and move on to the next level and on to the next worlds when a world is finished."
  CONT="Time is not up yet. Continue playing the Natural Number Game in the browser from wherever you are; solve the next level. Keep going until you are stopped."
fi
# Antigravity's agent also has its own tools (terminal, its own browser, files, sub-agents): the prompt says to use only the Playwright MCP tools
[ "$KIND" = agy ] && AGY_TEXT=" Use only the Playwright MCP browser tools (MCP server \"$AGY_SERVER\"): do not use any other tool, browser or agent."
PROMPT="You are playing the Natural Number Game (a Lean 4 theorem-proving game) in a web browser that you control with the Playwright browser tools. The browser is already open on the game at Tutorial World, Level 1 ($URL).

$GOAL_TEXT

${MODE_TEXT:+$MODE_TEXT

}Play like a human player: only click, type, press keys, read the page (snapshots/screenshots) and navigate. Running JavaScript or any other script or automation in the page is NOT allowed (no javascript: URLs either). You have no shell and no local Lean installation; do not try to use any.${AGY_TEXT:-} Do not stop to ask questions or write summaries. Keep playing continuously until you are stopped."

# run "$@" with a hard wall-clock limit; kills the agent's whole process group (incl. MCP server)
run_limited() {
  local left=$1; shift
  "$@" </dev/null 2>>"$OUT/agent.err" > >(python3 -u $B/ts.py "$OUT/agent.jsonl" "$OUT/agent.ts") &
  local pid=$!
  ( sleep "$left"; kill -KILL -- -$pid 2>/dev/null ) &
  local w=$!
  wait $pid; kill $w 2>/dev/null
}

# PAUSE_ON_API_ERROR=1: time from the last agent event to a failed turn ("model at capacity" etc.)
# plus the restart gap is added back to the deadline, so the agent gets DUR seconds of real play.
PAUSE=${PAUSE_ON_API_ERROR:-0}
node $B/recorder.mjs $PORT "$OUT" $((DUR+2400)) >"$OUT/recorder.log" 2>&1 &
REC_PID=$!
START=$(date +%s); DEADLINE=$((START+DUR))
echo "{\"name\":\"$NAME\",\"model\":\"$MODEL\",\"mode\":\"$MODE\",\"goal\":\"$GOAL\",\"start\":$START}" > "$OUT/meta.json"

cd "$OUT/work"
n=0
SID=$(uuidgen | tr A-Z a-z)
if [ "$GOAL" = end ]; then
  # stop the agent as soon as the game marks every level completed (recorder writes completed.txt every 10 s)
  ( while sleep 5; do
      c=$(cat "$OUT/completed.txt" 2>/dev/null || echo 0)
      if [ "${c:-0}" -ge $STOP_AT ] 2>/dev/null; then
        date +%s > "$OUT/finished"; echo "game finished ($c levels) at +$(( $(date +%s)-START ))s" >> "$OUT/runner.log"
        pkill -KILL -f -- "$SID"; break
      fi
    done ) &
  WATCH_PID=$!
fi
while [ $(date +%s) -lt $DEADLINE ] && [ ! -f "$OUT/finished" ]; do
  LEFT=$((DEADLINE-$(date +%s)))
  INV_START=$(date +%s)
  if [ "$KIND" = agy ]; then
    if [ $n -eq 0 ]; then
      CID=$($B/agy.sh new-conversation --model="$MODEL" --title="nng-$NAME" "$PROMPT" 2>>"$OUT/agent.err" | python3 -c "import json,sys; print(json.load(sys.stdin)['response']['newConversation']['conversationId'])")
      echo "$CID" > "$OUT/conversation_id"
      python3 -u $B/agy_follow.py "$CID" "$OUT" 2>>"$OUT/agent.err" &
      FOLLOW_PID=$!
    else
      $B/agy.sh send-message "$CID" "$CONT" >>"$OUT/agent.err" 2>&1
    fi
    # wait until the model ends its turn (last response without tool calls) or time is up
    while [ $(date +%s) -lt $DEADLINE ] && [ ! -f "$OUT/agy_idle" ]; do sleep 1; done
    rm -f "$OUT/agy_idle"
  elif [ "$KIND" = claude ]; then
    if [ $n -eq 0 ]; then ARGS=(--session-id $SID); P="$PROMPT"
    else ARGS=(--resume $SID); P="$CONT"; fi
    run_limited $LEFT $B/node_modules/.bin/claude -p "$P" --model "$MODEL" "${ARGS[@]}" --tools "" \
      --mcp-config "$OUT/mcp.json" --strict-mcp-config --allowedTools "mcp__playwright" --disallowedTools "${BLOCKED[@]/#/mcp__playwright__}" \
      --permission-mode bypassPermissions --setting-sources "" \
      --output-format stream-json --verbose --thinking-display summarized
  else
    # Codex >= 0.170 runs GPT 6.x in "code_mode_only": every tool is reached through an `exec` tool that runs
    # JavaScript, so the model can script the browser (chain actions, store helper functions). codex_catalog_direct.json
    # is the Codex model catalog with tool_mode=direct (browser tools called one at a time), no tool search,
    # no sub-agents and no apply_patch; apps/plugins are disabled so only the browser tools remain.
    CX=(-m "$MODEL" --json --skip-git-repo-check --ignore-user-config -c approval_policy=never -c web_search=disabled -c model_reasoning_summary=detailed
        -c "model_catalog_json=\"$B/codex_catalog_direct.json\""
        --disable shell_tool --disable unified_exec --disable browser_use
        --disable browser_use_external --disable computer_use --disable in_app_browser --disable image_generation
        --disable multi_agent --disable sleep_tool --disable goals --disable apps --disable plugins --disable tool_suggest --disable skill_search
        -c "mcp_servers.playwright.command=\"$MCP_BIN\""
        -c "mcp_servers.playwright.args=[\"--cdp-endpoint\",\"http://127.0.0.1:$PORT\",\"--output-dir\",\"$OUT/mcp-out\"]"
        -c "mcp_servers.playwright.tool_timeout_sec=120" -c "mcp_servers.playwright.default_tools_approval_mode=\"approve\"" -c "mcp_servers.playwright.disabled_tools=[$(printf '"%s",' "${BLOCKED[@]}" | sed 's/,$//')]")
    if [ $n -eq 0 ]; then
      run_limited $LEFT $B/node_modules/.bin/codex exec "${CX[@]}" "$PROMPT"
      TID=$(grep -m1 -o '"thread_id":"[^"]*"' "$OUT/agent.jsonl" | cut -d'"' -f4)
    else
      run_limited $LEFT $B/node_modules/.bin/codex exec resume "${CX[@]}" "$TID" "$CONT"
    fi
  fi
  n=$((n+1)); echo "agent invocation $n ended at +$(( $(date +%s)-START ))s" >> "$OUT/runner.log"
  sleep 2
  if [ "$PAUSE" = 1 ]; then
    W=$(python3 - "$OUT/agent.ts" $INV_START $START <<'PY'
import sys
path, inv_start, start = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
import time; now = time.time()
rows = [l.split("\t") for l in open(path).read().split("\n") if l]
rows = [(float(t), k) for t, k in rows if float(t) >= inv_start]
if any(k == "fail" for _, k in rows):
    prev = max([t for t, k in rows if k == "event"] or [inv_start])
    print(f"{now - prev:.0f} {prev - start:.0f} {now - start:.0f}")
PY
)
    if [ -n "$W" ]; then
      read secs from to <<<"$W"
      DEADLINE=$((DEADLINE+secs)); [ $DEADLINE -gt $((START+DUR+2400)) ] && DEADLINE=$((START+DUR+2400))
      echo "$from $to" >> "$OUT/paused.txt"
      echo "  API error: clock paused ${secs}s (video ${from}s-${to}s)" >> "$OUT/runner.log"
    fi
  fi
done
[ "$GOAL" = end ] && kill $WATCH_PID 2>/dev/null
date +%s > "$OUT/end"
if [ "$KIND" = agy ]; then
  $B/agy_rpc.sh CancelCascadeInvocation "{\"cascadeId\":\"$CID\"}" >>"$OUT/agent.err" 2>&1
  sleep 3; kill $FOLLOW_PID 2>/dev/null
fi
pkill -KILL -f "mcp-server-playwright.*$PORT"
kill -TERM $REC_PID; wait $REC_PID
echo "play time ${DUR}s, wall time $(( $(date +%s)-START ))s" >> "$OUT/runner.log"
kill $CHROME_PID; sleep 1; pkill -f "remote-debugging-port=$PORT"
echo "capacity/overload errors: $(grep -ciE 'at capacity|overloaded_error|rate_limit_error' "$OUT/agent.jsonl")" >> "$OUT/runner.log"
echo "done $NAME" >> "$OUT/runner.log"
