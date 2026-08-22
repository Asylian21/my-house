export type NavigationMode = "orbit" | "flight" | "walk";

export interface WheelEventSummary {
  readonly deltaY: number;
  readonly deltaMode: number;
}

/**
 * Orbit input tuning for Babylon 9's frame-independent movement pipeline.
 * macOS already supplies momentum, so rotation, pan and zoom deliberately use
 * the same short decay instead of stacking a second application-side glide.
 */
export const ORBIT_CONTROLS = Object.freeze({
  lowerRadiusLimitM: 4.5,
  upperRadiusLimitM: 64,
  wheelDeltaPercentage: 0.012,
  zoomToMouseLocation: true,
  rotationInertia: 0.58,
  panningInertia: 0.58,
  angularSensibilityX: 1_050,
  angularSensibilityY: 1_150,
  panningSensibility: 900,
  /** Firefox reports wheel distances in lines; one line ≈ 16 px of travel. */
  lineModePx: 16,
  pageModePx: 800,
  useNaturalPinchZoom: true,
  preventBrowserGesture: true,
});

const DOM_DELTA_PIXEL = 0;
const DOM_DELTA_LINE = 1;
const DOM_DELTA_PAGE = 2;

export function normalizeWheelPixels({
  deltaY,
  deltaMode,
}: Pick<WheelEventSummary, "deltaY" | "deltaMode">): number {
  if (!Number.isFinite(deltaY)) return 0;
  if (deltaMode === DOM_DELTA_LINE)
    return deltaY * ORBIT_CONTROLS.lineModePx;
  if (deltaMode === DOM_DELTA_PAGE) return deltaY * ORBIT_CONTROLS.pageModePx;
  return deltaMode === DOM_DELTA_PIXEL ? deltaY : 0;
}

export type FlightCommand =
  | "forward"
  | "backward"
  | "left"
  | "right"
  | "up"
  | "down";

export interface RenderQualityInput {
  readonly widthPx: number;
  readonly heightPx: number;
  readonly devicePixelRatio: number;
  readonly maxMsaaSamples: number;
  readonly isCoarsePointer?: boolean;
  readonly deviceMemoryGb?: number;
}

export interface RenderQualityProfile {
  readonly tier: "ULTRA" | "HIGH";
  readonly pixelRatio: number;
  readonly hardwareScalingLevel: number;
  readonly renderWidthPx: number;
  readonly renderHeightPx: number;
  readonly renderPixelCount: number;
  readonly msaaSamples: number;
  readonly fxaaEnabled: boolean;
  readonly sharpenEdgeAmount: number;
  readonly ssaoEnabled: boolean;
  readonly ssaoRatio: number;
  readonly shadowMapSize: number;
  readonly environmentTextureSize: number;
  readonly anisotropy: number;
}

const MAX_PIXEL_RATIO = 2;
const MIN_SUPERSAMPLED_RATIO = 1.5;
const MAX_RENDER_PIXELS = 12_000_000;
const ULTRA_RENDER_PIXELS = 7_000_000;
/** Below this surface area an 8× MSAA resolve stays affordable on desktops. */
const ULTRA_MSAA8_RENDER_PIXELS = 4_500_000;

const finitePositive = (value: number, fallback: number) =>
  Number.isFinite(value) && value > 0 ? value : fallback;

