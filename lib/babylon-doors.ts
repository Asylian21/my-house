import { BATHROOM_FITOUT, INTERIOR_DOORS } from "./twin-interior";
import { POOL_TECHNOLOGY_SHAFT } from "./twin-site";

export type DoorMotionKind = "HINGED" | "SLIDING" | "OVERHEAD" | "TRAVERSAL";
export type DoorPhase = "CLOSED" | "OPENING" | "OPEN" | "CLOSING";

export interface DoorPlanarPoint {
  readonly x: number;
  readonly z: number;
  /** Optional world elevation for stacked or otherwise vertically separated closures. */
  readonly y?: number;
}

export type DoorInteractionSubject =
  | "DOOR"
  | "APPLIANCE_DOOR"
  | "ACCESS_HATCH"
  | "LADDER";

export interface DoorActorState {
  readonly position: DoorPlanarPoint;
  readonly facing: DoorPlanarPoint;
  readonly radiusM?: number;
}

export interface AnimatedDoorRegistration {
  readonly id: string;
  readonly label: string;
  readonly kind: DoorMotionKind;
  readonly interactionPoint: DoorPlanarPoint;
  readonly subject?: DoorInteractionSubject;
  readonly initiallyOpen?: boolean;
  /** Optional moving/level-dependent target, used by the two ends of a ladder. */
  interactionPointAt?(progress: number): DoorPlanarPoint;
  /** Keeps a context action completely out of targeting until it is usable. */
  isInteractionEnabled?(progress: number): boolean;
  apply(progress: number, handleDepression: number): void;
  canOpen?(actor: DoorActorState, progress?: number): boolean;
  canClose?(actor: DoorActorState, progress?: number): boolean;
}

export interface DoorInteractionSnapshot {
  readonly id: string;
  readonly label: string;
  readonly kind: DoorMotionKind;
  readonly interactionPoint: DoorPlanarPoint;
  readonly subject?: DoorInteractionSubject;
  readonly phase: DoorPhase;
  readonly action: "OPEN" | "CLOSE" | null;
  readonly distanceM: number;
  readonly blockedMessage: string | null;
}

export interface DoorDebugSnapshot {
  readonly id: string;
  readonly kind: DoorMotionKind;
  readonly phase: DoorPhase;
  readonly progress: number;
  readonly targetProgress: 0 | 1;
}

interface RuntimeDoor extends AnimatedDoorRegistration {
  progress: number;
  startProgress: number;
  targetProgress: 0 | 1;
  animationElapsedMs: number;
  animationDurationMs: number;
  blockedUntilMs: number;
}

export const DOOR_INTERACTION = Object.freeze({
  maxDistanceM: 1.9,
  nearOmnidirectionalDistanceM: 0.82,
  minimumFacingDot: Math.cos((72 * Math.PI) / 180),
  actorRadiusM: 0.22,
  maximumFrameStepMs: 50,
  openingDurationMs: 760,
  closingDurationMs: 680,
  minimumReversalDurationMs: 220,
  blockedMessageMs: 1_800,
});

export const LIFT_SLIDE_MOTION = Object.freeze({
  /** Real lift-and-slide hardware raises the loaded sash only a few millimetres. */
  sashLiftM: 0.008,
  /** Finish lifting before the visible horizontal travel becomes dominant. */
  liftCompleteProgress: 0.05,
});

/**
 * Authoritative runtime contract: every architectural door that has a real
 * movable leaf in the current house model must register exactly once.
 */
export const ARCHITECTURAL_DOOR_INVENTORY: readonly {
  readonly id: string;
  readonly kind: DoorMotionKind;
}[] = Object.freeze([
  ...INTERIOR_DOORS.map(({ id, motion }) => ({
    id,
    kind: motion === "POCKET_SLIDING" ? "SLIDING" as const : "HINGED" as const,
  })),
  { id: "FRONT-ENTRY", kind: "HINGED" },
  { id: "EAST-03", kind: "HINGED" },
  { id: "LOGGIA-DOOR", kind: "HINGED" },
  { id: "GARDEN-02", kind: "SLIDING" },
  { id: "GARDEN-03", kind: "SLIDING" },
  { id: "WING-WEST-01", kind: "SLIDING" },
  { id: "GARAGE-DOOR", kind: "OVERHEAD" },
]);

/** Interactive drum doors share the architectural controller but not its inventory. */
export const APPLIANCE_DOOR_INVENTORY: readonly {
  readonly id: string;
  readonly kind: DoorMotionKind;
}[] = Object.freeze(
  BATHROOM_FITOUT.builtIn.appliances.map(({ door }) => ({
    id: door.id,
    kind: "HINGED" as const,
  })),
);

