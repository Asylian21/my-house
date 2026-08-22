import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the Slovak digital-twin product shell", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<html[^>]+lang="sk"/i);
  assert.match(html, /<title>Dom 6012\/26 · Digitálne dvojča<\/title>/i);
  assert.match(html, /DOM 6012\/26/);
  assert.match(html, /Březí u Mikulova/);
  assert.match(html, /Živý výkres/);
  assert.match(html, /Parcela 6012\/26/);
  assert.match(html, /Bazén 5,6 × 3 m/);
  assert.match(
    html,
    /role="treeitem"[^>]+aria-selected="false"[^>]*>[\s\S]{0,400}?Bazén 5,6 × 3 m/,
  );
  assert.match(
    html,
    /Areál a komunikácia<\/span><small>6<\/small>/,
  );
  assert.match(html, /ČÚZK/);
  assert.match(html, /DÁTOVÁ STOPA/);
  assert.match(html, /Skutočné prípojky/);
  assert.match(html, /aria-label="Prieskumník digitálneho dvojčaťa"/);
  assert.match(html, /aria-label="Detail vybraného objektu"/);
  assert.match(html, /class="twin-shell is-presentation"/);
  assert.match(html, /class="scene-panel "[^>]+aria-hidden="true"[^>]+inert/);
  assert.match(html, /class="inspector "[^>]+aria-hidden="true"[^>]+inert/);
  assert.match(html, /aria-pressed="true"[^>]*>[\s\S]{0,500}?Realita/i);
  assert.match(html, /aria-label="Kamera a navigácia"/);
  assert.match(html, /aria-label="Spustiť voľný 3D prelet"/);
  assert.match(html, /aria-keyshortcuts="H"/);
  assert.match(html, /H spustí voľný 3D prelet a G prechádzku interiérom/);
  assert.match(html, /aria-label="Prejsť sa interiérom domu"/);
  assert.match(html, /aria-keyshortcuts="G"/);
  assert.doesNotMatch(html, /Your site is taking shape|Building your site/);
  assert.doesNotMatch(html, /Overené 04|12 % realizácie|react-loading-skeleton/);
});

