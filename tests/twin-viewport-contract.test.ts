import { describe, expect, it } from "vitest";

import {
  FLIGHT_BOUNDS,
  FLIGHT_WHEEL_DOLLY_MAX_M,
  ORBIT_ZOOM,
  clampOrbitRadius,
  deriveRenderQualityProfile,
  easeOrbitRadius,
  flightCommandForCode,
  flightWheelDollyDistanceM,
  integrateFlightDolly,
  integrateFlightPosition,
  isSelectionTap,
  normalizeWheelPixels,
  orbitZoomMultiplier,
  stepOrbitZoom,
  wheelZoomGesture,
  type FlightCommand,
} from "../lib/twin-viewport-contract";

const commands = (...values: FlightCommand[]) => new Set(values);

describe("orbit zoom contract", () => {
  it("uses an exponential trackpad model and owns browser gestures", () => {
    expect(ORBIT_ZOOM).toEqual({
      lowerRadiusLimitM: 4.5,
      upperRadiusLimitM: 64,
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
      ssaoEnabled: true,
      ssaoRatio: 1,
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
    const { WALK_SPEED_MPS, FLIGHT_SPEED_MPS, WALK_COLLISION_ELLIPSOID_M } = await import(
      "../lib/twin-viewport-contract"
    );
    expect(WALK_SPEED_MPS.normal).toBeLessThan(FLIGHT_SPEED_MPS.normal);
    expect(WALK_SPEED_MPS.boost).toBeLessThan(FLIGHT_SPEED_MPS.boost);
    // The collider must pass a 700 mm leaf and a 2 100 mm door head.
    expect(WALK_COLLISION_ELLIPSOID_M.x * 2).toBeLessThan(0.7);
    expect(1.65 + WALK_COLLISION_ELLIPSOID_M.y).toBeLessThan(2.1);
  });
});