/** The pool hatch and ladder share the contextual E/touch interaction model. */
export const POOL_ACCESS_INVENTORY: readonly {
  readonly id: string;
  readonly kind: DoorMotionKind;
}[] = Object.freeze([
  { id: POOL_TECHNOLOGY_SHAFT.hatch.id, kind: "HINGED" },
  { id: POOL_TECHNOLOGY_SHAFT.ladder.id, kind: "TRAVERSAL" },
]);

export const INTERACTIVE_DOOR_INVENTORY: readonly {
  readonly id: string;
  readonly kind: DoorMotionKind;
}[] = Object.freeze([
  ...ARCHITECTURAL_DOOR_INVENTORY,
  ...APPLIANCE_DOOR_INVENTORY,
  ...POOL_ACCESS_INVENTORY,
]);

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));

/** Quintic ease with zero velocity and acceleration at both physical stops. */
export function smootherStep01(value: number): number {
  const t = clamp01(value);
  // Floating-point evaluation can overshoot the terminal value by ~1e-15,
  // which would make the following exact stop look like a backwards frame.
  return clamp01(t * t * t * (t * (t * 6 - 15) + 10));
}

/**
 * Mechanical lift for a lift-and-slide sash. It settles completely into the
 * floor track only at the closed stop and stays lifted while it rolls.
 */
export function liftSlideSashLiftM(progress: number): number {
  const liftProgress = clamp01(
    progress / LIFT_SLIDE_MOTION.liftCompleteProgress,
  );
  return LIFT_SLIDE_MOTION.sashLiftM * smootherStep01(liftProgress);
}

export function doorInteractionPromptLabel(
  interaction: Pick<
    DoorInteractionSnapshot,
    "kind" | "subject" | "phase" | "action" | "blockedMessage"
  >,
): string {
  if (interaction.blockedMessage) return interaction.blockedMessage;
  if (interaction.subject === "ACCESS_HATCH") {
    if (interaction.phase === "OPENING") return "Otváram vstup do šachty…";
    if (interaction.phase === "CLOSING") return "Zatváram vstup do šachty…";
    if (interaction.action === "OPEN") return "Otvoriť poklop šachty";
    if (interaction.action === "CLOSE") return "Zavrieť poklop šachty";
    return "Poklop sa práve pohybuje";
  }
  if (interaction.subject === "LADDER") {
    if (interaction.phase === "OPENING") return "Zostupujem po rebríku…";
    if (interaction.phase === "CLOSING") return "Vystupujem po rebríku…";
    if (interaction.action === "OPEN") return "Zostúpiť do šachty";
    if (interaction.action === "CLOSE") return "Vystúpiť na terasu";
    return "Prebieha presun po rebríku";
  }
  if (interaction.subject === "APPLIANCE_DOOR") {
    if (interaction.phase === "OPENING") return "Otváram dvierka…";
    if (interaction.phase === "CLOSING") return "Zatváram dvierka…";
    if (interaction.action === "OPEN") return "Otvoriť dvierka";
    if (interaction.action === "CLOSE") return "Zavrieť dvierka";
    return "Dvierka sa práve pohybujú";
  }
  if (interaction.kind === "SLIDING") {
    if (interaction.phase === "OPENING") return "Odsúvam panel…";
    if (interaction.phase === "CLOSING") return "Zasúvam panel…";
    if (interaction.action === "OPEN") return "Odsunúť panel";
    if (interaction.action === "CLOSE") return "Zasunúť panel";
    return "Panel ovláda automatický manéver";
  }
  if (interaction.kind === "OVERHEAD") {
    if (interaction.phase === "OPENING") return "Zdvíham garážovú bránu…";
    if (interaction.phase === "CLOSING") return "Spúšťam garážovú bránu…";
    if (interaction.action === "OPEN") return "Otvoriť garážovú bránu";
    if (interaction.action === "CLOSE") return "Zavrieť garážovú bránu";
    return "Bránu ovláda automatický manéver";
  }
  if (interaction.phase === "OPENING") return "Otváram dvere…";
  if (interaction.phase === "CLOSING") return "Zatváram dvere…";
  if (interaction.action === "OPEN") return "Otvoriť dvere";
  if (interaction.action === "CLOSE") return "Zavrieť dvere";
  return "Dvere ovláda automatický manéver";
}

/** Handle travels first, then returns while the leaf continues moving. */
export function doorHandleDepression(normalizedTime: number): number {
  const t = clamp01(normalizedTime);
  if (t >= 0.42) return 0;
  return Math.sin((Math.PI * t) / 0.42);
}

