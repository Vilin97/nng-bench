"""Cut the clock-paused stretches (runs/<name>/paused.txt, seconds from run start) out of screen.webm.
usage: .venv/bin/python cut_pauses.py <run_name> <out.mp4>"""
import subprocess, sys
from pathlib import Path
import imageio_ffmpeg

run = Path(__file__).parent / "runs" / sys.argv[1]
out = sys.argv[2]
paused = [tuple(map(float, l.split())) for l in (run / "paused.txt").read_text().split("\n") if l.strip()]
keep = "not(" + "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in paused) + ")" if paused else "1"
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-v", "error", "-i", str(run / "screen.webm"),
                "-vf", f"select='{keep}',setpts=N/FRAME_RATE/TB,crop=trunc(iw/2)*2:trunc(ih/2)*2", "-r", "25",
                "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p", out], check=True)
print(f"cut {len(paused)} paused stretches, {sum(b - a for a, b in paused):.0f}s total -> {out}")
