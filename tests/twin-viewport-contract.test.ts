import { describe, expect, it } from "vitest";

import {
  ADAPTIVE_POST_FX,
  EXTERIOR_RENDER_STABILITY,
  FLIGHT_BOUNDS,
  FLIGHT_WHEEL_DOLLY_MAX_M,
  INTERIOR_RENDER_QUALITY,
  ORBIT_ZOOM,
  PHOTOGRAPHIC_GRADE,
  WALK_CAMERA,
  WALK_COLLISION_ELLIPSOID_M,
  WALK_COLLISION_OFFSET_M,
  WALK_SURFACE,
  addWalkEscapeDirection,
  clampOrbitRadius,
  deriveRenderQualityProfile,
  easeOrbitRadius,
  flightCommandForCode,
  flightWheelDollyDistanceM,
  hasDiverseWalkEscapeDirections,
  initialAdaptivePostFxState,
  integrateAvatarVelocity,
  integrateFlightDolly,
  integrateFlightPosition,
  interiorPostFxPlan,
  isSelectionTap,
  normalizeWheelPixels,
  orbitZoomMultiplier,
  rayAabbDistance,
  resolveWalkCollisionVelocity,
  shouldAutoRecoverWalk,
  shouldEngageInteriorPostFx,
  shouldResetWalkCollisionCarry,
  shouldResolveWalkCollisionBatch,
  stepAdaptivePostFx,
  stepOrbitZoom,
  stepWalkCameraBoom,
  stepWalkCameraSurfaceHeight,
  stepWalkIndoorBlend,
  walkCameraRadiusForEnvironment,
  wheelZoomGesture,
  type FlightCommand,
} from "../lib/twin-viewport-contract";

const commands = (...values: FlightCommand[]) => new Set(values);

describe("exterior render stability contract", () => {
  it("keeps reality mode temporally stable and shadow-safe", () => {
    expect(EXTERIOR_RENDER_STABILITY).toMatchObject({
      orbitNearClipM: 0.3,
      shadowBias: 0.0007,
      shadowNormalBiasM: 0.025,
      shadowCascadeBlendPercentage: 0.18,
      filmGrainEnabled: false,
      filmGrainAnimated: false,
      screenSpaceAmbientOcclusionEnabled: false,
      pbrSpecularAntiAliasingEnabled: true,
      freezeDynamicShadowCasterBounds: false,
      roadContextSurfaceElevationM: -0.115,
      roofSeamVisibilityDistanceM: 36,
    });
    expect(EXTERIOR_RENDER_STABILITY.shadowNormalBiasM).toBeLessThanOrEqual(
      0.03,
    );
  });

  it("separates the broad terrain, lawn and replacement surfaces", () => {
    const terrainToRoadM =
      EXTERIOR_RENDER_STABILITY.roadContextSurfaceElevationM -
      EXTERIOR_RENDER_STABILITY.contextTerrainElevationM;
    const lawnToLowestReplacementM =
      -0.045 - EXTERIOR_RENDER_STABILITY.parcelGrassElevationM;

    expect(terrainToRoadM).toBeGreaterThanOrEqual(
      EXTERIOR_RENDER_STABILITY.minimumOpaqueLayerSeparationM,
    );
    expect(lawnToLowestReplacementM).toBeGreaterThanOrEqual(
      EXTERIOR_RENDER_STABILITY.minimumOpaqueLayerSeparationM,
    );
  });
});

