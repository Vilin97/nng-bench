# nng-bench: AI models speedrun the Natural Number Game

AI models play the [Natural Number Game](https://adam.math.hhu.de/#/g/leanprover-community/nng4) (NNG4, a Lean 4
theorem-proving game) in a real web browser for **10 minutes**, starting from Tutorial World level 1. The score is the
number of levels the game marks as solved. Every run is screen-recorded at 25 fps with a visible cursor.

**Videos (5x speed, banner with clock, levels solved and mistakes):**
[YouTube playlist "NNG Speedrun: AI models play the Natural Number Game"](https://www.youtube.com/playlist?list=PLXsryczdIguE).
Bonus: [Claude Haiku 5.5 finishes the whole game](https://youtu.be/SleW3H6I5Dw), all worlds in order, 78 of 79 levels in 36:38
(the 79th, Power World level 10, is Fermat's Last Theorem and cannot be solved in the game).

## Rules

- **Browser only, no scripts.** The model controls the browser with the [Playwright MCP](https://github.com/microsoft/playwright-mcp)
  tools: click, type, press keys, read the page (accessibility snapshots or screenshots), navigate. Tools that run code in the
  page (`browser_evaluate`, `browser_run_code`, ...) are removed, `javascript:` URLs are forbidden, and the model has no shell,
  no file access and no local Lean. `score.py` checks every run's log for violations; all runs below are clean.
- **10 minutes of play**, counted from the first action. Only levels solved before the clock stops count.
- **Two input modes** of the game:
  - *Editor mode*: a multi-line editor where the model writes each whole proof.
  - *Typewriter mode*: one tactic at a time.
- **In order**, starting at Tutorial World level 1; the model moves on with the game's own buttons and links.
- The same prompt for every model (`run.sh`), apart from one sentence for Antigravity (below).

## Results

| Model | Levels, editor | Levels, typewriter | Lean mistakes (ed / tw) | Computer-use mistakes (ed / tw) | Sec per action (ed) | Cost (ed / tw) |
|---|---|---|---|---|---|---|
| Claude Fable 5.2 | [65](https://youtu.be/0tthbfsxMbs)\* | [41](https://youtu.be/6kGi7D7Louk) | 2 / 0 | 2 / 1 | 2.1 | $8.37 / $11.02 |
| Claude Opus 5.5 | [61](https://youtu.be/pkY5jDzmcSc) | [32](https://youtu.be/JLuzhALE5T8) | 1 / 0 | 3 / 1 | 2.8 | $10.03 / $6.50 |
| GPT 6.1 Terra | [54](https://youtu.be/oJFH7DroT3Y) | [28](https://youtu.be/SBr3j_yHNco) | 4 / 2 | 1 / 1 | 2.9 | $2.28 / $2.29 |
| Claude Sonnet 5.5 | [48](https://youtu.be/_PHEtjzIyNI) | [35](https://youtu.be/h9Y3oupXq0U) | 3 / 2 | 2 / 0 | 2.1 | $4.20 / $3.92 |
| GPT 6.1 Sol | [47](https://youtu.be/0wv1XMi_OkA) | [31](https://youtu.be/7lTheaV6Oeg) | 1 / 2 | 1 / 1 | 3.7 | $3.11 / $3.72 |
| GPT 6.2 Sol | [38](https://youtu.be/JKVeRcO7q_w) | [43](https://youtu.be/7TFHn3zNWnM) | 2 / 2 | 1 / 2 | 6.0 | $1.35 / $4.39 |
| Gemini 4 Hydrogen | [36](https://youtu.be/mKBuDoa4UA0) | [18](https://youtu.be/-1UdG1ujw48) | 0 / 0 | 1 / 1 | 5.1 | $2.30 / $1.72 |
| Gemini 4 Neon | [36](https://youtu.be/Ud-epQWm1jQ) | [23](https://youtu.be/FPK7S6uGKoY) | 0 / 0 | 0 / 1 | 4.8 | $2.58 / $2.79 |
| Claude Haiku 5.5 | [34](https://youtu.be/KhBmXiToua8) | [17](https://youtu.be/i-xXe1fuVzk) | 3 / 4 | 0 / 2 | 2.6 | $0.30 / $0.50 |
| GPT 6.2 Astra | [23](https://youtu.be/qWTl2TvtGa0) | [24](https://youtu.be/FNNTgFAHkFI) | 1 / 1 | 1 / 0 | 10.5 | $2.13 / $4.86 |
| Gemini 4 Carbon | [22](https://youtu.be/qNrpqzFsOuE) | [21](https://youtu.be/sbaUd6-7Xsg) | 0 / 0 | 0 / 0 | 8.2 | $0.72 / $0.93 |
| GPT 6 Luna | [10](https://youtu.be/1corllJn1xg)\* | [13](https://youtu.be/8uDpMuTQcag) | 19 / 11 | 0 / 0 | 4.2 | $0.19 / $0.21 |
| DeepSeek V4.1 Flash | [8](https://youtu.be/U1ZNDKOjFSI) | [15](https://youtu.be/o_YbumHpv0Y) | 5 / 5 | 1 / 3 | 6.5 | $3.13 / $3.41 |

\* Jumped ahead by typing a level URL: Fable skipped Algorithm World level 3 and Power World level 10 (65 counted);
GPT 6 Luna got stuck on Tutorial World level 7 and went to Power World (10 counted, 6 of them in order).

Each level count links to that run's video.

- **Lean mistakes**: distinct errors the game showed for a tactic or proof the model entered ("unsolved goals" on an unfinished
  proof does not count), counted from the screen recording (`vision_mistakes.py`).
- **Computer-use mistakes**: browser actions that failed (stale element, click timeout, typing into a non-text element, ...).
- **Sec per action**: 600 s divided by the number of browser actions in the editor-mode run.
- **Cost**: what the run's tokens cost at API list prices (the Claude, GPT and Gemini runs used subscriptions; DeepSeek ran on a pay-as-you-go Token Factory key). Per-run token totals
  are in `results.csv`; prices and sources are in `cost.py`.

How each model was run:

| Models | Agent | Settings |
|---|---|---|
| Claude Fable 5.2, Opus 5.5, Sonnet 5.5, Haiku 5.5 | [Claude Code](https://github.com/anthropics/claude-code) CLI, `claude -p` | default effort, Playwright MCP tools only (`--tools ""`) |
| GPT 6.1 Terra / Sol, GPT 6.2 Sol / Astra | [Codex](https://github.com/openai/codex) CLI, `codex exec` | default effort; shell, web search, apps and sub-agents off; direct tool calls (see below) |
| Gemini 4 Hydrogen / Neon / Carbon | Google Antigravity agent via its `agentapi` | `gemini-4-*-high`; Playwright MCP added to Antigravity |
| GPT 6 Luna | Codex CLI | as the other GPT models |
| DeepSeek V4.1 Flash | Codex CLI with [Nebius Token Factory](https://nebius.com/services/token-factory) as the provider | `deepseek-ai/DeepSeek-V4.1-Flash-1017`, Responses API, same settings as GPT |

## Analysis

- **Speed decides the ranking.** In editor mode almost every model needs 3-4 browser actions per level; what differs is how
  long each action takes, from about 2 s (Fable, Sonnet, Haiku) to 5-8 s (Gemini) and 10 s (GPT 6.2 Astra). Fable beats
  Gemini 4 Neon mainly because it acts 2.5 times faster, not because it finds better proofs. Haiku is as fast as the big
  Claude models but needs more tries per level.
- **Gemini is accurate but slow.** None of the six Gemini runs made a single Lean error; every Claude and GPT model made 1-4
  per run. Care does not pay off on these short levels, where an error costs only one extra try.
- **The biggest model is not the best player.** Gemini 4 Carbon (Google's strongest) came last of the three Gemini models, and
  Hydrogen (the fast one) tied Neon in editor mode. GPT 6.2 Astra is likewise the slowest and lowest-scoring GPT. The levels
  are easy, so extra reasoning mostly adds waiting time.
- **Cost per level varies 18x.** Haiku solved 34 levels for $0.30 (about 1 cent per level); Fable ($0.13 per level) and Opus
  ($0.16) are the most expensive. GPT 6.1 Terra ($0.04), GPT 6.2 Sol ($0.04) and Gemini 4 Carbon ($0.03) are cheap. Most of
  the cost is re-reading the conversation (cached input) on every action: Opus re-read 35M cached tokens in its editor run,
  while Fable sent several actions per request (79 requests for 285 actions) and spent less than Opus despite twice the price
  per token.
- **The small open and budget models struggle.** GPT 6 Luna (10 / 13 levels) made by far the most Lean errors (19 in editor
  mode) and gave up on a Tutorial level by jumping to another world; DeepSeek V4.1 Flash (8 / 15) got stuck on Addition World
  level 1 in editor mode for over 5 minutes. Both did better in typewriter mode, where the game checks each tactic as it is entered.
  DeepSeek also costs more than Haiku here ($3.13 vs $0.30 for the editor run) because Token Factory does not discount cached input.
- **Editor mode is worth about 1.5x more levels** for most models, since a whole proof goes in at once. GPT 6.2 Sol is the
  exception (43 in typewriter mode vs 38 in editor mode); for the slowest models (Carbon, Astra) the mode barely matters,
  because thinking time per level dominates.

## Caveats

- **One run per model and mode.** Differences of a few levels are within run-to-run noise.
- **Different agents.** Each model ran in its own vendor's agent (Claude Code, Codex, Antigravity), with that agent's system
  prompt, context handling and tool plumbing, and at different effort settings. This measures model + agent, as people use them.
- **Codex "code mode".** Codex >= 0.160 runs GPT 6.x in a mode where every tool call goes through a JavaScript `exec` tool,
  which lets the model script the browser. The GPT runs here use a model catalog with direct tool calls
  (`make_codex_catalog.py`); earlier code-mode runs were discarded.
- **Antigravity** has its own terminal, browser agent and file tools that cannot be switched off from `agentapi`; the prompt
  tells the model to use only the Playwright tools, and the transcripts show it did. It also saves large tool results to files
  that the model reads back (`read_tool_output` in the logs), which costs extra steps.
- **Typewriter prompt.** Before 2026-11-18 the typewriter prompt did not say "stay in Typewriter mode"; GPT 6.2 Sol then switched
  itself to editor mode, and was re-run with the sentence (now part of the prompt for every typewriter run). The other
  typewriter runs predate the sentence; none of them switched modes.
- **API stalls.** GPT 6.2 Astra's first runs lost minutes to OpenAI API stalls (several minutes for a reply with no reasoning)
  and were re-run.
- **Parallel runs.** Some runs (5 of the 6 Gemini runs, Haiku, Luna and DeepSeek) ran at the same time on different browser ports.
- **Prices** for OpenAI and Google come from third-party summaries of their pricing pages; Gemini 4 Carbon is at its
  introductory price ($2 / $10 per million tokens until 2026-12-01).

## How it works

`run.sh <name> <claude|codex|agy> <model> [seconds]` (`INPUT_MODE=editor|typewriter`, `PORT=...`):

1. Starts a fresh headless Chromium on the game (Tutorial World level 1); `setmode.mjs` switches the game to editor mode if asked.
2. `recorder.mjs` records the page over the Chrome DevTools Protocol (screencast frames to a 25 fps VP8 WebM) and draws a cursor
   (`cursor.js`); it logs the URL and the number of levels the game marks completed, and saves the final game state.
3. Starts the agent with the prompt and the Playwright MCP server connected to that browser, and restarts it with a
   "keep going" message if it stops early. The clock stops after the given time; with `PAUSE_ON_API_ERROR=1`, time lost to
   failed API turns is added back and cut from the video.
   - `claude`: Claude Code with only the Playwright tools.
   - `codex`: Codex with shell/web/apps off and `codex_catalog_direct.json` (direct tool calls).
   - `agy`: Gemini through a running Antigravity app (`agy.sh` runs its `agentapi`, `agy_rpc.sh` calls its local API to refresh
     MCP servers and stop the conversation, `agy_follow.py` converts its transcript to the same log format as Claude's).
     Needs the Playwright MCP server in `~/.gemini/config/mcp_config.json` and an allow rule per tool, `mcp(<server>/<tool>)`,
     in `~/.gemini/config/config.json` (`userSettings.globalPermissionGrants.allow`), or every browser action waits for approval.

Scoring and videos:

| Script | What it does |
|---|---|
| `score.py <run>` | levels solved (final game state), order of levels, tool calls, rule check |
| `levels_timeline.py <run>` | when each level was solved, Lean and computer-use mistakes from the logs |
| `vision_mistakes.py <run>` | Lean mistakes from the screen recording (Claude Haiku flags frames, Claude Opus confirms) |
| `make_fast.py <run> <out.mp4> [speed]` | sped-up video with the banner (clock, counters) and the model's thinking/messages underneath |
| `token_usage.py`, `cost.py` | token totals per run and their cost at list prices |
| `results.py` | the table above and `results.csv` |
| `youtube/thumbs/make_thumbs.py` | 1280x720 thumbnails (needs the Claude/OpenAI/Gemini icons from `@lobehub/icons-static-svg` and the Lean logo from the leanprover-community website repo, `img/lean_logo.svg`) |
| `youtube/videos.py` | video titles and descriptions |

Setup: `npm install` (Claude Code, Codex, Playwright MCP, Playwright), `npx playwright install chromium`, Python 3 with
`imageio-ffmpeg` for the videos, and logins for the agents you run. Paths assume the repo at `~/Github/nng-bench` and macOS fonts.
