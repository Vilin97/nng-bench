"""Count Lean mistakes from the screen recording instead of the agent's logs.

1. Take one frame per second of play from screen.webm (middle panel only, where the game shows errors),
   dropping frames that look the same as the previous one.
2. Claude Haiku lists the Lean errors visible in each frame (6 frames per call).
3. For each error Haiku reports that is new (not yet seen on that level), Claude Opus looks at that frame
   alone and lists the errors it sees. Only errors Opus reports count.
4. A Lean mistake = a distinct confirmed error on a level, counted once, at the first frame showing it.
   Editor mode: the error box ("Line N, Character M" + message). Typewriter mode: a "Failed command".
   Errors on screen while the agent is typing one key at a time are skipped (after "r" of "rfl" the game briefly
   shows "unknown tactic"); if such an error is still there once the agent stops typing, it counts then.

Models are called through the `claude` CLI (the user's signed-in account; no API key on this machine).
Results are cached in runs/<run>/vision/, so re-running only does the missing calls.
usage: .venv/bin/python vision_mistakes.py <run_name> [<run_name> ...]   -> runs/<run>/vision_mistakes.json"""
import base64, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import imageio_ffmpeg

B = Path(__file__).parent
CLAUDE = str(B / "node_modules/.bin/claude")
HAIKU, OPUS = "claude-haiku-5-5", "claude-opus-5-5"
BATCH, WORKERS, PLAY = 6, 8, 600

DEFINITION = """These are screenshots of the middle panel of the Natural Number Game (a Lean 4 theorem-proving game in a web browser), taken while someone played it.
A Lean error is shown in one of two ways:
(a) Editor mode: a red/pink box whose first line is "Line N, Character M", followed by an error message.
(b) Typewriter mode: a grey bar "Failed command: <tactic>", followed by a red/pink box with the error message.
Do NOT report: a box whose message is "unsolved goals" (the proof is just unfinished), "declaration uses 'sorry'",
light-blue hint boxes, the "Level completed" message, or a red squiggle in the code without an error box.
For each error report "where" exactly as "Line N, Character M" (editor mode) or "Failed command: <tactic>" (typewriter mode),
and "message" = the first line of the error message, copied exactly."""

def ask(model, content):
    """one prompt (text and images) to a model through the claude CLI; returns the reply text"""
    req = json.dumps({"type": "user", "message": {"role": "user", "content": content}})
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    for _ in range(3):
        p = subprocess.run([CLAUDE, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
                            "--model", model, "--tools", "", "--strict-mcp-config", "--setting-sources", ""],
                           input=req, capture_output=True, text=True, env=env, timeout=600)
        for line in reversed(p.stdout.splitlines()):
            try: o = json.loads(line)
            except ValueError: continue
            if o.get("type") == "result" and not o.get("is_error"): return o["result"]
    raise RuntimeError(f"{model} call failed: {p.stderr[-500:]}")

def parse_json(text):
    """first JSON value in the reply (ignores any text before or after it)"""
    i = min(j for j in (text.find("["), text.find("{")) if j >= 0)
    return json.JSONDecoder().raw_decode(text[i:])[0]

def image(path):
    return {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(path.read_bytes()).decode()}}

def alnum(s): return re.sub(r"[\W_]+", "", s.lower())
def key(level, err):
    """identity of an error: level + where + message (typewriter: level + rejected tactic)"""
    w = err.get("where", "")
    if "failed command" in w.lower():
        return (level, "cmd:" + alnum(w.split(":", 1)[-1]))
    m = re.search(r"line\s*(\d+)\D+(\d+)", w, re.I)
    return (level, f"{m[1]}:{m[2]}" if m else alnum(w)[:30], alnum(err.get("message", ""))[:40])

def actions(run):
    """(epoch, tool, args) of every browser action the agent started, from its logs"""
    from datetime import datetime
    lines = (run / "agent.jsonl").read_text().split("\n")
    tsf = run / "agent.ts"
    stamps = [float(l.split("\t")[0]) for l in tsf.read_text().split("\n") if l] if tsf.exists() else [None] * len(lines)
    out = []
    for line, t in zip(lines, stamps):
        try: o = json.loads(line)
        except ValueError: continue
        if o.get("timestamp"): t = datetime.fromisoformat(o["timestamp"].replace("Z", "+00:00")).timestamp()
        if t is None: continue
        if o.get("type") == "assistant":
            out += [(t, b["name"].split("__")[-1], b.get("input") or {}) for b in o["message"].get("content", []) if b.get("type") == "tool_use"]
        it = o.get("item", {})
        if o.get("type") == "item.started" and it.get("type") == "mcp_tool_call":
            out.append((t, it["tool"], it.get("arguments") or {}))
    return sorted(out, key=lambda x: x[0])

