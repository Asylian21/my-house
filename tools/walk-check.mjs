// Assertion-based Chromium/WebGL regression check for the walkthrough:
//   npx -p playwright node tools/walk-check.mjs
//
// A development server must already be running at http://localhost:3000.
import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { createRequire } from "node:module";
import { delimiter, dirname, join } from "node:path";

const APP_URL = "http://localhost:3000/";
const WALK_CHECK_FPS = Number(process.env.WALK_CHECK_FPS ?? 60);
assert.ok(
  Number.isFinite(WALK_CHECK_FPS) && WALK_CHECK_FPS > 0,
  `WALK_CHECK_FPS must be a positive finite number, got ${process.env.WALK_CHECK_FPS}`,
);
const framesFrom60Hz = (framesAt60Hz) =>
  Math.max(1, Math.round((framesAt60Hz * WALK_CHECK_FPS) / 60));
const FIXED_DELTA_MS = 1000 / WALK_CHECK_FPS;
const LAUNCH_ARGS =
  process.platform === "darwin"
    ? ["--use-gl=angle", "--use-angle=metal", "--ignore-gpu-blocklist"]
    : [
        "--use-gl=angle",
        "--use-angle=swiftshader",
        "--enable-unsafe-swiftshader",
        "--ignore-gpu-blocklist",
      ];

// npm 10/11 exposes `npx -p playwright` through a temporary node_modules/.bin
// PATH entry, but Node ESM does not search that entry for bare imports. Anchor
// a CommonJS resolver in each advertised node_modules directory so the exact
// documented invocation works without adding Playwright to package.json.
function loadPlaywright() {
  const resolvers = [createRequire(import.meta.url)];
  for (const binDirectory of (process.env.PATH ?? "").split(delimiter)) {
    if (!binDirectory || dirname(binDirectory) === binDirectory) continue;
    if (binDirectory !== join(dirname(binDirectory), ".bin")) continue;
    resolvers.push(
      createRequire(join(dirname(binDirectory), "walk-check-loader.cjs")),
    );
  }
  const failures = [];
  for (const requireFrom of resolvers) {
    try {
      return requireFrom("playwright");
    } catch (error) {
      failures.push(errorMessage(error));
    }
  }
  assert.fail(
    `Playwright is unavailable; run with npx -p playwright. ${failures.at(-1) ?? ""}`,
  );
}

function errorMessage(error) {
  return error instanceof Error ? error.message : String(error);
}

const { chromium } = loadPlaywright();

async function launchChromium() {
  const candidates = [];
  const addExecutable = (label, executablePath) => {
    if (
      executablePath &&
      existsSync(executablePath) &&
      !candidates.some((candidate) => candidate.executablePath === executablePath)
    ) {
      candidates.push({ label, executablePath });
    }
  };

  addExecutable(
    "PLAYWRIGHT_CHROMIUM_EXECUTABLE",
    process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
  );
  addExecutable("workspace Chromium", "/opt/pw-browsers/chromium");
  addExecutable(
    "Google Chrome (macOS)",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  );
  addExecutable("Google Chrome (Linux)", "/usr/bin/google-chrome");

  try {
    addExecutable("Playwright Chromium", chromium.executablePath());
  } catch {
    // The npx package can be present without its optional browser download.
  }

  const failures = [];
  for (const candidate of candidates) {
    try {
      return await chromium.launch({
        executablePath: candidate.executablePath,
        headless: true,
        args: LAUNCH_ARGS,
      });
    } catch (error) {
      failures.push(`${candidate.label}: ${errorMessage(error)}`);
    }
  }

  const channel = process.env.PLAYWRIGHT_CHANNEL || "chrome";
  try {
    return await chromium.launch({ channel, headless: true, args: LAUNCH_ARGS });
  } catch (error) {
    failures.push(`channel ${channel}: ${errorMessage(error)}`);
  }

  try {
    return await chromium.launch({ headless: true, args: LAUNCH_ARGS });
  } catch (error) {
    failures.push(`Playwright default: ${errorMessage(error)}`);
  }

  assert.fail(`Chromium could not be launched:\n${failures.join("\n")}`);
}

function assertNoCameraErrors(result, label) {
  assert.deepEqual(
    result.cameraErrors,
    [],
    `${label}: camera invariant failures:\n${result.cameraErrors.join("\n")}`,
  );
}

