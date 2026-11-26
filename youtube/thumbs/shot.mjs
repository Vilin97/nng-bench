// screenshot each HTML file given on the command line at exactly 1280x720
import { chromium } from "../../node_modules/playwright/index.mjs";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
for (const f of process.argv.slice(2)) {
  await page.goto("file://" + f); await page.waitForLoadState("networkidle");
  await page.screenshot({ path: f.replace(/\.html$/, ".png") });
}
await browser.close();
