import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium } from 'playwright';

const root = resolve(import.meta.dirname, '../..');
const capture = JSON.parse(await readFile(resolve(root, 'lib/house-visualizations.generated.json'), 'utf8'));
const origin = process.env.DOM_TEST_URL ?? 'http://localhost:3001';
const output = resolve(root, 'output/playwright/house-visualizations');
await mkdir(output, { recursive: true });
assert.equal(capture.design, 'C/B/B');
assert.equal(capture.views.filter(view => view.group === 'exterior').length, 7);
assert.equal(capture.views.filter(view => view.group === 'interior').length, 3);
for (const view of capture.views) {
  const bytes = await readFile(resolve(root, 'public', view.url.slice(1)));
  assert.equal(bytes.length, view.bytes);
  assert.equal(createHash('sha256').update(bytes).digest('hex'), view.sha256);
  assert.ok((await readFile(resolve(root, 'public', view.thumbnailUrl.slice(1)))).length > 1000);
}
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const report = { capture: { width: capture.width, height: capture.height, images: capture.views.length }, checks: [] };
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(20_000);
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(`${origin}/docs`, { waitUntil: 'networkidle' });
  // A decoded JPEG can still be an empty WebGL buffer after resize.
  const imageChecks = await page.evaluate(async views => {
    const results = [];
    for (const view of views) for (const url of [view.url, view.thumbnailUrl]) {
      const image = new Image(); image.src = `${url}?verify=${view.sha256}`; await image.decode();
      const canvas = document.createElement('canvas'); canvas.width = 32; canvas.height = 20;
      const context = canvas.getContext('2d'); context.drawImage(image, 0, 0, 32, 20);
      const pixels = context.getImageData(0, 0, 32, 20).data;
      let visible = 0; const colors = new Set();
      for (let i = 0; i < pixels.length; i += 4) {
        if (pixels[i] + pixels[i + 1] + pixels[i + 2] > 90) visible++;
        colors.add(`${pixels[i]},${pixels[i + 1]},${pixels[i + 2]}`);
      }
      results.push({ url, width: image.naturalWidth, height: image.naturalHeight, visible, colors: colors.size });
    }
    return results;
  }, capture.views);
  for (const image of imageChecks) {
    assert.ok(image.visible > 320 && image.colors > 100, `Blank model capture: ${image.url}`);
    assert.equal(image.width, image.url.includes('-thumb') ? 800 : 2400);
    assert.equal(image.height, image.url.includes('-thumb') ? 500 : 1500);
  }
  report.checks.push('All 20 full images and thumbnails decode, have correct dimensions and contain a rendered scene');
  assert.equal(await page.locator('.hv-card').count(), 2);
  await page.screenshot({ path: resolve(output, 'docs-desktop.png') });
  await page.getByRole('button', { name: 'Všetkých 10 záberov' }).click();
  assert.equal(new URL(page.url()).searchParams.get('folder'), 'visualizations');
  assert.equal(await page.locator('.hv-card').count(), 10);
  await page.locator('.hv-card img').evaluateAll(images => images.forEach(image => { image.loading = 'eager'; }));
  await page.waitForFunction(() => [...document.querySelectorAll('.hv-card img')].every(image => image.complete && image.naturalWidth > 0));
  await page.screenshot({ path: resolve(output, 'gallery-desktop.png') });
  const living = page.getByRole('button', { name: 'Zväčšiť: Obývačka · katedrálový strop', exact: true });
  await living.click();
  await page.locator('.hv-full-image').evaluate(image => image.decode());
  assert.equal(await page.locator('dialog[open]').count(), 1);
  assert.equal(await page.locator('.hv-full-image').evaluate(image => image.naturalWidth), 2400);
  await page.screenshot({ path: resolve(output, 'living-desktop.png') });
  await page.keyboard.press('ArrowRight');
  assert.equal(new URL(page.url()).searchParams.get('file'), 'visualization-living-kitchen');
  await page.goBack();
  assert.equal(await page.locator('#hv-viewer-title').textContent(), 'Obývačka · katedrálový strop');
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('dialog[open]').count(), 0);
  await page.waitForFunction(element => element === document.activeElement, await living.elementHandle());
  await living.click();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Stiahnuť obrázok' }).click();
  const download = await downloadPromise;
  assert.equal(download.suggestedFilename(), 'dom-cbb-living-vault.jpg');
  assert.equal(await download.failure(), null);
  await page.reload({ waitUntil: 'networkidle' });
  assert.equal(await page.locator('#hv-viewer-title').textContent(), 'Obývačka · katedrálový strop');
  await page.keyboard.press('Escape');
  await page.getByRole('searchbox').fill('katedralovy');
  await page.getByRole('combobox', { name: 'Typ súboru', exact: true }).selectOption('JPG');
  assert.equal(await page.locator('.dl-file-row').count(), 3);
  await page.getByRole('searchbox').fill('');
  assert.equal(await page.locator('.dl-file-row').count(), 10);
  report.checks.push('Desktop gallery, all 10 files, full resolution, keyboard, history, focus return, direct URL, download, search and JPG filter');

  await page.goto(`${origin}/docs?folder=visualizations&file=visualization-living-vault`, { waitUntil: 'networkidle' });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ colorScheme: 'dark', reducedMotion: 'reduce' });
  await page.locator('.hv-full-image').evaluate(image => image.decode());
  assert.ok(await page.locator('.hv-viewer').evaluate(element => element.scrollWidth <= element.clientWidth));
  await page.screenshot({ path: resolve(output, 'living-mobile-dark.png') });
  await page.getByRole('button', { name: 'Nasledujúci záber', exact: true }).click();
  assert.equal(await page.locator('#hv-viewer-title').textContent(), 'Obývačka smerom ku kuchyni');
  await page.getByRole('button', { name: 'Zavrieť vizualizáciu', exact: true }).click();
  assert.ok(await page.locator('.dl-main').evaluate(element => element.scrollWidth <= element.clientWidth));
  await page.screenshot({ path: resolve(output, 'gallery-mobile-dark.png') });
  await page.goto(`${origin}/docs`, { waitUntil: 'networkidle' });
  await page.emulateMedia({ colorScheme: 'light' });
  await page.screenshot({ path: resolve(output, 'docs-mobile.png') });
  report.checks.push('Mobile 390px, light and dark, reduced motion, image navigation, no horizontal overflow');

  let fail = true;
  await page.route('**/visualizations/cbb/living-vault.jpg?*', route => fail ? route.abort() : route.continue());
  await page.getByRole('button', { name: 'Zväčšiť: Obývačka · katedrálový strop', exact: true }).click();
  await page.getByRole('alert').waitFor();
  fail = false;
  await page.getByRole('button', { name: 'Skúsiť znova', exact: true }).click();
  await page.locator('.hv-full-image').evaluate(image => image.decode());
  assert.equal(await page.locator('.hv-full-image').evaluate(image => image.naturalWidth), 2400);
  report.checks.push('Image failure and successful retry');
  assert.deepEqual(errors, []);
  await writeFile(resolve(output, 'verification.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} finally { await browser.close(); }
