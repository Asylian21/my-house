export type NavigationMode = "orbit" | "flight";

export const ORBIT_ZOOM = Object.freeze({
  lowerRadiusLimitM: 4.5,
  upperRadiusLimitM: 64,
  // Radius-relative zoom keeps a Mac trackpad smooth at small deltas while a
  // conventional wheel remains useful in the wider site views.
  wheelDeltaPercentage: 0.015,
  useNaturalPinchZoom: true,
  preventBrowserGesture: true,
});

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
  const msaaSamples = Math.min(tier === "ULTRA" ? 4 : 2, supportedMsaa);

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