test("keeps Babylon client-only and removes the disposable starter preview", async () => {
  const [viewport, scene, page, layout, packageJson] = await Promise.all([
    readFile(new URL("../app/babylon-viewport.tsx", import.meta.url), "utf8"),
    readFile(new URL("../lib/babylon-scene.ts", import.meta.url), "utf8"),
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);

  assert.match(viewport, /void import\("@\/lib\/babylon-scene"\)/);
  assert.match(viewport, /ResizeObserver/);
  assert.match(viewport, /window\.matchMedia/);
  assert.match(viewport, /controllerRef\.current\?\.dispose\(\)/);
  assert.match(scene, /adaptToDeviceRatio: false/);
  assert.match(scene, /setHardwareScalingLevel\(/);
  assert.match(
    scene,
    /removeByType\("ArcRotateCameraMouseWheelInput"\)/,
  );
  assert.match(scene, /useNaturalPinchZoom = ORBIT_ZOOM\.useNaturalPinchZoom/);
  assert.match(scene, /!ORBIT_ZOOM\.preventBrowserGesture/);
  // Dedicated exponential wheel zoom: normalized pixels, pinch gain and a
  // framerate-independent glide, with the canvas listener owning the gesture.
  assert.match(scene, /addEventListener\("wheel", this\.handleCanvasWheel/);
  assert.match(scene, /normalizeWheelPixels\(event\)/);
  assert.match(scene, /orbitZoomMultiplier\(pixels, gesture\)/);
  // The glide step lives in the contract (`stepOrbitZoom` wraps
  // `easeOrbitRadius`) so the scene only consumes the settled result.
  assert.match(scene, /stepOrbitZoom\(/);
  assert.match(scene, /\[this\.orbitCamera, this\.flightCamera\]/);
  assert.match(scene, /CascadedShadowGenerator\.IsSupported/);
  // Water keeps true refraction; glazing is alpha-blended so the interior
  // fit-out shows through from outside and the terrace from inside.
  assert.match(scene, /poolWater\.subSurface\.isRefractionEnabled = true/);
  assert.match(scene, /glass\.subSurface\.isRefractionEnabled = false/);
  // Walkthrough: collider-driven walking with the interior fit-out.
  assert.match(scene, /enterWalkthrough\(/);
  assert.match(scene, /Collisions\/collisionCoordinator/);
  assert.match(scene, /AvatarController/);
  assert.match(scene, /buildPorchCurtainWall\(/);
  assert.match(scene, /Štítové okno · zasklenie/);
  assert.match(scene, /zdvižno-posuvné dvere 2 500/);
  assert.match(scene, /pool-water-normal\.png/);
  assert.match(scene, /hedge-privet-albedo\.png/);
  assert.match(scene, /krížená botanická karta/);
  assert.doesNotMatch(scene, /BILLBOARDMODE_Y/);
  assert.doesNotMatch(scene, /material\.unlit = true/);
  assert.match(scene, /return this\.scene\.whenReadyAsync\(\)/);
  assert.match(page, /<TwinStudio \/>/);
  assert.match(layout, /lang="sk"/);
  assert.match(layout, /Dom 6012\/26 · Digitálne dvojča/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);
  await assert.rejects(access(new URL("../app/_sites-preview", import.meta.url)));
  await assert.rejects(access(new URL("../public/_sites-preview", import.meta.url)));
});

test("ships and discloses every local illustrative rendering asset", async () => {
  const assets = [
    ["../public/assets/environment/suburban-field-01-2k.jpg", "ffd8ff"],
    ["../public/assets/environment/suburban-field-01-4k.jpg", "ffd8ff"],
    ["../public/assets/environment/suburban-field-01-8k.jpg", "ffd8ff"],
    ["../public/assets/textures/lawn-albedo.jpg", "ffd8ff"],
    ["../public/assets/textures/lawn-normal.jpg", "ffd8ff"],
    ["../public/assets/textures/plaster-white-albedo.jpg", "ffd8ff"],
    ["../public/assets/textures/plaster-white-normal.jpg", "ffd8ff"],
    ["../public/assets/textures/larch-albedo.jpg", "ffd8ff"],
    ["../public/assets/textures/larch-normal.jpg", "ffd8ff"],
    ["../public/assets/textures/deck-plank-albedo.jpg", "ffd8ff"],
    ["../public/assets/textures/deck-plank-normal.jpg", "ffd8ff"],
    ["../public/assets/textures/metal-anthracite-albedo.jpg", "ffd8ff"],
    ["../public/assets/textures/metal-anthracite-normal.jpg", "ffd8ff"],
    ["../public/assets/textures/gravel-albedo.jpg", "ffd8ff"],
    ["../public/assets/textures/gravel-normal.jpg", "ffd8ff"],
    ["../public/assets/textures/concrete-albedo.jpg", "ffd8ff"],
    ["../public/assets/textures/concrete-normal.jpg", "ffd8ff"],
    ["../public/assets/textures/vinyl-oak-albedo.jpg", "ffd8ff"],
    ["../public/assets/textures/vinyl-oak-normal.jpg", "ffd8ff"],
    ["../public/assets/textures/tile-porcelain-albedo.jpg", "ffd8ff"],
    ["../public/assets/textures/tile-porcelain-normal.jpg", "ffd8ff"],
    ["../public/assets/textures/epoxy-grey-albedo.jpg", "ffd8ff"],
    ["../public/assets/textures/epoxy-grey-normal.jpg", "ffd8ff"],
    ["../public/assets/textures/tile-wall-albedo.jpg", "ffd8ff"],
    ["../public/assets/textures/tile-wall-normal.jpg", "ffd8ff"],
    ["../public/assets/textures/oak-veneer-albedo.jpg", "ffd8ff"],
    ["../public/assets/textures/oak-veneer-normal.jpg", "ffd8ff"],
    ["../public/assets/textures/stone-dark-albedo.jpg", "ffd8ff"],
    ["../public/assets/textures/stone-dark-normal.jpg", "ffd8ff"],
    ["../public/assets/avatar/avatar.glb", "676c5446"],
    ["../public/assets/textures/hedge-privet-albedo.png", "89504e470d0a1a0a"],
    ["../public/assets/textures/pool-water-normal.png", "89504e470d0a1a0a"],
    ["../public/assets/vegetation/ornamental-grass-card.png", "89504e470d0a1a0a"],
    ["../public/assets/vegetation/perennial-cluster-card.png", "89504e470d0a1a0a"],
  ];
  const [sceneSource, interiorSource, avatarSource, readme] = await Promise.all([
    readFile(new URL("../lib/babylon-scene.ts", import.meta.url), "utf8"),
    readFile(new URL("../lib/babylon-interior.ts", import.meta.url), "utf8"),
    readFile(new URL("../lib/babylon-avatar.ts", import.meta.url), "utf8"),
    readFile(new URL("../README.md", import.meta.url), "utf8"),
  ]);

  for (const [relativePath, signature] of assets) {
    const bytes = await readFile(new URL(relativePath, import.meta.url));
    assert.ok(bytes.byteLength > 3 * 1024, `${relativePath} is unexpectedly small`);
    assert.equal(
      bytes.subarray(0, signature.length / 2).toString("hex"),
      signature,
      `${relativePath} has an unexpected file signature`,
    );
    const publicUrl = relativePath.replace("../public", "");
    const textureName = publicUrl
      .replace("/assets/textures/", "")
      .replace(".jpg", "");
    if (publicUrl.endsWith(".glb")) {
      assert.ok(avatarSource.includes(publicUrl), `${publicUrl} is not wired into Babylon`);
      assert.ok(readme.includes("avatar.glb"), `${relativePath} is not disclosed`);
      continue;
    }
    const wired = [sceneSource, interiorSource, avatarSource].some(
      (source) =>
        source.includes(publicUrl) ||
        source.includes(`"${textureName}"`) ||
        source.includes(`"${textureName.replace(/-(albedo|normal)$/, "")}-albedo"`),
    );
    assert.ok(wired, `${publicUrl} is not wired into Babylon`);
    const fileName = relativePath.split("/").at(-1);
    const setName = fileName.replace(/-(albedo|normal)\.jpg$/, "");
    assert.ok(
      readme.includes(fileName) || readme.includes(`\`${setName}\``),
      `${relativePath} is not disclosed`,
    );
  }
  assert.match(readme, /OpenAI imagegen/);
  assert.match(readme, /ilustračný záhradný koncept/);
});
