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

const source = (relativePath) =>
  readFile(new URL(`../${relativePath}`, import.meta.url), "utf8");

test("server-renders the Slovak digital-twin product shell", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<html[^>]+lang="sk"/i);
  assert.match(html, /<title>Dom 6012\/26 · Digitálne dvojča<\/title>/i);
  assert.match(html, /Březí u Mikulova/);
  assert.match(html, /Živý výkres/);
  assert.match(html, /Parcela 6012\/26/);
  assert.match(html, /Bazén 5,6 × 3 m/);
  assert.match(
    html,
    /role="treeitem"[^>]+aria-selected="false"[^>]*>[\s\S]{0,400}?Bazén 5,6 × 3 m/,
  );
  assert.match(html, /Areál a komunikácia<\/span><small>6<\/small>/);
  assert.match(html, /ČÚZK/);
  assert.match(html, /Skutočné prípojky|Evidovaná výmera/);
  assert.match(html, /aria-label="Prieskumník digitálneho dvojčaťa"/);
  assert.match(html, /aria-label="Detail vybraného objektu"/);
  assert.doesNotMatch(html, /Your site is taking shape|Building your site/);
  assert.doesNotMatch(html, /Overené 04|12 % realizácie|react-loading-skeleton/);
});

test("opens in the experience with nothing on screen but the drawing", async () => {
  const html = await (await render()).text();

  // The product became a visualisation, so the first frame is the model.
  assert.match(
    html,
    /<main class="twin-shell" data-workspace="experience" data-panels="overlay">/,
  );
  assert.match(html, /<section class="viewport" data-workspace="experience"/);
  assert.match(html, /class="scene-canvas"/);
  assert.match(html, /class="viewport-state" role="status"/);
  assert.match(html, /Skladám digitálne dvojča/);

  // No control may be painted before there is a model to control: the HUD is
  // mounted only once the scene reports ready.
  assert.doesNotMatch(html, /class="hud"/);
  assert.doesNotMatch(html, /aria-label="Kamera a navigácia"/);
  assert.doesNotMatch(html, /aria-label="Otvoriť príkazy modelu"/);
  assert.doesNotMatch(html, /class="palette-scrim"/);
  assert.doesNotMatch(html, /class="help-sheet"/);

  // Documentation still exists for readers and crawlers, only folded away.
  for (const panel of ["scene-panel", "inspector"]) {
    assert.match(
      html,
      new RegExp(`class="${panel}"[^>]+data-open="false"[^>]+inert`),
      `${panel} should stay in the document but out of the tab order`,
    );
  }
  assert.match(html, /class="skip-link"[^>]*>Preskočiť na prieskumník modelu/);
  assert.match(
    html,
    /class="panel-scrim" data-active="false"[^>]+tabindex="-1"/,
  );
});

