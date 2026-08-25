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
  assert.match(html, /aria-label="Prehľad parciel v mojom rade a oproti"/);
  assert.match(html, /aria-keyshortcuts="5"/);
  assert.match(html, />Parcely</);
  assert.match(html, /ČÚZK · overené 24\. 8\. 2026/);
  assert.match(html, /aria-label="Spustiť voľný 3D prelet"/);
  assert.match(html, /aria-keyshortcuts="H"/);
  assert.match(html, /H spustí voľný 3D prelet a G prechádzku interiérom/);
  assert.match(html, /aria-label="Prejsť sa interiérom domu"/);
  assert.match(html, /aria-keyshortcuts="G"/);
  assert.doesNotMatch(html, /Your site is taking shape|Building your site/);
  assert.doesNotMatch(html, /Overené 04|12 % realizácie|react-loading-skeleton/);
});

test("keeps Babylon client-only and removes the disposable starter preview", async () => {
  const [viewport, studio, scene, garage, page, layout, globals, packageJson] = await Promise.all([
    readFile(new URL("../app/babylon-viewport.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/twin-studio.tsx", import.meta.url), "utf8"),
    readFile(new URL("../lib/babylon-scene.ts", import.meta.url), "utf8"),
    readFile(new URL("../lib/twin-garage.ts", import.meta.url), "utf8"),
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
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
  assert.match(scene, /assertInventory\(ARCHITECTURAL_DOOR_INVENTORY\)/);
  assert.match(scene, /event\.code === "KeyE"/);
  assert.match(scene, /getDoorInteraction\(\)/);
  assert.match(scene, /doorInteractionHasLineOfSight/);
  assert.match(scene, /pickWithRay/);
  assert.match(scene, /toggleDoorInteraction\(restoreCanvasFocus = true\)/);
  assert.match(scene, /buildPorchCurtainWall\(/);
  assert.match(scene, /Štítový trojuholníkový svetlík · zasklenie/);
  assert.match(scene, /pevné presklenie 2 000/);
  assert.match(scene, /pás venca/);
  assert.match(scene, /pool-water-normal\.png/);
  assert.match(scene, /street-grey-block-paver-albedo/);
  assert.match(scene, /street-grey-block-paver-normal/);
  assert.match(scene, /surfaceFinish\.visualJointMm/);
  assert.match(scene, /paverJointInsetPx = paverJointPx \/ 2/);
  assert.match(scene, /realisticMaterials\.roadReserve/);
  assert.match(scene, /road\.backFaceCulling = false/);
  assert.match(scene, /roadReserve\.backFaceCulling = false/);
  assert.match(scene, /Riedka náletová vegetácia krajnice/);
  assert.match(scene, /Stožiar verejného osvetlenia/);
  assert.match(scene, /LED hlavica verejného osvetlenia/);
  assert.match(scene, /Orientačný popis parcely/);
  assert.match(scene, /parcel\.overviewVisibility === "ORIENTATION"/);
  assert.match(scene, /if \(parcel\.displayLabel\)/);
  assert.match(scene, /parcel\.sjtskHoleRingsMm/);
  assert.match(scene, /ROAD_CONTEXT\.visibleCarriagewayPolygonMm/);
  assert.match(scene, /ROAD_CONTEXT\.overviewOuterRoadEdgeMm/);
  assert.match(
    scene,
    /Miestna komunikácia 6012\/1 \+ 6013 · súvislá vozovka cez celý parcelný prehľad/,
  );
  assert.doesNotMatch(scene, /ROAD_CONTEXT\.frontagePolygonMm/);
  assert.doesNotMatch(scene, /ROAD_CONTEXT\.cornerCarriagewayPolygonMm/);
  assert.match(scene, /parcelCameraForWidth/);
  assert.match(scene, /parcelLabelScaleForRadius/);
  assert.match(scene, /hedge-privet-albedo\.png/);
  assert.match(scene, /krížená botanická karta/);
  assert.doesNotMatch(scene, /BILLBOARDMODE_Y/);
  assert.doesNotMatch(scene, /material\.unlit = true/);
  assert.match(scene, /return this\.scene\.whenReadyAsync\(\)/);
  // The room chooser remains available without permanently covering the
  // interior view: a real button owns the expanded state and hidden content.
  assert.match(viewport, /const \[walkHudCollapsed, setWalkHudCollapsed\] = useState\(false\)/);
  assert.match(viewport, /aria-expanded=\{!walkHudCollapsed\}/);
  assert.match(viewport, /aria-controls="walk-hud-content"/);
  assert.match(viewport, /id="walk-hud-content"/);
  assert.match(viewport, /hidden=\{walkHudCollapsed\}/);
  assert.match(viewport, /<fieldset[\s\S]*className="walk-avatar-picker"/);
  assert.match(viewport, /WALK_AVATARS\.map/);
  assert.match(viewport, /type="radio"/);
  assert.match(viewport, /aria-busy=\{pendingWalkAvatarId !== null\}/);
  assert.match(viewport, /controller\.setWalkAvatar\(id\)/);
  assert.match(viewport, /WALK_AVATAR_STORAGE_KEY/);
  assert.match(viewport, /event\.detail !== 0/);
  assert.match(viewport, /canvasRef\.current\?\.focus\(\{ preventScroll: true \}\)/);
  assert.match(viewport, /controllerRef\.current\?\.getDoorInteraction\(\)/);
  assert.match(viewport, /className=\{`door-interaction-prompt/);
  assert.match(viewport, /aria-keyshortcuts="E"/);
  assert.match(viewport, /aria-live="polite"/);
  assert.match(viewport, /E alebo dotyk na výzvu otvorí a zavrie blízke dvere/);
  assert.match(studio, /Dvere v prechádzke/);
  assert.match(viewport, /walkRoomId === GARAGE_VEHICLE\.roomId/);
  assert.match(viewport, /aria-label="Ovládanie auta v garáži"/);
  assert.match(viewport, /disabled=\{!garageAction\}/);
  assert.match(viewport, /requestGarageVehicleAction\(garageAction\)/);
  assert.match(scene, /buildInteractiveGarageDoor\(\)/);
  assert.match(scene, /buildGarageVehicle\(\)/);
  assert.match(scene, /garageVehicleSurfaceElevationM/);
  assert.match(scene, /prefers-reduced-motion: reduce/);
  assert.match(garage, /GARAGE-VEHICLE-SKODA-SUPERB/);
  assert.match(garage, /state: "closing-after-park"/);
  assert.match(garage, /state: "closing-after-leave"/);
  assert.match(viewport, /event\.key === "5"\) applyPreset\("parcels"\)/);
  assert.match(viewport, /preset === "parcels"\) onParcelOverviewRequest\(\)/);
  assert.match(studio, /preset === "parcels"[\s\S]{0,180}?cadastre: true/);
  assert.match(globals, /\.walk-hud\.is-collapsed/);
  assert.match(globals, /\.walk-hud-content\[hidden\] \{ display: none; \}/);
  assert.match(globals, /\.walk-avatar-options/);
  assert.match(globals, /\.walk-avatar-option\.is-selected/);
  assert.match(globals, /\.door-interaction-prompt/);
  assert.match(globals, /bottom: 194px/);
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
    ["../public/assets/textures/boucle-taupe-albedo.jpg", "ffd8ff"],
    ["../public/assets/textures/boucle-taupe-normal.jpg", "ffd8ff"],
    ["../public/assets/textures/rug-wool-taupe-albedo.jpg", "ffd8ff"],
    ["../public/assets/textures/rug-wool-taupe-normal.jpg", "ffd8ff"],
    ["../public/assets/avatar/avatar.glb", "676c5446"],
    ["../public/assets/avatar/vanguard.glb", "676c5446"],
    ["../public/assets/avatar/robot-expressive.glb", "676c5446"],
    ["../public/assets/avatar/michelle-light-diffuse.png", "89504e470d0a1a0a"],
    ["../public/assets/textures/hedge-privet-albedo.png", "89504e470d0a1a0a"],
    ["../public/assets/textures/pool-water-normal.png", "89504e470d0a1a0a"],
    ["../public/assets/vegetation/ornamental-grass-card.png", "89504e470d0a1a0a"],
    ["../public/assets/vegetation/perennial-cluster-card.png", "89504e470d0a1a0a"],
  ];
  const [sceneSource, interiorSource, avatarSource, avatarContract, readme] = await Promise.all([
    readFile(new URL("../lib/babylon-scene.ts", import.meta.url), "utf8"),
    readFile(new URL("../lib/babylon-interior.ts", import.meta.url), "utf8"),
    readFile(new URL("../lib/babylon-avatar.ts", import.meta.url), "utf8"),
    readFile(new URL("../lib/twin-avatar.ts", import.meta.url), "utf8"),
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
    const fileName = relativePath.split("/").at(-1);
    const textureName = publicUrl
      .replace("/assets/textures/", "")
      .replace(".jpg", "");
    if (publicUrl.endsWith(".glb")) {
      assert.ok(
        avatarSource.includes(publicUrl) || avatarContract.includes(publicUrl),
        `${publicUrl} is not wired into Babylon`,
      );
      assert.ok(readme.includes(fileName), `${relativePath} is not disclosed`);
      continue;
    }
    const wired = [sceneSource, interiorSource, avatarSource, avatarContract].some(
      (source) =>
        source.includes(publicUrl) ||
        source.includes(`"${textureName}"`) ||
        source.includes(`"${textureName.replace(/-(albedo|normal)$/, "")}-albedo"`),
    );
    assert.ok(wired, `${publicUrl} is not wired into Babylon`);
    const setName = fileName.replace(/-(albedo|normal)\.jpg$/, "");
    assert.ok(
      readme.includes(fileName) || readme.includes(`\`${setName}\``),
      `${relativePath} is not disclosed`,
    );
  }
  assert.match(readme, /OpenAI imagegen/);
  assert.match(avatarSource, /material\.albedoTexture = avatarDiffuse/);
  assert.match(readme, /ilustračný záhradný koncept/);
});