export function deriveRenderQualityProfile({
  widthPx,
  heightPx,
  devicePixelRatio,
  maxMsaaSamples,
  isCoarsePointer = false,
  deviceMemoryGb,
}: RenderQualityInput): RenderQualityProfile {
  const width = Math.max(1, Math.round(finitePositive(widthPx, 1)));
  const height = Math.max(1, Math.round(finitePositive(heightPx, 1)));
  const nativeRatio = Math.min(
    MAX_PIXEL_RATIO,
    finitePositive(devicePixelRatio, 1),
  );
  const desiredRatio = Math.max(MIN_SUPERSAMPLED_RATIO, nativeRatio);
  const pixelBudgetRatio = Math.sqrt(MAX_RENDER_PIXELS / (width * height));
  const pixelRatio = Math.max(
    1,
    Math.min(desiredRatio, pixelBudgetRatio, MAX_PIXEL_RATIO),
  );
  const renderWidthPx = Math.round(width * pixelRatio);
  const renderHeightPx = Math.round(height * pixelRatio);
  const renderPixelCount = renderWidthPx * renderHeightPx;
  const supportedMsaa = Math.max(
    1,
    Math.floor(finitePositive(maxMsaaSamples, 1)),
  );
  const hasConstrainedMemory =
    typeof deviceMemoryGb === "number" &&
    Number.isFinite(deviceMemoryGb) &&
    deviceMemoryGb > 0 &&
    deviceMemoryGb < 8;
  const tier =
    !isCoarsePointer &&
    !hasConstrainedMemory &&
    renderPixelCount <= ULTRA_RENDER_PIXELS &&
    supportedMsaa >= 2
      ? "ULTRA"
      : "HIGH";
  const msaaTarget =
    tier === "ULTRA"
      ? renderPixelCount <= ULTRA_MSAA8_RENDER_PIXELS && supportedMsaa >= 8
        ? 8
        : 4
      : 2;
  const msaaSamples = Math.min(msaaTarget, supportedMsaa);

  return {
    tier,
    pixelRatio,
    hardwareScalingLevel: 1 / pixelRatio,
    renderWidthPx,
    renderHeightPx,
    renderPixelCount,
    msaaSamples,
    // FXAA is a fallback only. At Retina density it softens fine facade and
    // fence edges more than it helps them.
    fxaaEnabled: msaaSamples < 2 && pixelRatio <= MIN_SUPERSAMPLED_RATIO,
    sharpenEdgeAmount: tier === "ULTRA" ? 0.12 : 0.08,
    ssaoEnabled: tier === "ULTRA",
    ssaoRatio: tier === "ULTRA" ? 1 : 0,
    // Four stabilized cascades provide materially more useful texel density
    // than one oversized map. 2K/1K per cascade also keeps GPU memory bounded.
    shadowMapSize: tier === "ULTRA" ? 2048 : 1024,
    // The reflection cube is created once, so keep this invariant across
    // responsive tier changes. A dedicated 2K source keeps conversion memory
    // bounded while preserving the full 512 px cube on every display.
    environmentTextureSize: 512,
    anisotropy: 16,
  };
}

export const FLIGHT_BOUNDS = Object.freeze({
  // These limits include every built-in orbit preset and the orbit camera's
  // maximum radius, so switching to flight does not reframe a valid view.
  minX: -96,
  maxX: 96,
  minY: 0.8,
  maxY: 92,
  minZ: -96,
  maxZ: 96,
});

export const FLIGHT_SPEED_MPS = Object.freeze({
  precision: 0.6,
  normal: 2.4,
  boost: 6,
});

export interface FlightPosition {
  readonly x: number;
  readonly y: number;
  readonly z: number;
}

export interface FlightMotionInput {
  readonly position: FlightPosition;
  readonly heading: { readonly x: number; readonly z: number };
  readonly commands: ReadonlySet<FlightCommand>;
  readonly deltaMs: number;
  readonly boost?: boolean;
  readonly precision?: boolean;
}

export function flightCommandForCode(code: string): FlightCommand | null {
  switch (code) {
    case "KeyW":
    case "ArrowUp":
      return "forward";
    case "KeyS":
    case "ArrowDown":
      return "backward";
    case "KeyA":
    case "ArrowLeft":
      return "left";
    case "KeyD":
    case "ArrowRight":
      return "right";
    case "KeyE":
    case "PageUp":
      return "up";
    case "KeyQ":
    case "PageDown":
      return "down";
    default:
      return null;
  }
}

const clamp = (value: number, minimum: number, maximum: number) =>
  Math.max(minimum, Math.min(maximum, value));

/** Wheel dolly in flight mode, metres of travel per normalised pixel. */
export const FLIGHT_WHEEL_DOLLY_M_PER_PX = 0.011;
export const FLIGHT_WHEEL_DOLLY_MAX_M = 5;

