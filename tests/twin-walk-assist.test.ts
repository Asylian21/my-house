import { describe, expect, it } from "vitest";

import {
  DOORWAY_ASSIST,
  doorwayAssistCorrection,
  movementProgress,
  rotatePlanar,
  shouldAttemptDeflection,
  steerVelocityThroughPassages,
  type WalkPassage,
} from "../lib/twin-walk-assist";

/** A 700 mm clear door in a 150 mm wall along the X axis, centred at origin. */
const passage: WalkPassage = {
  id: "DOOR-TEST",
  center: { x: 0, z: 0 },
  along: { x: 1, z: 0 },
  halfClearWidthM: 0.35,
  halfDepthM: 0.075,
};

describe("doorway funnel assist", () => {
  it("turns an offset approach toward the centreline without changing speed", () => {
    const velocity = { x: 0, z: 1.2 };
    const steered = steerVelocityThroughPassages(
      velocity,
      { x: 0.22, z: -0.6 },
      [passage],
    );
    expect(Math.hypot(steered.x, steered.z)).toBeCloseTo(1.2, 10);
    // Standing right of centre, the heading now carries the walker left.
    expect(steered.x).toBeLessThan(-0.05);
    expect(steered.z).toBeGreaterThan(1.0);

    const mirrored = steerVelocityThroughPassages(
      velocity,
      { x: -0.22, z: -0.6 },
      [passage],
    );
    expect(mirrored.x).toBeCloseTo(-steered.x, 10);
  });

  it("works symmetrically from both sides of the wall", () => {
    const fromFront = doorwayAssistCorrection(
      { x: 0, z: 1 },
      { x: 0.2, z: -0.5 },
      passage,
    );
    const fromBack = doorwayAssistCorrection(
      { x: 0, z: -1 },
      { x: 0.2, z: 0.5 },
      passage,
    );
    expect(fromFront).not.toBeNull();
    expect(fromBack).not.toBeNull();
    expect(fromFront?.x).toBeCloseTo(fromBack?.x ?? Number.NaN, 10);
  });

  it("leaves the walker alone when not approaching the opening", () => {
    // Walking parallel to the wall in front of the door.
    expect(
      doorwayAssistCorrection({ x: 1, z: 0 }, { x: 0.1, z: -0.5 }, passage),
    ).toBeNull();
    // Walking away from the wall.
    expect(
      doorwayAssistCorrection({ x: 0, z: -1 }, { x: 0.1, z: -0.5 }, passage),
    ).toBeNull();
    // Too far from the wall plane.
    expect(
      doorwayAssistCorrection(
        { x: 0, z: 1 },
        { x: 0.1, z: -(passage.halfDepthM + DOORWAY_ASSIST.approachDistanceM + 0.05) },
        passage,
      ),
    ).toBeNull();
    // Beyond the lateral capture (aiming at the wall, not the opening).
    expect(
      doorwayAssistCorrection(
        { x: 0, z: 1 },
        {
          x: passage.halfClearWidthM + DOORWAY_ASSIST.lateralCaptureMarginM + 0.05,
          z: -0.5,
        },
        passage,
      ),
    ).toBeNull();
    // Repositioning speeds are never steered.
    expect(
      doorwayAssistCorrection({ x: 0, z: 0.1 }, { x: 0.2, z: -0.5 }, passage),
    ).toBeNull();
  });

  it("fades the funnel in over the approach distance", () => {
    const near = doorwayAssistCorrection(
      { x: 0, z: 1 },
      { x: 0.2, z: -0.3 },
      passage,
    );
    const far = doorwayAssistCorrection(
      { x: 0, z: 1 },
      { x: 0.2, z: -(passage.halfDepthM + DOORWAY_ASSIST.approachDistanceM - 0.1) },
      passage,
    );
    expect(near).not.toBeNull();
    expect(far).not.toBeNull();
    expect(Math.abs(far?.x ?? 0)).toBeLessThan(Math.abs(near?.x ?? 0) * 0.35);
  });

  it("caps the lateral correction and picks the strongest passage", () => {
    const wide = doorwayAssistCorrection(
      { x: 0, z: 1.4 },
      { x: 0.6, z: -0.3 },
      { ...passage, halfClearWidthM: 0.9 },
    );
    expect(Math.abs(wide?.x ?? 0)).toBeLessThanOrEqual(
      DOORWAY_ASSIST.maxLateralSpeedMps + 1e-9,
    );

    const secondary: WalkPassage = {
      ...passage,
      id: "DOOR-FAR",
      center: { x: 3, z: 0 },
    };
    const steered = steerVelocityThroughPassages(
      { x: 0, z: 1 },
      { x: 0.2, z: -0.4 },
      [secondary, passage],
    );
    expect(steered.x).toBeLessThan(0);
  });

  it("passes through velocity untouched without passages or with NaN input", () => {
    expect(steerVelocityThroughPassages({ x: 0.3, z: 0.4 }, { x: 0, z: 0 }, []))
      .toEqual({ x: 0.3, z: 0.4 });
    expect(
      steerVelocityThroughPassages(
        { x: Number.NaN, z: 1 },
        { x: 0, z: -0.5 },
        [passage],
      ),
    ).toEqual({ x: 0, z: 1 });
  });
});

