import { describe, expect, it } from "vitest";

import {
  CHROME_IDLE,
  DEFAULT_WORKSPACE_MODE,
  INITIAL_CHROME_STATE,
  IMMERSIVE_KEY_CODES,
  WORKSPACE_MODES,
  WORKSPACE_MODE_OPTIONS,
  chromeContract,
  isImmersiveKeyCode,
  isWorkspaceMode,
  movementForWorkspace,
  stepChrome,
  viewModeForWorkspace,
  workspaceForMovement,
  workspaceModeOption,
  type ChromeOptions,
  type ChromeState,
  type PointerPoint,
} from "../lib/twin-ui-mode";

const IMMERSIVE: ChromeOptions = {
  autoHide: true,
  pinned: false,
  idleMs: 1000,
};
const HELD: ChromeOptions = { autoHide: true, pinned: true, idleMs: 1000 };
const DOCUMENTATION: ChromeOptions = { autoHide: false, pinned: false };

const visibleAt = (
  sinceMs: number,
  pointer: PointerPoint | null = null,
): ChromeState => ({
  visible: true,
  sinceMs,
  pointer,
});
const hiddenAt = (
  sinceMs: number,
  pointer: PointerPoint | null = null,
): ChromeState => ({
  visible: false,
  sinceMs,
  pointer,
});
const at = (x: number, y: number): PointerPoint => ({ x, y });
const moveTo = (x: number, y: number, dragging = false) =>
  ({ kind: "pointer", dragging, x, y }) as const;

describe("workspace mode", () => {
  it("offers exactly the two top-level modes, in reading order", () => {
    expect(WORKSPACE_MODES).toEqual(["documentation", "experience"]);
    expect(WORKSPACE_MODE_OPTIONS.map((option) => option.id)).toEqual([
      ...WORKSPACE_MODES,
    ]);
    for (const option of WORKSPACE_MODE_OPTIONS) {
      expect(option.label.length).toBeGreaterThan(0);
      expect(option.tagline.length).toBeGreaterThan(0);
    }
  });

  it("opens on the visualisation, because that is what the product became", () => {
    expect(DEFAULT_WORKSPACE_MODE).toBe("experience");
  });

  it("recognises stored values and falls back rather than throwing", () => {
    expect(isWorkspaceMode("documentation")).toBe(true);
    expect(isWorkspaceMode("experience")).toBe(true);
    expect(isWorkspaceMode("walk")).toBe(false);
    expect(isWorkspaceMode(null)).toBe(false);
    expect(workspaceModeOption("experience").id).toBe("experience");
  });

  it("binds the render style to the mode instead of leaving it free", () => {
    expect(viewModeForWorkspace("documentation")).toBe("technical");
    expect(viewModeForWorkspace("experience")).toBe("realistic");
  });
});

describe("movement and workspace stay consistent", () => {
  it("refuses to fly or walk inside the documentation layout", () => {
    expect(movementForWorkspace("documentation", "flight")).toBe("orbit");
    expect(movementForWorkspace("documentation", "walk")).toBe("orbit");
    expect(movementForWorkspace("documentation", "orbit")).toBe("orbit");
  });

  it("keeps every movement available inside the experience", () => {
    for (const movement of ["orbit", "flight", "walk"] as const) {
      expect(movementForWorkspace("experience", movement)).toBe(movement);
    }
  });

  it("promotes a movement request into the mode that can host it", () => {
    expect(workspaceForMovement("documentation", "walk")).toBe("experience");
    expect(workspaceForMovement("documentation", "flight")).toBe("experience");
  });

  it("leaves the current mode alone when the request is orbit", () => {
    expect(workspaceForMovement("documentation", "orbit")).toBe(
      "documentation",
    );
    expect(workspaceForMovement("experience", "orbit")).toBe("experience");
  });
});

describe("chrome contract", () => {
  it("gives documentation its dense, permanently visible frame", () => {
    expect(chromeContract("documentation", "orbit")).toEqual({
      autoHide: false,
      dockedPanels: true,
      appRails: true,
      surveyOverlays: true,
      cameraPresets: true,
      reticle: false,
      virtualPad: false,
    });
  });

  it("empties the experience: no rails, no survey overlays, chrome fades", () => {
    const chrome = chromeContract("experience", "orbit");
    expect(chrome.autoHide).toBe(true);
    expect(chrome.appRails).toBe(false);
    expect(chrome.dockedPanels).toBe(false);
    expect(chrome.surveyOverlays).toBe(false);
  });

  it("keeps camera presets in documentation, where framing is the task", () => {
    expect(chromeContract("documentation", "orbit").cameraPresets).toBe(true);
    // The Experience reaches the same views through ⌘K and the number keys,
    // so the dock stays down to movement and the command button.
    expect(chromeContract("experience", "orbit").cameraPresets).toBe(false);
    expect(chromeContract("experience", "flight").cameraPresets).toBe(false);
    expect(chromeContract("experience", "walk").cameraPresets).toBe(false);
  });

  it("keeps walking controls visible without a game-like aiming reticle", () => {
    expect(chromeContract("experience", "walk").autoHide).toBe(false);
    expect(chromeContract("experience", "walk").reticle).toBe(false);
    expect(chromeContract("experience", "flight").reticle).toBe(false);
    expect(chromeContract("documentation", "orbit").reticle).toBe(false);
  });

  it("offers held direction controls to free movement only", () => {
    expect(chromeContract("experience", "walk").virtualPad).toBe(true);
    expect(chromeContract("experience", "flight").virtualPad).toBe(true);
    expect(chromeContract("experience", "orbit").virtualPad).toBe(false);
  });
});

