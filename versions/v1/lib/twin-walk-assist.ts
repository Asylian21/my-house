/**
 * Walkthrough movement assistance.
 *
 * Two pure, frame-rate-independent helpers that make a 440 mm collision
 * capsule feel natural in 680–780 mm framed openings and 1.0 m halls:
 *
 * 1. Doorway funnel — while the walker approaches a passage, the intended
 *    velocity is rotated a little toward the opening's centreline. The speed
 *    is preserved, only the heading changes, so the walker glides through the
 *    lining instead of clipping a jamb with a shoulder.
 * 2. Blocked-corner deflection — candidate headings the collider may try when
 *    a move is almost fully rejected (a jamb edge, a wardrobe corner). The
 *    controller accepts a candidate only when most of the original intent is
 *    still honoured, so a flat wall stays a wall and the auto-recovery
 *    contract remains untouched.
 */

export interface PlanarVector {
  readonly x: number;
  readonly z: number;
}

/** Clear walk-through envelope of a door opening in world metres. */
export interface WalkPassage {
  readonly id: string;
  /** Opening centre in the wall's mid-plane. */
  readonly center: PlanarVector;
  /** Unit vector along the wall (across the opening). */
  readonly along: PlanarVector;
  /** Half of the clear opening between the frame linings. */
  readonly halfClearWidthM: number;
  /** Half of the wall thickness the passage runs through. */
  readonly halfDepthM: number;
}

export const DOORWAY_ASSIST = Object.freeze({
  /** The funnel begins this far in front of the wall plane. */
  approachDistanceM: 1.15,
  /** Full steering strength is reached this close to the wall plane. */
  fullStrengthDistanceM: 0.45,
  /** Lateral capture beyond the clear opening on each side. */
  lateralCaptureMarginM: 0.32,
  /** Heading must point through the opening (cos 60°) before assisting. */
  minApproachCos: 0.5,
  /** Proportional lateral correction per metre of centreline offset. */
  gainPerSecond: 3.4,
  maxLateralSpeedMps: 0.62,
  /** Below this speed the walker is repositioning, not walking through. */
  minSpeedMps: 0.15,
  /** Headings tried, in order, when a move is almost fully rejected. */
  deflectionAnglesRad: Object.freeze([0.5, -0.5, 1.0, -1.0]),
  /** Original progress below which deflection is attempted. */
  deflectProgressBelow: 0.35,
  /** Share of the original intent a deflected move must still achieve. */
  deflectMinimumProgress: 0.5,
});

const finite = (value: number, fallback = 0) =>
  Number.isFinite(value) ? value : fallback;

/**
 * Lateral velocity correction toward the centreline of one passage, or null
 * when the walker is not approaching that opening.
 */