export function doorPhase(progress: number, targetProgress: 0 | 1): DoorPhase {
  if (progress <= 0.0001 && targetProgress === 0) return "CLOSED";
  if (progress >= 0.9999 && targetProgress === 1) return "OPEN";
  return targetProgress === 1 ? "OPENING" : "CLOSING";
}

export function doorMotionDurationMs(
  kind: DoorMotionKind,
  targetProgress: 0 | 1,
): number {
  const baseDuration = targetProgress === 1
    ? DOOR_INTERACTION.openingDurationMs
    : DOOR_INTERACTION.closingDurationMs;
  const kindScale =
    kind === "OVERHEAD"
      ? 1.65
      : kind === "SLIDING"
        ? 1.25
        : kind === "TRAVERSAL"
          ? 1.4
          : 1;
  return baseDuration * kindScale;
}

function normalizedFacing(facing: DoorPlanarPoint): DoorPlanarPoint {
  const length = Math.hypot(facing.x, facing.y ?? 0, facing.z);
  return length > 1e-6
    ? {
        x: facing.x / length,
        y: (facing.y ?? 0) / length,
        z: facing.z / length,
      }
    : { x: 0, y: 0, z: 1 };
}

/** Deterministic, forgiving GTA-style target selection in front of the player. */
export function selectDoorInteractionTarget<T extends {
  readonly id: string;
  readonly interactionPoint: DoorPlanarPoint;
}>(doors: readonly T[], actor: DoorActorState): { door: T; distanceM: number } | null {
  const facing = normalizedFacing(actor.facing);
  let best: { door: T; distanceM: number; score: number } | null = null;
  for (const door of doors) {
    const dx = door.interactionPoint.x - actor.position.x;
    const dy =
      door.interactionPoint.y !== undefined && actor.position.y !== undefined
        ? door.interactionPoint.y - actor.position.y
        : 0;
    const dz = door.interactionPoint.z - actor.position.z;
    const distanceM = Math.hypot(dx, dz);
    if (distanceM > DOOR_INTERACTION.maxDistanceM) continue;
    const aimDistanceM = Math.hypot(dx, dy, dz);
    const facingDot = aimDistanceM > 1e-6
      ? (dx * facing.x + dy * (facing.y ?? 0) + dz * facing.z) / aimDistanceM
      : 1;
    if (
      distanceM > DOOR_INTERACTION.nearOmnidirectionalDistanceM &&
      facingDot < DOOR_INTERACTION.minimumFacingDot
    ) {
      continue;
    }
    const score = distanceM + (1 - facingDot) * 0.48;
    if (
      !best ||
      score < best.score - 1e-6 ||
      (Math.abs(score - best.score) <= 1e-6 && door.id < best.door.id)
    ) {
      best = { door, distanceM, score };
    }
  }
  return best ? { door: best.door, distanceM: best.distanceM } : null;
}

function pointToSegmentDistance(
  point: DoorPlanarPoint,
  start: DoorPlanarPoint,
  end: DoorPlanarPoint,
) {
  const dx = end.x - start.x;
  const dz = end.z - start.z;
  const lengthSquared = dx * dx + dz * dz;
  const t = lengthSquared > 1e-9
    ? clamp01(
        ((point.x - start.x) * dx + (point.z - start.z) * dz) /
          lengthSquared,
      )
    : 0;
  return Math.hypot(
    point.x - (start.x + dx * t),
    point.z - (start.z + dz * t),
  );
}

/**
 * Samples the complete leaf arc, preventing a close command from sweeping
 * through the walker. This is intentionally conservative near narrow doors.
 */
export function hingedDoorSweepIsClear(
  actor: DoorActorState,
  hinge: DoorPlanarPoint,
  closedEnd: DoorPlanarPoint,
  openAngleRad: number,
  leafThicknessM = 0.04,
  fromProgress = 0,
  toProgress = 1,
): boolean {
  const actorRadius = actor.radiusM ?? DOOR_INTERACTION.actorRadiusM;
  const dx = closedEnd.x - hinge.x;
  const dz = closedEnd.z - hinge.z;
  const clearance = actorRadius + leafThicknessM / 2 + 0.045;
  const samples = 18;
  for (let index = 0; index <= samples; index += 1) {
    const progress =
      clamp01(fromProgress) +
      (clamp01(toProgress) - clamp01(fromProgress)) * (index / samples);
    const angle = openAngleRad * progress;
    const cosine = Math.cos(angle);
    const sine = Math.sin(angle);
    const end = {
      x: hinge.x + dx * cosine + dz * sine,
      z: hinge.z - dx * sine + dz * cosine,
    };
    if (pointToSegmentDistance(actor.position, hinge, end) < clearance) {
      return false;
    }
  }
  return true;
}