async function run() {
  console.log(`walk-check: launching Chromium for ${APP_URL}`);
  const browser = await launchChromium();
  try {
    const page = await browser.newPage({
      viewport: { width: 480, height: 320 },
      deviceScaleFactor: 1,
    });
    const pageErrors = [];
    page.on("pageerror", (error) => pageErrors.push(error.message));
    page.on("console", (message) => {
      const text = message.text();
      if (text.startsWith("[walk-check]")) console.log(text);
    });

    const response = await page.goto(APP_URL, {
      waitUntil: "domcontentloaded",
      timeout: 120_000,
    });
    assert.ok(response, `${APP_URL} did not return a document response`);
    assert.ok(
      response.ok(),
      `${APP_URL} returned HTTP ${response.status()} ${response.statusText()}`,
    );
    console.log(`walk-check: document loaded (HTTP ${response.status()})`);

    await page.waitForFunction(() => Boolean(window.twinDebug), null, {
      timeout: 120_000,
    });
    console.log("walk-check: Babylon controller exposed");
    await page.evaluate(() => window.twinDebug.engine.stopRenderLoop());
    console.log("walk-check: continuous render loop stopped; awaiting scene contract");
    const readiness = await page.evaluate(async () => {
      const controller = window.twinDebug;
      const ready = await Promise.race([
        controller.whenReady().then(() => true),
        new Promise((resolve) => window.setTimeout(() => resolve(false), 180_000)),
      ]);
      return {
        ready,
        sceneReady: controller.scene.isReady(),
        viewportState: document.querySelector(".viewport-state")?.textContent ?? null,
      };
    });
    assert.equal(
      readiness.ready,
      true,
      `Babylon whenReady() timed out; sceneReady=${readiness.sceneReady}, UI=${readiness.viewportState}`,
    );
    await page.waitForSelector(".viewport-state", {
      state: "detached",
      timeout: 15_000,
    });
    console.log("walk-check: authoritative viewport ready state reached");

    const load = await page.evaluate(async ({ fixedDeltaMs, fps }) => {
      const controller = window.twinDebug;
      controller.engine.stopRenderLoop();
      await controller.avatar.load();
      const avatarSceneReady = await Promise.race([
        controller.whenReady().then(() => true),
        new Promise((resolve) => window.setTimeout(() => resolve(false), 60_000)),
      ]);

      // Manual renders otherwise see near-zero delta time and cannot exercise
      // acceleration, collision substeps or camera-boom recovery deterministically.
      controller.engine.getDeltaTime = () => fixedDeltaMs;

      const pose = () => ({ ...controller.avatar.pose });
      const distance = (from, to) =>
        Math.hypot(to.x - from.x, to.z - from.z);
      const framesFrom60Hz = (framesAt60Hz) =>
        Math.max(1, Math.round((framesAt60Hz * fps) / 60));
      const addError = (errors, message) => {
        if (errors.length < 30 && !errors.includes(message)) errors.push(message);
      };
      const inspectCamera = (label, errors) => {
        const state = controller.getWalkDebugState();
        const camera = controller.avatar.camera;
        const active = controller.scene.activeCamera;
        const position = active?.position;
        const target = camera.target;
        const lower = camera.lowerRadiusLimit ?? 0;
        const upper = camera.upperRadiusLimit ?? Number.POSITIVE_INFINITY;
        const requested = state.camera.requestedRadiusM;
        const desired = state.camera.desiredRadiusM;
        const effective = state.camera.effectiveRadiusM;
        const targetDistance = position
          ? Math.hypot(
              position.x - target.x,
              position.y - target.y,
              position.z - target.z,
            )
          : Number.NaN;
        const finiteValues = {
          poseX: state.pose.x,
          poseY: state.pose.y,
          poseZ: state.pose.z,
          poseYaw: state.pose.yaw,
          cameraX: position?.x,
          cameraY: position?.y,
          cameraZ: position?.z,
          targetX: target.x,
          targetY: target.y,
          targetZ: target.z,
          alpha: camera.alpha,
          beta: camera.beta,
          requested,
          desired,
          effective,
          indoorBlend: state.camera.indoorBlend,
          surfaceY: state.camera.surfaceY,
          cameraSurfaceY: state.camera.cameraSurfaceY,
          renderedRadius: camera.radius,
          targetDistance,
        };
        for (const [name, value] of Object.entries(finiteValues)) {
          if (!Number.isFinite(value)) {
            addError(errors, `${label}: ${name} is not finite (${String(value)})`);
          }
        }
        if (state.mode !== "walk") {
          addError(errors, `${label}: mode is ${state.mode}, expected walk`);
        }
        if (state.view !== "third") {
          addError(errors, `${label}: view is ${state.view}, expected third`);
        }
        if (!state.camera.surfaceValid) {
          addError(
            errors,
            `${label}: no valid walk surface at ${state.pose.x}, ${state.pose.z}`,
          );
        }
        if (
          state.camera.indoorBlend < -0.001 ||
          state.camera.indoorBlend > 1.001
        ) {
          addError(
            errors,
            `${label}: indoor blend ${state.camera.indoorBlend} is outside [0, 1]`,
          );
        }
        if (Math.abs(state.pose.y - state.camera.surfaceY) > 0.006) {
          addError(
            errors,
            `${label}: avatar Y ${state.pose.y} does not follow surface Y ${state.camera.surfaceY}`,
          );
        }
        if (
          Math.abs(state.camera.cameraSurfaceY - state.camera.surfaceY) > 0.161
        ) {
          addError(
            errors,
            `${label}: camera surface lag ${Math.abs(state.camera.cameraSurfaceY - state.camera.surfaceY)} m exceeds contract`,
          );
        }
        if (active !== camera || active?.name !== "avatar-camera") {
          addError(
            errors,
            `${label}: active camera is ${active?.name ?? "none"}, expected avatar-camera`,
          );
        }
        if (desired < lower - 0.001 || desired > upper + 0.001) {
          addError(
            errors,
            `${label}: desired radius ${desired} is outside [${lower}, ${upper}]`,
          );
        }
        if (desired > requested + 0.001) {
          addError(
            errors,
            `${label}: desired radius ${desired} exceeds requested ${requested}`,
          );
        }
        if (effective < lower - 0.015 || effective > desired + 0.015) {
          addError(
            errors,
            `${label}: effective radius ${effective} is outside [${lower}, ${desired}]`,
          );
        }
        if (Math.abs(camera.radius - effective) > 0.015) {
          addError(
            errors,
            `${label}: rendered radius ${camera.radius} differs from effective ${effective}`,
          );
        }
        if (Math.abs(targetDistance - camera.radius) > 0.08) {
          addError(
            errors,
            `${label}: camera-target distance ${targetDistance} differs from radius ${camera.radius}`,
          );
        }
      };
      const render = (frames, label, errors) => {
        for (let frame = 0; frame < frames; frame += 1) {
          controller.scene.render();
          inspectCamera(`${label} frame ${frame + 1}`, errors);
        }
      };
      const begin = (roomId, label = roomId) => {
        controller.setWalkView("third");
        controller.enterWalkthrough(roomId);
        controller.setWalkView("third");
        if (typeof controller.applyWalkView === "function") {
          controller.applyWalkView();
        }
        const cameraErrors = [];
        render(framesFrom60Hz(3), `${label} settle`, cameraErrors);
        return {
          pose: pose(),
          roomId: controller.getWalkRoom()?.id ?? null,
          cameraErrors,
        };
      };
      const measureFrames = (frames, label, tailFrames = 0) => {
        const cameraErrors = [];
        const start = pose();
        let tailStart = null;
        for (let frame = 0; frame < frames; frame += 1) {
          if (tailFrames > 0 && frame === frames - tailFrames) {
            tailStart = pose();
          }
          render(1, `${label} frame ${frame + 1}`, cameraErrors);
        }
        const end = pose();
        return {
          start,
          end,
          travelled: distance(start, end),
          tailTravelled: tailStart ? distance(tailStart, end) : null,
          roomId: controller.getWalkRoom()?.id ?? null,
          blocked: controller.isWalkBlocked(),
          cameraErrors,
        };
      };
      window.__walkCheckHarness = {
        controller,
        pose,
        distance,
        inspectCamera,
        render,
        framesFrom60Hz,
        begin,
        measureFrames,
      };

      const initial = begin("ROOM-1-03", "initial load");
      return {
        httpReadyState: document.readyState,
        canvasCount: document.querySelectorAll("canvas").length,
        webGlVersion: controller.engine.webGLVersion,
        renderWidth: controller.engine.getRenderWidth(),
        renderHeight: controller.engine.getRenderHeight(),
        avatarLoaded: controller.avatar.isLoaded,
        avatarSceneReady,
        environmentReady: Boolean(controller.scene.environmentTexture),
        // Effect-layer render targets are frame-local GPU surfaces, not source
        // assets. They can report not-ready while the continuous loop is
        // intentionally paused; keep the gate strict for every content texture.
        texturesNotReady: controller.scene.textures
          .filter((texture) => !texture.isRenderTarget && !texture.isReady())
          .map((texture) => texture.name || texture.url || "unnamed"),
        collidables: controller.scene.meshes.filter((mesh) => mesh.checkCollisions)
          .length,
        mode: controller.getNavigationMode(),
        view: controller.getWalkView(),
        activeCamera: controller.scene.activeCamera?.name ?? null,
        roomId: initial.roomId,
        cameraErrors: initial.cameraErrors,
      };
    }, { fixedDeltaMs: FIXED_DELTA_MS, fps: WALK_CHECK_FPS });

    assert.match(load.httpReadyState, /^(interactive|complete)$/);
    assert.equal(load.canvasCount, 1, "walkthrough must expose exactly one canvas");
    assert.ok(load.webGlVersion >= 1, "Babylon engine did not obtain WebGL");
    assert.ok(load.renderWidth > 0 && load.renderHeight > 0, "WebGL render target is empty");
    assert.equal(load.avatarLoaded, true, "avatar GLB did not load");
    assert.equal(
      load.avatarSceneReady,
      true,
      `avatar resources did not become ready: ${load.texturesNotReady.join(", ")}`,
    );
    assert.equal(load.environmentReady, true, "environment texture did not load");
    assert.deepEqual(
      load.texturesNotReady,
      [],
      `scene textures are not ready: ${load.texturesNotReady.join(", ")}`,
    );
    assert.ok(load.collidables > 0, "scene has no collision meshes");
    assert.equal(load.mode, "walk");
    assert.equal(load.view, "third");
    assert.equal(load.activeCamera, "avatar-camera");
    assert.equal(load.roomId, "ROOM-1-03");
    assertNoCameraErrors(load, "initial load");
    console.log("walk-check: load, avatar and initial camera assertions passed");

    const suite = await page.evaluate(async () => {
      const harness = window.__walkCheckHarness;
      const controller = harness.controller;

      const movementCases = [
        {
          id: "wcForward",
          roomId: "ROOM-1-06",
          command: "forward",
          frames: harness.framesFrom60Hz(80),
          expectedRoomId: "ROOM-1-02",
          openDoorId: "DOOR-102-106",
        },
        {
          id: "wcBackward",
          roomId: "ROOM-1-06",
          command: "backward",
          frames: harness.framesFrom60Hz(40),
          expectedRoomId: "ROOM-1-06",
        },
        {
          id: "bathroomBuiltInLeft",
          roomId: "ROOM-1-05",
          command: "left",
          frames: harness.framesFrom60Hz(40),
          expectedRoomId: "ROOM-1-05",
          expectedBlocked: true,
        },
        {
          id: "livingForward",
          roomId: "ROOM-1-03",
          command: "forward",
          frames: harness.framesFrom60Hz(40),
          expectedRoomId: "ROOM-1-03",
        },
        {
          id: "bedroomLeft",
          roomId: "ROOM-1-10",
          command: "left",
          frames: harness.framesFrom60Hz(40),
          expectedRoomId: "ROOM-1-10",
        },
      ];
      const movements = movementCases.map((testCase) => {
        if (testCase.openDoorId) {
          harness.begin("ROOM-1-03", `${testCase.id} pre-open`);
          controller.setDoorOpen(testCase.openDoorId, true, true);
        }
        const settled = harness.begin(testCase.roomId, testCase.id);
        const cameraErrors = [...settled.cameraErrors];
        const start = harness.pose();
        let movingFrames = 0;
        let maxStepM = 0;
        controller.setFlightCommand(testCase.command, true);
        try {
          for (let frame = 0; frame < testCase.frames; frame += 1) {
            const before = harness.pose();
            harness.render(1, `${testCase.id} move ${frame + 1}`, cameraErrors);
            const stepM = harness.distance(before, harness.pose());
            if (stepM > 0.0005) movingFrames += 1;
            maxStepM = Math.max(maxStepM, stepM);
          }
        } finally {
          controller.setFlightCommand(testCase.command, false);
        }
        const end = harness.pose();
        return {
          ...testCase,
          start,
          end,
          travelled: harness.distance(start, end),
          movingFrames,
          maxStepM,
          endRoomId: controller.getWalkRoom()?.id ?? null,
          blocked: controller.isWalkBlocked(),
          cameraErrors,
        };
      });

      const moduleCandidates = ["/lib/twin-interior.ts", "/lib/twin-interior"];
      let interiorModule = null;
      let moduleUrl = null;
      const importFailures = [];
      for (const candidate of moduleCandidates) {
        try {
          const loaded = await import(candidate);
          if (
            Array.isArray(loaded.INTERIOR_DOORS) &&
            Array.isArray(loaded.INTERIOR_ROOMS) &&
            typeof loaded.roomAt === "function"
          ) {
            interiorModule = loaded;
            moduleUrl = candidate;
            break;
          }
          importFailures.push(`${candidate}: required exports missing`);
        } catch (error) {
          importFailures.push(
            `${candidate}: ${error instanceof Error ? error.message : String(error)}`,
          );
        }
      }

      const doors = {
        moduleUrl,
        importError: interiorModule ? null : importFailures.join(" | "),
        doorCount: interiorModule?.INTERIOR_DOORS.length ?? 0,
        expectedDirections: (interiorModule?.INTERIOR_DOORS.length ?? 0) * 2,
        transformResidualM: null,
        setupErrors: [],
        cameraErrors: [],
        entries: [],
      };
      let toScene = null;

      if (interiorModule) {
        const rooms = [...interiorModule.INTERIOR_ROOMS];
        const roomAt = interiorModule.roomAt;
        const reference = rooms.find((room) => room.id === "ROOM-1-03") ?? rooms[0];
        const referenceStart = harness.begin(reference.id, "door transform reference");
        doors.cameraErrors.push(...referenceStart.cameraErrors);
        const referencePose = harness.pose();
        const offset = {
          x: referencePose.x - reference.standingPointMm.x / 1000,
          z: referencePose.z + reference.standingPointMm.y / 1000,
        };
        toScene = (point) => ({
          x: point.x / 1000 + offset.x,
          z: -point.y / 1000 + offset.z,
        });
        const verification = rooms.find((room) => room.id !== reference.id) ?? reference;
        const verificationStart = harness.begin(
          verification.id,
          "door transform verification",
        );
        doors.cameraErrors.push(...verificationStart.cameraErrors);
        doors.transformResidualM = harness.distance(
          toScene(verification.standingPointMm),
          harness.pose(),
        );

        const preferredDistancesMm = [
          450, 400, 500, 350, 550, 300, 600, 250, 700, 200, 800, 900, 1000,
          1200,
        ];
        const centerAndNormal = (door) =>
          door.axis === "X"
            ? {
                center: {
                  x: door.startMm + door.widthMm / 2,
                  y: (door.wallSpanMm[0] + door.wallSpanMm[1]) / 2,
                },
                normal: { x: 0, y: 1 },
              }
            : {
                center: {
                  x: (door.wallSpanMm[0] + door.wallSpanMm[1]) / 2,
                  y: door.startMm + door.widthMm / 2,
                },
                normal: { x: 1, y: 0 },
              };
        const pointInRoom = (door, roomId, sign) => {
          const { center, normal } = centerAndNormal(door);
          for (const distanceMm of preferredDistancesMm) {
            const point = {
              x: center.x + normal.x * sign * distanceMm,
              y: center.y + normal.y * sign * distanceMm,
            };
            if (roomAt(point)?.id === roomId) return { point, distanceMm, sign };
          }
          return null;
        };

        const traverse = (door, direction, startSide, targetSide) => {
          const startScene = toScene(startSide.point);
          const targetScene = toScene(targetSide.point);
          const dx = targetScene.x - startScene.x;
          const dz = targetScene.z - startScene.z;
          const distanceM = Math.hypot(dx, dz);
          const unit = { x: dx / distanceM, z: dz / distanceM };
          const yaw = Math.atan2(unit.x, unit.z);
          const cameraErrors = [];

          const preOpen = harness.begin("ROOM-1-03", `${door.id} pre-open`);
          cameraErrors.push(...preOpen.cameraErrors);
          controller.setDoorOpen(door.id, true, true);
          const settled = harness.begin(direction.startRoomId, `${door.id} ${direction.id}`);
          cameraErrors.push(...settled.cameraErrors);
          controller.avatar.place(startScene.x, startScene.z, yaw);
          controller.setWalkView("third");
          if (typeof controller.applyWalkView === "function") {
            controller.applyWalkView();
          }
          harness.render(
            harness.framesFrom60Hz(3),
            `${door.id} ${direction.id} placed`,
            cameraErrors,
          );

          const observedStartRoomId = controller.getWalkRoom()?.id ?? null;
          const requiredProjectedM = Math.max(0.1, distanceM - 0.16);
          let targetFrames = 0;
          let targetSeen = false;
          let arrived = false;
          let maxProjectedM = 0;
          let maxLateralM = 0;
          let frames = 0;
          controller.setFlightCommand("forward", true);
          try {
            for (
              frames = 1;
              frames <= harness.framesFrom60Hz(110);
              frames += 1
            ) {
              harness.render(
                1,
                `${door.id} ${direction.id} traversal`,
                cameraErrors,
              );
              const current = harness.pose();
              const travelledX = current.x - startScene.x;
              const travelledZ = current.z - startScene.z;
              const projectedM = travelledX * unit.x + travelledZ * unit.z;
              const lateralM = Math.abs(-travelledX * unit.z + travelledZ * unit.x);
              maxProjectedM = Math.max(maxProjectedM, projectedM);
              maxLateralM = Math.max(maxLateralM, lateralM);
              const currentRoomId = controller.getWalkRoom()?.id ?? null;
              if (currentRoomId === direction.targetRoomId) targetSeen = true;
              if (
                currentRoomId === direction.targetRoomId &&
                projectedM >= requiredProjectedM
              ) {
                targetFrames += 1;
              } else {
                targetFrames = 0;
              }
              if (targetFrames >= harness.framesFrom60Hz(3)) {
                arrived = true;
                break;
              }
            }
          } finally {
            controller.setFlightCommand("forward", false);
          }

          const end = harness.pose();
          return {
            doorId: door.id,
            doorWidthMm: door.widthMm,
            direction: direction.id,
            startRoomId: direction.startRoomId,
            targetRoomId: direction.targetRoomId,
            observedStartRoomId,
            endRoomId: controller.getWalkRoom()?.id ?? null,
            startDistanceMm: startSide.distanceMm,
            targetDistanceMm: targetSide.distanceMm,
            plannedDistanceM: distanceM,
            requiredProjectedM,
            maxProjectedM,
            maxLateralM,
            travelledM: harness.distance(startScene, end),
            frames,
            targetSeen,
            arrived,
            blocked: controller.isWalkBlocked(),
            cameraErrors,
          };
        };

        for (const door of interiorModule.INTERIOR_DOORS) {
          const candidates = [
            {
              from: pointInRoom(door, door.fromRoomId, -1),
              to: pointInRoom(door, door.toRoomId, 1),
            },
            {
              from: pointInRoom(door, door.fromRoomId, 1),
              to: pointInRoom(door, door.toRoomId, -1),
            },
          ].filter((candidate) => candidate.from && candidate.to);
          if (candidates.length === 0) {
            doors.setupErrors.push(
              `${door.id}: cannot resolve opposite room-side points for ${door.fromRoomId}/${door.toRoomId}`,
            );
            continue;
          }
          const sides = candidates[0];
          doors.entries.push(
            traverse(
              door,
              {
                id: `${door.fromRoomId}->${door.toRoomId}`,
                startRoomId: door.fromRoomId,
                targetRoomId: door.toRoomId,
              },
              sides.from,
              sides.to,
            ),
          );
          doors.entries.push(
            traverse(
              door,
              {
                id: `${door.toRoomId}->${door.fromRoomId}`,
                startRoomId: door.toRoomId,
                targetRoomId: door.fromRoomId,
              },
              sides.to,
              sides.from,
            ),
          );
          console.info(
            `[walk-check] ${door.id}: both traversal directions sampled`,
          );
        }
      }

      const adaptive = {
        importError: null,
        indoor: null,
        outdoor: null,
        driveway: null,
        cameraErrors: [],
      };
      const indoorStart = harness.begin("ROOM-1-03", "adaptive indoor profile");
      adaptive.cameraErrors.push(...indoorStart.cameraErrors);
      adaptive.indoor = controller.getWalkDebugState().camera;

      let siteModule = null;
      const siteImportFailures = [];
      for (const candidate of ["/lib/twin-site.ts", "/lib/twin-site"]) {
        try {
          const loaded = await import(candidate);
          if (loaded.SITE_SURFACES?.driveway?.polygonMm) {
            siteModule = loaded;
            break;
          }
          siteImportFailures.push(`${candidate}: SITE_SURFACES.driveway missing`);
        } catch (error) {
          siteImportFailures.push(
            `${candidate}: ${error instanceof Error ? error.message : String(error)}`,
          );
        }
      }
      if (!siteModule || !toScene) {
        adaptive.importError = [
          ...siteImportFailures,
          ...(toScene ? [] : ["plan-to-scene transform unavailable"]),
        ].join(" | ");
      } else {
        const driveway = siteModule.SITE_SURFACES.driveway;
        const openRing =
          driveway.polygonMm.length > 1 &&
          driveway.polygonMm[0].x === driveway.polygonMm.at(-1).x &&
          driveway.polygonMm[0].y === driveway.polygonMm.at(-1).y
            ? driveway.polygonMm.slice(0, -1)
            : driveway.polygonMm;
        const minX = Math.min(...openRing.map((point) => point.x));
        const maxX = Math.max(...openRing.map((point) => point.x));
        const minY = Math.min(...openRing.map((point) => point.y));
        const maxY = Math.max(...openRing.map((point) => point.y));
        // This real point is well inside both triangles of the live graded
        // driveway mesh, not on an edge or on the flat terrain below it.
        const planPoint = {
          x: (minX + maxX) / 2,
          y: Math.max(minY + 1, Math.min(maxY - 1, -2500)),
        };
        const scenePoint = toScene(planPoint);
        // createGradedPolygon linearly interpolates its endpoint elevations.
        const expectedSurfaceY =
          -0.11 + ((planPoint.y - minY) / Math.max(1, maxY - minY)) * 0.095;
        controller.avatar.place(scenePoint.x, scenePoint.z, 0);
        controller.setWalkView("third");
        if (typeof controller.applyWalkView === "function") {
          controller.applyWalkView();
        }
        harness.render(
          harness.framesFrom60Hz(8),
          "graded driveway sample",
          adaptive.cameraErrors,
        );
        const drivewayState = controller.getWalkDebugState();
        adaptive.outdoor = drivewayState.camera;
        adaptive.driveway = {
          id: driveway.id,
          planPoint,
          scenePoint,
          expectedSurfaceY,
          pose: drivewayState.pose,
          surfaceId: drivewayState.camera.surfaceId,
          surfaceKind: drivewayState.camera.surfaceKind,
          surfaceY: drivewayState.camera.surfaceY,
        };
      }

      const recoveryStart = harness.begin("ROOM-1-06", "recovery");
      const recoveryCameraErrors = [...recoveryStart.cameraErrors];
      // ROOM-1-06 normally faces its open door. Face the chase camera east so
      // W deliberately drives into the solid wall and establishes a genuine
      // blocked/recovery checkpoint scenario.
      controller.avatar.camera.alpha = Math.PI;
      controller.avatar.camera.inertialAlphaOffset = 0;
      controller.avatar.noteCameraInput();
      harness.render(
        harness.framesFrom60Hz(1),
        "recovery wall heading",
        recoveryCameraErrors,
      );
      const beforeInput = harness.pose();
      const autoRecoveryCountBefore =
        controller.getWalkDebugState().recovery.autoRecoveryCount;
      controller.setFlightCommand("forward", true);
      let blockedPose;
      let recovered;
      let afterRecovery;
      let blockedReached = false;
      let firstBlockedFrame = null;
      const singleWallHoldFrames = harness.framesFrom60Hz(100);
      let singleWallState;
      try {
        for (let frame = 1; frame <= singleWallHoldFrames; frame += 1) {
          harness.render(1, "recovery blocked precondition", recoveryCameraErrors);
          if (controller.isWalkBlocked() && !blockedReached) {
            blockedReached = true;
            firstBlockedFrame = frame;
          }
        }
        blockedPose = harness.pose();
        singleWallState = controller.getWalkDebugState();
        controller.recoverWalkthrough();
        recovered = harness.pose();
        harness.render(
          harness.framesFrom60Hz(30),
          "recovery released",
          recoveryCameraErrors,
        );
        afterRecovery = harness.pose();
      } finally {
        controller.setFlightCommand("forward", false);
      }
      const recovery = {
        blockedReached,
        blockedFrames: firstBlockedFrame,
        singleWallHoldFrames,
        autoRecoveryCountBefore,
        autoRecoveryCountAfter:
          singleWallState.recovery.autoRecoveryCount,
        attemptedDirectionMask:
          singleWallState.recovery.attemptedDirectionMask,
        attemptedDirectionCount: singleWallState.recovery.attemptedDirectionMask
          .toString(2)
          .replaceAll("0", "").length,
        preconditionTravelled: harness.distance(beforeInput, blockedPose),
        rewindDistance: harness.distance(blockedPose, recovered),
        blockedPose,
        recovered,
        afterRecovery,
        postRecoveryDrift: harness.distance(recovered, afterRecovery),
        roomId: controller.getWalkRoom()?.id ?? null,
        blocked: controller.isWalkBlocked(),
        cameraErrors: recoveryCameraErrors,
      };

      const autoRecovery = {
        setupError: null,
        cameraErrors: [],
        start: null,
        trapped: null,
        recovered: null,
        afterRelease: null,
        firstHeadingFrames: 0,
        secondHeadingFrames: 0,
        firstBlocked: false,
        countBefore: null,
        countAfter: null,
        firstDirectionMask: 0,
        finalState: null,
      };
      const wcRoom = interiorModule?.INTERIOR_ROOMS.find(
        (room) => room.id === "ROOM-1-06",
      );
      if (!wcRoom || !toScene) {
        autoRecovery.setupError = "ROOM-1-06 geometry or plan transform unavailable";
      } else {
        const rect = wcRoom.rectsMm[0];
        // Approach the solid south-west WC corner along two distinct headings.
        // The point remains outside the fixture envelopes and below the door.
        const startPlan = { x: rect.x0 + 420, y: rect.y0 + 420 };
        const startScene = toScene(startPlan);
        const firstDirection = { x: -0.95, z: 0.31 };
        const alphaForDirection = (direction) =>
          Math.atan2(-direction.z, -direction.x);
        const setup = harness.begin("ROOM-1-06", "multi-direction trap");
        autoRecovery.cameraErrors.push(...setup.cameraErrors);
        controller.avatar.place(startScene.x, startScene.z, 0);
        controller.setWalkView("third");
        if (typeof controller.applyWalkView === "function") {
          controller.applyWalkView();
        }
        controller.avatar.camera.alpha = alphaForDirection(firstDirection);
        controller.avatar.camera.inertialAlphaOffset = 0;
        controller.avatar.noteCameraInput();
        harness.render(
          harness.framesFrom60Hz(2),
          "multi-direction trap placed",
          autoRecovery.cameraErrors,
        );
        autoRecovery.start = harness.pose();
        autoRecovery.countBefore =
          controller.getWalkDebugState().recovery.autoRecoveryCount;

        controller.setFlightCommand("forward", true);
        try {
          for (
            autoRecovery.firstHeadingFrames = 1;
            autoRecovery.firstHeadingFrames <= harness.framesFrom60Hz(120);
            autoRecovery.firstHeadingFrames += 1
          ) {
            harness.render(
              1,
              "multi-direction first blocked heading",
              autoRecovery.cameraErrors,
            );
            if (controller.isWalkBlocked()) break;
          }
          const firstState = controller.getWalkDebugState();
          autoRecovery.firstBlocked = firstState.blocked;
          autoRecovery.firstDirectionMask =
            firstState.recovery.attemptedDirectionMask;
          autoRecovery.trapped = harness.pose();

          // Escape diversity is intentionally based on physical commands, not
          // camera-relative world headings. Release W for one neutral frame,
          // then make physical Left push west into the second corner wall.
          controller.setFlightCommand("forward", false);
          harness.render(
            harness.framesFrom60Hz(1),
            "multi-direction neutral release",
            autoRecovery.cameraErrors,
          );
          controller.avatar.camera.alpha = Math.PI / 2;
          controller.avatar.camera.inertialAlphaOffset = 0;
          controller.avatar.noteCameraInput();
          controller.setFlightCommand("left", true);
          for (
            autoRecovery.secondHeadingFrames = 1;
            autoRecovery.secondHeadingFrames <= harness.framesFrom60Hz(70);
            autoRecovery.secondHeadingFrames += 1
          ) {
            harness.render(
              1,
              "multi-direction second blocked heading",
              autoRecovery.cameraErrors,
            );
            const state = controller.getWalkDebugState();
            if (
              state.recovery.autoRecoveryCount > autoRecovery.countBefore
            ) {
              break;
            }
          }
          autoRecovery.recovered = harness.pose();
          autoRecovery.finalState = controller.getWalkDebugState();
          autoRecovery.countAfter =
            autoRecovery.finalState.recovery.autoRecoveryCount;
        } finally {
          controller.setFlightCommand("forward", false);
          controller.setFlightCommand("left", false);
        }
        harness.render(
          harness.framesFrom60Hz(30),
          "multi-direction recovery released",
          autoRecovery.cameraErrors,
        );
        autoRecovery.afterRelease = harness.pose();
      }

      console.info(
        "[walk-check] movement, doors, surfaces and recovery scenarios sampled",
      );

      return { movements, doors, adaptive, recovery, autoRecovery };
    });

    assert.equal(suite.movements.length, 5);
    for (const movement of suite.movements) {
      assert.ok(
        movement.travelled > 0.04,
        `${movement.id}: travelled only ${movement.travelled.toFixed(4)} m`,
      );
      assert.ok(
        movement.travelled < 3,
        `${movement.id}: implausible travel ${movement.travelled.toFixed(4)} m`,
      );
      assert.ok(
        movement.movingFrames >= framesFrom60Hz(3),
        `${movement.id}: no sustained movement`,
      );
      assert.ok(
        movement.maxStepM > 0 && movement.maxStepM < 0.12,
        `${movement.id}: invalid maximum frame step ${movement.maxStepM}`,
      );
      assert.equal(
        movement.endRoomId,
        movement.expectedRoomId,
        `${movement.id}: ended in ${movement.endRoomId}, expected ${movement.expectedRoomId}; travelled ${movement.travelled.toFixed(3)} m, blocked=${movement.blocked}`,
      );
      if (typeof movement.expectedBlocked === "boolean") {
        assert.equal(
          movement.blocked,
          movement.expectedBlocked,
          `${movement.id}: blocked=${movement.blocked}, expected ${movement.expectedBlocked}`,
        );
      }
      assertNoCameraErrors(movement, movement.id);
    }

    assert.equal(
      suite.doors.importError,
      null,
      `cannot import the live interior door contract: ${suite.doors.importError}`,
    );
    assert.ok(suite.doors.doorCount > 0, "live interior contract has no doors");
    assert.ok(
      suite.doors.transformResidualM < 0.001,
      `plan-to-scene transform residual is ${suite.doors.transformResidualM} m`,
    );
    assert.deepEqual(
      suite.doors.setupErrors,
      [],
      `door matrix setup failed:\n${suite.doors.setupErrors.join("\n")}`,
    );
    assert.equal(
      suite.doors.entries.length,
      suite.doors.expectedDirections,
      "every declared interior door must be exercised in both directions",
    );
    assertNoCameraErrors(suite.doors, "door matrix setup");
    for (const entry of suite.doors.entries) {
      const label = `${entry.doorId} ${entry.direction}`;
      assert.equal(
        entry.observedStartRoomId,
        entry.startRoomId,
        `${label}: start placement resolved to ${entry.observedStartRoomId}`,
      );
      assert.equal(entry.targetSeen, true, `${label}: target room was never observed`);
      assert.equal(
        entry.arrived,
        true,
        `${label}: failed to clear doorway after ${entry.frames} frames; projected ${entry.maxProjectedM.toFixed(3)}/${entry.requiredProjectedM.toFixed(3)} m, final room ${entry.endRoomId}`,
      );
      assert.equal(
        entry.endRoomId,
        entry.targetRoomId,
        `${label}: ended in ${entry.endRoomId}`,
      );
      assert.ok(
        entry.maxProjectedM >= entry.requiredProjectedM,
        `${label}: insufficient forward clearance`,
      );
      assert.ok(
        entry.maxLateralM < entry.doorWidthMm / 1000,
        `${label}: lateral drift ${entry.maxLateralM.toFixed(3)} m exceeds opening width`,
      );
      assertNoCameraErrors(entry, label);
    }

    assert.equal(
      suite.adaptive.importError,
      null,
      `adaptive surface setup failed: ${suite.adaptive.importError}`,
    );
    assert.equal(
      suite.adaptive.indoor.surfaceKind,
      "interior",
      `indoor profile resolved ${suite.adaptive.indoor.surfaceKind}`,
    );
    assert.ok(
      suite.adaptive.indoor.surfaceId?.startsWith("interior-"),
      `indoor profile resolved ${suite.adaptive.indoor.surfaceId}`,
    );
    assert.ok(
      suite.adaptive.indoor.indoorBlend > 0.99,
      `indoor blend is only ${suite.adaptive.indoor.indoorBlend}`,
    );
    assert.ok(
      Math.abs(suite.adaptive.indoor.desiredRadiusM - 1.9) < 0.01,
      `indoor desired radius is ${suite.adaptive.indoor.desiredRadiusM}, expected 1.9 m`,
    );
    assert.ok(
      suite.adaptive.indoor.requestedRadiusM -
        suite.adaptive.indoor.desiredRadiusM >
        0.5,
      "indoor profile did not reduce the requested outdoor camera radius",
    );
    assert.equal(
      suite.adaptive.driveway.surfaceId,
      "site-surface-SITE-DRIVEWAY",
      `driveway sample resolved ${suite.adaptive.driveway.surfaceId}`,
    );
    assert.equal(suite.adaptive.driveway.surfaceKind, "exterior");
    assert.ok(
      Math.abs(
        suite.adaptive.driveway.surfaceY -
          suite.adaptive.driveway.expectedSurfaceY,
      ) < 0.004,
      `driveway surface Y ${suite.adaptive.driveway.surfaceY} differs from graded mesh ${suite.adaptive.driveway.expectedSurfaceY}`,
    );
    assert.ok(
      Math.abs(
        suite.adaptive.driveway.pose.y -
          suite.adaptive.driveway.expectedSurfaceY,
      ) < 0.004,
      `avatar Y ${suite.adaptive.driveway.pose.y} does not follow the driveway grade`,
    );
    assert.ok(
      suite.adaptive.outdoor.indoorBlend < 0.01,
      `outdoor blend remained ${suite.adaptive.outdoor.indoorBlend}`,
    );
    assert.ok(
      Math.abs(
        suite.adaptive.outdoor.desiredRadiusM -
          suite.adaptive.outdoor.requestedRadiusM,
      ) < 0.01,
      `outdoor desired radius ${suite.adaptive.outdoor.desiredRadiusM} did not restore requested ${suite.adaptive.outdoor.requestedRadiusM}`,
    );
    assert.ok(
      Math.abs(
        suite.adaptive.outdoor.requestedRadiusM -
          suite.adaptive.indoor.requestedRadiusM,
      ) < 0.001,
      "environment adaptation overwrote the user's requested radius",
    );
    assertNoCameraErrors(suite.adaptive, "adaptive surface/camera profile");

    assert.equal(
      suite.recovery.blockedReached,
      true,
      `recovery smoke did not latch blocked state in ${suite.recovery.blockedFrames} frames`,
    );
    assert.equal(
      suite.recovery.autoRecoveryCountAfter,
      suite.recovery.autoRecoveryCountBefore,
      "holding one wall heading triggered an automatic rewind",
    );
    assert.equal(
      suite.recovery.attemptedDirectionCount,
      1,
      `single-wall hold recorded ${suite.recovery.attemptedDirectionCount} direction sectors`,
    );
    assert.ok(suite.recovery.preconditionTravelled > 0.03, "recovery did not move toward wall");
    assert.ok(
      suite.recovery.rewindDistance > 0.08 && suite.recovery.rewindDistance < 0.7,
      `recovery rewind ${suite.recovery.rewindDistance.toFixed(4)} m is not a useful local checkpoint`,
    );
    assert.ok(
      suite.recovery.postRecoveryDrift < 0.003,
      `recovery left input/velocity active (${suite.recovery.postRecoveryDrift.toFixed(4)} m drift)`,
    );
    assert.equal(suite.recovery.blocked, false, "recovery left the blocked state latched");
    assertNoCameraErrors(suite.recovery, "recovery");

    assert.equal(
      suite.autoRecovery.setupError,
      null,
      `auto-recovery setup failed: ${suite.autoRecovery.setupError}`,
    );
    assert.equal(
      suite.autoRecovery.firstBlocked,
      true,
      `first trap heading did not latch after ${suite.autoRecovery.firstHeadingFrames} frames`,
    );
    assert.ok(
      suite.autoRecovery.firstDirectionMask !== 0 &&
        (suite.autoRecovery.firstDirectionMask &
          (suite.autoRecovery.firstDirectionMask - 1)) ===
          0,
      `first trap heading recorded a non-single mask ${suite.autoRecovery.firstDirectionMask}`,
    );
    assert.equal(
      suite.autoRecovery.countAfter,
      suite.autoRecovery.countBefore + 1,
      `multi-direction trap changed recovery count ${suite.autoRecovery.countBefore} -> ${suite.autoRecovery.countAfter}; ${JSON.stringify(suite.autoRecovery)}`,
    );
    const autoRewindDistance = Math.hypot(
      suite.autoRecovery.trapped.x - suite.autoRecovery.recovered.x,
      suite.autoRecovery.trapped.z - suite.autoRecovery.recovered.z,
    );
    assert.ok(
      autoRewindDistance > 0.08 && autoRewindDistance < 0.7,
      `automatic rewind ${autoRewindDistance.toFixed(4)} m is outside the local checkpoint contract`,
    );
    assert.equal(
      suite.autoRecovery.finalState.blocked,
      false,
      "automatic recovery left the blocked state latched",
    );
    assert.equal(
      suite.autoRecovery.finalState.recovery.awaitingRelease,
      true,
      "automatic recovery did not suppress the still-held movement key",
    );
    assert.ok(
      suite.autoRecovery.finalState.recovery.cooldownS > 0,
      "automatic recovery did not arm its cooldown",
    );
    assert.ok(
      Math.hypot(
        suite.autoRecovery.recovered.x - suite.autoRecovery.afterRelease.x,
        suite.autoRecovery.recovered.z - suite.autoRecovery.afterRelease.z,
      ) < 0.003,
      "automatic recovery left residual movement after input release",
    );
    assertNoCameraErrors(suite.autoRecovery, "multi-direction auto-recovery");

    // The scenario matrix above intentionally owns the main thread for many
    // synchronous manual renders. Let queued React work settle before testing
    // a trusted browser key, then focus the live controller canvas again.
    await page.evaluate(
      () => new Promise((resolve) => window.setTimeout(resolve, 0)),
    );
    const canvas = page.locator("canvas").first();
    const keyboardStart = await page.evaluate(() =>
      window.__walkCheckHarness.begin("ROOM-1-03", "keyboard input"),
    );
    assertNoCameraErrors(keyboardStart, "keyboard input setup");
    await page.evaluate(
      () => new Promise((resolve) => window.setTimeout(resolve, 0)),
    );
    await canvas.focus();
    const keyboardTarget = await page.evaluate(() => {
      const harness = window.__walkCheckHarness;
      const canvasElement = document.querySelector("canvas");
      window.__walkCheckLastKeyW = null;
      canvasElement?.addEventListener(
        "keydown",
        (event) => {
          if (event.code !== "KeyW") return;
          window.__walkCheckLastKeyW = {
            code: event.code,
            key: event.key,
            trusted: event.isTrusted,
            defaultPrevented: event.defaultPrevented,
            focused: document.activeElement === canvasElement,
          };
        },
        { once: true },
      );
      return {
        focused: document.activeElement === canvasElement,
        connected: Boolean(canvasElement?.isConnected),
        harnessIsCurrentController: harness.controller === window.twinDebug,
        controllerCanvasIsDocumentCanvas:
          harness.controller.canvas === canvasElement,
      };
    });
    assert.deepEqual(
      keyboardTarget,
      {
        focused: true,
        connected: true,
        harnessIsCurrentController: true,
        controllerCanvasIsDocumentCanvas: true,
      },
      `KeyW target became stale after the synchronous suite: ${JSON.stringify(keyboardTarget)}`,
    );
    let keyboardMotion;
    let keyWEvent;
    try {
      await page.keyboard.down("KeyW");
      keyWEvent = await page.evaluate(() => ({
        event: window.__walkCheckLastKeyW,
        accepted: Boolean(
          window.__walkCheckHarness.controller.keyboardFlightCommands?.has(
            "forward",
          ),
        ),
        focused:
          document.activeElement === document.querySelector("canvas"),
      }));
      keyboardMotion = await page.evaluate(() =>
        window.__walkCheckHarness.measureFrames(
          window.__walkCheckHarness.framesFrom60Hz(40),
          "keyboard W",
        ),
      );
    } finally {
      await page.keyboard.up("KeyW");
    }
    assert.deepEqual(
      keyWEvent,
      {
        event: {
          code: "KeyW",
          key: "w",
          trusted: true,
          defaultPrevented: true,
          focused: true,
        },
        accepted: true,
        focused: true,
      },
      `trusted KeyW did not reach the live canvas/controller: ${JSON.stringify(keyWEvent)}`,
    );
    assert.ok(
      keyboardMotion.travelled > 0.04,
      `real KeyW input travelled only ${keyboardMotion.travelled.toFixed(4)} m; target=${JSON.stringify(keyboardTarget)} event=${JSON.stringify(keyWEvent)}`,
    );
    assertNoCameraErrors(keyboardMotion, "real KeyW input");

    const blurStart = await page.evaluate(() =>
      window.__walkCheckHarness.begin("ROOM-1-03", "blur input"),
    );
    assertNoCameraErrors(blurStart, "blur input setup");
    await canvas.focus();
    let blurMotion;
    let blurReleased;
    try {
      await page.keyboard.down("KeyW");
      blurMotion = await page.evaluate(() =>
        window.__walkCheckHarness.measureFrames(
          window.__walkCheckHarness.framesFrom60Hz(18),
          "blur precondition",
        ),
      );
      const blurred = await page.evaluate(() => {
        const canvasElement = document.querySelector("canvas");
        canvasElement?.blur();
        return document.activeElement !== canvasElement;
      });
      assert.equal(blurred, true, "canvas did not lose focus");
      blurReleased = await page.evaluate(() =>
        window.__walkCheckHarness.measureFrames(
          window.__walkCheckHarness.framesFrom60Hz(70),
          "blur release",
          window.__walkCheckHarness.framesFrom60Hz(15),
        ),
      );
    } finally {
      await page.keyboard.up("KeyW");
    }
    assert.ok(
      blurMotion.travelled > 0.02,
      `blur smoke did not establish keyboard movement (${blurMotion.travelled.toFixed(4)} m)`,
    );
    assert.ok(
      blurReleased.tailTravelled < 0.02,
      `blur did not clear held input; final ${framesFrom60Hz(15)} frames travelled ${blurReleased.tailTravelled.toFixed(4)} m`,
    );
    assertNoCameraErrors(blurMotion, "blur precondition");
    assertNoCameraErrors(blurReleased, "blur release");

    const backToOrbit = await page.evaluate(() => {
      const controller = window.__walkCheckHarness.controller;
      controller.setNavigationMode("orbit");
      return {
        mode: controller.getNavigationMode(),
        activeCamera: controller.scene.activeCamera?.name ?? null,
      };
    });
    assert.equal(backToOrbit.mode, "orbit", "walkthrough did not return to orbit mode");
    assert.notEqual(
      backToOrbit.activeCamera,
      "avatar-camera",
      "avatar camera remained active after leaving walkthrough",
    );
    assert.deepEqual(pageErrors, [], `uncaught browser errors:\n${pageErrors.join("\n")}`);

    const report = {
      fps: WALK_CHECK_FPS,
      load,
      movements: suite.movements.map((movement) => ({
        id: movement.id,
        travelledM: Number(movement.travelled.toFixed(3)),
        movingFrames: movement.movingFrames,
        roomId: movement.endRoomId,
      })),
      doors: {
        source: suite.doors.moduleUrl,
        declarations: suite.doors.doorCount,
        directionsPassed: suite.doors.entries.length,
        entries: suite.doors.entries.map((entry) => ({
          doorId: entry.doorId,
          direction: entry.direction,
          frames: entry.frames,
          projectedM: Number(entry.maxProjectedM.toFixed(3)),
        })),
      },
      adaptive: {
        indoorDesiredRadiusM: Number(
          suite.adaptive.indoor.desiredRadiusM.toFixed(3),
        ),
        outdoorDesiredRadiusM: Number(
          suite.adaptive.outdoor.desiredRadiusM.toFixed(3),
        ),
        drivewaySurfaceId: suite.adaptive.driveway.surfaceId,
        drivewaySurfaceYM: Number(
          suite.adaptive.driveway.surfaceY.toFixed(4),
        ),
      },
      recovery: {
        blockedReached: suite.recovery.blockedReached,
        blockedFrames: suite.recovery.blockedFrames,
        singleWallHoldFrames: suite.recovery.singleWallHoldFrames,
        singleWallDirectionCount: suite.recovery.attemptedDirectionCount,
        preconditionTravelledM: Number(
          suite.recovery.preconditionTravelled.toFixed(3),
        ),
        rewindDistanceM: Number(suite.recovery.rewindDistance.toFixed(3)),
        postRecoveryDriftM: Number(suite.recovery.postRecoveryDrift.toFixed(4)),
        autoRecoveryCount: suite.autoRecovery.countAfter,
        autoRewindDistanceM: Number(autoRewindDistance.toFixed(3)),
      },
      input: {
        keyWTravelledM: Number(keyboardMotion.travelled.toFixed(3)),
        keyWTrusted: keyWEvent.event.trusted,
        keyWAccepted: keyWEvent.accepted,
        blurTailTravelledM: Number(blurReleased.tailTravelled.toFixed(4)),
      },
      backToOrbit,
    };
    console.log(JSON.stringify(report, null, 2));
    console.log(
      `walk-check PASS @ ${WALK_CHECK_FPS} FPS: ${suite.doors.doorCount} doors / ${suite.doors.entries.length} directions`,
    );
  } finally {
    await browser.close();
  }
}

await run().catch((error) => {
  if (error?.code === "ERR_ASSERTION") throw error;
  assert.fail(`walk-check execution failed: ${errorMessage(error)}`);
});
