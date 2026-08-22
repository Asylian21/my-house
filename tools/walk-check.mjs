// Headless functional check of the walkthrough collider (QA, needs `npx -p playwright`):
//   npx -p playwright node tools/walk-check.mjs
import { chromium } from "playwright";

const browser = await chromium.launch({
  executablePath: "/opt/pw-browsers/chromium",
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
});
const page = await browser.newPage({ viewport: { width: 480, height: 320 }, deviceScaleFactor: 1 });
page.on("pageerror", (e) => console.log("PAGEERROR", e.message));
await page.goto("http://localhost:3000/", { waitUntil: "networkidle", timeout: 120000 });
await page.waitForFunction(() => !!window.twinDebug, null, { timeout: 120000 });
await page.waitForFunction(() => { const t = window.twinDebug; return t.scene.environmentTexture && t.scene.textures.every((x) => x.isReady()) && t.scene.isReady(); }, null, { timeout: 300000 });
await page.waitForSelector(".viewport-state", { state: "detached", timeout: 300000 });
await page.evaluate(() => { window.twinDebug.engine.stopRenderLoop(); });
const result = await page.evaluate(async () => {
  const t = window.twinDebug;
  const out = {};
  const walk = (roomId, command, frames) => {
    t.enterWalkthrough(roomId);
    const start = t.flightCamera.position.clone();
    t.setFlightCommand(command, true);
    const steps = [];
    for (let i = 0; i < frames; i += 1) {
      const before = t.flightCamera.position.clone();
      t.scene.render();
      const after = t.flightCamera.position.clone();
      steps.push(Number(Math.hypot(after.x - before.x, after.z - before.z).toFixed(3)));
    }
    t.setFlightCommand(command, false);
    const end = t.flightCamera.position.clone();
    return {
      room: t.getWalkRoom()?.number ?? null,
      travelled: Math.hypot(end.x - start.x, end.z - start.z),
      y: end.y,
      mode: t.getNavigationMode(),
      steps,
    };
  };
  out.wcForward = walk("ROOM-1-06", "forward", 60);
  out.wcBackward = walk("ROOM-1-06", "backward", 60);
  out.livingForward = walk("ROOM-1-03", "forward", 60);
  out.bedroomLeft = walk("ROOM-1-10", "left", 60);
  t.setNavigationMode("orbit");
  out.backToOrbit = t.getNavigationMode();
  out.collidables = t.scene.meshes.filter((m) => m.checkCollisions).length;
  return out;
});
console.log(JSON.stringify(result, null, 2));
await browser.close();