export function doorwayAssistCorrection(
  velocity: PlanarVector,
  position: PlanarVector,
  passage: WalkPassage,
): PlanarVector | null {
  const speed = Math.hypot(finite(velocity.x), finite(velocity.z));
  if (speed < DOORWAY_ASSIST.minSpeedMps) return null;
  const alongLength = Math.hypot(passage.along.x, passage.along.z);
  if (!(alongLength > 1e-9)) return null;
  const alongX = passage.along.x / alongLength;
  const alongZ = passage.along.z / alongLength;
  // Wall normal (either orientation; only the magnitude matters below).
  const normalX = -alongZ;
  const normalZ = alongX;
  const relX = finite(position.x) - passage.center.x;
  const relZ = finite(position.z) - passage.center.z;
  const lateral = relX * alongX + relZ * alongZ;
  const across = relX * normalX + relZ * normalZ;
  const depth = Math.abs(across);
  if (depth > passage.halfDepthM + DOORWAY_ASSIST.approachDistanceM) return null;
  if (
    Math.abs(lateral) >
    passage.halfClearWidthM + DOORWAY_ASSIST.lateralCaptureMarginM
  ) {
    return null;
  }
  // Heading must carry the walker toward (or through) the wall plane.
  const approachSign = across > 1e-6 ? -1 : across < -1e-6 ? 1 : 0;
  const headingAcross = (velocity.x * normalX + velocity.z * normalZ) / speed;
  if (approachSign !== 0) {
    if (headingAcross * approachSign < DOORWAY_ASSIST.minApproachCos) return null;
  } else if (Math.abs(headingAcross) < DOORWAY_ASSIST.minApproachCos) {
    return null;
  }
  const outside = Math.max(0, depth - passage.halfDepthM);
  const strength =
    outside <= DOORWAY_ASSIST.fullStrengthDistanceM
      ? 1
      : 1 -
        (outside - DOORWAY_ASSIST.fullStrengthDistanceM) /
          (DOORWAY_ASSIST.approachDistanceM - DOORWAY_ASSIST.fullStrengthDistanceM);
  if (strength <= 0) return null;
  const desiredLateralSpeed = Math.max(
    -DOORWAY_ASSIST.maxLateralSpeedMps,
    Math.min(
      DOORWAY_ASSIST.maxLateralSpeedMps,
      -lateral * DOORWAY_ASSIST.gainPerSecond,
    ),
  ) * strength;
  const currentLateralSpeed = velocity.x * alongX + velocity.z * alongZ;
  const delta = desiredLateralSpeed - currentLateralSpeed;
  if (Math.abs(delta) < 1e-6) return null;
  return { x: alongX * delta, z: alongZ * delta };
}

/**
 * Applies the strongest applicable doorway correction and re-normalises the
 * result to the original speed, so the assist only ever turns the walker.
 */
export function steerVelocityThroughPassages(
  velocity: PlanarVector,
  position: PlanarVector,
  passages: readonly WalkPassage[],
): PlanarVector {
  const sanitized = { x: finite(velocity.x), z: finite(velocity.z) };
  const speed = Math.hypot(sanitized.x, sanitized.z);
  if (speed < DOORWAY_ASSIST.minSpeedMps || passages.length === 0) {
    return sanitized;
  }
  let best: PlanarVector | null = null;
  let bestMagnitude = 0;
  for (const passage of passages) {
    const correction = doorwayAssistCorrection(sanitized, position, passage);
    if (!correction) continue;
    const magnitude = Math.hypot(correction.x, correction.z);
    if (magnitude > bestMagnitude) {
      best = correction;
      bestMagnitude = magnitude;
    }
  }
  if (!best) return sanitized;
  const steeredX = sanitized.x + best.x;
  const steeredZ = sanitized.z + best.z;
  const steeredSpeed = Math.hypot(steeredX, steeredZ);
  if (steeredSpeed < 1e-9) return sanitized;
  return {
    x: (steeredX / steeredSpeed) * speed,
    z: (steeredZ / steeredSpeed) * speed,
  };
}

/** Rotates a planar displacement about the vertical axis. */
export function rotatePlanar(vector: PlanarVector, angleRad: number): PlanarVector {
  const cosine = Math.cos(angleRad);
  const sine = Math.sin(angleRad);
  return {
    x: vector.x * cosine - vector.z * sine,
    z: vector.x * sine + vector.z * cosine,
  };
}

/** Share of the original intent achieved by an actual displacement. */
export function movementProgress(
  intended: PlanarVector,
  moved: PlanarVector,
): number {
  const lengthSquared = intended.x * intended.x + intended.z * intended.z;
  if (!(lengthSquared > 1e-10)) return 1;
  return Math.max(
    0,
    Math.min(1, (moved.x * intended.x + moved.z * intended.z) / lengthSquared),
  );
}

/** Whether a rejected move is worth retrying on deflected headings. */
export function shouldAttemptDeflection(
  hasDirectionalInput: boolean,
  intendedDistanceM: number,
  progress: number,
): boolean {
  return (
    hasDirectionalInput &&
    Number.isFinite(intendedDistanceM) &&
    intendedDistanceM > 1e-5 &&
    Number.isFinite(progress) &&
    progress < DOORWAY_ASSIST.deflectProgressBelow
  );
}