describe("orbit zoom contract", () => {
  it("uses an exponential trackpad model and owns browser gestures", () => {
    expect(ORBIT_ZOOM).toEqual({
      lowerRadiusLimitM: 4.5,
      upperRadiusLimitM: 150,
      scrollGainPerPx: 0.0018,
      pinchGainPerPx: 0.009,
      lineModePx: 16,
      pageModePx: 800,
      maxMultiplierPerEvent: 2,
      minMultiplierPerEvent: 0.5,
      glideHalfLifeMs: 42,
      settleEpsilonM: 0.0015,
      useNaturalPinchZoom: true,
      preventBrowserGesture: true,
    });
  });

  it("normalizes pixel, line and page wheel modes into pixels", () => {
    expect(normalizeWheelPixels({ deltaY: 12, deltaMode: 0 })).toBe(12);
    expect(normalizeWheelPixels({ deltaY: 3, deltaMode: 1 })).toBe(48);
    expect(normalizeWheelPixels({ deltaY: 0.5, deltaMode: 2 })).toBe(400);
    expect(normalizeWheelPixels({ deltaY: 7, deltaMode: 9 })).toBe(0);
    expect(
      normalizeWheelPixels({ deltaY: Number.NaN, deltaMode: 0 }),
    ).toBe(0);
  });

  it("treats ctrl-modified wheels as trackpad pinch", () => {
    expect(wheelZoomGesture({ ctrlKey: true })).toBe("pinch");
    expect(wheelZoomGesture({ ctrlKey: false })).toBe("scroll");
  });

  it("zooms out on downward scroll and in on upward scroll", () => {
    const down = orbitZoomMultiplier(100, "scroll");
    const up = orbitZoomMultiplier(-100, "scroll");
    expect(down).toBeGreaterThan(1);
    expect(up).toBeLessThan(1);
    // Exponential model is symmetric around 1.
    expect(down * up).toBeCloseTo(1, 10);
  });

  it("keeps one physical notch responsive without teleporting", () => {
    // Chrome reports a physical notch as ~100 px; Firefox as ~3 lines.
    expect(orbitZoomMultiplier(100, "scroll")).toBeCloseTo(1.1972, 3);
    expect(orbitZoomMultiplier(normalizeWheelPixels({ deltaY: 3, deltaMode: 1 }), "scroll"))
      .toBeCloseTo(orbitZoomMultiplier(48, "scroll"), 10);
  });

  it("gives pinch gestures five times the scroll response", () => {
    const pinch = orbitZoomMultiplier(25, "pinch");
    const scroll = orbitZoomMultiplier(25, "scroll");
    expect(pinch).toBeGreaterThan(scroll);
    expect(Math.log(pinch)).toBeCloseTo(5 * Math.log(scroll), 6);
  });

  it("clamps a single event so momentum bursts cannot teleport the camera", () => {
    expect(orbitZoomMultiplier(10_000, "scroll")).toBe(
      ORBIT_ZOOM.maxMultiplierPerEvent,
    );
    expect(orbitZoomMultiplier(-10_000, "pinch")).toBeLessThanOrEqual(
      1 / ORBIT_ZOOM.minMultiplierPerEvent,
    );
    expect(clampOrbitRadius(0.5)).toBe(ORBIT_ZOOM.lowerRadiusLimitM);
    expect(clampOrbitRadius(500)).toBe(ORBIT_ZOOM.upperRadiusLimitM);
  });

  it("glides exponentially and stays consistent at any frame rate", () => {
    const single = easeOrbitRadius(40, 20, 100);
    const twoSteps = easeOrbitRadius(easeOrbitRadius(40, 20, 50), 20, 50);
    expect(twoSteps).toBeCloseTo(single, 8);

    const afterHalfLife = easeOrbitRadius(40, 20, ORBIT_ZOOM.glideHalfLifeMs);
    expect(afterHalfLife).toBeCloseTo(30, 6);

    // A long frame gap (tab switch) converges fully instead of overshooting.
    expect(easeOrbitRadius(40, 20, 5_000)).toBeCloseTo(20, 6);
    expect(easeOrbitRadius(40, 20, Number.NaN)).toBe(40);
    expect(easeOrbitRadius(40, 20, -5)).toBe(40);
  });

  it("finishes every glide exactly instead of dropping its idle tail", () => {
    let radiusM = 16;
    let settled = false;
    for (let frame = 0; frame < 240 && !settled; frame += 1) {
      const step = stepOrbitZoom(radiusM, 10, 1000 / 120);
      radiusM = step.radiusM;
      settled = step.settled;
    }
    expect(settled).toBe(true);
    expect(radiusM).toBe(10);
    expect(stepOrbitZoom(10, 500, 5_000)).toEqual({
      radiusM: ORBIT_ZOOM.upperRadiusLimitM,
      settled: true,
    });
  });
});

describe("Retina render quality contract", () => {
  it("renders a desktop Retina viewport at a true two-times backing resolution", () => {
    const profile = deriveRenderQualityProfile({
      widthPx: 1440,
      heightPx: 900,
      devicePixelRatio: 2,
      maxMsaaSamples: 8,
    });
    expect(profile).toMatchObject({
      tier: "ULTRA",
      pixelRatio: 2,
      hardwareScalingLevel: 0.5,
      renderWidthPx: 2880,
      renderHeightPx: 1800,
      msaaSamples: 4,
      fxaaEnabled: false,
      ssaoEnabled: false,
      ssaoRatio: 0,
      shadowMapSize: 2048,
      environmentTextureSize: 512,
      anisotropy: 16,
    });
  });

  it("spends eight MSAA samples only on compact ultra-tier surfaces", () => {
    const compactDesktop = deriveRenderQualityProfile({
      widthPx: 1280,
      heightPx: 800,
      devicePixelRatio: 2,
      maxMsaaSamples: 16,
    });
    expect(compactDesktop.renderPixelCount).toBeLessThanOrEqual(4_500_000);
    expect(compactDesktop.tier).toBe("ULTRA");
    expect(compactDesktop.msaaSamples).toBe(8);

    const withoutHardwareMsaa = deriveRenderQualityProfile({
      widthPx: 1280,
      heightPx: 800,
      devicePixelRatio: 2,
      maxMsaaSamples: 4,
    });
    expect(withoutHardwareMsaa.msaaSamples).toBe(4);

    const largeSurface = deriveRenderQualityProfile({
      widthPx: 1512,
      heightPx: 982,
      devicePixelRatio: 2,
      maxMsaaSamples: 16,
    });
    expect(largeSurface.renderPixelCount).toBeGreaterThan(4_500_000);
    expect(largeSurface.msaaSamples).toBe(4);
  });

  it("supersamples standard-density displays without exceeding the Retina cap", () => {
    const standard = deriveRenderQualityProfile({
      widthPx: 1280,
      heightPx: 720,
      devicePixelRatio: 1,
      maxMsaaSamples: 4,
    });
    expect(standard.pixelRatio).toBe(1.5);
    expect(standard.hardwareScalingLevel).toBeCloseTo(2 / 3, 12);
    expect(standard.renderWidthPx).toBe(1920);
    expect(standard.renderHeightPx).toBe(1080);

    const mobileRetina = deriveRenderQualityProfile({
      widthPx: 390,
      heightPx: 844,
      devicePixelRatio: 3,
      maxMsaaSamples: 4,
      isCoarsePointer: true,
    });
    expect(mobileRetina.pixelRatio).toBe(2);
    expect(mobileRetina.hardwareScalingLevel).toBe(0.5);
    expect(mobileRetina.renderWidthPx).toBe(780);
    expect(mobileRetina.renderHeightPx).toBe(1688);
    expect(mobileRetina.tier).toBe("HIGH");
    expect(mobileRetina.msaaSamples).toBe(2);
    expect(mobileRetina.ssaoEnabled).toBe(false);
  });

  it("uses a pixel budget before reducing antialiasing quality", () => {
    const profile = deriveRenderQualityProfile({
      widthPx: 3840,
      heightPx: 2160,
      devicePixelRatio: 2,
      maxMsaaSamples: 8,
    });
    expect(profile.renderPixelCount).toBeLessThanOrEqual(12_010_000);
    expect(profile.pixelRatio).toBeGreaterThanOrEqual(1);
    expect(profile.pixelRatio).toBeLessThan(1.5);
    expect(profile.tier).toBe("HIGH");
    expect(profile.msaaSamples).toBe(2);
    expect(profile.fxaaEnabled).toBe(false);
  });

  it("sanitizes invalid capabilities and never inverts the scaling level", () => {
    for (const devicePixelRatio of [0, Number.NaN, Number.POSITIVE_INFINITY]) {
      const profile = deriveRenderQualityProfile({
        widthPx: 800,
        heightPx: 600,
        devicePixelRatio,
        maxMsaaSamples: 0,
      });
      expect(profile.pixelRatio).toBe(1.5);
      expect(profile.hardwareScalingLevel).toBeCloseTo(
        1 / profile.pixelRatio,
        12,
      );
      expect(profile.renderWidthPx).toBe(
        Math.round(800 * profile.pixelRatio),
      );
      expect(profile.renderHeightPx).toBe(
        Math.round(600 * profile.pixelRatio),
      );
      expect(profile.msaaSamples).toBe(1);
      expect(profile.fxaaEnabled).toBe(true);
    }
  });
});

