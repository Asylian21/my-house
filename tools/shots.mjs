// Headless multi-screenshot helper (QA, needs `npx -p playwright` — not a project dependency):
//   npx -p playwright node tools/shots.mjs shots.json [w] [h]
import { readFileSync } from "node:fs";
import { chromium } from "playwright";

const [, , listPath, w = "1280", h = "900"] = process.argv;
const shots = JSON.parse(readFileSync(listPath, "utf8"));
const browser = await chromium.launch({
  executablePath: "/opt/pw-browsers/chromium",
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
});
const page = await browser.newPage({ viewport: { width: Number(w), height: Number(h) }, deviceScaleFactor: 1 });
page.on("pageerror", (e) => console.log("PAGEERROR", e.message));
page.on("console", (m) => { if (m.type() === "error") console.log("CONSOLE", m.text().slice(0, 300), m.location()?.url); });
await page.goto("http://localhost:3000/", { waitUntil: "networkidle", timeout: 120000 });
await page.waitForFunction(() => !!window.twinDebug, null, { timeout: 120000 });
await page.waitForFunction(() => { const t = window.twinDebug; return t.scene.environmentTexture && t.scene.textures.every((x) => x.isReady()) && t.scene.isReady(); }, null, { timeout: 300000 });
await page.waitForSelector(".viewport-state", { state: "detached", timeout: 300000 });
await page.waitForTimeout(1500);
await page.evaluate(() => { window.twinDebug.engine.stopRenderLoop(); });
for (const shot of shots) {
  await page.evaluate(`(async () => { const t = window.twinDebug; ${shot.setup || ""} })()`);
  // Parallel shader compilation needs event-loop turns: render, yield, repeat
  // until every enabled mesh is ready (e.g. the freshly loaded avatar).
  for (let attempt = 0; attempt < 30; attempt += 1) {
    const ready = await page.evaluate(() => { const t = window.twinDebug; t.scene.render(); return t.scene.meshes.every((m) => !m.isEnabled() || m.isReady(true)); });
    if (ready) break;
    await page.waitForTimeout(250);
  }
  await page.evaluate(() => { const t = window.twinDebug; for (let i = 0; i < 2; i += 1) t.scene.render(); });
  await page.screenshot({ path: shot.out, timeout: 180000 });
  const pose = await page.evaluate(() => { const t = window.twinDebug; const c = t.scene.activeCamera; return `${c.name} @ ${c.position.x.toFixed(2)}, ${c.position.y.toFixed(2)}, ${c.position.z.toFixed(2)} mode=${t.getNavigationMode()}`; });
  console.log("shot", shot.out, pose);
}
await browser.close();