test("keeps the two workspaces and the auto-hiding chrome wired to one model", async () => {
  const [studio, viewport, visibility, palette, globals] = await Promise.all([
    source("app/twin-studio.tsx"),
    source("app/babylon-viewport.tsx"),
    source("app/use-chrome-visibility.ts"),
    source("app/command-palette.tsx"),
    source("app/globals.css"),
  ]);

  // Documentation and Experience are the only top-level axis; the render style
  // and the chrome are derived from it rather than set by hand.
  assert.match(studio, /viewModeForWorkspace\(workspace\)/);
  assert.match(studio, /chromeContract\(workspace, movement\)/);
  assert.match(studio, /data-workspace=\{workspace\}/);
  assert.match(studio, /workspaceForMovement\(current, next\)/);

  // Chrome visibility is one hook over one pure model, pinned by anything the
  // user opened on purpose.
  assert.match(studio, /useChromeVisibility\(\{/);
  assert.match(studio, /pinned: panelOpen \|\| paletteOpen \|\| helpOpen/);
  assert.match(visibility, /stepChrome\(/);
  assert.match(visibility, /window\.addEventListener\("pointermove"/);
  assert.match(visibility, /CHROME_IDLE\.tickMs/);
  // High-frequency input must not re-render React on every event.
  assert.match(visibility, /if \(next === previous\) return;/);
  assert.match(visibility, /if \(next\.visible !== previous\.visible\) setVisible/);
  // A camera drag is not a request for controls; a tap on touch is.
  assert.match(visibility, /TAP_SLOP_PX/);
  assert.match(visibility, /dragging: draggingRef\.current/);
  // The pointer position reaches the model, which is what lets it tell a real
  // move from the one a resting cursor gets when the layout shifts under it.
  assert.match(visibility, /x: event\.clientX,\s*\n\s*y: event\.clientY,/);

  // The HUD is a safe-area grid of slots, never hand-placed overlays.
  assert.match(viewport, /className="hud"/);
  assert.match(viewport, /data-autohide=\{chrome\.autoHide\}/);
  assert.match(viewport, /data-visible=\{chromeVisible\}/);
  for (const slot of ["hud-row-top", "hud-row-middle", "hud-row-bottom"]) {
    assert.match(viewport, new RegExp(`className="${slot}"|${slot}"`));
  }
  assert.match(globals, /\.hud \{[\s\S]{0,220}?grid-template-rows: auto minmax\(0, 1fr\) auto;/);
  assert.match(
    globals,
    /\.hud\[data-autohide="true"\]\[data-visible="false"\] \.hud-fade \{[\s\S]{0,120}?opacity: 0;/,
  );
  assert.match(globals, /\.hud-slot > \* \{\n {2}pointer-events: auto;/);

  // Survey instruments belong to Documentation only, so the Experience bottom
  // row carries nothing but the dock.
  assert.match(viewport, /\{chrome\.surveyOverlays && \(/);
  assert.match(viewport, /className="survey-compass glass hud-fade"/);
  assert.match(viewport, /className="render-readout glass hud-fade"/);
  // Provenance has exactly one home; the floating duplicate legend is gone.
  assert.doesNotMatch(viewport, /evidence-strip/);
  assert.doesNotMatch(globals, /\.evidence-strip/);
  assert.match(studio, /className="evidence-rail-title"[\s\S]{0,160}?openInspector\("sources"\)/);
  // The HUD sizes itself against the canvas, which the docked panels shrink to
  // roughly half the window in Documentation.
  assert.match(globals, /\.canvas-region \{\n {2}container: viewport \/ inline-size;/);
  assert.match(globals, /@container viewport \(max-width: \d+px\)/);
  assert.match(globals, /\.hud-slot \{[\s\S]{0,220}?max-width: 100%;/);
  assert.match(viewport, /\{chrome\.reticle && /);
  assert.match(viewport, /data-enabled=\{chrome\.virtualPad\}/);

  // One searchable surface replaces the scattered buttons it grew out of.
  assert.match(viewport, /aria-label="Otvoriť príkazy modelu"/);
  assert.match(viewport, /aria-keyshortcuts="Meta\+K Control\+K"/);
  assert.match(studio, /event\.key\.toLowerCase\(\) === "k"/);
  assert.match(palette, /role="combobox"/);
  assert.match(palette, /aria-activedescendant=/);
  assert.match(palette, /role="listbox"/);
  assert.match(palette, /filterCommands\(commands, query\)/);
  assert.match(studio, /\{paletteOpen && \(/);
  // Rooms and characters live in the palette instead of over the render.
  assert.match(studio, /rooms: INTERIOR_ROOMS\.map/);
  assert.match(studio, /avatars: WALK_AVATARS\.map/);
  assert.doesNotMatch(viewport, /walk-avatar-picker|walk-hud/);
  assert.doesNotMatch(globals, /\.walk-hud|\.walk-avatar-option/);

  // The mode switch is one segmented control, not a scatter of toggles.
  assert.match(viewport, /aria-label="Režim pracovného priestoru"/);
  assert.match(viewport, /WORKSPACE_MODE_OPTIONS\.map/);
  assert.match(studio, /event\.key\.toLowerCase\(\) === "m"/);
});

test("keeps Babylon client-only and removes the disposable starter preview", async () => {
  const [viewport, studio, scene, garage, page, layout, globals, packageJson] =
    await Promise.all([
      source("app/babylon-viewport.tsx"),
      source("app/twin-studio.tsx"),
      source("lib/babylon-scene.ts"),
      source("lib/twin-garage.ts"),
      source("app/page.tsx"),
      source("app/layout.tsx"),
      source("app/globals.css"),
      source("package.json"),
    ]);

  assert.match(viewport, /void import\("@\/lib\/babylon-scene"\)/);
  assert.match(viewport, /ResizeObserver/);
  assert.match(viewport, /window\.matchMedia/);
  assert.match(viewport, /controllerRef\.current\?\.dispose\(\)/);
  assert.match(scene, /adaptToDeviceRatio: false/);
  assert.match(scene, /setHardwareScalingLevel\(/);
  assert.match(scene, /removeByType\("ArcRotateCameraMouseWheelInput"\)/);
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
  assert.match(
    scene,
    /const cameras = \[\s*this\.orbitCamera,\s*this\.flightCamera,\s*this\.garageCinematicCamera,\s*this\.avatar\.camera,\s*\];/,
  );
  assert.match(scene, /CascadedShadowGenerator\.IsSupported/);
  // Water keeps true refraction; glazing is alpha-blended so the interior
  // fit-out shows through from outside and the terrace from inside.
  assert.match(scene, /poolWater\.subSurface\.isRefractionEnabled = true/);
  assert.match(scene, /glass\.subSurface\.isRefractionEnabled = false/);
  // Walkthrough: collider-driven walking with the interior fit-out.
  assert.match(scene, /enterWalkthrough\(/);
  assert.match(scene, /Collisions\/collisionCoordinator/);
  assert.match(scene, /AvatarController/);
  assert.match(scene, /assertInventory\(INTERACTIVE_DOOR_INVENTORY\)/);
  assert.match(scene, /event\.code === "KeyE"/);
  assert.match(scene, /getDoorInteraction\(id\?: string\)/);
  assert.match(scene, /doorInteractionHasLineOfSight/);
  assert.match(scene, /pickWithRay/);
  assert.match(
    scene,
    /toggleDoorInteraction\(restoreCanvasFocus = true, id\?: string\)/,
  );
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
  assert.match(scene, /if \(parcel\.labelPointSjtskMm && !parcel\.isSubject\)/);
  assert.match(scene, /parcelCameraForWidth/);
  assert.match(scene, /parcelLabelScaleForRadius/);
  assert.match(scene, /hedge-privet-albedo\.png/);
  assert.match(scene, /krížená botanická karta/);
  assert.doesNotMatch(scene, /BILLBOARDMODE_Y/);
  assert.doesNotMatch(scene, /material\.unlit = true/);
  assert.match(scene, /return this\.scene\.whenReadyAsync\(\)/);

  // Walking: the character is chosen from the palette and remembered.
  assert.match(viewport, /controller\.setWalkAvatar\(id\)/);
  assert.match(viewport, /WALK_AVATAR_STORAGE_KEY/);
  assert.match(
    studio,
    /case "avatar":[\s\S]{0,120}?setWalkAvatar\(action\.avatarId\)/,
  );
  // Movement keys are read from the canvas, so a pointer click on the HUD has
  // to give the keyboard back; keyboard activation keeps its place.
  assert.match(viewport, /hud\.addEventListener\("click", restoreCanvasFocus\)/);
  assert.match(viewport, /if \(event\.detail === 0\) return;/);
  assert.match(viewport, /canvasRef\.current\?\.focus\(\{ preventScroll: true \}\)/);
  assert.match(viewport, /event\.detail !== 0/);

  // Doors keep their diegetic prompt at the centre of the view.
  assert.match(viewport, /controllerRef\.current\?\.getDoorInteraction\(\)/);
  assert.match(viewport, /className="door-prompt glass"/);
  assert.match(viewport, /aria-keyshortcuts="E"/);
  assert.match(viewport, /aria-live="polite"/);
  assert.match(
    viewport,
    /E alebo dotyk na výzvu otvorí a zavrie blízke dvere alebo dvierka spotrebičov/,
  );
  assert.match(
    viewport,
    /obe dvierka spotrebičov majú animovaný pohyb a fyzickú kolíziu/,
  );
  // The door key is disclosed in the one help sheet rather than in a panel.
  assert.match(viewport, /<dt>Dvere a dvierka<\/dt>\s*<dd>E<\/dd>/);
  assert.match(globals, /\.door-prompt/);

  // Garage cinematic keeps its own call to action while standing in 1.12.
  assert.match(viewport, /walkRoomId === GARAGE_VEHICLE\.roomId/);
  assert.match(viewport, /aria-label="Ovládanie auta v garáži"/);
  assert.match(viewport, /requestGarageVehicleAction\(\)/);
  assert.match(scene, /buildInteractiveGarageDoor\(\)/);
  assert.match(scene, /buildGarageVehicle\(\)/);
  assert.match(scene, /garageVehicleSurfaceElevationM/);
  assert.match(scene, /prefers-reduced-motion: reduce/);
  assert.match(garage, /GARAGE-VEHICLE-SKODA-SUPERB/);
  assert.match(garage, /state: "closing-after-park"/);
  assert.match(garage, /state: "closing-after-leave"/);

  // The parcel overview still turns the cadastre layer back on.
  assert.match(viewport, /event\.key === "5"\) applyPreset\("parcels"\)/);
  assert.match(viewport, /preset === "parcels"\) onParcelOverviewRequest\(\)/);
  assert.match(studio, /preset === "parcels"[\s\S]{0,220}?cadastre: true/);

  assert.match(page, /<TwinStudio \/>/);
  assert.match(layout, /lang="sk"/);
  assert.match(layout, /Dom 6012\/26 · Digitálne dvojča/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);
  await assert.rejects(access(new URL("../app/_sites-preview", import.meta.url)));
  await assert.rejects(
    access(new URL("../public/_sites-preview", import.meta.url)),
  );
});

test("styles the interface from one token set rather than ad-hoc values", async () => {
  const globals = await source("app/globals.css");

  // One accent, one spacing scale, one elevation scale, one motion scale.
  for (const token of [
    "--accent:",
    "--sp-4:",
    "--r-md:",
    "--e-2:",
    "--glass-blur:",
    "--dur-3:",
    "--ease-soft:",
    "--hud-gutter:",
    "--ctl-lg:",
  ]) {
    assert.ok(
      globals.includes(token),
      `${token} is missing from the design tokens`,
    );
  }

  // Every floating surface shares one material.
  assert.match(globals, /\.glass \{[\s\S]{0,320}?backdrop-filter: var\(--glass-blur\);/);

  // The shell is a grid keyed on the workspace, not a pile of fixed overlays.
  assert.match(globals, /\.twin-shell\[data-workspace="documentation"\] \{/);
  assert.match(globals, /\.twin-shell\[data-workspace="experience"\] \{/);
  assert.match(globals, /\.twin-shell\[data-panels="overlay"\] \.scene-panel/);

  // Motion and translucency are preferences, not decoration.
  assert.match(globals, /@media \(prefers-reduced-motion: reduce\)/);

  // Every interactive control keeps a visible keyboard ring.
  assert.match(globals, /:focus-visible \{/);

  // The interface must survive a phone and a coarse pointer.
  assert.match(globals, /@media \(max-width: \d+px\)/);
  assert.match(globals, /@media \(pointer: coarse\)/);
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
  const [sceneSource, interiorSource, avatarSource, avatarContract, readme] =
    await Promise.all([
      source("lib/babylon-scene.ts"),
      source("lib/babylon-interior.ts"),
      source("lib/babylon-avatar.ts"),
      source("lib/twin-avatar.ts"),
      source("README.md"),
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
      (candidate) =>
        candidate.includes(publicUrl) ||
        candidate.includes(`"${textureName}"`) ||
        candidate.includes(`"${textureName.replace(/-(albedo|normal)$/, "")}-albedo"`),
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