describe("free-flight camera contract", () => {
  it("maps layout-independent keyboard codes to helicopter movement", () => {
    expect(flightCommandForCode("KeyW")).toBe("forward");
    expect(flightCommandForCode("ArrowDown")).toBe("backward");
    expect(flightCommandForCode("KeyA")).toBe("left");
    expect(flightCommandForCode("KeyD")).toBe("right");
    expect(flightCommandForCode("KeyE")).toBe("up");
    expect(flightCommandForCode("PageDown")).toBe("down");
    expect(flightCommandForCode("Digit1")).toBeNull();
  });

  it("keeps forward motion horizontal and Q/E strictly world-up", () => {
    const start = { x: 2, y: 8, z: 3 };
    const forward = integrateFlightPosition({
      position: start,
      heading: { x: 0.6, z: -0.8 },
      commands: commands("forward"),
      deltaMs: 50,
    });
    expect(forward.y).toBe(start.y);
    expect(forward.x).toBeGreaterThan(start.x);
    expect(forward.z).toBeLessThan(start.z);

    const upward = integrateFlightPosition({
      position: start,
      heading: { x: 0.6, z: -0.8 },
      commands: commands("up"),
      deltaMs: 50,
    });
    expect(upward.x).toBe(start.x);
    expect(upward.z).toBe(start.z);
    expect(upward.y).toBeGreaterThan(start.y);
  });

  it("normalizes diagonal input and caps long frame gaps", () => {
    const start = { x: 0, y: 8, z: 0 };
    const axial = integrateFlightPosition({
      position: start,
      heading: { x: 0, z: -1 },
      commands: commands("forward"),
      deltaMs: 50,
    });
    const diagonal = integrateFlightPosition({
      position: start,
      heading: { x: 0, z: -1 },
      commands: commands("forward", "right"),
      deltaMs: 50,
    });
    const delayed = integrateFlightPosition({
      position: start,
      heading: { x: 0, z: -1 },
      commands: commands("forward"),
      deltaMs: 5_000,
    });
    expect(Math.hypot(axial.x, axial.y - 8, axial.z)).toBeCloseTo(0.12, 12);
    expect(Math.hypot(diagonal.x, diagonal.y - 8, diagonal.z)).toBeCloseTo(
      0.12,
      12,
    );
    expect(delayed).toEqual(axial);
  });

  it("supports turbo and precision speeds while respecting the flight envelope", () => {
    const start = { x: 0, y: 8, z: 0 };
    const normal = integrateFlightPosition({
      position: start,
      heading: { x: 0, z: -1 },
      commands: commands("forward"),
      deltaMs: 50,
    });
    const boosted = integrateFlightPosition({
      position: start,
      heading: { x: 0, z: -1 },
      commands: commands("forward"),
      deltaMs: 50,
      boost: true,
    });
    const precise = integrateFlightPosition({
      position: start,
      heading: { x: 0, z: -1 },
      commands: commands("forward"),
      deltaMs: 50,
      precision: true,
    });
    expect(Math.abs(boosted.z)).toBeCloseTo(Math.abs(normal.z) * 2.5, 12);
    expect(Math.abs(precise.z)).toBeCloseTo(Math.abs(normal.z) * 0.25, 12);

    const clamped = integrateFlightPosition({
      position: {
        x: FLIGHT_BOUNDS.maxX,
        y: FLIGHT_BOUNDS.maxY,
        z: FLIGHT_BOUNDS.minZ,
      },
      heading: { x: 1, z: -1 },
      commands: commands("forward", "right", "up"),
      deltaMs: 50,
      boost: true,
    });
    expect(clamped.x).toBeLessThanOrEqual(FLIGHT_BOUNDS.maxX);
    expect(clamped.y).toBe(FLIGHT_BOUNDS.maxY);
    expect(clamped.z).toBeGreaterThanOrEqual(FLIGHT_BOUNDS.minZ);
  });

  it("bounds an out-of-range entry pose before the first flight input", () => {
    const bounded = integrateFlightPosition({
      position: { x: 400, y: 200, z: -400 },
      heading: { x: 0, z: -1 },
      commands: commands(),
      deltaMs: 0,
    });
    expect(bounded).toEqual({
      x: FLIGHT_BOUNDS.maxX,
      y: FLIGHT_BOUNDS.maxY,
      z: FLIGHT_BOUNDS.minZ,
    });
  });

  it("selects only a short single-pointer primary tap, never a camera drag", () => {
    expect(
      isSelectionTap({
        travelPx: 3,
        durationMs: 180,
        maximumPointers: 1,
        button: 0,
      }),
    ).toBe(true);
    expect(
      isSelectionTap({
        travelPx: 18,
        durationMs: 180,
        maximumPointers: 1,
        button: 0,
      }),
    ).toBe(false);
    expect(
      isSelectionTap({
        travelPx: 2,
        durationMs: 180,
        maximumPointers: 2,
        button: 0,
      }),
    ).toBe(false);
    expect(
      isSelectionTap({
        travelPx: 2,
        durationMs: 180,
        maximumPointers: 1,
        button: 2,
      }),
    ).toBe(false);
  });

  it("dollies along the view ray with trackpad scroll and caps momentum", () => {
    // Scrolling towards you moves backwards, mirroring orbit zoom direction.
    const forward = flightWheelDollyDistanceM(-100);
    const backward = flightWheelDollyDistanceM(100);
    expect(forward).toBeGreaterThan(0);
    expect(backward).toBeLessThan(0);
    expect(forward).toBeCloseTo(-backward, 12);
    expect(Math.abs(flightWheelDollyDistanceM(-50_000))).toBe(
      FLIGHT_WHEEL_DOLLY_MAX_M,
    );
    expect(flightWheelDollyDistanceM(Number.NaN)).toBe(0);

    const start = { x: 0, y: 6, z: 0 };
    const ray = { x: 0, y: -0.5, z: -1 };
    const rayLength = Math.hypot(ray.x, ray.y, ray.z);
    const flown = integrateFlightDolly(start, ray, 4);
    expect(flown.x).toBeCloseTo(start.x, 10);
    expect(flown.y).toBeCloseTo(6 + (ray.y * 4) / rayLength, 10);
    expect(flown.z).toBeCloseTo((ray.z * 4) / rayLength, 10);

    const bounded = integrateFlightDolly(
      { x: FLIGHT_BOUNDS.maxX, y: FLIGHT_BOUNDS.minY, z: 0 },
      { x: 1, y: -1, z: 0 },
      40,
    );
    expect(bounded.x).toBe(FLIGHT_BOUNDS.maxX);
    expect(bounded.y).toBe(FLIGHT_BOUNDS.minY);
  });
});

