// Real-time 25 fps recording of a Chromium instance via the CDP screencast stream
// (Page.startScreencast: Chrome pushes a frame every time the page repaints).
// The latest frame is written at a constant 25 fps into ffmpeg -> VP8 webm.
// Also logs the active URL once per second, and at the end dumps localStorage (game progress).
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const [port, outDir, durationS] = process.argv.slice(2);
const FPS = 25;
const pw = path.join(process.env.HOME, process.platform === 'darwin' ? 'Library/Caches/ms-playwright' : '.cache/ms-playwright');
const ffmpegBin = fs.readdirSync(pw).filter(d => d.startsWith('ffmpeg-')).map(d => path.join(pw, d, process.platform === 'darwin' ? 'ffmpeg-mac' : 'ffmpeg-linux'))[0];

const browser = await chromium.connectOverCDP(`http://127.0.0.1:${port}`);
const ff = spawn(ffmpegBin, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', 'pipe:0',
  '-c:v', 'vp8', '-b:v', '5M', '-qmin', '0', '-qmax', '30', '-deadline', 'realtime', '-cpu-used', '4', '-threads', '8',
  '-r', String(FPS), path.join(outDir, 'screen.webm')], { stdio: ['pipe', 'inherit', 'inherit'] });
const CURSOR_JS = fs.readFileSync(new URL('./cursor.js', import.meta.url), 'utf8');
const log = fs.createWriteStream(path.join(outDir, 'progress.jsonl'));

let stop = false;
process.on('SIGTERM', () => { stop = true; });
process.on('SIGINT', () => { stop = true; });

let latest = null, castPage = null, castSession = null, frames = 0;
function activePage() {
  const pages = browser.contexts().flatMap(c => c.pages()).filter(p => !p.isClosed());
  const game = pages.filter(p => p.url().includes('adam.math.hhu.de'));
  return (game.length ? game : pages).at(-1);
}
async function follow() {
  const page = activePage();
  if (!page || page === castPage) return;
  try { await castSession?.send('Page.stopScreencast'); } catch {}
  const s = await page.context().newCDPSession(page);
  s.on('Page.screencastFrame', ev => {
    latest = Buffer.from(ev.data, 'base64'); frames++;
    s.send('Page.screencastFrameAck', { sessionId: ev.sessionId }).catch(() => {});
  });
  try { await s.send('Page.addScriptToEvaluateOnNewDocument', { source: CURSOR_JS }); await s.send('Runtime.evaluate', { expression: CURSOR_JS }); } catch {}
  // grab one still immediately so the video never starts black
  try { latest = Buffer.from((await s.send('Page.captureScreenshot', { format: 'jpeg', quality: 85 })).data, 'base64'); } catch {}
  await s.send('Page.startScreencast', { format: 'jpeg', quality: 85, maxWidth: 1440, maxHeight: 1100, everyNthFrame: 1 });
  castPage = page; castSession = s;
}

await follow();
const t0 = Date.now();
let written = 0, lastLog = -1, completed = null;
const COUNT_JS = `(() => { try { const d = JSON.parse(localStorage.game_progress).games['g/leanprover-community/nng4'].data; let n = 0;
  for (const w in d) for (const l in d[w]) if (d[w][l] && d[w][l].completed) n++; return n; } catch (e) { return -1; } })()`;
while (!stop && Date.now() - t0 < Number(durationS) * 1000) {
  const elapsed = Date.now() - t0;
  const target = Math.floor(elapsed * FPS / 1000) + 1;
  if (latest) while (written < target) { ff.stdin.write(latest); written++; }
  const sec = Math.floor(elapsed / 1000);
  if (sec !== lastLog) {
    lastLog = sec;
    follow().catch(() => {});
    if (castPage) log.write(JSON.stringify({ t: sec, url: castPage.url(), frames, completed }) + '\n');
    // every 10 s: number of levels the game marks completed (lets the harness stop when the whole game is done)
    if (sec % 10 === 0 && castSession) castSession.send('Runtime.evaluate', { expression: COUNT_JS, returnByValue: true })
      .then(r => { completed = r.result.value; fs.writeFileSync(path.join(outDir, 'completed.txt'), String(completed)); }).catch(() => {});
  }
  await new Promise(r => setTimeout(r, 1000 / FPS / 2));
}

try {
  const page = activePage();
  const state = await page.evaluate(() => Object.fromEntries(Object.entries(localStorage)));
  fs.writeFileSync(path.join(outDir, 'final_state.json'), JSON.stringify({ url: page.url(), localStorage: state }, null, 1));
  fs.writeFileSync(path.join(outDir, 'final.png'), await page.screenshot());
} catch (e) { fs.writeFileSync(path.join(outDir, 'final_state.err'), String(e)); }
ff.stdin.end();
await new Promise(r => ff.on('close', r));
log.end();
process.exit(0);
