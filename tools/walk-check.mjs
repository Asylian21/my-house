// Assertion-based Chromium/WebGL regression check for the walkthrough:
//   npx -p playwright node tools/walk-check.mjs
//
// A development server must already be running at http://localhost:3000.
import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { createRequire } from "node:module";
import { delimiter, dirname, join } from "node:path";

const APP_URL = "http://localhost:3000/";
const FIXED_DELTA_MS = 1000 / 60;
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

    const load = await page.evaluate(async (fixedDeltaMs) => {
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
          desired,
          effective,
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
        render(3, `${label} settle`, cameraErrors);
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
        texturesNotReady: controller.scene.textures
          .filter((texture) => !texture.isReady())
          .map((texture) => texture.name || texture.url || "unnamed"),
        collidables: controller.scene.meshes.filter((mesh) => mesh.checkCollisions)
          .length,
        mode: controller.getNavigationMode(),
        view: controller.getWalkView(),
        activeCamera: controller.scene.activeCamera?.name ?? null,
        roomId: initial.roomId,
        cameraErrors: initial.cameraErrors,
      };
    }, FIXED_DELTA_MS);

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
          frames: 55,
          expectedRoomId: "ROOM-1-02",
        },
        {
          id: "wcBackward",
          roomId: "ROOM-1-06",
          command: "backward",
          frames: 40,
          expectedRoomId: "ROOM-1-06",
        },
        {
          id: "livingForward",
          roomId: "ROOM-1-03",
          command: "forward",
          frames: 40,
          expectedRoomId: "ROOM-1-03",
        },
        {
          id: "bedroomLeft",
          roomId: "ROOM-1-10",
          command: "left",
          frames: 40,
          expectedRoomId: "ROOM-1-10",
        },
      ];
      const movements = movementCases.map((testCase) => {
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
        const toScene = (point) => ({
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

          const settled = harness.begin(direction.startRoomId, `${door.id} ${direction.id}`);
          cameraErrors.push(...settled.cameraErrors);
          controller.avatar.place(startScene.x, startScene.z, yaw);
          controller.setWalkView("third");
          if (typeof controller.applyWalkView === "function") {
            controller.applyWalkView();
          }
          harness.render(3, `${door.id} ${direction.id} placed`, cameraErrors);

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
            for (frames = 1; frames <= 110; frames += 1) {
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
              if (targetFrames >= 3) {
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

      const recoveryStart = harness.begin("ROOM-1-06", "recovery");
      const recoveryCameraErrors = [...recoveryStart.cameraErrors];
      // ROOM-1-06 normally faces its open door. Face the chase camera east so
      // W deliberately drives into the solid wall and establishes a genuine
      // blocked/recovery checkpoint scenario.
      controller.avatar.camera.alpha = Math.PI;
      controller.avatar.camera.inertialAlphaOffset = 0;
      controller.avatar.noteCameraInput();
      harness.render(1, "recovery wall heading", recoveryCameraErrors);
      const beforeInput = harness.pose();
      controller.setFlightCommand("forward", true);
      let blockedPose;
      let recovered;
      let afterRecovery;
      let blockedReached = false;
      let blockedFrames = 0;
      try {
        for (blockedFrames = 1; blockedFrames <= 100; blockedFrames += 1) {
          harness.render(1, "recovery blocked precondition", recoveryCameraErrors);
          if (controller.isWalkBlocked()) {
            blockedReached = true;
            break;
          }
        }
        blockedPose = harness.pose();
        controller.recoverWalkthrough();
        recovered = harness.pose();
        harness.render(30, "recovery released", recoveryCameraErrors);
        afterRecovery = harness.pose();
      } finally {
        controller.setFlightCommand("forward", false);
      }
      const recovery = {
        blockedReached,
        blockedFrames,
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

      console.info("[walk-check] movement, door and recovery scenarios sampled");

      return { movements, doors, recovery };
    });

    assert.equal(suite.movements.length, 4);
    for (const movement of suite.movements) {
      assert.ok(
        movement.travelled > 0.04,
        `${movement.id}: travelled only ${movement.travelled.toFixed(4)} m`,
      );
      assert.ok(
        movement.travelled < 3,
        `${movement.id}: implausible travel ${movement.travelled.toFixed(4)} m`,
      );
      assert.ok(movement.movingFrames >= 3, `${movement.id}: no sustained movement`);
      assert.ok(
        movement.maxStepM > 0 && movement.maxStepM < 0.12,
        `${movement.id}: invalid maximum frame step ${movement.maxStepM}`,
      );
      assert.equal(
        movement.endRoomId,
        movement.expectedRoomId,
        `${movement.id}: ended in ${movement.endRoomId}, expected ${movement.expectedRoomId}`,
      );
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
      suite.recovery.blockedReached,
      true,
      `recovery smoke did not latch blocked state in ${suite.recovery.blockedFrames} frames`,
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

    const canvas = page.locator("canvas").first();
    const keyboardStart = await page.evaluate(() =>
      window.__walkCheckHarness.begin("ROOM-1-03", "keyboard input"),
    );
    assertNoCameraErrors(keyboardStart, "keyboard input setup");
    await canvas.focus();
    let keyboardMotion;
    try {
      await page.keyboard.down("w");
      keyboardMotion = await page.evaluate(() =>
        window.__walkCheckHarness.measureFrames(40, "keyboard W"),
      );
    } finally {
      await page.keyboard.up("w");
    }
    assert.ok(
      keyboardMotion.travelled > 0.04,
      `real KeyW input travelled only ${keyboardMotion.travelled.toFixed(4)} m`,
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
      await page.keyboard.down("w");
      blurMotion = await page.evaluate(() =>
        window.__walkCheckHarness.measureFrames(18, "blur precondition"),
      );
      const blurred = await page.evaluate(() => {
        const canvasElement = document.querySelector("canvas");
        canvasElement?.blur();
        return document.activeElement !== canvasElement;
      });
      assert.equal(blurred, true, "canvas did not lose focus");
      blurReleased = await page.evaluate(() =>
        window.__walkCheckHarness.measureFrames(70, "blur release", 15),
      );
    } finally {
      await page.keyboard.up("w");
    }
    assert.ok(
      blurMotion.travelled > 0.02,
      `blur smoke did not establish keyboard movement (${blurMotion.travelled.toFixed(4)} m)`,
    );
    assert.ok(
      blurReleased.tailTravelled < 0.02,
      `blur did not clear held input; final 15 frames travelled ${blurReleased.tailTravelled.toFixed(4)} m`,
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
      recovery: {
        blockedReached: suite.recovery.blockedReached,
        blockedFrames: suite.recovery.blockedFrames,
        preconditionTravelledM: Number(
          suite.recovery.preconditionTravelled.toFixed(3),
        ),
        rewindDistanceM: Number(suite.recovery.rewindDistance.toFixed(3)),
        postRecoveryDriftM: Number(suite.recovery.postRecoveryDrift.toFixed(4)),
      },
      input: {
        keyWTravelledM: Number(keyboardMotion.travelled.toFixed(3)),
        blurTailTravelledM: Number(blurReleased.tailTravelled.toFixed(4)),
      },
      backToOrbit,
    };
    console.log(JSON.stringify(report, null, 2));
    console.log(
      `walk-check PASS: ${suite.doors.doorCount} doors / ${suite.doors.entries.length} directions`,
    );
  } finally {
    await browser.close();
  }
}

await run().catch((error) => {
  if (error?.code === "ERR_ASSERTION") throw error;
  assert.fail(`walk-check execution failed: ${errorMessage(error)}`);
});
