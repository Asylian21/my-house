// Real WebGL integration checks against the development server.
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { chromium } from "playwright";

const output = new URL("../output/playwright/", import.meta.url).pathname;
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ channel: "chrome", headless: true,
  args: ["--use-gl=angle", `--use-angle=${process.platform === "darwin" ? "metal" : "swiftshader"}`, "--ignore-gpu-blocklist"] });
const report = {};
try {
  for (const mobile of [false, true]) {
    const page = await browser.newPage({ viewport: mobile ? { width: 390, height: 844 } : { width: 1200, height: 850 },
      deviceScaleFactor: mobile ? 3 : 2, isMobile: mobile, hasTouch: mobile });
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("console", (message) => { if (/GL_INVALID|WebGL.*(error|warning)/i.test(message.text())) errors.push(message.text()); });
    await page.goto("http://localhost:3000/", { waitUntil: "domcontentloaded" });
    await page.waitForFunction(() => window.twinDebug?.getArchvizStatus().status === "ready", null, { timeout: 180_000 });
    await page.evaluate(() => window.twinDebug.whenReady());
    const state = await page.evaluate(async () => {
      const c = window.twinDebug;
      const frames = async () => { for (let i = 0; i < 3; i++) await new Promise(requestAnimationFrame); };
      await frames();
      const visuals = c.scene.meshes.filter((mesh) => mesh.metadata?.archviz);
      const grassCount = visuals.filter((mesh) => mesh.metadata.grass).reduce((count, mesh) => count + mesh.thinInstanceCount, 0);
      const door = visuals.find((mesh) => mesh.metadata.doorId === "DOOR-101-102");
      if (!door) throw new Error("No imported interactive door");
      c.setDoorOpen("DOOR-101-102", false, true);
      const closed = Array.from(door.computeWorldMatrix(true).m);
      c.setDoorOpen("DOOR-101-102", true, true);
      const opened = Array.from(door.computeWorldMatrix(true).m);
      const doorMotion = Math.max(...opened.map((value, index) => Math.abs(value - closed[index])));
      c.setDoorOpen("DOOR-101-102", false, true);
      const snapshot = c.snapshot;
      c.update({ ...snapshot, viewMode: "technical" });
      const technicalVisuals = visuals.filter((mesh) => mesh.visibility > 0).length;
      c.update(snapshot);
      const base = c.getArchvizStatus();
      c.setNavigationMode("flight");
      await frames();
      const flight = c.navigationMode;
      const rooms = [];
      for (let index = 1; index <= 12; index++) {
        const id = `ROOM-1-${String(index).padStart(2, "0")}`;
        c.enterWalkthrough(id);
        await c.avatar.load();
        await frames();
        rooms.push({ requested: id, actual: c.getWalkRoom()?.id });
      }
      c.enterWalkthrough("ROOM-1-03");
      c.setWalkView("first");
      await frames();
      return { ...base, grassCount, doorMotion, technicalVisuals, flight, rooms, quality: c.renderQuality };
    });
    assert.ok(state.replaced > 1600);
    assert.ok(state.doorMotion > 0.1, "Blender door did not follow its interactive hinge");
    assert.equal(state.technicalVisuals, 0);
    assert.equal(state.flight, "flight");
    assert.equal(state.grassCount, mobile ? 2048 : 5531);
    for (const room of state.rooms) assert.equal(room.actual, room.requested, "Room entry drifted");
    await page.screenshot({ path: `${output}archviz-${mobile ? "mobile" : "desktop"}-interior.png` });
    await page.evaluate(() => window.twinDebug.setCameraPreset("garden"));
    await page.screenshot({ path: `${output}archviz-${mobile ? "mobile" : "desktop"}-garden.png` });
    assert.deepEqual(errors, []);
    report[mobile ? "mobile" : "desktop"] = state;
    console.log(`archviz-check: ${mobile ? "mobile" : "desktop"} passed`);
    await page.close();
  }
  const fallback = await browser.newPage({ viewport: { width: 900, height: 700 } });
  await fallback.route("**/assets/archviz/dom-interior-02.glb", (route) => route.abort());
  await fallback.goto("http://localhost:3000/", { waitUntil: "domcontentloaded" });
  await fallback.waitForSelector(".archviz-notice", { timeout: 120_000 });
  report.fallback = await fallback.evaluate(() => {
    const c = window.twinDebug;
    c.enterWalkthrough("ROOM-1-03");
    return { ...c.getArchvizStatus(), room: c.getWalkRoom()?.id,
      visibleOriginals: c.archviz.sources.filter(({ mesh }) => mesh.visibility > 0 && mesh.isEnabled()).length };
  });
  assert.equal(report.fallback.status, "fallback");
  assert.equal(report.fallback.visuals, 0);
  assert.equal(report.fallback.room, "ROOM-1-03");
  assert.ok(report.fallback.visibleOriginals > 1000);
  await writeFile(`${output}archviz-check.json`, JSON.stringify(report, null, 2));
  console.log("archviz-check PASS: desktop, mobile, 12 rooms, imported door animation, flight, technical mode, failed-download fallback");
} finally {
  await browser.close();
}
