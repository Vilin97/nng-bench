"""Sped-up video of a run with a banner on top: model, input mode, play-time clock and running counts of solved levels,
Lean mistakes and computer-use mistakes (see levels_timeline.py for what counts).
Stretches where the clock was paused for API errors (paused.txt) are cut out, so the clock never jumps.
Full-game runs (name full-<mode>-<model>, GOAL=end) use the actual play time (until runs/<run>/end_play if present, else end) and show solved levels out of 79.
runs/<run>/mode_switch (epoch) marks when the agent switched the game's input mode itself; the banner shows it from then on.
A caption strip under the game shows the agent's thinking summaries and messages (see thoughts()); --no-captions turns it off.
usage: .venv/bin/python make_fast.py <run_name> <out.mp4> [speed=5] [--no-captions]"""
import json, re, subprocess, sys, tempfile, textwrap
from pathlib import Path
import imageio_ffmpeg

B = Path(__file__).parent
name, out = sys.argv[1], sys.argv[2]
speed = float(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else 5
run = B / "runs" / name
MODELS = {"claude-haiku-5-5": "Claude Haiku 5.5", "claude-fable-5-2": "Claude Fable 5.2", "claude-opus-5-5": "Claude Opus 5.5", "claude-sonnet-5-5": "Claude Sonnet 5.5",
          "gpt-6-luna": "GPT 6 Luna", "deepseek-4.1-flash": "DeepSeek V4.1 Flash", "gpt-6.1-terra": "GPT 6.1 Terra", "gpt-6.1-sol": "GPT 6.1 Sol", "gpt-6.2-astra": "GPT 6.2 Astra", "gpt-6.2-sol": "GPT 6.2 Sol",
          "gemini-4-hydrogen": "Gemini 4 Hydrogen", "gemini-4-neon": "Gemini 4 Neon", "gemini-4-carbon": "Gemini 4 Carbon"}
full = name.startswith("full-")
mode, model = name.removeprefix("full-").split("-", 1)
mode_text = {"editor": "Editor mode: whole proof", "typewriter": "Typewriter mode: one tactic at a time"}[mode]
if full: mode_text += " · whole game, in order"
TOTAL = 79

tl = json.loads(subprocess.run([sys.executable, str(B / "levels_timeline.py"), name], capture_output=True, text=True, check=True).stdout)
off = tl["start"] - tl["t0"]          # video time at which the play clock started
# paused stretches in video time (paused.txt is in seconds since the clock start)
paused = []
if (run / "paused.txt").exists():
    paused = [tuple(float(x) + off for x in l.split()) for l in (run / "paused.txt").read_text().split("\n") if l.strip()]

# play time: 10 minutes for timed runs; for full-game runs, until the game was finished (or the safety cap), minus pauses
PLAY = 600
if full:
    endf = run / "end_play" if (run / "end_play").exists() else run / "end"
    PLAY = int(float(endf.read_text()) - tl["start"] - sum(b - a for a, b in paused))

def cut_time(v):
    """source video time -> time in the video with paused stretches removed"""
    return v - sum(min(b, v) - a for a, b in paused if v > a)

solves = sorted(cut_time(t - tl["t0"]) for t, _ in tl["solved"])
solves = [v for v in solves if v <= off + PLAY]     # a level solved after the clock stopped does not count
# Lean mistakes: from the screen recording (vision_mistakes.py) when available, else from the agent's logs
vision = run / "vision_mistakes.json"
lean_src = json.loads(vision.read_text())["lean_mistakes"] if vision.exists() else tl["lean_mistakes"]
lean = sorted(cut_time(m[0] - tl["t0"]) for m in lean_src)
cu = sorted(cut_time(m[0] - tl["t0"]) for m in tl["cu_mistakes"])
end = off + PLAY + 1                   # trim one second after the play clock stops

def thoughts():
    """(epoch, kind, text) of what the agent thought ("Thinking": thinking/reasoning summaries) and wrote ("Says": its
    text messages), from its logs. Runs from before 2026-11-17 logged no thinking text, only the messages."""
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
            for b in o["message"].get("content", []):
                if b.get("type") == "thinking" and b.get("thinking", "").strip(): out.append((t, "Thinking", b["thinking"]))
                if b.get("type") == "text" and b.get("text", "").strip(): out.append((t, "Says", b["text"]))
        it = o.get("item", {})
        if o.get("type") == "item.completed" and it.get("type") in ("reasoning", "agent_message") and it.get("text", "").strip():
            out.append((t, "Thinking" if it["type"] == "reasoning" else "Says", it["text"]))
    return out
CAPTIONS = "--no-captions" not in sys.argv
caps = [(cut_time(t - tl["t0"]), k, x) for t, k, x in thoughts()] if CAPTIONS else []
caps = [c for c in caps if c[0] < end]
CAP = 156 if caps else 0               # caption strip under the game

tmp = Path(tempfile.mkdtemp())
def textfile(s):
    p = tmp / f"t{len(list(tmp.iterdir()))}.txt"; p.write_text(s); return str(p)

SANS, MONO = "/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Menlo.ttc"
BAR = 132
clock = f"max(0,min({PLAY},t-{off:.2f}))"
filters = []
if paused:
    keep = "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in paused)
    filters += [f"select='not({keep})'", "setpts=N/FRAME_RATE/TB"]
filters += [f"trim=end={end:.2f}", "crop=trunc(iw/2)*2:trunc(ih/2)*2",
            f"pad=iw:ih+{BAR}+{CAP}:0:{BAR}:color=0x111827"]
def draw(text_file, font, size, x, y, color="white", enable=None):
    f = f"drawtext=fontfile={font}:textfile={text_file}:fontsize={size}:fontcolor={color}:x={x}:y={y}"
    return f + (f":enable='{enable}'" if enable else "")
filters.append(draw(textfile(MODELS[model]), SANS, 40, 28, 26))
# runs/<run>/mode_switch: epoch at which the agent switched the game's input mode itself (the banner says so from then on)
switch = None
if (run / "mode_switch").exists():
    switch = cut_time(float((run / "mode_switch").read_text()) - tl["t0"])
    other = {"editor": "Typewriter", "typewriter": "Editor"}[mode]
    at = switch - off
    filters.append(draw(textfile(mode_text), SANS, 24, 30, 78, "0x9ca3af", enable=f"lt(t,{switch:.2f})"))
    filters.append(draw(textfile(f"{mode_text.split(':')[0]}, switched itself to {other} mode at {int(at // 60)}:{int(at % 60):02d}"),
                        SANS, 24, 30, 78, "0xfcd34d", enable=f"gte(t,{switch:.2f})"))
else:
    filters.append(draw(textfile(mode_text), SANS, 24, 30, 78, "0x9ca3af"))
if PLAY >= 3600:
    clock_text = f"%{{eif:trunc({clock}/3600):d:1}}:%{{eif:mod(trunc({clock}/60),60):d:2}}:%{{eif:mod(trunc({clock}),60):d:2}}"
else:
    clock_text = f"%{{eif:trunc({clock}/60):d:2}}:%{{eif:mod(trunc({clock}),60):d:2}}"
filters.append(draw(textfile(clock_text), MONO, 56, "(w-tw)/2", 34))
filters[-1] = filters[-1] + ":expansion=normal"
filters.append(draw(textfile(f"{speed:g}x speed"), SANS, 20, "(w-tw)/2+136", 70, "0x9ca3af"))
def counter(label, times, y, color, flash):
    """running count: one drawtext per value, each shown until the next event, flashing briefly when it goes up"""
    marks = [0.0] + times
    for n, a in enumerate(marks):
        b = marks[n + 1] if n + 1 < len(marks) else end + 1
        text = f"{label}: {n}" + (f" / {TOTAL}" if full and label == "Levels solved" else "")
        filters.append(draw(textfile(text), SANS, 32, "w-tw-28", y, color, enable=f"gte(t,{a:.2f})*lt(t,{b:.2f})"))
        if n:
            filters.append(draw(textfile(text), SANS, 32, "w-tw-28", y, flash, enable=f"gte(t,{a:.2f})*lt(t,{min(b, a + 2.5):.2f})"))
counter("Levels solved", solves, 8, "white", "0x4ade80")
counter("Lean mistakes", lean, 50, "0xfca5a5", "0xef4444")
counter("Computer-use mistakes", cu, 92, "0xfcd34d", "0xf97316")
# captions: each thought/message is shown from when it was logged until the next one (or the end)
WRAP, LINES = 118, 4
for i, (a, kind, text) in enumerate(caps):
    b = caps[i + 1][0] if i + 1 < len(caps) else end + 1
    text = re.sub(r"\*\*|`", "", re.sub(r"\s+", " ", text)).strip()
    lines = textwrap.wrap(text, WRAP)
    if len(lines) > LINES: lines = lines[:LINES - 1] + [textwrap.shorten(" ".join(lines[LINES - 1:]), WRAP - 2, placeholder=" …")]
    en = f"gte(t,{a:.2f})*lt(t,{b:.2f})"
    filters.append(draw(textfile(kind), SANS, 22, 28, f"h-{CAP - 16}", "0x9ca3af" if kind == "Thinking" else "0x93c5fd", enable=en) + ":expansion=none")
    filters.append(draw(textfile("\n".join(lines)), SANS, 22, 140, f"h-{CAP - 16}", "0xe5e7eb" if kind == "Says" else "0xd1d5db", enable=en)
                   + ":expansion=none:line_spacing=8")
filters += [f"setpts=PTS/{speed}", "fps=25"]

script = tmp / "filter.txt"; script.write_text(",".join(filters))
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-v", "error", "-i", str(run / "screen.webm"), "-/vf", str(script),
                "-an", "-c:v", "libx264", "-crf", "22", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=True)
print(f"{name}: {len(solves)} levels, clock starts at video {off:.1f}s, {len(paused)} paused stretches cut -> {out}")