/** Safe close check for a leaf translating within the facade plane. */
export function slidingDoorPathIsClear(
  actor: DoorActorState,
  closedCenter: DoorPlanarPoint,
  openCenter: DoorPlanarPoint,
  halfLeafWidthM: number,
  perpendicularClearanceM = 0.08,
  fromProgress = 0,
  toProgress = 1,
): boolean {
  const startProgress = clamp01(fromProgress);
  const endProgress = clamp01(toProgress);
  const fullTravelX = openCenter.x - closedCenter.x;
  const fullTravelZ = openCenter.z - closedCenter.z;
  const startCenter = {
    x: closedCenter.x + fullTravelX * startProgress,
    z: closedCenter.z + fullTravelZ * startProgress,
  };
  const endCenter = {
    x: closedCenter.x + fullTravelX * endProgress,
    z: closedCenter.z + fullTravelZ * endProgress,
  };
  const travelX = endCenter.x - startCenter.x;
  const travelZ = endCenter.z - startCenter.z;
  const travelLength = Math.hypot(travelX, travelZ);
  if (travelLength < 1e-6) {
    return Math.hypot(
      actor.position.x - startCenter.x,
      actor.position.z - startCenter.z,
    ) > halfLeafWidthM + (actor.radiusM ?? DOOR_INTERACTION.actorRadiusM);
  }
  const alongX = travelX / travelLength;
  const alongZ = travelZ / travelLength;
  const relX = actor.position.x - startCenter.x;
  const relZ = actor.position.z - startCenter.z;
  const along = relX * alongX + relZ * alongZ;
  const perpendicular = Math.abs(relX * -alongZ + relZ * alongX);
  const actorRadius = actor.radiusM ?? DOOR_INTERACTION.actorRadiusM;
  return !(
    along >= -halfLeafWidthM - actorRadius &&
    along <= travelLength + halfLeafWidthM + actorRadius &&
    perpendicular < perpendicularClearanceM + actorRadius
  );
}

export class BabylonDoorController {
  private readonly doors = new Map<string, RuntimeDoor>();
  private actor: DoorActorState | null = null;
  private clockMs = 0;

  constructor(private readonly motionScale = 1) {}

  register(registration: AnimatedDoorRegistration) {
    if (this.doors.has(registration.id)) {
      throw new Error(`Duplicate interactive door id: ${registration.id}`);
    }
    const progress = registration.initiallyOpen ? 1 : 0;
    const runtime: RuntimeDoor = {
      ...registration,
      progress,
      startProgress: progress,
      targetProgress: progress === 1 ? 1 : 0,
      animationElapsedMs: 0,
      animationDurationMs: 0,
      blockedUntilMs: 0,
    };
    this.doors.set(runtime.id, runtime);
    runtime.apply(progress, 0);
  }

  setActor(actor: DoorActorState | null) {
    this.actor = actor;
  }

  update(deltaMs: number): boolean {
    const frameMs = Math.min(
      DOOR_INTERACTION.maximumFrameStepMs,
      Math.max(0, Number.isFinite(deltaMs) ? deltaMs : 0),
    );
    this.clockMs += frameMs;
    let changed = false;
    for (const door of this.doors.values()) {
      if (door.animationDurationMs <= 0) continue;
      const pathIsClear =
        door.targetProgress === 1 ? door.canOpen : door.canClose;
      if (
        this.actor &&
        pathIsClear &&
        !pathIsClear(this.actor, door.progress)
      ) {
        // A kinematic leaf cannot rely on the avatar initiating a collision.
        // Pause it on the current frame and resume only after the sweep clears.
        door.blockedUntilMs =
          this.clockMs + DOOR_INTERACTION.blockedMessageMs;
        door.apply(door.progress, 0);
        continue;
      }
      door.animationElapsedMs = Math.min(
        door.animationDurationMs,
        door.animationElapsedMs + frameMs,
      );
      const normalized = door.animationElapsedMs / door.animationDurationMs;
      const eased = smootherStep01(normalized);
      door.progress = clamp01(
        door.startProgress +
          (door.targetProgress - door.startProgress) * eased,
      );
      if (door.animationElapsedMs >= door.animationDurationMs) {
        door.progress = door.targetProgress;
        door.animationDurationMs = 0;
      }
      door.apply(door.progress, doorHandleDepression(normalized));
      changed = true;
    }
    return changed;
  }

