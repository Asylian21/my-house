export type NavigationMode = "orbit" | "flight" | "walk";

export type WheelZoomGesture = "scroll" | "pinch";

export interface WheelEventSummary {
  readonly deltaY: number;
  readonly deltaMode: number;
  readonly ctrlKey: boolean;
}

/**
 * Exponential orbit zoom. Every input contributes a multiplicative factor
 * `exp(-gain * pixels)` to a target radius, so the same two-finger distance
 * feels identical at 6 m and at 60 m — the behaviour Mac trackpad users expect
 * from map applications. Trackpad scroll and pinch are reported through the
 * same wheel stream, but pinch deltas are an order of magnitude smaller, so
 * they carry their own higher gain.
 */
export const ORBIT_ZOOM = Object.freeze({
  lowerRadiusLimitM: 4.5,
  // The cadastral overview spans two full parcel rows. Keep the ordinary
  // house presets compact, but allow an explicit wide context view on mobile.
  upperRadiusLimitM: 150,
  /** Two-finger scroll and physical wheel notches, per normalised pixel. */
  scrollGainPerPx: 0.0018,
  /** Browser-synthesised pinch (wheel + ctrlKey), per normalised pixel. */
  pinchGainPerPx: 0.009,
  /** Firefox reports wheel distances in lines; one line ≈ 16 px of travel. */
  lineModePx: 16,
  pageModePx: 800,
  /** Safety clamp on a single event so momentum bursts cannot teleport. */
  maxMultiplierPerEvent: 2,
  minMultiplierPerEvent: 0.5,
  /** Framerate-independent glide half-life towards the target radius. */
  glideHalfLifeMs: 42,
  /** Snap once the camera is visually indistinguishable from the target. */
  settleEpsilonM: 0.0015,
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
    return deltaY * ORBIT_ZOOM.lineModePx;
  if (deltaMode === DOM_DELTA_PAGE) return deltaY * ORBIT_ZOOM.pageModePx;
  return deltaMode === DOM_DELTA_PIXEL ? deltaY : 0;
}

export function wheelZoomGesture({ ctrlKey }: WheelEventSummary): WheelZoomGesture {
  // macOS browsers report trackpad pinch as wheel events with ctrlKey set.
  // A real keyboard-ctrl scroll is indistinguishable; treating it as pinch
  // keeps both fast, which matches user intent in either case.
  return ctrlKey ? "pinch" : "scroll";
}

/** Multiplicative radius change for one wheel event; >1 zooms out. */
export function orbitZoomMultiplier(
  pixels: number,
  gesture: WheelZoomGesture,
): number {
  const gain =
    gesture === "pinch"
      ? ORBIT_ZOOM.pinchGainPerPx
      : ORBIT_ZOOM.scrollGainPerPx;
  // Positive deltaY (scroll towards you / closing pinch) moves the camera
  // back, matching the previous natural-direction behaviour.
  const raw = Math.exp(gain * pixels);
  return Math.max(
    ORBIT_ZOOM.minMultiplierPerEvent,
    Math.min(ORBIT_ZOOM.maxMultiplierPerEvent, raw),
  );
}

export function clampOrbitRadius(radiusM: number): number {
  return Math.max(
    ORBIT_ZOOM.lowerRadiusLimitM,
    Math.min(ORBIT_ZOOM.upperRadiusLimitM, radiusM),
  );
}

/** Exponential glide used by the render loop; exact at any frame rate. */
export function easeOrbitRadius(
  currentM: number,
  targetM: number,
  deltaMs: number,
): number {
  // Exponential blending is unconditionally stable: a long frame gap simply
  // converges further towards the target instead of overshooting it.
  const seconds = Math.max(0, Number.isFinite(deltaMs) ? deltaMs : 0) / 1000;
  const blend = 1 - Math.pow(0.5, seconds / (ORBIT_ZOOM.glideHalfLifeMs / 1000));
  return currentM + (targetM - currentM) * blend;
}

export interface OrbitZoomStep {
  readonly radiusM: number;
  readonly settled: boolean;
}

/**
 * Advances one zoom frame and snaps exactly to the target at the end. Keeping
 * the settled state explicit prevents an idle timer from discarding the last
 * part of a Mac trackpad gesture before the camera reaches its target.
 */
export function stepOrbitZoom(
  currentM: number,
  targetM: number,
  deltaMs: number,
): OrbitZoomStep {
  const target = clampOrbitRadius(targetM);
  const radius = easeOrbitRadius(currentM, target, deltaMs);
  if (Math.abs(target - radius) <= ORBIT_ZOOM.settleEpsilonM) {
    return { radiusM: target, settled: true };
  }
  return { radiusM: radius, settled: false };
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

/**
 * Temporal and depth-stability contract for the exterior reality view.
 *
 * These values deliberately live beside the camera/render profile instead of
 * being scattered through the Babylon scene. The scene is large enough that
 * millimetre-scale coplanar layers, an aggressive shadow bias, or animated
 * post-process noise all read as crawling textures while the orbit camera
 * moves.
 */
export const EXTERIOR_RENDER_STABILITY = Object.freeze({
  /** Keep the orbit depth buffer precise without clipping the 4.5 m close view. */
  orbitNearClipM: 0.3,
  /** Constant depth bias for the 2K/1K cascaded PCF shadow maps. */
  shadowBias: 0.0007,
  /** World-normal offset: removes facade/roof self-shadow acne at grazing angles. */
  shadowNormalBiasM: 0.025,
  /** Softly cross-fade cascade boundaries instead of exposing a moving seam. */
  shadowCascadeBlendPercentage: 0.18,
  /** Film grain must never animate over architectural materials. */
  filmGrainEnabled: false,
  filmGrainAnimated: false,
  /** Suppress highlight sparkle on roof seams and normal-mapped materials. */
  pbrSpecularAntiAliasingEnabled: true,
  /** Doors and the garage gate move, so CSM caster bounds must stay live. */
  freezeDynamicShadowCasterBounds: false,
  /** Broad context surface below roads, lawns and every designed hardscape. */
  contextTerrainElevationM: -0.2,
  /** One shared road datum prevents a 1 mm seam between adjacent polygons. */
  roadContextSurfaceElevationM: -0.115,
  /** Lawn base is recessed below gravel, mulch and graded access surfaces. */
  parcelGrassElevationM: -0.065,
  /** Minimum intentional gap for overlapping opaque landscape layers. */
  minimumOpaqueLayerSeparationM: 0.018,
  /** Sub-pixel standing seams disappear before they can sparkle at parcel scale. */
  roofSeamVisibilityDistanceM: 36,
});

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
    // A restrained pass preserves joinery edges without amplifying roof,
    // paving and foliage mip transitions during camera motion.
    sharpenEdgeAmount: tier === "ULTRA" ? 0.05 : 0.035,
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

/**
 * Walkthrough mode: a person standing on the floor slab. Horizontal motion
 * only — the eye height is pinned above the floor under the camera, the
 * vertical flight commands are ignored and wall collisions are resolved by
 * the renderer's collider around this kinematic step.
 */
export const WALK_EYE_HEIGHT_M = 1.65;
export const WALK_SPEED_MPS = Object.freeze({
  precision: 0.5,
  normal: 1.55,
  boost: 3.6,
});
/**
 * Third-person chase camera and the walker's motion feel: short
 * acceleration and turning time constants give an immediate but smooth,
 * inertia-free-feeling response (no GTA-style drift or foot sliding).
 */
export const WALK_CAMERA = Object.freeze({
  /** Comfortable indoor distance requested by the user. */
  radiusM: 2.6,
  /** Wheel/pinch limits. Obstruction may compress below this range. */
  minRadiusM: 0.75,
  maxRadiusM: 4.5,
  /** Near-first-person fallback used only while a wall blocks the boom. */
  obstructionMinRadiusM: 0.08,
  betaRad: 1.32,
  lowerBetaRad: 0.93,
  upperBetaRad: 1.5,
  targetHeightM: 1.4,
  closeTargetHeightM: 1.62,
  /** Target smoothing is capped as well, so it never trails into a partition. */
  followTauS: 0.03,
  maxTargetLagM: 0.055,
  turnTauS: 0.075,
  accelTauS: 0.09,
  decelTauS: 0.055,
  /** Idle time after the last drag before the camera drifts back behind the walker. */
  recenterDelayS: 0.58,
  recenterTauS: 0.44,
  rotationInertia: 0.58,
  angularSensibilityX: 820,
  angularSensibilityY: 920,
  collisionProbeRadiusM: 0.17,
  collisionPaddingM: 0.09,
  collisionHysteresisM: 0.025,
  recoveryHalfLifeMs: 120,
  avatarFadeNearM: 0.85,
  avatarFadeFarM: 1.25,
  /**
   * Babylon stops a collision retry below 10 * CollisionsEpsilon in
   * ellipsoid space. Batch smaller render-frame displacements so a 45-degree
   * slide still clears that floor with the 220 mm horizontal radius.
   */
  minCollisionSolveDistanceM: 0.004,
  /** Bound latency when inputs cancel before reaching the distance floor. */
  maxCollisionBatchMs: 50,
  /** Rejected motion retained for a shallow slide, bounded below one substep. */
  maxRejectedCollisionCarryM: 0.025,
  /** Carry is stale once a new input turns at least 60 degrees away from it. */
  rejectedCarryResetDirectionCos: 0.5,
  maxMoveSubstepM: 0.05,
});

/**
 * Shared surface/environment policy for the walkthrough. The collider follows
 * the resolved surface exactly; only the eye/chase target is damped so ramps
 * and small thresholds read naturally without letting the feet float.
 */
export const WALK_SURFACE = Object.freeze({
  maxStepUpM: 0.22,
  maxDropM: 0.78,
  probeHeadroomM: 0.035,
  cameraRiseHalfLifeMs: 58,
  cameraFallHalfLifeMs: 86,
  maxCameraLagM: 0.16,
  /** Indoor cap is applied without overwriting the user's requested zoom. */
  indoorCameraMaxRadiusM: 1.9,
  environmentHalfLifeMs: 170,
  /** A single blocked heading is a wall, not a reason to teleport. */
  autoRecoveryBlockedS: 0.52,
  autoRecoveryCooldownS: 1.35,
  autoRecoveryAttemptWindowS: 0.9,
  autoRecoveryMinRewindM: 0.08,
  autoRecoveryMaxRewindM: 0.7,
  escapeDirectionSectorCount: 8,
  escapeDirectionMinimumGap: 2,
});

export type WalkSurfaceKind = "interior" | "exterior" | "terrain";

/** Smoothly blends the environment profile; 1 is indoors, 0 is outdoors. */
export function stepWalkIndoorBlend(
  currentBlend: number,
  indoors: boolean,
  deltaMs: number,
): number {
  const current = clamp(Number.isFinite(currentBlend) ? currentBlend : 0, 0, 1);
  const target = indoors ? 1 : 0;
  const elapsed = clamp(Number.isFinite(deltaMs) ? deltaMs : 0, 0, 50);
  const blend = 1 - Math.pow(0.5, elapsed / WALK_SURFACE.environmentHalfLifeMs);
  const next = current + (target - current) * blend;
  return Math.abs(target - next) <= 0.002 ? target : next;
}

/** Environment-aware boom length that always preserves a closer user zoom. */
export function walkCameraRadiusForEnvironment(
  requestedRadiusM: number,
  indoorBlend: number,
): number {
  const requested = clamp(
    Number.isFinite(requestedRadiusM) ? requestedRadiusM : WALK_CAMERA.radiusM,
    WALK_CAMERA.minRadiusM,
    WALK_CAMERA.maxRadiusM,
  );
  const indoors = clamp(Number.isFinite(indoorBlend) ? indoorBlend : 0, 0, 1);
  const indoorTarget = Math.min(
    requested,
    WALK_SURFACE.indoorCameraMaxRadiusM,
  );
  return requested + (indoorTarget - requested) * indoors;
}

/** Frame-rate-independent eye/target height over a surface transition. */
export function stepWalkCameraSurfaceHeight(
  currentY: number,
  surfaceY: number,
  deltaMs: number,
): number {
  const target = Number.isFinite(surfaceY) ? surfaceY : 0;
  const current = Number.isFinite(currentY) ? currentY : target;
  const elapsed = clamp(Number.isFinite(deltaMs) ? deltaMs : 0, 0, 50);
  const halfLifeMs =
    target >= current
      ? WALK_SURFACE.cameraRiseHalfLifeMs
      : WALK_SURFACE.cameraFallHalfLifeMs;
  const blend = 1 - Math.pow(0.5, elapsed / halfLifeMs);
  const eased = current + (target - current) * blend;
  return clamp(
    eased,
    target - WALK_SURFACE.maxCameraLagM,
    target + WALK_SURFACE.maxCameraLagM,
  );
}

/** Quantised attempted heading used to distinguish a wall from a real trap. */
export function addWalkEscapeDirection(
  directionMask: number,
  direction: { readonly x: number; readonly z: number },
): number {
  const length = Math.hypot(direction.x, direction.z);
  if (!Number.isFinite(length) || length <= 1e-5) return directionMask >>> 0;
  const sectors = WALK_SURFACE.escapeDirectionSectorCount;
  const angle = Math.atan2(direction.z / length, direction.x / length);
  const sector =
    ((Math.round((angle / (Math.PI * 2)) * sectors) % sectors) + sectors) %
    sectors;
  return (directionMask | (1 << sector)) >>> 0;
}

/** At least two materially different failed headings are required. */
export function hasDiverseWalkEscapeDirections(directionMask: number): boolean {
  const sectors = WALK_SURFACE.escapeDirectionSectorCount;
  const active: number[] = [];
  for (let sector = 0; sector < sectors; sector += 1) {
    if ((directionMask & (1 << sector)) !== 0) active.push(sector);
  }
  for (let left = 0; left < active.length; left += 1) {
    for (let right = left + 1; right < active.length; right += 1) {
      const raw = Math.abs(active[left] - active[right]);
      const circularGap = Math.min(raw, sectors - raw);
      if (circularGap >= WALK_SURFACE.escapeDirectionMinimumGap) return true;
    }
  }
  return false;
}

export function shouldAutoRecoverWalk({
  blockedForS,
  directionMask,
  rewindDistanceM,
  cooldownS,
  hasDirectionalInput,
}: {
  readonly blockedForS: number;
  readonly directionMask: number;
  readonly rewindDistanceM: number;
  readonly cooldownS: number;
  readonly hasDirectionalInput: boolean;
}): boolean {
  return (
    hasDirectionalInput &&
    Number.isFinite(blockedForS) &&
    blockedForS >= WALK_SURFACE.autoRecoveryBlockedS &&
    hasDiverseWalkEscapeDirections(directionMask) &&
    Number.isFinite(rewindDistanceM) &&
    rewindDistanceM >= WALK_SURFACE.autoRecoveryMinRewindM &&
    rewindDistanceM <= WALK_SURFACE.autoRecoveryMaxRewindM &&
    (!Number.isFinite(cooldownS) || cooldownS <= 0)
  );
}
/** Radii of the walker's collision ellipsoid (half extents in metres). */
export const WALK_COLLISION_ELLIPSOID_M = Object.freeze({
  x: 0.22,
  y: 0.8,
  z: 0.22,
});
export const WALK_COLLISION_OFFSET_M = Object.freeze({
  x: 0,
  y: 0.82,
  z: 0,
});

export interface WalkCameraBoomInput {
  readonly desiredRadiusM: number;
  readonly currentRadiusM: number;
  readonly hitDistanceM: number | null;
  readonly deltaMs: number;
  readonly wasObstructed: boolean;
}

export interface RayAabbInput {
  readonly origin: {
    readonly x: number;
    readonly y: number;
    readonly z: number;
  };
  readonly direction: {
    readonly x: number;
    readonly y: number;
    readonly z: number;
  };
  readonly minimum: {
    readonly x: number;
    readonly y: number;
    readonly z: number;
  };
  readonly maximum: {
    readonly x: number;
    readonly y: number;
    readonly z: number;
  };
  readonly maxDistanceM: number;
  readonly paddingM?: number;
}

/** Distance to a world-axis-aligned box, or null when the finite ray misses. */
export function rayAabbDistance({
  origin,
  direction,
  minimum,
  maximum,
  maxDistanceM,
  paddingM = 0,
}: RayAabbInput): number | null {
  const directionLength = Math.hypot(direction.x, direction.y, direction.z);
  if (!Number.isFinite(directionLength) || directionLength < 1e-9) return null;
  const limit = Number.isFinite(maxDistanceM) ? Math.max(0, maxDistanceM) : 0;
  const padding = Number.isFinite(paddingM) ? clamp(paddingM, 0, 1) : 0;
  let near = 0;
  let far = limit;

  // This helper also runs in the chase-camera broad phase. Keep the slab
  // calculation scalar and allocation-free: creating axis/value arrays here
  // produced visible garbage-collection bumps while sprinting indoors.
  const xSpeed = direction.x / directionLength;
  const xLow = Math.min(minimum.x, maximum.x) - padding;
  const xHigh = Math.max(minimum.x, maximum.x) + padding;
  if (
    !Number.isFinite(origin.x) ||
    !Number.isFinite(xSpeed) ||
    !Number.isFinite(xLow) ||
    !Number.isFinite(xHigh)
  ) return null;
  if (Math.abs(xSpeed) < 1e-9) {
    if (origin.x < xLow || origin.x > xHigh) return null;
  } else {
    let entry = (xLow - origin.x) / xSpeed;
    let exit = (xHigh - origin.x) / xSpeed;
    if (entry > exit) {
      const swap = entry;
      entry = exit;
      exit = swap;
    }
    near = Math.max(near, entry);
    far = Math.min(far, exit);
    if (near > far) return null;
  }

  const ySpeed = direction.y / directionLength;
  const yLow = Math.min(minimum.y, maximum.y) - padding;
  const yHigh = Math.max(minimum.y, maximum.y) + padding;
  if (
    !Number.isFinite(origin.y) ||
    !Number.isFinite(ySpeed) ||
    !Number.isFinite(yLow) ||
    !Number.isFinite(yHigh)
  ) return null;
  if (Math.abs(ySpeed) < 1e-9) {
    if (origin.y < yLow || origin.y > yHigh) return null;
  } else {
    let entry = (yLow - origin.y) / ySpeed;
    let exit = (yHigh - origin.y) / ySpeed;
    if (entry > exit) {
      const swap = entry;
      entry = exit;
      exit = swap;
    }
    near = Math.max(near, entry);
    far = Math.min(far, exit);
    if (near > far) return null;
  }

  const zSpeed = direction.z / directionLength;
  const zLow = Math.min(minimum.z, maximum.z) - padding;
  const zHigh = Math.max(minimum.z, maximum.z) + padding;
  if (
    !Number.isFinite(origin.z) ||
    !Number.isFinite(zSpeed) ||
    !Number.isFinite(zLow) ||
    !Number.isFinite(zHigh)
  ) return null;
  if (Math.abs(zSpeed) < 1e-9) {
    if (origin.z < zLow || origin.z > zHigh) return null;
  } else {
    let entry = (zLow - origin.z) / zSpeed;
    let exit = (zHigh - origin.z) / zSpeed;
    if (entry > exit) {
      const swap = entry;
      entry = exit;
      exit = swap;
    }
    near = Math.max(near, entry);
    far = Math.min(far, exit);
    if (near > far) return null;
  }
  return near <= limit ? near : null;
}

/**
 * Resolves a wall-compressed chase-camera boom without ever overwriting the
 * user's requested radius. Compression is immediate; clearing or receding
 * geometry restores the view with a short frame-rate-independent half-life.
 */
export function stepWalkCameraBoom({
  desiredRadiusM,
  currentRadiusM,
  hitDistanceM,
  deltaMs,
  wasObstructed,
}: WalkCameraBoomInput) {
  const desired = clamp(
    Number.isFinite(desiredRadiusM) ? desiredRadiusM : WALK_CAMERA.radiusM,
    WALK_CAMERA.minRadiusM,
    WALK_CAMERA.maxRadiusM,
  );
  const current = clamp(
    Number.isFinite(currentRadiusM) ? currentRadiusM : desired,
    WALK_CAMERA.obstructionMinRadiusM,
    desired,
  );
  const collisionLimit =
    typeof hitDistanceM === "number" && Number.isFinite(hitDistanceM)
      ? clamp(
          hitDistanceM - WALK_CAMERA.collisionPaddingM,
          WALK_CAMERA.obstructionMinRadiusM,
          desired,
        )
      : desired;
  const hitObstructs =
    collisionLimit < desired - WALK_CAMERA.collisionHysteresisM;

  if (hitObstructs && collisionLimit <= current) {
    return { radiusM: collisionLimit, obstructed: true } as const;
  }
  if (!hitObstructs && !wasObstructed) {
    return { radiusM: desired, obstructed: false } as const;
  }

  const target = hitObstructs ? collisionLimit : desired;
  const elapsed = clamp(Number.isFinite(deltaMs) ? deltaMs : 0, 0, 50);
  const blend = 1 - Math.pow(0.5, elapsed / WALK_CAMERA.recoveryHalfLifeMs);
  const restored = current + (target - current) * blend;
  if (!hitObstructs && Math.abs(desired - restored) <= 0.012) {
    return { radiusM: desired, obstructed: false } as const;
  }
  return { radiusM: restored, obstructed: true } as const;
}

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
  const eyeY = (Number.isFinite(floorY) ? floorY : 0) + WALK_EYE_HEIGHT_M;
  let dx = forwardX * forwardAxis + rightX * strafeAxis;
  let dz = forwardZ * forwardAxis + rightZ * strafeAxis;
  const length = Math.hypot(dx, dz);
  const bounded = {
    x: clamp(position.x, FLIGHT_BOUNDS.minX, FLIGHT_BOUNDS.maxX),
    y: eyeY,
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
    y: eyeY,
    z: clamp(bounded.z + dz * speed * seconds, FLIGHT_BOUNDS.minZ, FLIGHT_BOUNDS.maxZ),
  };
}

export interface AvatarVelocityInput {
  readonly velocity: { readonly x: number; readonly z: number };
  /** Unit ground-plane forward of the chase camera. */
  readonly forward: { readonly x: number; readonly z: number };
  readonly commands: ReadonlySet<FlightCommand>;
  readonly deltaMs: number;
  readonly boost?: boolean;
  readonly precision?: boolean;
}

/**
 * Whether an accumulated planar displacement is large enough to hand to
 * Babylon's ellipsoid collision solver. Keeping this pure makes the
 * high-refresh movement contract deterministic and regression-testable.
 */
export function shouldResolveWalkCollisionBatch(
  displacement: { readonly x: number; readonly z: number },
  elapsedMs: number,
): boolean {
  const x = Number.isFinite(displacement.x) ? displacement.x : 0;
  const z = Number.isFinite(displacement.z) ? displacement.z : 0;
  const distanceM = Math.hypot(x, z);
  if (distanceM >= WALK_CAMERA.minCollisionSolveDistanceM) return true;
  return (
    distanceM >= WALK_CAMERA.minCollisionSolveDistanceM * 0.5 &&
    Number.isFinite(elapsedMs) &&
    elapsedMs >= WALK_CAMERA.maxCollisionBatchMs
  );
}

/**
 * Release clears settled carry; active input clears carry after a meaningful
 * direction change. The normalized dot keeps this independent of speed and
 * preserves accumulation while the player continues in the same direction.
 */
export function shouldResetWalkCollisionCarry(
  hasDirectionalInput: boolean,
  velocity: { readonly x: number; readonly z: number },
  carry: { readonly x: number; readonly z: number } = { x: 0, z: 0 },
): boolean {
  const velocityM = Math.hypot(velocity.x, velocity.z);
  if (!hasDirectionalInput) return velocityM <= 1e-4;
  const carryM = Math.hypot(carry.x, carry.z);
  if (velocityM <= 1e-4 || carryM <= 1e-7) return false;
  const directionCos =
    (carry.x * velocity.x + carry.z * velocity.z) / (carryM * velocityM);
  return directionCos <= WALK_CAMERA.rejectedCarryResetDirectionCos;
}

/**
 * Removes the velocity component rejected by a solved collision while
 * retaining the terminal tangent speed. This keeps a real wall slide without
 * re-introducing the wall-normal component on the following frame.
 */
export function resolveWalkCollisionVelocity({
  terminal,
  intended,
  moved,
  elapsedMs,
}: {
  readonly terminal: { readonly x: number; readonly z: number };
  readonly intended: { readonly x: number; readonly z: number };
  readonly moved: { readonly x: number; readonly z: number };
  readonly elapsedMs: number;
}): { x: number; z: number } {
  const correctionX = intended.x - moved.x;
  const correctionZ = intended.z - moved.z;
  const correctionM = Math.hypot(correctionX, correctionZ);
  if (correctionM <= 1e-5) return { x: terminal.x, z: terminal.z };
  const seconds = clamp(finitePositive(elapsedMs, 0), 0, 50_000) / 1000;
  if (Math.hypot(moved.x, moved.z) <= 1e-5 || seconds <= 1e-5) {
    return {
      x: seconds > 1e-5 ? moved.x / seconds : 0,
      z: seconds > 1e-5 ? moved.z / seconds : 0,
    };
  }
  const normalX = correctionX / correctionM;
  const normalZ = correctionZ / correctionM;
  const rejectedSpeed = Math.max(
    0,
    terminal.x * normalX + terminal.z * normalZ,
  );
  return {
    x: terminal.x - normalX * rejectedSpeed,
    z: terminal.z - normalZ * rejectedSpeed,
  };
}

/**
 * Camera-relative walking velocity with exponential acceleration and
 * braking. Commands are resolved against the camera forward (W walks where
 * the camera looks, A/D strafe), so the walker always reads as "push the
 * stick, go that way".
 */
export function integrateAvatarVelocity({
  velocity,
  forward,
  commands,
  deltaMs,
  boost = false,
  precision = false,
}: AvatarVelocityInput): { x: number; z: number } {
  const length = Math.hypot(forward.x, forward.z);
  const fx = length > 1e-6 ? forward.x / length : 0;
  const fz = length > 1e-6 ? forward.z / length : -1;
  const rx = -fz;
  const rz = fx;
  const forwardAxis =
    Number(commands.has("forward")) - Number(commands.has("backward"));
  const strafeAxis =
    Number(commands.has("right")) - Number(commands.has("left"));
  let dx = fx * forwardAxis + rx * strafeAxis;
  let dz = fz * forwardAxis + rz * strafeAxis;
  const wish = Math.hypot(dx, dz);
  const speed = precision
    ? WALK_SPEED_MPS.precision
    : boost
      ? WALK_SPEED_MPS.boost
      : WALK_SPEED_MPS.normal;
  if (wish > 1e-9) {
    dx = (dx / wish) * speed;
    dz = (dz / wish) * speed;
  } else {
    dx = 0;
    dz = 0;
  }
  const seconds = clamp(finitePositive(deltaMs, 0), 0, 50) / 1000;
  const tau = wish > 1e-9 ? WALK_CAMERA.accelTauS : WALK_CAMERA.decelTauS;
  const blend = 1 - Math.exp(-seconds / tau);
  const vx = velocity.x + (dx - velocity.x) * blend;
  const vz = velocity.z + (dz - velocity.z) * blend;
  return {
    x: Math.abs(vx) < 1e-4 ? 0 : vx,
    z: Math.abs(vz) < 1e-4 ? 0 : vz,
  };
}
