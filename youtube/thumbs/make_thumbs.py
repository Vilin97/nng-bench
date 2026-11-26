"""YouTube thumbnails (1280x720) for the NNG Speedrun videos: maker logo + model name, result, mode, Lean logo + NNG.
Renders one HTML page per video and screenshots it with Playwright (shot.mjs). usage: python3 make_thumbs.py [run ...]  -> out/<run>.png"""
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
RUNS = HERE.parent.parent / "runs"
OUT = HERE / "out"; OUT.mkdir(exist_ok=True)

# run -> (model, levels, extra line)
VIDEOS = {
    "editor-claude-fable-5-2": ("Claude Fable 5.2", 65, None),
    "editor-claude-opus-5-5": ("Claude Opus 5.5", 61, None),
    "editor-claude-sonnet-5-5": ("Claude Sonnet 5.5", 48, None),
    "editor-gpt-6.1-terra": ("GPT 6.1 Terra", 54, None),
    "editor-gpt-6.1-sol": ("GPT 6.1 Sol", 47, None),
    "editor-gpt-6.2-sol": ("GPT 6.2 Sol", 38, None),
    "editor-gpt-6.2-astra": ("GPT 6.2 Astra", 23, None),
    "typewriter-claude-fable-5-2": ("Claude Fable 5.2", 41, None),
    "typewriter-claude-sonnet-5-5": ("Claude Sonnet 5.5", 35, None),
    "typewriter-claude-opus-5-5": ("Claude Opus 5.5", 32, None),
    "typewriter-gpt-6.1-sol": ("GPT 6.1 Sol", 31, None),
    "typewriter-gpt-6.1-terra": ("GPT 6.1 Terra", 28, None),
    "typewriter-gpt-6.2-astra": ("GPT 6.2 Astra", 24, None),
    "typewriter-gpt-6.2-sol": ("GPT 6.2 Sol", 43, None),
    "full-editor-claude-haiku-5-5": ("Claude Haiku 5.5", 78, "full"),
    "editor-gemini-4-hydrogen": ("Gemini 4 Hydrogen", 36, None),
    "editor-gemini-4-neon": ("Gemini 4 Neon", 36, None),
    "editor-gemini-4-carbon": ("Gemini 4 Carbon", 22, None),
    "typewriter-gemini-4-hydrogen": ("Gemini 4 Hydrogen", 18, None),
    "typewriter-gemini-4-neon": ("Gemini 4 Neon", 23, None),
    "typewriter-gemini-4-carbon": ("Gemini 4 Carbon", 21, None),
}

def svg(name, color=None):
    s = (HERE / name).read_text()
    s = s[s.index("<svg"):]
    return s.replace('height="1em"', "").replace('width="1em"', "").replace("currentColor", color or "currentColor")

def page(run, model, levels, extra):
    maker = model.split()[0]   # Claude / GPT / Gemini
    logo = {"Claude": lambda: svg("claude-color.svg"), "GPT": lambda: svg("openai.svg", "#ffffff"),
            "Gemini": lambda: svg("gemini-color.svg")}[maker]()
    family, _, version = model.partition(" ")
    accent = {"Claude": "#d97757", "GPT": "#10a37f", "Gemini": "#4285f4"}[maker]
    mode = "Editor mode" if "editor" in run else "Typewriter mode"
    if extra == "full":
        score, unit, sub = "78<span class=of>/79</span>", "levels", "whole game, in order · 36:38"
    else:
        score, unit, sub = str(levels), "levels", "in 10 minutes"
    shot = (RUNS / run / "final.png").resolve()
    return f"""<!doctype html><html><head><meta charset=utf-8><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1280px;height:720px;overflow:hidden;font-family:-apple-system,"Helvetica Neue",Helvetica,Arial,sans-serif;
  background:#0b1020;color:#fff;position:relative}}
.shot{{position:absolute;right:-60px;top:70px;width:760px;border-radius:14px;transform:perspective(1400px) rotateY(-14deg);
  box-shadow:0 30px 80px rgba(0,0,0,.6);opacity:.95}}
.fade{{position:absolute;inset:0;background:linear-gradient(90deg,#0b1020 0%,#0b1020 44%,rgba(11,16,32,.55) 62%,rgba(11,16,32,.05) 100%)}}
.glow{{position:absolute;left:-200px;top:-200px;width:800px;height:800px;border-radius:50%;
  background:radial-gradient(circle,{accent}55 0%,transparent 65%)}}
.content{{position:absolute;left:64px;top:52px;right:520px}}
.maker{{display:flex;align-items:center;gap:22px}}
.maker svg{{width:104px;height:104px;flex:none}}
.family{{font-size:58px;font-weight:700;color:#cbd5e1;letter-spacing:-1px}}
.version{{font-size:118px;font-weight:800;letter-spacing:-3px;line-height:1;margin-top:18px;white-space:nowrap}}
.score{{margin-top:34px;display:flex;align-items:baseline;gap:18px}}
.num{{font-size:150px;font-weight:900;line-height:.9;color:#4ade80;letter-spacing:-4px}}
.of{{font-size:80px;color:#86efac}}
.unit{{font-size:46px;font-weight:700}}
.sub{{font-size:34px;color:#cbd5e1;margin-top:10px;font-weight:600}}
.mode{{display:inline-block;margin-top:22px;padding:8px 20px;border-radius:999px;background:{accent};font-size:28px;font-weight:800;
  text-transform:uppercase;letter-spacing:1px}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:96px;background:rgba(255,255,255,.96);display:flex;align-items:center;padding:0 40px;gap:26px;color:#0b1020}}
.foot img{{height:66px}}
.foot .nng{{font-size:44px;font-weight:900;letter-spacing:-1px}}
.foot .t{{font-size:30px;font-weight:600;color:#334155}}
.foot .r{{margin-left:auto;font-size:28px;font-weight:800;color:#0b1020}}
</style></head><body>
<img class=shot src="file://{shot}">
<div class=fade></div><div class=glow></div>
<div class=content>
 <div class=maker>{logo}<div class=family>{family}</div></div>
 <div class=version>{version}</div>
 <div class=score><div class=num>{score}</div><div class=unit>{unit}</div></div>
 <div class=sub>{sub}</div>
 <div class=mode>{mode}</div>
</div>
<div class=foot><img src="file://{(HERE / 'lean_logo.svg').resolve()}"><div class=nng>NNG</div><div class=t>Natural Number Game</div>
 <div class=r>AI Speedrun</div></div>
</body></html>"""

pages = []
for run in sys.argv[1:] or VIDEOS:
    html = OUT / f"{run}.html"
    html.write_text(page(run, *VIDEOS[run]))
    pages.append(str(html.resolve()))
subprocess.run(["node", str(HERE / "shot.mjs"), *pages], check=True)   # Playwright, exact 1280x720 viewport
print("\n".join(p.replace(".html", ".png") for p in pages))
