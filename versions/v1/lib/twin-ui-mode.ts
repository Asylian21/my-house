import type { ViewMode } from "./twin-site";
import type { NavigationMode } from "./twin-viewport-contract";

/**
 * The product grew from a technical drawing into a walkable visualisation, so
 * the interface now has two clearly separated jobs. Documentation is dense and
 * evidence-first; Experience is a quiet, cinematic space where the model itself
 * carries the screen. Everything the shell shows is derived from this one axis
 * instead of the previous free combination of `ViewMode` and `NavigationMode`,
 * which allowed six states and gave none of them a chrome contract.
 */
export type WorkspaceMode = "documentation" | "experience";

export const WORKSPACE_MODES = ["documentation", "experience"] as const;

export interface WorkspaceModeOption {
  readonly id: WorkspaceMode;
  readonly label: string;
  readonly tagline: string;
}

export const WORKSPACE_MODE_OPTIONS = [
  {
    id: "documentation",
    label: "Dokumentácia",
    tagline: "Výkres, parametre a dôkazová stopa",
  },
  {
    id: "experience",
    label: "Zážitok",
    tagline: "Prehliadka domu, záhrady a interiéru",
  },
] as const satisfies readonly WorkspaceModeOption[];

export const DEFAULT_WORKSPACE_MODE: WorkspaceMode = "experience";

export function isWorkspaceMode(value: unknown): value is WorkspaceMode {
  return (
    typeof value === "string" &&
    (WORKSPACE_MODES as readonly string[]).includes(value)
  );
}

export function workspaceModeOption(id: WorkspaceMode): WorkspaceModeOption {
  return (
    WORKSPACE_MODE_OPTIONS.find((option) => option.id === id) ??
    WORKSPACE_MODE_OPTIONS[0]
  );
}

/** Documentation reads the schematic model; Experience reads the built one. */
export function viewModeForWorkspace(workspace: WorkspaceMode): ViewMode {
  return workspace === "documentation" ? "technical" : "realistic";
}

/**
 * Flying and walking are ways of moving through the Experience, never a state
 * the dense documentation layout can hold. Requesting them therefore implies
 * the mode switch rather than producing a contradictory hybrid.
 */
export function movementForWorkspace(
  workspace: WorkspaceMode,
  requested: NavigationMode,
): NavigationMode {
  return workspace === "documentation" ? "orbit" : requested;
}

export function workspaceForMovement(
  current: WorkspaceMode,
  movement: NavigationMode,
): WorkspaceMode {
  return movement === "orbit" ? current : "experience";
}

/**
 * A single description of which chrome each mode is allowed to show. The React
 * shell only reads this, so a control can never quietly reappear in the mode it
 * was supposed to stay out of.
 */
export interface ChromeContract {
  /** Controls fade out after a period without deliberate input. */
  readonly autoHide: boolean;
  /** Explorer and inspector occupy real layout columns instead of floating. */
  readonly dockedPanels: boolean;
  /** The persistent application rails frame the viewport. */
  readonly appRails: boolean;
  /** Compass, evidence legend and the Retina readout are documentation tools. */
  readonly surveyOverlays: boolean;
  /** Framing the drawing is a survey task; the Experience uses ⌘K and 1–5. */
  readonly cameraPresets: boolean;
  /** A centre reticle only helps while aiming at doors on foot. */
  readonly reticle: boolean;
  /** Held direction controls are offered to touch input during free movement. */
  readonly virtualPad: boolean;
}

export function chromeContract(
  workspace: WorkspaceMode,
  movement: NavigationMode,
): ChromeContract {
  const experience = workspace === "experience";
  return {
    autoHide: experience,
    dockedPanels: !experience,
    appRails: !experience,
    surveyOverlays: !experience,
    cameraPresets: !experience && movement === "orbit",
    reticle: experience && movement === "walk",
    virtualPad: experience && movement !== "orbit",
  };
}

export const CHROME_IDLE = Object.freeze({
  /** Long enough to finish reading a label, short enough to feel invisible. */
  idleMs: 2600,
  /** Polling cadence of the idle check; well below the idle window. */
  tickMs: 240,
});

