import { describe, expect, it } from "vitest";

import {
  ARCHITECTURAL_DOOR_INVENTORY,
  BabylonDoorController,
  doorHandleDepression,
  hingedDoorSweepIsClear,
  selectDoorInteractionTarget,
  slidingDoorPathIsClear,
  smootherStep01,
  type DoorActorState,
} from "../lib/babylon-doors";

const actor = (
  x: number,
  z: number,
  facingX = 1,
  facingZ = 0,
): DoorActorState => ({
  position: { x, z },
  facing: { x: facingX, z: facingZ },
});

describe("animated architectural doors", () => {
  it("defines one exact controller contract for all 18 architectural systems", () => {
    expect(ARCHITECTURAL_DOOR_INVENTORY).toHaveLength(18);
    expect(new Set(ARCHITECTURAL_DOOR_INVENTORY.map(({ id }) => id)).size).toBe(18);
    expect(
      ARCHITECTURAL_DOOR_INVENTORY.reduce<Record<string, number>>(
        (counts, { kind }) => ({ ...counts, [kind]: (counts[kind] ?? 0) + 1 }),
        {},
      ),
    ).toEqual({ HINGED: 14, SLIDING: 3, OVERHEAD: 1 });

    const controller = new BabylonDoorController();
    for (const door of ARCHITECTURAL_DOOR_INVENTORY) {
      controller.register({
        ...door,
        label: door.id,
        interactionPoint: { x: 0, z: 0 },
        apply: () => undefined,
      });
    }
    expect(() => controller.assertInventory()).not.toThrow();
  });

  it("uses a monotonic physical ease and a handle-first gesture", () => {
    const samples = Array.from({ length: 101 }, (_, index) =>
      smootherStep01(index / 100),
    );
    expect(samples[0]).toBe(0);
    expect(samples.at(-1)).toBe(1);
    for (let index = 1; index < samples.length; index += 1) {
      expect(samples[index]).toBeGreaterThanOrEqual(samples[index - 1]);
      expect(samples[index]).toBeGreaterThanOrEqual(0);
      expect(samples[index]).toBeLessThanOrEqual(1);
    }
    expect(doorHandleDepression(0)).toBe(0);
    expect(doorHandleDepression(0.21)).toBeCloseTo(1, 8);
    expect(doorHandleDepression(0.42)).toBe(0);
    expect(doorHandleDepression(1)).toBe(0);
  });

  it("selects only a nearby door in front of the walker deterministically", () => {
    const doors = [
      { id: "B", interactionPoint: { x: 1.2, z: 0.08 } },
      { id: "A", interactionPoint: { x: 1.2, z: -0.08 } },
      { id: "BEHIND", interactionPoint: { x: -1.1, z: 0 } },
      { id: "FAR", interactionPoint: { x: 3, z: 0 } },
    ];
    expect(selectDoorInteractionTarget(doors, actor(0, 0))?.door.id).toBe("A");
    expect(
      selectDoorInteractionTarget(
        [{ id: "NEAR-BEHIND", interactionPoint: { x: -0.4, z: 0 } }],
        actor(0, 0),
      )?.door.id,
    ).toBe("NEAR-BEHIND");
  });

  it("reaches the same open state at 60, 144 and 240 Hz", () => {
    const run = (fps: number) => {
      let lastProgress = -1;
      const controller = new BabylonDoorController();
      controller.register({
        id: "DOOR",
        label: "Dvere",
        kind: "HINGED",
        interactionPoint: { x: 1, z: 0 },
        apply: (progress) => {
          expect(progress).toBeGreaterThanOrEqual(lastProgress);
          lastProgress = progress;
        },
      });
      controller.setActor(actor(0, 0));
      expect(controller.toggleInteractionTarget()).toBe(true);
      for (let elapsed = 0; elapsed < 850; elapsed += 1000 / fps) {
        controller.update(1000 / fps);
      }
      return controller.debugState()[0];
    };
    for (const fps of [60, 144, 240]) {
      expect(run(fps)).toMatchObject({ phase: "OPEN", progress: 1 });
    }
  });

  it("keeps opening and closing progress equivalent across refresh rates", () => {
    const progressAt = (fps: number, elapsedTargetMs: number, closing = false) => {
      const controller = new BabylonDoorController();
      controller.register({
        id: "DOOR",
        label: "Dvere",
        kind: "HINGED",
        interactionPoint: { x: 1, z: 0 },
        initiallyOpen: closing,
        apply: () => undefined,
      });
      controller.setOpen("DOOR", !closing);
      let elapsedMs = 0;
      while (elapsedMs < elapsedTargetMs) {
        const stepMs = Math.min(1000 / fps, elapsedTargetMs - elapsedMs);
        controller.update(stepMs);
        elapsedMs += stepMs;
      }
      return controller.debugState()[0].progress;
    };

    for (const elapsedMs of [190, 380, 680]) {
      const opening = [60, 144, 240].map((fps) =>
        progressAt(fps, elapsedMs),
      );
      expect(Math.max(...opening) - Math.min(...opening)).toBeLessThan(1e-9);
    }
    for (const elapsedMs of [170, 340, 620]) {
      const closing = [60, 144, 240].map((fps) =>
        progressAt(fps, elapsedMs, true),
      );
      expect(Math.max(...closing) - Math.min(...closing)).toBeLessThan(1e-9);
    }
  });

  it("clamps a background frame and pauses a closing sweep entered mid-motion", () => {
    const controller = new BabylonDoorController();
    controller.register({
      id: "DOOR",
      label: "Dvere",
      kind: "HINGED",
      interactionPoint: { x: 1, z: 0 },
      initiallyOpen: true,
      apply: () => undefined,
      canClose: ({ position }) => position.z > 0.5,
    });
    controller.setActor(actor(0, 1));
    expect(controller.setOpen("DOOR", false)).toBe(true);
    controller.update(1_000);
    const afterClampedFrame = controller.debugState()[0].progress;
    expect(afterClampedFrame).toBeCloseTo(1 - smootherStep01(50 / 680), 8);

    controller.setActor(actor(0, 0));
    controller.update(100);
    expect(controller.debugState()[0].progress).toBeCloseTo(afterClampedFrame, 10);
    expect(controller.getInteraction()?.blockedMessage).toBe(
      "Ustúpte z dráhy dverí",
    );

    controller.setActor(actor(0, 1));
    for (let elapsed = 0; elapsed < 800; elapsed += 20) controller.update(20);
    expect(controller.debugState()[0]).toMatchObject({
      phase: "CLOSED",
      progress: 0,
    });
  });

  it("keeps independent state and refuses to close through the avatar", () => {
    const controller = new BabylonDoorController();
    const register = (id: string, x: number) =>
      controller.register({
        id,
        label: id,
        kind: "HINGED",
        interactionPoint: { x, z: 0 },
        apply: () => undefined,
        canClose: ({ position }) => position.z > 0.5,
      });
    register("A", 1);
    register("B", 4);
    controller.setActor(actor(0, 0));
    expect(controller.setOpen("A", true, true)).toBe(true);
    expect(controller.setOpen("A", false)).toBe(false);
    expect(controller.getInteraction()).toMatchObject({
      id: "A",
      phase: "OPEN",
      blockedMessage: "Ustúpte z dráhy dverí",
    });
    expect(controller.debugState()).toEqual([
      expect.objectContaining({ id: "A", progress: 1 }),
      expect.objectContaining({ id: "B", progress: 0 }),
    ]);
  });

  it("protects hinged and sliding sweep envelopes while allowing a safe side", () => {
    const hinge = { x: 0, z: 0 };
    const closedEnd = { x: 0.8, z: 0 };
    expect(
      hingedDoorSweepIsClear(actor(0.5, -0.25), hinge, closedEnd, Math.PI / 2),
    ).toBe(false);
    expect(
      hingedDoorSweepIsClear(actor(-0.7, -0.7), hinge, closedEnd, Math.PI / 2),
    ).toBe(true);
    expect(
      hingedDoorSweepIsClear(
        actor(0.5, 0.05),
        hinge,
        closedEnd,
        Math.PI / 2,
        0.04,
        0.7,
        1,
      ),
    ).toBe(true);

    expect(
      slidingDoorPathIsClear(
        actor(0.2, 0.1),
        { x: 0, z: 0 },
        { x: -1, z: 0 },
        0.5,
      ),
    ).toBe(false);
    expect(
      slidingDoorPathIsClear(
        actor(0.2, 1),
        { x: 0, z: 0 },
        { x: -1, z: 0 },
        0.5,
      ),
    ).toBe(true);
    expect(
      slidingDoorPathIsClear(
        actor(0.2, 0.4),
        { x: 0, z: 0 },
        { x: -1, z: 0 },
        0.5,
      ),
    ).toBe(true);
    expect(
      slidingDoorPathIsClear(
        actor(0, 0.1),
        { x: 0, z: 0 },
        { x: -1, z: 0 },
        0.5,
        0.08,
        0.8,
        1,
      ),
    ).toBe(true);
  });
});