describe("walkthrough motion", () => {
  it("pins the eye height above the floor and ignores vertical commands", async () => {
    const { integrateWalkPosition, WALK_EYE_HEIGHT_M, WALK_SPEED_MPS } = await import(
      "../lib/twin-viewport-contract"
    );
    const still = integrateWalkPosition({
      position: { x: 1, y: 9, z: 2 },
      heading: { x: 0, z: -1 },
      commands: new Set(["up", "down"]),
      deltaMs: 16,
      floorY: 0,
    });
    expect(still).toEqual({ x: 1, y: WALK_EYE_HEIGHT_M, z: 2 });
    const forward = integrateWalkPosition({
      position: { x: 0, y: WALK_EYE_HEIGHT_M, z: 0 },
      heading: { x: 0, z: -1 },
      commands: new Set(["forward"]),
      deltaMs: 40,
      floorY: 0,
    });
    expect(forward.z).toBeCloseTo(-WALK_SPEED_MPS.normal * 0.04, 5);
    expect(forward.y).toBe(WALK_EYE_HEIGHT_M);
    const boosted = integrateWalkPosition({
      position: { x: 0, y: WALK_EYE_HEIGHT_M, z: 0 },
      heading: { x: 1, z: 0 },
      commands: new Set(["right"]),
      deltaMs: 50,
      boost: true,
      floorY: 0,
    });
    expect(boosted.x).toBeCloseTo(0, 5);
    expect(boosted.z).toBeCloseTo(WALK_SPEED_MPS.boost * 0.05, 5);
  });

  it("walks slower than it flies so rooms stay controllable", async () => {
    const { WALK_SPEED_MPS, FLIGHT_SPEED_MPS } = await import(
      "../lib/twin-viewport-contract"
    );
    expect(WALK_SPEED_MPS.normal).toBeLessThan(FLIGHT_SPEED_MPS.normal);
    expect(WALK_SPEED_MPS.boost).toBeLessThan(FLIGHT_SPEED_MPS.boost);
    // The capsule has usable shoulder tolerance in the 601 mm corridor and
    // the 680 mm clear framed opening, while its head clears 2 100 mm.
    expect(0.601 - WALK_COLLISION_ELLIPSOID_M.x * 2).toBeGreaterThan(0.15);
    expect(0.68 - WALK_COLLISION_ELLIPSOID_M.x * 2).toBeGreaterThan(0.2);
    expect(
      WALK_COLLISION_OFFSET_M.y + WALK_COLLISION_ELLIPSOID_M.y,
    ).toBeLessThan(2.1);
    expect(
      WALK_COLLISION_OFFSET_M.y - WALK_COLLISION_ELLIPSOID_M.y,
    ).toBeGreaterThanOrEqual(0.015);
  });

  it("normalizes diagonal locomotion and brakes faster than it accelerates", () => {
    const axial = integrateAvatarVelocity({
      velocity: { x: 0, z: 0 },
      forward: { x: 0, z: -1 },
      commands: commands("forward"),
      deltaMs: 50,
    });
    const diagonal = integrateAvatarVelocity({
      velocity: { x: 0, z: 0 },
      forward: { x: 0, z: -1 },
      commands: commands("forward", "right"),
      deltaMs: 50,
    });
    expect(Math.hypot(diagonal.x, diagonal.z)).toBeCloseTo(
      Math.hypot(axial.x, axial.z),
      10,
    );
    const braking = integrateAvatarVelocity({
      velocity: axial,
      forward: { x: 0, z: -1 },
      commands: commands(),
      deltaMs: 50,
    });
    expect(Math.hypot(braking.x, braking.z)).toBeLessThan(
      Math.hypot(axial.x, axial.z) * 0.42,
    );
  });

  it("keeps a shallow authoritative wall slide time-equivalent at 60/144/240 Hz", () => {
    const results = [60, 144, 240].map((fps) => {
      const deltaMs = 1000 / fps;
      const babylonHorizontalFloorM =
        WALK_COLLISION_ELLIPSOID_M.x * 0.001 * 10;
      const shallowAngleRad = Math.PI / 12;
      let velocity = { x: 0, z: 0 };
      let pending = { x: 0, z: 0 };
      let sinceSolve = { x: 0, z: 0 };
      let pendingMs = 0;
      let sinceSolveMs = 0;
      let travelledAlongWallM = 0;
      let solves = 0;
      let rejectedSolves = 0;
      let minimumSuccessfulTangentM = Number.POSITIVE_INFINITY;
      let maximumNormalVelocityAfterSolve = 0;

      // Exactly one second at every refresh rate.
      for (let frame = 0; frame < fps; frame += 1) {
        const terminal = integrateAvatarVelocity({
          velocity,
          forward: {
            x: Math.cos(shallowAngleRad),
            z: -Math.sin(shallowAngleRad),
          },
          commands: commands("forward"),
          deltaMs,
          precision: true,
        });
        pending = {
          x: pending.x + terminal.x * (deltaMs / 1000),
          z: pending.z + terminal.z * (deltaMs / 1000),
        };
        sinceSolve = {
          x: sinceSolve.x + terminal.x * (deltaMs / 1000),
          z: sinceSolve.z + terminal.z * (deltaMs / 1000),
        };
        pendingMs += deltaMs;
        sinceSolveMs += deltaMs;
        if (!shouldResolveWalkCollisionBatch(sinceSolve, sinceSolveMs)) {
          velocity = terminal;
          continue;
        }

        // A wall blocks +x. Babylon may discard its recursive slide when the
        // remaining tangent is below its ellipsoid-scaled epsilon floor.
        const movedZ =
          Math.abs(pending.z) > babylonHorizontalFloorM ? pending.z : 0;
        velocity = resolveWalkCollisionVelocity({
          terminal,
          intended: pending,
          moved: { x: 0, z: movedZ },
          elapsedMs: pendingMs,
        });
        travelledAlongWallM += Math.abs(movedZ);
        maximumNormalVelocityAfterSolve = Math.max(
          maximumNormalVelocityAfterSolve,
          Math.abs(velocity.x),
        );
        solves += 1;
        if (movedZ === 0) {
          // Runtime retains a rejected displacement: the next collision call
          // receives enough real tangent to pass Babylon's recursive floor.
          rejectedSolves += 1;
          const carryM = Math.hypot(pending.x, pending.z);
          if (carryM > WALK_CAMERA.maxRejectedCollisionCarryM) {
            const scale = WALK_CAMERA.maxRejectedCollisionCarryM / carryM;
            pending = { x: pending.x * scale, z: pending.z * scale };
            pendingMs *= scale;
          }
          sinceSolve = { x: 0, z: 0 };
          sinceSolveMs = 0;
        } else {
          minimumSuccessfulTangentM = Math.min(
            minimumSuccessfulTangentM,
            Math.abs(pending.z),
          );
          pending = { x: 0, z: 0 };
          sinceSolve = { x: 0, z: 0 };
          pendingMs = 0;
          sinceSolveMs = 0;
        }
      }

      expect(solves).toBeGreaterThan(10);
      expect(rejectedSolves).toBeGreaterThan(0);
      expect(travelledAlongWallM).toBeGreaterThan(0.025);
      expect(minimumSuccessfulTangentM).toBeGreaterThan(
        babylonHorizontalFloorM,
      );
      expect(maximumNormalVelocityAfterSolve).toBe(0);
      return travelledAlongWallM;
    });
    expect(Math.max(...results) - Math.min(...results)).toBeLessThan(0.025);

    // A long idle must not make the first 240 Hz precision frame eligible for
    // a sub-epsilon solve merely because wall-clock time elapsed.
    const firstPrecisionFrame = integrateAvatarVelocity({
      velocity: { x: 0, z: 0 },
      forward: { x: 0, z: -1 },
      commands: commands("forward"),
      deltaMs: 1000 / 240,
      precision: true,
    });
    expect(
      shouldResolveWalkCollisionBatch(
        {
          x: firstPrecisionFrame.x / 240,
          z: firstPrecisionFrame.z / 240,
        },
        1000 + 1000 / 240,
      ),
    ).toBe(false);

    // A rejected wall-normal carry is discarded on release, so a later
    // perpendicular key press cannot discharge it as a positional impulse.
    let rejectedCarry = {
      x: WALK_CAMERA.minCollisionSolveDistanceM,
      z: 0,
    };
    let rejectedCarryMs = 40;
    if (shouldResetWalkCollisionCarry(false, { x: 0, z: 0 })) {
      rejectedCarry = { x: 0, z: 0 };
      rejectedCarryMs = 0;
    }
    const firstNewDirectionFrame = integrateAvatarVelocity({
      velocity: { x: 0, z: 0 },
      forward: { x: 0, z: -1 },
      commands: commands("forward"),
      deltaMs: 1000 / 240,
    });
    rejectedCarry.z += firstNewDirectionFrame.z / 240;
    rejectedCarryMs += 1000 / 240;
    expect(rejectedCarry.x).toBe(0);
    expect(
      shouldResolveWalkCollisionBatch(rejectedCarry, rejectedCarryMs),
    ).toBe(false);

    // Immediate W -> A without a release frame must discard the old rejected
    // carry, while another W frame must keep accumulating it.
    const rejectedForwardCarry = {
      x: 0,
      z: -WALK_CAMERA.minCollisionSolveDistanceM,
    };
    const sameDirectionFrame = integrateAvatarVelocity({
      velocity: { x: 0, z: 0 },
      forward: { x: 0, z: -1 },
      commands: commands("forward"),
      deltaMs: 1000 / 240,
    });
    const perpendicularFrame = integrateAvatarVelocity({
      velocity: { x: 0, z: 0 },
      forward: { x: 0, z: -1 },
      commands: commands("left"),
      deltaMs: 1000 / 240,
    });
    expect(
      shouldResetWalkCollisionCarry(
        true,
        sameDirectionFrame,
        rejectedForwardCarry,
      ),
    ).toBe(false);
    expect(
      shouldResetWalkCollisionCarry(
        true,
        perpendicularFrame,
        rejectedForwardCarry,
      ),
    ).toBe(true);
    let immediatePerpendicularCarry = { ...rejectedForwardCarry };
    if (
      shouldResetWalkCollisionCarry(
        true,
        perpendicularFrame,
        immediatePerpendicularCarry,
      )
    ) {
      immediatePerpendicularCarry = { x: 0, z: 0 };
    }
    immediatePerpendicularCarry.x += perpendicularFrame.x / 240;
    immediatePerpendicularCarry.z += perpendicularFrame.z / 240;
    expect(immediatePerpendicularCarry.z).toBeCloseTo(0, 12);
    expect(
      shouldResolveWalkCollisionBatch(
        immediatePerpendicularCarry,
        1000 / 240,
      ),
    ).toBe(false);
  });
});