def analyse(name):
    run = B / "runs" / name
    vis = run / "vision"; frames = vis / "frames"
    tl = json.loads(subprocess.run([sys.executable, str(B / "levels_timeline.py"), name], capture_output=True, text=True, check=True).stdout)
    off = tl["start"] - tl["t0"]   # video time when the play clock started
    paused = []
    if (run / "paused.txt").exists():
        paused = [tuple(float(x) + off for x in l.split()) for l in (run / "paused.txt").read_text().split("\n") if l.strip()]
    play_end = off + PLAY + sum(b - a for a, b in paused)
    if (run / "end").exists() and json.loads((run / "meta.json").read_text()).get("goal") == "end":
        play_end = float((run / ("end_play" if (run / "end_play").exists() else "end")).read_text()) - tl["t0"]   # full-game run: until the game was finished
    if not frames.exists():
        frames.mkdir(parents=True)
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", str(run / "screen.webm"),
                        "-vf", "fps=1,crop=730:ih:355:0,mpdecimate=hi=1536:lo=640:frac=0.1", "-fps_mode", "vfr",
                        "-frame_pts", "1", "-q:v", "3", str(frames / "%06d.jpg")], check=True)
    ts = sorted(int(p.stem) for p in frames.glob("*.jpg"))
    ts = [t for t in ts if off - 1 <= t <= play_end and not any(a <= t <= b for a, b in paused)]
    # level shown at each second of video
    url = {}
    for l in (run / "progress.jsonl").read_text().split("\n"):
        if l:
            r = json.loads(l); m = re.search(r"/world/(\w+)/level/(\d+)", r["url"])
            url[r["t"]] = f"{m[1]} {m[2]}" if m else None
    level = lambda t: url.get(t) or url.get(t - 1) or url.get(t + 1)
    acts = actions(run)
    keys = [a[0] for a in acts if a[1] == "browser_press_key" and len(str(a[2].get("key", ""))) == 1]
    allts = sorted(int(p.stem) for p in frames.glob("*.jpg"))
    stretch_end = {t: (allts[i + 1] if i + 1 < len(allts) else t + 1) for i, t in enumerate(allts)}
    def typing(t):
        """a passing error while the agent types one key at a time: a single-key press sent up to 4 s before (or 2 s after)
        the frame, and the screen changed again within 4.5 s of that key message. Keys sent in one message share its
        timestamp and run one after another; 2 s also covers the ~1 s mismatch between video and log timestamps.
        (A frame stands for the whole unchanged stretch until the next kept frame.)"""
        near = [k for k in keys if -2 <= tl["t0"] + t - k <= 4]   # keys run after the message that sends them
        return bool(near) and tl["t0"] + stretch_end[t] <= max(near) + 4.5

    # 2. Haiku over all frames
    hdir = vis / "haiku"; hdir.mkdir(exist_ok=True)
    batches = [ts[i:i + BATCH] for i in range(0, len(ts), BATCH)]
    def haiku(batch):
        out = hdir / f"{batch[0]:06d}.json"
        if out.exists(): return json.loads(out.read_text())
        content = []
        for t in batch:
            content += [{"type": "text", "text": f"Frame t={t}"}, image(frames / f"{t:06d}.jpg")]
        content.append({"type": "text", "text": DEFINITION + '\nReturn only JSON, one entry per frame: [{"t": <frame t>, "errors": [{"where": "...", "message": "..."}]}] (errors: [] when the frame shows none).'})
        res = parse_json(ask(HAIKU, content))
        out.write_text(json.dumps(res)); return res
    with ThreadPoolExecutor(WORKERS) as ex:
        hres = [r for rs in ex.map(haiku, batches) for r in rs]
    flagged = sorted(((int(r["t"]), e) for r in hres for e in r.get("errors") or []), key=lambda x: x[0])

    # 3. Opus checks the first frame of each new error Haiku reported
    odir = vis / "opus"; odir.mkdir(exist_ok=True)
    seen, to_check = set(), []
    for t, e in flagged:
        if typing(t): continue
        k = key(level(t), e)
        if k not in seen: seen.add(k); to_check.append(t)
    to_check = sorted(set(to_check))
    def opus(t):
        out = odir / f"{t:06d}.json"
        if out.exists(): return t, json.loads(out.read_text())
        content = [image(frames / f"{t:06d}.jpg"), {"type": "text", "text": DEFINITION + '\nOnly report errors that are clearly visible in this screenshot. Return only JSON: {"errors": [{"where": "...", "message": "..."}]} (errors: [] if there are none).'}]
        res = parse_json(ask(OPUS, content))
        out.write_text(json.dumps(res)); return t, res
    with ThreadPoolExecutor(WORKERS) as ex:
        ores = dict(ex.map(opus, to_check))

    # 4. distinct confirmed errors, at the first frame where Opus confirmed them
    confirmed = {}
    for t in sorted(ores):
        if typing(t): continue
        for e in ores[t].get("errors") or []:
            k = key(level(t), e)
            if k not in confirmed: confirmed[k] = (t, e)
    mistakes = sorted([tl["t0"] + t, k[0], e.get("where", ""), e.get("message", "")] for k, (t, e) in confirmed.items())
    result = {"frames": len(ts), "haiku_calls": len(batches), "haiku_flagged_frames": len({t for t, _ in flagged}),
              "opus_calls": len(to_check), "opus_rejected": sum(1 for t in to_check if not ores[t].get("errors")),
              "lean_mistakes": mistakes}
    (run / "vision_mistakes.json").write_text(json.dumps(result, indent=1))
    log_count = len(tl["lean_mistakes"])
    print(f"{name}: {len(mistakes)} Lean mistakes from video (logs: {log_count}); {len(ts)} frames, "
          f"{len(batches)} Haiku calls, {len(to_check)} Opus checks ({result['opus_rejected']} found no error)", flush=True)

for n in sys.argv[1:]:
    analyse(n)
