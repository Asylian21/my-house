import { describe, expect, it } from "vitest";

import {
  APPLIANCE_DOOR_INVENTORY,
  ARCHITECTURAL_DOOR_INVENTORY,
  BabylonDoorController,
  doorHandleDepression,
  doorInteractionPromptLabel,
  doorMotionDurationMs,
  hingedDoorSweepIsClear,
  INTERACTIVE_DOOR_INVENTORY,
  liftSlideSashLiftM,
  LIFT_SLIDE_MOTION,
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
  it("keeps 18 architectural systems and adds exactly two appliance doors", () => {
    expect(ARCHITECTURAL_DOOR_INVENTORY).toHaveLength(18);
    expect(new Set(ARCHITECTURAL_DOOR_INVENTORY.map(({ id }) => id)).size).toBe(18);
    expect(
      ARCHITECTURAL_DOOR_INVENTORY.reduce<Record<string, number>>(
        (counts, { kind }) => ({ ...counts, [kind]: (counts[kind] ?? 0) + 1 }),
        {},
      ),
    ).toEqual({ HINGED: 14, SLIDING: 3, OVERHEAD: 1 });

    expect(APPLIANCE_DOOR_INVENTORY).toEqual([
      { id: "BATH-105-WASHER-DOOR", kind: "HINGED" },
      { id: "BATH-105-DRYER-DOOR", kind: "HINGED" },
    ]);
    expect(INTERACTIVE_DOOR_INVENTORY).toHaveLength(20);
    expect(new Set(INTERACTIVE_DOOR_INVENTORY.map(({ id }) => id)).size).toBe(20);

    const controller = new BabylonDoorController();
    for (const door of INTERACTIVE_DOOR_INVENTORY) {
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

  it("lifts a sliding sash before travel and settles it only at the closed stop", () => {
    expect(liftSlideSashLiftM(0)).toBe(0);
    expect(liftSlideSashLiftM(0.025)).toBeGreaterThan(0);
    expect(liftSlideSashLiftM(0.025)).toBeLessThan(
      LIFT_SLIDE_MOTION.sashLiftM,
    );
    expect(liftSlideSashLiftM(0.05)).toBeCloseTo(
      LIFT_SLIDE_MOTION.sashLiftM,
      10,
    );
    expect(liftSlideSashLiftM(1)).toBeCloseTo(
      LIFT_SLIDE_MOTION.sashLiftM,
      10,
    );
  });

  it("uses action copy that matches hinged, sliding and garage motion", () => {
    const prompt = (
      kind: "HINGED" | "SLIDING" | "OVERHEAD",
      phase: "CLOSED" | "OPENING" | "OPEN" | "CLOSING",
      action: "OPEN" | "CLOSE" | null,
    ) => doorInteractionPromptLabel({ kind, phase, action, blockedMessage: null });

    expect(prompt("HINGED", "CLOSED", "OPEN")).toBe("Otvoriť dvere");
    expect(prompt("SLIDING", "CLOSED", "OPEN")).toBe("Odsunúť panel");
    expect(prompt("SLIDING", "OPEN", "CLOSE")).toBe("Zasunúť panel");
    expect(prompt("OVERHEAD", "OPENING", null)).toBe(
      "Zdvíham garážovú bránu…",
    );
    expect(prompt("OVERHEAD", "OPEN", "CLOSE")).toBe(
      "Zavrieť garážovú bránu",
    );
    expect(
      doorInteractionPromptLabel({
        kind: "HINGED",
        subject: "APPLIANCE_DOOR",
        phase: "CLOSED",
        action: "OPEN",
        blockedMessage: null,
      }),
    ).toBe("Otvoriť dvierka");
    expect(
      doorInteractionPromptLabel({
        kind: "HINGED",
        subject: "APPLIANCE_DOOR",
        phase: "OPEN",
        action: "CLOSE",
        blockedMessage: null,
      }),
    ).toBe("Zavrieť dvierka");
    expect(
      doorInteractionPromptLabel({
        kind: "SLIDING",
        phase: "CLOSING",
        action: null,
        blockedMessage: "Ustúpte z dráhy panelu",
      }),
    ).toBe("Ustúpte z dráhy panelu");
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

  it("uses vertical gaze and an explicit picked id to reach both stacked doors", () => {
    const stacked = [
      {
        id: "BATH-105-WASHER-DOOR",
        interactionPoint: { x: 1, y: 0.5, z: 0 },
      },
      {
        id: "BATH-105-DRYER-DOOR",
        interactionPoint: { x: 1, y: 1.39, z: 0 },
      },
    ];
    const eye = { x: 0, y: 1.55, z: 0 };
    expect(
      selectDoorInteractionTarget(stacked, {
        position: eye,
        facing: { x: 0.69, y: -0.72, z: 0 },
      })?.door.id,
    ).toBe("BATH-105-WASHER-DOOR");
    expect(
      selectDoorInteractionTarget(stacked, {
        position: eye,
        facing: { x: 0.99, y: -0.16, z: 0 },
      })?.door.id,
    ).toBe("BATH-105-DRYER-DOOR");

    const controller = new BabylonDoorController();
    for (const door of stacked) {
      controller.register({
        ...door,
        label: door.id,
        kind: "HINGED",
        subject: "APPLIANCE_DOOR",
        apply: () => undefined,
      });
    }
    controller.setActor({
      position: eye,
      facing: { x: 1, y: 0, z: 0 },
    });
    expect(controller.toggleInteractionTarget("BATH-105-WASHER-DOOR")).toBe(true);
    for (let elapsed = 0; elapsed < 850; elapsed += 20) controller.update(20);
    expect(controller.debugState()).toEqual([
      expect.objectContaining({ id: "BATH-105-DRYER-DOOR", progress: 0 }),
      expect.objectContaining({ id: "BATH-105-WASHER-DOOR", progress: 1 }),
    ]);
  });

  it("reaches the same open state for every motion kind at 60, 144 and 240 Hz", () => {
    const run = (kind: "HINGED" | "SLIDING" | "OVERHEAD", fps: number) => {
      let lastProgress = -1;
      const controller = new BabylonDoorController();
      controller.register({
        id: "DOOR",
        label: "Dvere",
        kind,
        interactionPoint: { x: 1, z: 0 },
        apply: (progress) => {
          expect(progress).toBeGreaterThanOrEqual(lastProgress);
          lastProgress = progress;
        },
      });
      controller.setActor(actor(0, 0));
      expect(controller.toggleInteractionTarget()).toBe(true);
      const totalMs = doorMotionDurationMs(kind, 1) + 60;
      for (let elapsed = 0; elapsed < totalMs; elapsed += 1000 / fps) {
        controller.update(1000 / fps);
      }
      return controller.debugState()[0];
    };
    for (const kind of ["HINGED", "SLIDING", "OVERHEAD"] as const) {
      for (const fps of [60, 144, 240]) {
        expect(run(kind, fps)).toMatchObject({ phase: "OPEN", progress: 1 });
      }
    }
  });

  it("keeps every opening and closing motion equivalent across refresh rates", () => {
    const progressAt = (
      kind: "HINGED" | "SLIDING" | "OVERHEAD",
      fps: number,
      elapsedTargetMs: number,
      closing = false,
    ) => {
      const controller = new BabylonDoorController();
      controller.register({
        id: "DOOR",
        label: "Dvere",
        kind,
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

    for (const kind of ["HINGED", "SLIDING", "OVERHEAD"] as const) {
      for (const closing of [false, true]) {
        const durationMs = doorMotionDurationMs(kind, closing ? 0 : 1);
        for (const fraction of [0.25, 0.5, 0.9]) {
          const elapsedMs = durationMs * fraction;
          const progress = [60, 144, 240].map((fps) =>
            progressAt(kind, fps, elapsedMs, closing),
          );
          expect(Math.max(...progress) - Math.min(...progress)).toBeLessThan(1e-9);
        }
      }
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