describe("blocked-corner deflection", () => {
  it("rotates displacements about the vertical axis", () => {
    const quarter = rotatePlanar({ x: 1, z: 0 }, Math.PI / 2);
    expect(quarter.x).toBeCloseTo(0, 10);
    expect(quarter.z).toBeCloseTo(1, 10);
    const back = rotatePlanar(quarter, -Math.PI / 2);
    expect(back.x).toBeCloseTo(1, 10);
    expect(back.z).toBeCloseTo(0, 10);
  });

  it("measures achieved progress as the share of the original intent", () => {
    expect(movementProgress({ x: 1, z: 0 }, { x: 1, z: 0 })).toBe(1);
    expect(movementProgress({ x: 1, z: 0 }, { x: 0.25, z: 0.5 })).toBeCloseTo(
      0.25,
      10,
    );
    expect(movementProgress({ x: 1, z: 0 }, { x: -0.4, z: 0 })).toBe(0);
    expect(movementProgress({ x: 1, z: 0 }, { x: 2, z: 0 })).toBe(1);
    expect(movementProgress({ x: 0, z: 0 }, { x: 0, z: 0 })).toBe(1);
  });

  it("only retries a nearly rejected move that came from real input", () => {
    expect(shouldAttemptDeflection(true, 0.02, 0.1)).toBe(true);
    expect(
      shouldAttemptDeflection(true, 0.02, DOORWAY_ASSIST.deflectProgressBelow),
    ).toBe(false);
    expect(shouldAttemptDeflection(false, 0.02, 0.1)).toBe(false);
    expect(shouldAttemptDeflection(true, 0, 0.1)).toBe(false);
    expect(shouldAttemptDeflection(true, Number.NaN, 0.1)).toBe(false);
    expect(shouldAttemptDeflection(true, 0.02, Number.NaN)).toBe(false);
  });

  it("tries gentle headings before steep ones, symmetrically", () => {
    const angles = DOORWAY_ASSIST.deflectionAnglesRad;
    expect(angles.length % 2).toBe(0);
    for (let index = 0; index < angles.length; index += 2) {
      expect(angles[index]).toBeCloseTo(-angles[index + 1], 10);
      if (index >= 2) {
        expect(Math.abs(angles[index])).toBeGreaterThan(
          Math.abs(angles[index - 2]),
        );
      }
    }
    expect(DOORWAY_ASSIST.deflectMinimumProgress).toBeGreaterThan(
      DOORWAY_ASSIST.deflectProgressBelow,
    );
  });
});