describe("auto-hiding chrome", () => {
  it("starts visible so the controls are never a secret", () => {
    expect(INITIAL_CHROME_STATE.visible).toBe(true);
    expect(INITIAL_CHROME_STATE.pointer).toBe(null);
  });

  it("checks for idleness far more often than the idle window", () => {
    expect(CHROME_IDLE.tickMs).toBeLessThan(CHROME_IDLE.idleMs / 4);
  });

  it("fades the interface once the idle window has fully elapsed", () => {
    const state = visibleAt(0);
    expect(stepChrome(state, { kind: "tick" }, 999, IMMERSIVE)).toBe(state);
    expect(stepChrome(state, { kind: "tick" }, 1000, IMMERSIVE)).toEqual(
      hiddenAt(1000),
    );
  });

  it("never wakes on movement keys — holding W is immersion, not intent", () => {
    const hidden = hiddenAt(0);
    for (const code of IMMERSIVE_KEY_CODES) {
      expect(stepChrome(hidden, { kind: "press", code }, 500, IMMERSIVE)).toBe(
        hidden,
      );
      expect(isImmersiveKeyCode(code)).toBe(true);
    }
  });

  it("wakes on a key that asks for something", () => {
    expect(
      stepChrome(hiddenAt(0), { kind: "press", code: "KeyK" }, 500, IMMERSIVE),
    ).toEqual(visibleAt(500));
    expect(isImmersiveKeyCode("KeyK")).toBe(false);
  });

  it("treats a dragging pointer as camera work, not as a request", () => {
    const hidden = hiddenAt(0);
    expect(
      stepChrome(hidden, moveTo(40, 40, true), 500, IMMERSIVE).visible,
    ).toBe(false);
    expect(stepChrome(hidden, moveTo(40, 40), 500, IMMERSIVE)).toEqual(
      visibleAt(500, at(40, 40)),
    );
  });

  it("ignores the moves a resting cursor receives when the page moves under it", () => {
    // The browser re-runs the hit test whenever the layout changes, so fading
    // the chrome out delivers a `pointermove` at unchanged coordinates. Waking
    // on those would make the interface hold itself open forever.
    const resting = hiddenAt(0, at(120, 300));
    expect(stepChrome(resting, moveTo(120, 300), 500, IMMERSIVE)).toBe(resting);
    expect(stepChrome(resting, moveTo(121, 300), 500, IMMERSIVE)).toEqual(
      visibleAt(500, at(121, 300)),
    );
  });

  it("remembers where a drag left the cursor, so the next move is measured from it", () => {
    const dragged = stepChrome(
      hiddenAt(0),
      moveTo(80, 80, true),
      500,
      IMMERSIVE,
    );
    expect(dragged.visible).toBe(false);
    expect(dragged.pointer).toEqual(at(80, 80));
    expect(stepChrome(dragged, moveTo(80, 80), 600, IMMERSIVE)).toBe(dragged);
  });

  it("wakes on a tap, the one gesture a touch screen has", () => {
    // A finger never hovers, so a press and release in place is the only way
    // back to the controls.
    expect(
      stepChrome(hiddenAt(0, at(10, 10)), { kind: "tap" }, 500, IMMERSIVE),
    ).toEqual(visibleAt(500, at(10, 10)));
  });

  it("wakes on scrolling and on keyboard focus arriving", () => {
    expect(stepChrome(hiddenAt(0), { kind: "wheel" }, 400, IMMERSIVE)).toEqual(
      visibleAt(400),
    );
    expect(stepChrome(hiddenAt(0), { kind: "focus" }, 400, IMMERSIVE)).toEqual(
      visibleAt(400),
    );
  });

  it("returns the same state when nothing changed, so React need not render", () => {
    const state = visibleAt(500, at(12, 12));
    expect(stepChrome(state, moveTo(90, 90), 500, IMMERSIVE)).toBe(state);
    const hidden = hiddenAt(500);
    expect(stepChrome(hidden, { kind: "tick" }, 9000, IMMERSIVE)).toBe(hidden);
  });

  it("holds the interface open while a panel or the palette is pinned", () => {
    expect(stepChrome(visibleAt(0), { kind: "tick" }, 9000, HELD)).toEqual(
      visibleAt(9000),
    );
    expect(stepChrome(hiddenAt(0), { kind: "tick" }, 9000, HELD)).toEqual(
      visibleAt(9000),
    );
  });

  it("keeps documentation permanently visible whatever the input", () => {
    expect(
      stepChrome(visibleAt(0), { kind: "tick" }, 9000, DOCUMENTATION).visible,
    ).toBe(true);
    expect(
      stepChrome(
        hiddenAt(0),
        { kind: "press", code: "KeyW" },
        9000,
        DOCUMENTATION,
      ).visible,
    ).toBe(true);
  });

  it("restarts the idle clock while held, so releasing gives a full window", () => {
    const released = stepChrome(visibleAt(0), { kind: "tick" }, 9000, HELD);
    expect(stepChrome(released, { kind: "tick" }, 9500, IMMERSIVE)).toBe(
      released,
    );
    expect(stepChrome(released, { kind: "tick" }, 10_000, IMMERSIVE)).toEqual(
      hiddenAt(10_000),
    );
  });

  it("falls back to the shared idle window when none is supplied", () => {
    const state = visibleAt(0);
    const options: ChromeOptions = { autoHide: true, pinned: false };
    expect(
      stepChrome(state, { kind: "tick" }, CHROME_IDLE.idleMs - 1, options),
    ).toBe(state);
    expect(
      stepChrome(state, { kind: "tick" }, CHROME_IDLE.idleMs, options).visible,
    ).toBe(false);
  });
});