describe("adaptive indoor chase camera", () => {
  it("caps only a wide indoor boom and restores the outdoor request", () => {
    expect(walkCameraRadiusForEnvironment(WALK_CAMERA.radiusM, 1)).toBe(
      WALK_SURFACE.indoorCameraMaxRadiusM,
    );
    expect(walkCameraRadiusForEnvironment(1.25, 1)).toBe(1.25);
    expect(walkCameraRadiusForEnvironment(WALK_CAMERA.radiusM, 0)).toBe(
      WALK_CAMERA.radiusM,
    );
    expect(walkCameraRadiusForEnvironment(WALK_CAMERA.radiusM, 0.5)).toBeCloseTo(
      (WALK_CAMERA.radiusM + WALK_SURFACE.indoorCameraMaxRadiusM) / 2,
      10,
    );
    expect(walkCameraRadiusForEnvironment(1.25, 0.5)).toBe(1.25);

    const blendAfter = (fps: number, indoors: boolean) => {
      let blend = indoors ? 0 : 1;
      for (let frame = 0; frame < fps; frame += 1) {
        blend = stepWalkIndoorBlend(blend, indoors, 1000 / fps);
      }
      return blend;
    };
    expect(blendAfter(60, true)).toBeCloseTo(blendAfter(240, true), 10);
    expect(blendAfter(60, false)).toBeCloseTo(blendAfter(240, false), 10);
  });

  it("follows ramps smoothly at any refresh rate without excessive eye lag", () => {
    const settle = (fps: number, targetY: number) => {
      let y = 0;
      for (let frame = 0; frame < fps; frame += 1) {
        y = stepWalkCameraSurfaceHeight(y, targetY, 1000 / fps);
      }
      return y;
    };
    expect(settle(60, 0.18)).toBeCloseTo(settle(240, 0.18), 6);
    expect(settle(60, -0.13)).toBeCloseTo(settle(240, -0.13), 6);

    const afterDrop = stepWalkCameraSurfaceHeight(0.3, -0.48, 16);
    expect(Math.abs(afterDrop - -0.48)).toBeCloseTo(
      WALK_SURFACE.maxCameraLagM,
      10,
    );
  });

  it("auto-rewinds only after distinct failed escape directions", () => {
    const forwardMask = addWalkEscapeDirection(0, { x: 0, z: -1 });
    const repeatedForwardMask = addWalkEscapeDirection(forwardMask, {
      x: 0,
      z: -1,
    });
    const trappedMask = addWalkEscapeDirection(repeatedForwardMask, {
      x: -1,
      z: 0,
    });
    expect(hasDiverseWalkEscapeDirections(repeatedForwardMask)).toBe(false);
    expect(hasDiverseWalkEscapeDirections(trappedMask)).toBe(true);

    const base = {
      blockedForS: WALK_SURFACE.autoRecoveryBlockedS,
      rewindDistanceM: 0.2,
      cooldownS: 0,
      hasDirectionalInput: true,
    } as const;
    expect(
      shouldAutoRecoverWalk({ ...base, directionMask: repeatedForwardMask }),
    ).toBe(false);
    expect(
      shouldAutoRecoverWalk({ ...base, directionMask: trappedMask }),
    ).toBe(true);
    expect(
      shouldAutoRecoverWalk({
        ...base,
        directionMask: trappedMask,
        cooldownS: 0.1,
      }),
    ).toBe(false);
    expect(
      shouldAutoRecoverWalk({
        ...base,
        directionMask: trappedMask,
        rewindDistanceM: WALK_SURFACE.autoRecoveryMaxRewindM + 0.01,
      }),
    ).toBe(false);
  });

  it("finds the first finite world-box contact without triangle picking", () => {
    expect(
      rayAabbDistance({
        origin: { x: 0, y: 1.4, z: 0 },
        direction: { x: 0, y: 0.25, z: -1 },
        minimum: { x: -2, y: 0, z: -1.1 },
        maximum: { x: 2, y: 2.6, z: -0.9 },
        maxDistanceM: 2.6,
      }),
    ).toBeCloseTo(0.9277, 3);
    expect(
      rayAabbDistance({
        origin: { x: 0, y: 1.4, z: 0 },
        direction: { x: 1, y: 0, z: 0 },
        minimum: { x: -2, y: 0, z: -1.1 },
        maximum: { x: 2, y: 2.6, z: -0.9 },
        maxDistanceM: 2.6,
      }),
    ).toBeNull();
  });

  it("compresses immediately before a wall but preserves the requested zoom", () => {
    const compressed = stepWalkCameraBoom({
      desiredRadiusM: WALK_CAMERA.radiusM,
      currentRadiusM: WALK_CAMERA.radiusM,
      hitDistanceM: 0.48,
      deltaMs: 16,
      wasObstructed: false,
    });
    expect(compressed.radiusM).toBeCloseTo(
      0.48 - WALK_CAMERA.collisionPaddingM,
      10,
    );
    expect(compressed.obstructed).toBe(true);

    const clearing = stepWalkCameraBoom({
      desiredRadiusM: WALK_CAMERA.radiusM,
      currentRadiusM: compressed.radiusM,
      hitDistanceM: null,
      deltaMs: 16,
      wasObstructed: true,
    });
    expect(clearing.radiusM).toBeGreaterThan(compressed.radiusM);
    expect(clearing.radiusM).toBeLessThan(WALK_CAMERA.radiusM);
  });

  it("restores at the same rate across common frame rates", () => {
    const restore = (frameMs: number, frames: number) => {
      let radiusM = 0.4;
      let obstructed = true;
      for (let frame = 0; frame < frames; frame += 1) {
        const next = stepWalkCameraBoom({
          desiredRadiusM: WALK_CAMERA.radiusM,
          currentRadiusM: radiusM,
          hitDistanceM: null,
          deltaMs: frameMs,
          wasObstructed: obstructed,
        });
        radiusM = next.radiusM;
        obstructed = next.obstructed;
      }
      return radiusM;
    };
    expect(restore(20, 6)).toBeCloseTo(restore(40, 3), 10);
  });

  it("ignores grazing hits inside the anti-jitter hysteresis", () => {
    const grazing = stepWalkCameraBoom({
      desiredRadiusM: 2,
      currentRadiusM: 2,
      hitDistanceM:
        2 + WALK_CAMERA.collisionPaddingM - WALK_CAMERA.collisionHysteresisM / 2,
      deltaMs: 16,
      wasObstructed: false,
    });
    expect(grazing).toEqual({ radiusM: 2, obstructed: false });
  });
});

