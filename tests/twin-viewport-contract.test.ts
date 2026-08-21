import { describe, expect, it } from "vitest";

import {
  FLIGHT_BOUNDS,
  deriveRenderQualityProfile,
  flightCommandForCode,
  integrateFlightPosition,
  isSelectionTap,
  type FlightCommand,
} from "../lib/twin-viewport-contract";

const commands = (...values: FlightCommand[]) => new Set(values);

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
});