export function flightWheelDollyDistanceM(pixels: number): number {
  if (!Number.isFinite(pixels)) return 0;
  const raw = pixels * FLIGHT_WHEEL_DOLLY_M_PER_PX;
  return Math.max(
    -FLIGHT_WHEEL_DOLLY_MAX_M,
    Math.min(FLIGHT_WHEEL_DOLLY_MAX_M, -raw),
  );
}

/** Moves a flight pose along an arbitrary 3-D view ray, respecting bounds. */
export function integrateFlightDolly(
  position: FlightPosition,
  direction: FlightPosition,
  distanceM: number,
): FlightPosition {
  const length = Math.hypot(direction.x, direction.y, direction.z);
  if (!Number.isFinite(distanceM) || length < 1e-6) {
    return {
      x: clamp(position.x, FLIGHT_BOUNDS.minX, FLIGHT_BOUNDS.maxX),
      y: clamp(position.y, FLIGHT_BOUNDS.minY, FLIGHT_BOUNDS.maxY),
      z: clamp(position.z, FLIGHT_BOUNDS.minZ, FLIGHT_BOUNDS.maxZ),
    };
  }
  const step = distanceM / length;
  return {
    x: clamp(position.x + direction.x * step, FLIGHT_BOUNDS.minX, FLIGHT_BOUNDS.maxX),
    y: clamp(position.y + direction.y * step, FLIGHT_BOUNDS.minY, FLIGHT_BOUNDS.maxY),
    z: clamp(position.z + direction.z * step, FLIGHT_BOUNDS.minZ, FLIGHT_BOUNDS.maxZ),
  };
}

export function integrateFlightPosition({
  position,
  heading,
  commands,
  deltaMs,
  boost = false,
  precision = false,
}: FlightMotionInput): FlightPosition {
  const boundedPosition = {
    x: clamp(position.x, FLIGHT_BOUNDS.minX, FLIGHT_BOUNDS.maxX),
    y: clamp(position.y, FLIGHT_BOUNDS.minY, FLIGHT_BOUNDS.maxY),
    z: clamp(position.z, FLIGHT_BOUNDS.minZ, FLIGHT_BOUNDS.maxZ),
  };
  const headingLength = Math.hypot(heading.x, heading.z);
  const forwardX = headingLength > 1e-6 ? heading.x / headingLength : 0;
  const forwardZ = headingLength > 1e-6 ? heading.z / headingLength : -1;
  const rightX = -forwardZ;
  const rightZ = forwardX;
  const forwardAxis =
    Number(commands.has("forward")) - Number(commands.has("backward"));
  const strafeAxis =
    Number(commands.has("right")) - Number(commands.has("left"));
  const verticalAxis = Number(commands.has("up")) - Number(commands.has("down"));
  let dx = forwardX * forwardAxis + rightX * strafeAxis;
  let dy = verticalAxis;
  let dz = forwardZ * forwardAxis + rightZ * strafeAxis;
  const length = Math.hypot(dx, dy, dz);
  if (length < 1e-9) return boundedPosition;
  dx /= length;
  dy /= length;
  dz /= length;
  const speed = precision
    ? FLIGHT_SPEED_MPS.precision
    : boost
      ? FLIGHT_SPEED_MPS.boost
      : FLIGHT_SPEED_MPS.normal;
  const seconds = clamp(finitePositive(deltaMs, 0), 0, 50) / 1000;

  return {
    x: clamp(boundedPosition.x + dx * speed * seconds, FLIGHT_BOUNDS.minX, FLIGHT_BOUNDS.maxX),
    y: clamp(boundedPosition.y + dy * speed * seconds, FLIGHT_BOUNDS.minY, FLIGHT_BOUNDS.maxY),
    z: clamp(boundedPosition.z + dz * speed * seconds, FLIGHT_BOUNDS.minZ, FLIGHT_BOUNDS.maxZ),
  };
}

export interface PointerGestureSummary {
  readonly travelPx: number;
  readonly durationMs: number;
  readonly maximumPointers: number;
  readonly button: number;
}

export function isSelectionTap({
  travelPx,
  durationMs,
  maximumPointers,
  button,
}: PointerGestureSummary): boolean {
  return (
    button === 0 &&
    maximumPointers === 1 &&
    travelPx <= 7 &&
    durationMs <= 650
  );
}