describe("interior photographic contract", () => {
  it("keeps the exterior clean and reserves screen-space passes for indoors", () => {
    expect(EXTERIOR_RENDER_STABILITY.screenSpaceAmbientOcclusionEnabled).toBe(
      false,
    );
    const ao = INTERIOR_RENDER_QUALITY.ambientOcclusion;
    // The kernel must read skirtings and linings, not the roof's eave stack.
    expect(ao.radiusM).toBeGreaterThan(0.2);
    expect(ao.radiusM).toBeLessThan(0.5);
    expect(ao.base).toBeGreaterThan(0);
    expect(ao.samples.ULTRA).toBeGreaterThan(ao.samples.HIGH);
    expect(ao.ssaoRatio.ULTRA).toBeGreaterThan(ao.ssaoRatio.HIGH);
    expect(INTERIOR_RENDER_QUALITY.screenSpaceReflections.tiers).toEqual([
      "ULTRA",
    ]);
    expect(INTERIOR_RENDER_QUALITY.walkShadowMaxZ).toBeLessThan(78);
    expect(INTERIOR_RENDER_QUALITY.engageIndoorBlend).toBeGreaterThan(
      INTERIOR_RENDER_QUALITY.releaseIndoorBlend,
    );
  });

  it("engages only while walking indoors, with hysteresis at the threshold", () => {
    const { engageIndoorBlend, releaseIndoorBlend } = INTERIOR_RENDER_QUALITY;
    expect(
      shouldEngageInteriorPostFx({
        navigationMode: "orbit",
        indoorBlend: 1,
        wasEngaged: true,
      }),
    ).toBe(false);
    expect(
      shouldEngageInteriorPostFx({
        navigationMode: "walk",
        indoorBlend: engageIndoorBlend - 0.01,
        wasEngaged: false,
      }),
    ).toBe(false);
    expect(
      shouldEngageInteriorPostFx({
        navigationMode: "walk",
        indoorBlend: engageIndoorBlend,
        wasEngaged: false,
      }),
    ).toBe(true);
    // A doorway crossing in the band between the two thresholds keeps state.
    const between = (engageIndoorBlend + releaseIndoorBlend) / 2;
    expect(
      shouldEngageInteriorPostFx({
        navigationMode: "walk",
        indoorBlend: between,
        wasEngaged: true,
      }),
    ).toBe(true);
    expect(
      shouldEngageInteriorPostFx({
        navigationMode: "walk",
        indoorBlend: between,
        wasEngaged: false,
      }),
    ).toBe(false);
    expect(
      shouldEngageInteriorPostFx({
        navigationMode: "walk",
        indoorBlend: Number.NaN,
        wasEngaged: true,
      }),
    ).toBe(false);
  });

  it("sheds reflections first, then AO quality, and never restores", () => {
    const heavy = ADAPTIVE_POST_FX.shedFrameMs + 6;
    let state = initialAdaptivePostFxState();
    // Warm-up frames are absorbed without judgement.
    for (let elapsed = 0; elapsed < ADAPTIVE_POST_FX.warmupMs; elapsed += heavy) {
      state = stepAdaptivePostFx(state, heavy);
    }
    expect(state.shedLevel).toBe(0);
    const runWindow = (frameMs: number) => {
      for (let elapsed = 0; elapsed < ADAPTIVE_POST_FX.windowMs; elapsed += frameMs) {
        state = stepAdaptivePostFx(state, frameMs);
      }
    };
    runWindow(heavy);
    expect(state.shedLevel).toBe(1);
    runWindow(heavy);
    expect(state.shedLevel).toBe(2);
    runWindow(heavy);
    expect(state.shedLevel).toBe(ADAPTIVE_POST_FX.maxShedLevel);
    // Recovered performance does not bring effects back within the session.
    runWindow(8);
    expect(state.shedLevel).toBe(ADAPTIVE_POST_FX.maxShedLevel);
  });

  it("ignores tab sleeps and shader compiles when judging load", () => {
    let state = { ...initialAdaptivePostFxState(), warmupRemainingMs: 0 };
    for (let frame = 0; frame < 4; frame += 1) {
      state = stepAdaptivePostFx(state, ADAPTIVE_POST_FX.ignoreFrameAboveMs + 1);
    }
    expect(state).toMatchObject({ shedLevel: 0, windowMs: 0, windowFrames: 0 });
    state = stepAdaptivePostFx(state, Number.NaN);
    state = stepAdaptivePostFx(state, -5);
    expect(state.windowFrames).toBe(0);
    // A smooth window never sheds.
    for (let elapsed = 0; elapsed < ADAPTIVE_POST_FX.windowMs; elapsed += 8) {
      state = stepAdaptivePostFx(state, 8);
    }
    expect(state.shedLevel).toBe(0);
  });

  it("resolves the interior plan per tier and shed level", () => {
    const ao = INTERIOR_RENDER_QUALITY.ambientOcclusion;
    expect(interiorPostFxPlan({ engaged: false, tier: "ULTRA", shedLevel: 0 }))
      .toEqual({
        ambientOcclusion: false,
        ambientOcclusionSamples: 0,
        screenSpaceReflections: false,
      });
    expect(interiorPostFxPlan({ engaged: true, tier: "ULTRA", shedLevel: 0 }))
      .toEqual({
        ambientOcclusion: true,
        ambientOcclusionSamples: ao.samples.ULTRA,
        screenSpaceReflections: true,
      });
    expect(interiorPostFxPlan({ engaged: true, tier: "HIGH", shedLevel: 0 }))
      .toEqual({
        ambientOcclusion: true,
        ambientOcclusionSamples: ao.samples.HIGH,
        screenSpaceReflections: false,
      });
    expect(interiorPostFxPlan({ engaged: true, tier: "ULTRA", shedLevel: 1 }))
      .toMatchObject({
        ambientOcclusionSamples: ao.samples.ULTRA,
        screenSpaceReflections: false,
      });
    expect(interiorPostFxPlan({ engaged: true, tier: "ULTRA", shedLevel: 2 }))
      .toMatchObject({
        ambientOcclusion: true,
        ambientOcclusionSamples: ao.samples.HIGH,
        screenSpaceReflections: false,
      });
  });

  it("grades reality mode like a restrained architectural photograph", () => {
    expect(PHOTOGRAPHIC_GRADE.exposure).toBeGreaterThanOrEqual(1);
    expect(PHOTOGRAPHIC_GRADE.exposure).toBeLessThan(1.1);
    expect(PHOTOGRAPHIC_GRADE.contrast).toBeGreaterThan(1);
    expect(PHOTOGRAPHIC_GRADE.contrast).toBeLessThan(1.15);
    const curves = PHOTOGRAPHIC_GRADE.colorCurves;
    // Warm shadows, cool highlights, and a saturation lift kept in single digits.
    expect(curves.shadowsHue).toBeGreaterThan(0);
    expect(curves.shadowsHue).toBeLessThan(60);
    expect(curves.highlightsHue).toBeGreaterThan(180);
    expect(curves.highlightsHue).toBeLessThan(260);
    expect(Math.abs(curves.globalSaturation)).toBeLessThan(10);
    expect(Math.abs(curves.shadowsDensity)).toBeLessThan(15);
    expect(Math.abs(curves.highlightsDensity)).toBeLessThan(15);
  });
});