  private start(door: RuntimeDoor, targetProgress: 0 | 1, immediate: boolean) {
    door.startProgress = door.progress;
    door.targetProgress = targetProgress;
    door.animationElapsedMs = 0;
    if (immediate) {
      door.progress = targetProgress;
      door.animationDurationMs = 0;
      door.apply(door.progress, 0);
      return;
    }
    const reducedScale = Math.max(0.12, Math.min(1, this.motionScale));
    door.animationDurationMs = Math.max(
      90,
      DOOR_INTERACTION.minimumReversalDurationMs * reducedScale,
      doorMotionDurationMs(door.kind, targetProgress) *
        reducedScale *
        Math.abs(targetProgress - door.progress),
    );
  }

  setOpen(id: string, open: boolean, immediate = false): boolean {
    const door = this.doors.get(id);
    if (!door) return false;
    const pathIsClear = open ? door.canOpen : door.canClose;
    if (
      this.actor &&
      pathIsClear &&
      !pathIsClear(this.actor, door.progress)
    ) {
      door.blockedUntilMs = this.clockMs + DOOR_INTERACTION.blockedMessageMs;
      return false;
    }
    this.start(door, open ? 1 : 0, immediate);
    return true;
  }

  toggle(id: string): boolean {
    const door = this.doors.get(id);
    if (!door || door.animationDurationMs > 0) return false;
    return this.setOpen(id, door.progress < 0.5);
  }

  toggleInteractionTarget(id?: string): boolean {
    const target = this.targetRuntime(id);
    return target ? this.toggle(target.door.id) : false;
  }

  private targetRuntime(id?: string) {
    if (!this.actor) return null;
    const candidates = [...this.doors.values()]
      .filter((door) => door.isInteractionEnabled?.(door.progress) !== false)
      .filter((door) => !id || door.id === id)
      .map((door) => ({
        id: door.id,
        door,
        interactionPoint:
          door.interactionPointAt?.(door.progress) ?? door.interactionPoint,
      }));
    const target = selectDoorInteractionTarget(candidates, this.actor);
    return target
      ? {
          door: target.door.door,
          distanceM: target.distanceM,
          interactionPoint: target.door.interactionPoint,
        }
      : null;
  }

  getInteraction(id?: string): DoorInteractionSnapshot | null {
    const target = this.targetRuntime(id);
    if (!target) return null;
    const phase = doorPhase(target.door.progress, target.door.targetProgress);
    return {
      id: target.door.id,
      label: target.door.label,
      kind: target.door.kind,
      interactionPoint: target.interactionPoint,
      subject: target.door.subject ?? "DOOR",
      phase,
      action: phase === "CLOSED" ? "OPEN" : phase === "OPEN" ? "CLOSE" : null,
      distanceM: target.distanceM,
      blockedMessage:
        target.door.blockedUntilMs > this.clockMs
          ? target.door.subject === "APPLIANCE_DOOR"
            ? "Ustúpte z dráhy dvierok"
            : target.door.subject === "ACCESS_HATCH"
              ? "Ustúpte od poklopu šachty"
              : target.door.subject === "LADDER"
                ? "Rebrík je momentálne zablokovaný"
                : "Ustúpte z dráhy dverí"
          : null,
    };
  }

  get count() {
    return this.doors.size;
  }

  assertInventory(
    expected: readonly {
      readonly id: string;
      readonly kind: DoorMotionKind;
    }[] = INTERACTIVE_DOOR_INVENTORY,
  ) {
    const expectedById = new Map(expected.map((door) => [door.id, door.kind]));
    const missing = [...expectedById.keys()].filter((id) => !this.doors.has(id));
    const unexpected = [...this.doors.keys()].filter((id) => !expectedById.has(id));
    const wrongKind = [...this.doors.values()]
      .filter((door) => {
        const expectedKind = expectedById.get(door.id);
        return expectedKind !== undefined && expectedKind !== door.kind;
      })
      .map((door) => `${door.id}:${door.kind}`);
    if (
      expectedById.size !== expected.length ||
      missing.length > 0 ||
      unexpected.length > 0 ||
      wrongKind.length > 0
    ) {
      throw new Error(
        `Interactive door inventory mismatch; missing=[${missing.join(", ")}], unexpected=[${unexpected.join(", ")}], wrongKind=[${wrongKind.join(", ")}]`,
      );
    }
  }

  debugState(): readonly DoorDebugSnapshot[] {
    return [...this.doors.values()]
      .map((door) => ({
        id: door.id,
        kind: door.kind,
        phase: doorPhase(door.progress, door.targetProgress),
        progress: door.progress,
        targetProgress: door.targetProgress,
      }))
      .sort((left, right) => left.id.localeCompare(right.id));
  }
}
