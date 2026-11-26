// Harness setup (runs before the clock starts): switch the game to Editor mode,
// where the whole proof is written in a multi-line editor instead of one tactic at a time.
// usage: node setmode.mjs <cdp_port>
import { chromium } from 'playwright';

const browser = await chromium.connectOverCDP(`http://127.0.0.1:${process.argv[2]}`);
const page = browser.contexts().flatMap(c => c.pages()).find(p => p.url().includes('adam.math.hhu.de'));
await page.click('a[title="Editor mode"]');
await page.waitForTimeout(2000);
const prog = JSON.parse(await page.evaluate(() => localStorage.game_progress));
const tw = prog.games['g/leanprover-community/nng4'].typewriterMode;
console.log(`typewriterMode=${tw}`);
process.exit(tw === false ? 0 : 1);