/**
 * Movement input is the one thing that must never wake the interface: holding
 * W to cross a room is immersion, not a request for controls. Everything else —
 * moving a free pointer, scrolling, tabbing — is read as intent to act.
 */
export const IMMERSIVE_KEY_CODES = [
  "KeyW",
  "KeyA",
  "KeyS",
  "KeyD",
  "KeyQ",
  "KeyE",
  "KeyR",
  "KeyV",
  "ArrowUp",
  "ArrowDown",
  "ArrowLeft",
  "ArrowRight",
  "ShiftLeft",
  "ShiftRight",
  "AltLeft",
  "AltRight",
  "Space",
] as const;

export function isImmersiveKeyCode(code: string): boolean {
  return (IMMERSIVE_KEY_CODES as readonly string[]).includes(code);
}

export interface PointerPoint {
  readonly x: number;
  readonly y: number;
}

export type ChromeSignal =
  | {
      readonly kind: "pointer";
      readonly dragging: boolean;
      readonly x: number;
      readonly y: number;
    }
  /** A press and release in one place: the touch equivalent of moving a mouse. */
  | { readonly kind: "tap" }
  | { readonly kind: "press"; readonly code: string }
  | { readonly kind: "wheel" }
  | { readonly kind: "focus" }
  | { readonly kind: "tick" };

export interface ChromeState {
  readonly visible: boolean;
  /** Timestamp of the signal that produced the current visibility. */
  readonly sinceMs: number;
  /** Last pointer position seen, used to tell real movement from noise. */
  readonly pointer: PointerPoint | null;
}

export interface ChromeOptions {
  readonly autoHide: boolean;
  /** An open panel, palette or hovered control holds the chrome in place. */
  readonly pinned: boolean;
  readonly idleMs?: number;
}

export const INITIAL_CHROME_STATE: ChromeState = Object.freeze({
  visible: true,
  sinceMs: 0,
  pointer: null,
});

function wakesChrome(signal: ChromeSignal, state: ChromeState): boolean {
  if (signal.kind === "tick") return false;
  if (signal.kind === "pointer") {
    if (signal.dragging) return false;
    // A resting cursor keeps receiving `pointermove`, because the browser
    // re-runs the hit test whenever the layout underneath changes — and the
    // chrome fading out is exactly such a change. Reading those as intent lets
    // the interface wake itself forever, so only a changed position counts.
    const last = state.pointer;
    return !last || last.x !== signal.x || last.y !== signal.y;
  }
  if (signal.kind === "press") return !isImmersiveKeyCode(signal.code);
  return true;
}

function pointerAfter(
  signal: ChromeSignal,
  state: ChromeState,
): PointerPoint | null {
  if (signal.kind !== "pointer") return state.pointer;
  const last = state.pointer;
  if (last && last.x === signal.x && last.y === signal.y) return last;
  return { x: signal.x, y: signal.y };
}

/**
 * Pure idle model behind the auto-hiding interface. It returns the received
 * state unchanged whenever nothing meaningful happened, so the React layer can
 * drive it from high-frequency pointer events without re-rendering.
 */
export function stepChrome(
  state: ChromeState,
  signal: ChromeSignal,
  nowMs: number,
  options: ChromeOptions,
): ChromeState {
  const pointer = pointerAfter(signal, state);
  // While the interface is held open — documentation mode, an open panel, the
  // palette — the idle clock is continuously reset, so releasing the hold
  // starts a fresh countdown rather than an already-expired one.
  if (!options.autoHide || options.pinned) {
    return { visible: true, sinceMs: nowMs, pointer };
  }
  if (signal.kind === "tick") {
    if (!state.visible) return state;
    const idleMs = options.idleMs ?? CHROME_IDLE.idleMs;
    return nowMs - state.sinceMs >= idleMs
      ? { visible: false, sinceMs: nowMs, pointer }
      : state;
  }
  if (!wakesChrome(signal, state)) {
    // A drag still tells us where the cursor is, so the move that ends it is
    // measured from the right place.
    return pointer === state.pointer ? state : { ...state, pointer };
  }
  if (state.visible && state.sinceMs === nowMs) return state;
  return { visible: true, sinceMs: nowMs, pointer };
}