export type PersonCameraView = "shoulder" | "close" | "first-person";

/** GTA-style chase-camera presets. Radius is still user-adjustable by wheel or pinch. */
export const PERSON_CAMERA = Object.freeze({
  shoulderRadiusM: 3.35,
  closeRadiusM: 1.75,
  firstPersonRadiusM: 0.18,
  lowerRadiusLimitM: 0.16,
  upperRadiusLimitM: 4.8,
  lowerBetaLimit: 0.72,
  upperBetaLimit: 1.5,
  targetHeightM: 1.43,
  firstPersonTargetHeightM: 1.64,
  // A view-matrix composition offset keeps the actor over one shoulder while
  // the physical boom still starts at the centre of the head. That prevents
  // the collision ray from starting inside a nearby wall.
  shoulderScreenOffsetM: 0.28,
  closeShoulderScreenOffsetM: 0.12,
  fieldOfViewRad: 1.02,
  wheelDeltaPercentage: 0.018,
  rotationInertia: 0.5,
  angularSensibilityX: 820,
  angularSensibilityY: 920,
  collisionRadiusM: 0.18,
});

export interface PersonCameraBoomInput {
  readonly desiredRadiusM: number;
  readonly currentRadiusM: number;
  readonly hitDistanceM: number | null;
  readonly deltaMs: number;
  readonly wasObstructed: boolean;
  readonly reduceMotion?: boolean;
}

/** Resolves a wall-compressed chase boom without losing the user's radius. */
export function stepPersonCameraBoom({
  desiredRadiusM,
  currentRadiusM,
  hitDistanceM,
  deltaMs,
  wasObstructed,
  reduceMotion = false,
}: PersonCameraBoomInput) {
  const desired = clamp(
    Number.isFinite(desiredRadiusM)
      ? desiredRadiusM
      : PERSON_CAMERA.shoulderRadiusM,
    PERSON_CAMERA.lowerRadiusLimitM,
    PERSON_CAMERA.upperRadiusLimitM,
  );
  const current = clamp(
    Number.isFinite(currentRadiusM) ? currentRadiusM : desired,
    PERSON_CAMERA.lowerRadiusLimitM,
    desired,
  );
  const collisionRadius =
    typeof hitDistanceM === "number" && Number.isFinite(hitDistanceM)
      ? clamp(
          hitDistanceM - PERSON_CAMERA.collisionRadiusM,
          PERSON_CAMERA.lowerRadiusLimitM,
          desired,
        )
      : desired;
  if (collisionRadius < desired - 0.01) {
    if (collisionRadius <= current || reduceMotion) {
      return {
        radiusM: collisionRadius,
        obstructed: true,
      } as const;
    }
    // A receding wall should let the boom breathe out while it is still in
    // the ray. Expanding immediately looks like a camera pop, so use the same
    // short half-life as the fully-cleared recovery path.
    const elapsed = clamp(Number.isFinite(deltaMs) ? deltaMs : 0, 0, 50);
    const blend = 1 - Math.pow(0.5, elapsed / 90);
    return {
      radiusM: current + (collisionRadius - current) * blend,
      obstructed: true,
    } as const;
  }
  if (!wasObstructed || reduceMotion) {
    return { radiusM: desired, obstructed: false } as const;
  }
  const elapsed = clamp(Number.isFinite(deltaMs) ? deltaMs : 0, 0, 50);
  const blend = 1 - Math.pow(0.5, elapsed / 90);
  const restored = current + (desired - current) * blend;
  return Math.abs(desired - restored) < 0.015
    ? ({ radiusM: desired, obstructed: false } as const)
    : ({ radiusM: restored, obstructed: true } as const);
}

export function personCameraRadius(view: PersonCameraView): number {
  if (view === "first-person") return PERSON_CAMERA.firstPersonRadiusM;
  if (view === "close") return PERSON_CAMERA.closeRadiusM;
  return PERSON_CAMERA.shoulderRadiusM;
}

