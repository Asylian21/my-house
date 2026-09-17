import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium } from 'playwright';
import { views } from './views.mjs';

const draft = process.argv.includes('--draft');
const origin = process.env.DOM_TEST_URL ?? 'http://localhost:3001';
const root = resolve(import.meta.dirname, '../..');
const output = resolve(root, draft ? 'output/playwright/house-visualizations/draft' : 'public/visualizations/cbb');
const width = draft ? 1200 : 2400, height = draft ? 750 : 1500;
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ channel: 'chrome', headless: true,
  args: ['--use-gl=angle', `--use-angle=${process.platform === 'darwin' ? 'metal' : 'swiftshader'}`, '--ignore-gpu-blocklist'] });
const errors = [], records = [];
const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
page.on('pageerror', error => errors.push(error.message));
page.on('response', response => { if (response.status() >= 400 && !response.url().endsWith('/favicon.ico')) errors.push(`${response.status()} ${response.url()}`); });
try {
  await page.goto(`${origin}/3d?variant=c&heating=b&living=b`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => !!window.twinDebug, null, { timeout: 120_000 });
  await page.evaluate(async () => {
    const t = window.twinDebug;
    await t.whenReady();
    t.setCameraPreset('garden');
    t.update({ ...t.snapshot, selectionId: null, visibleLayers: { ...t.snapshot.visibleLayers, cadastre: false } });
    t.setNavigationMode('flight');
    t.engine.stopRenderLoop();
    t.engine.setHardwareScalingLevel(1);
    t.engine.resize();
    // Keep the drawing buffer populated through asynchronous resize callbacks
    // and the browser compositor's screenshot frame.
    t.engine.runRenderLoop(() => t.scene.render());
  });
  await page.addStyleTag({ content: '.canvas-region > :not(canvas){visibility:hidden!important} canvas.scene-canvas{outline:none!important;border:0!important;border-radius:0!important}' });
  const design = await page.locator('canvas.scene-canvas').evaluate(canvas => ({ ...canvas.dataset }));
  assert.equal(design.heatingLayout, 'B'); assert.equal(design.livingLayout, 'B');
  for (const view of views) {
    await page.setViewportSize({ width, height });
    await page.evaluate(() => window.twinDebug.engine.resize());
    await page.evaluate(view => {
      const t = window.twinDebug, camera = t.scene.activeCamera;
      camera.position.set(...view.position);
      camera.rotationQuaternion = null;
      camera.setTarget(camera.position.clone().set(...view.target));
      camera.fov = view.fov;
      camera.minZ = 0.025;
      camera.cameraDirection.setAll(0); camera.cameraRotation.setAll(0);
      t.scene.render();
    }, view);
    // Render until every newly visible shader and texture is ready.
    await page.waitForFunction(() => { const t = window.twinDebug; t.scene.render(); return t.scene.isReady(); }, null, { timeout: 120_000 });
    await page.evaluate(() => { for (let i = 0; i < 12; i++) window.twinDebug.scene.render(); });
    const extension = draft ? 'png' : 'jpg';
    const path = resolve(output, `${view.id}.${extension}`);
    const box = await page.locator('canvas.scene-canvas').boundingBox();
    assert.equal(box.width, width); assert.equal(box.height, height);
    await page.locator('canvas.scene-canvas').screenshot({ path, ...(draft ? {} : { quality: 94 }), timeout: 120_000 });
    const bytes = await readFile(path);
    if (!draft) {
      await page.setViewportSize({ width: 800, height: 500 });
      await page.evaluate(async () => { const t = window.twinDebug; t.engine.resize(); for (let i = 0; i < 4; i++) await new Promise(requestAnimationFrame); });
      await page.waitForFunction(() => window.twinDebug.scene.isReady());
      await page.locator('canvas.scene-canvas').screenshot({ path: resolve(output, `${view.id}-thumb.jpg`), quality: 85 });
    }
    records.push({ ...view, url: `/visualizations/cbb/${view.id}.${extension}`, thumbnailUrl: `/visualizations/cbb/${view.id}-thumb.jpg`, bytes: bytes.length,
      sha256: createHash('sha256').update(bytes).digest('hex') });
    console.log(`Captured ${view.id} (${Math.round(bytes.length / 1024)} kB)`);
  }
  const readiness = await page.evaluate(() => ({ sceneReady: window.twinDebug.scene.isReady(), archviz: window.twinDebug.getArchvizStatus() }));
  assert.equal(readiness.sceneReady, true); assert.equal(readiness.archviz.status, 'ready'); assert.deepEqual(errors, []);
  const report = { design: 'C/B/B', capturedAt: new Date().toISOString(), width, height, readiness, views: records };
  await writeFile(draft ? resolve(output, 'capture.json') : resolve(root, 'lib/house-visualizations.generated.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(`Verified ${records.length} model views, ${width} × ${height}, C/B/B.`);
} finally { await browser.close(); }
