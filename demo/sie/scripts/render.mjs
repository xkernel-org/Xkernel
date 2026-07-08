/**
 * Headless renderer: drives render.html in headless Chrome.
 * Usage: node scripts/render.mjs [fps] [scale]
 * Requires the vite dev server running on :9000 and puppeteer installed.
 */
import puppeteer from 'puppeteer';

const fps = process.argv[2] ?? '30';
const scale = process.argv[3] ?? '1';
const start = process.argv[4] ?? '0';
const end = process.argv[5] ?? '';

const browser = await puppeteer.launch({
  headless: 'new',
  args: [
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--force-color-profile=srgb',
    '--disable-gpu',
    '--font-render-hinting=none',
  ],
});
const page = await browser.newPage();
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => console.error('[pageerror]', e.message));

await page.goto(`http://localhost:9000/render.html?fps=${fps}&scale=${scale}&start=${start}${end ? `&end=${end}` : ''}`, {
  waitUntil: 'networkidle2',
  timeout: 120000,
});
await page.waitForFunction('window.__done === true || window.__error !== null', {
  timeout: 30 * 60 * 1000,
  polling: 1000,
});
const err = await page.evaluate('window.__error');
await browser.close();
if (err) {
  console.error('FAILED:', err);
  process.exit(1);
}
console.log('OK');