export function cyclePersonCameraView(view: PersonCameraView): PersonCameraView {
  if (view === "shoulder") return "close";
  if (view === "close") return "first-person";
  return "shoulder";
}

/** Normalized shortest signed rotation from `from` to `to`. */
export function shortestAngleDelta(from: number, to: number): number {
  if (!Number.isFinite(from) || !Number.isFinite(to)) return 0;
  return Math.atan2(Math.sin(to - from), Math.cos(to - from));
}

/** Frame-rate-independent turn used by the visible avatar. */
export function easeAngleRadians(
  current: number,
  target: number,
  deltaMs: number,
  halfLifeMs = 72,
): number {
  const seconds = Math.max(0, Number.isFinite(deltaMs) ? deltaMs : 0) / 1000;
  const halfLifeSeconds = Math.max(0.001, halfLifeMs / 1000);
  const blend = 1 - Math.pow(0.5, seconds / halfLifeSeconds);
  return current + shortestAngleDelta(current, target) * blend;
}

/** Local -Z is the avatar's forward direction. */
export function walkFacingYaw(
  displacement: { readonly x: number; readonly z: number },
  fallbackYaw: number,
): number {
  if (!Number.isFinite(displacement.x) || !Number.isFinite(displacement.z)) {
    return fallbackYaw;
  }
  if (Math.hypot(displacement.x, displacement.z) < 1e-6) return fallbackYaw;
  return Math.atan2(displacement.x, -displacement.z);
}

/**
 * Walk mode uses a feet-level actor pivot. The independent chase camera owns
 * the view while this compact ellipsoid resolves walls and furniture.
 */
export const WALK_SPEED_MPS = Object.freeze({
  precision: 0.55,
  normal: 1.55,
  boost: 3.4,
});
/** Radii of the walker's collision ellipsoid (half extents in metres). */
export const WALK_COLLISION_ELLIPSOID_M = Object.freeze({
  x: 0.28,
  y: 0.84,
  z: 0.28,
});
export const WALK_COLLISION_OFFSET_M = Object.freeze({
  x: 0,
  y: 0.86,
  z: 0,
});

export interface WalkMotionInput extends FlightMotionInput {
  /** Elevation of the floor under the walker, metres. */
  readonly floorY: number;
}

export function integrateWalkPosition({
  position,
  heading,
  commands,
  deltaMs,
  boost = false,
  precision = false,
  floorY,
}: WalkMotionInput): FlightPosition {
  const headingLength = Math.hypot(heading.x, heading.z);
  const forwardX = headingLength > 1e-6 ? heading.x / headingLength : 0;
  const forwardZ = headingLength > 1e-6 ? heading.z / headingLength : -1;
  const rightX = -forwardZ;
  const rightZ = forwardX;
  const forwardAxis =
    Number(commands.has("forward")) - Number(commands.has("backward"));
  const strafeAxis =
    Number(commands.has("right")) - Number(commands.has("left"));
  const actorY = Number.isFinite(floorY) ? floorY : 0;
  let dx = forwardX * forwardAxis + rightX * strafeAxis;
  let dz = forwardZ * forwardAxis + rightZ * strafeAxis;
  const length = Math.hypot(dx, dz);
  const bounded = {
    x: clamp(position.x, FLIGHT_BOUNDS.minX, FLIGHT_BOUNDS.maxX),
    y: actorY,
    z: clamp(position.z, FLIGHT_BOUNDS.minZ, FLIGHT_BOUNDS.maxZ),
  };
  if (length < 1e-9) return bounded;
  dx /= length;
  dz /= length;
  const speed = precision
    ? WALK_SPEED_MPS.precision
    : boost
      ? WALK_SPEED_MPS.boost
      : WALK_SPEED_MPS.normal;
  const seconds = clamp(finitePositive(deltaMs, 0), 0, 50) / 1000;
  return {
    x: clamp(bounded.x + dx * speed * seconds, FLIGHT_BOUNDS.minX, FLIGHT_BOUNDS.maxX),
    y: actorY,
    z: clamp(bounded.z + dz * speed * seconds, FLIGHT_BOUNDS.minZ, FLIGHT_BOUNDS.maxZ),
  };
}
