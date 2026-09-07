"use client";

import { useEffect, useRef, useState } from "react";

import {
  CHROME_IDLE,
  INITIAL_CHROME_STATE,
  stepChrome,
  type ChromeOptions,
  type ChromeSignal,
  type ChromeState,
} from "@/versions/v2/lib/twin-ui-mode";

/** A tap is a reveal gesture; anything longer is a camera drag. */
const TAP_SLOP_PX = 8;

/**
 * Drives the auto-hiding interface from real input. The idle decision itself
 * lives in `stepChrome` so it stays testable; this hook only classifies browser
 * events and keeps React out of the high-frequency path — state is written once
 * per visibility flip, not once per pointer move.
 */
export function useChromeVisibility(options: ChromeOptions): boolean {
  const [visible, setVisible] = useState(true);
  const stateRef = useRef<ChromeState>(INITIAL_CHROME_STATE);
  const optionsRef = useRef(options);
  const draggingRef = useRef(false);
  const pointerStartRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    optionsRef.current = options;
  });

  useEffect(() => {
    const apply = (signal: ChromeSignal) => {
      const previous = stateRef.current;
      const next = stepChrome(
        previous,
        signal,
        performance.now(),
        optionsRef.current,
      );
      if (next === previous) return;
      stateRef.current = next;
      if (next.visible !== previous.visible) setVisible(next.visible);
    };

    const onPointerMove = (event: PointerEvent) => {
      apply({
        kind: "pointer",
        dragging: draggingRef.current,
        x: event.clientX,
        y: event.clientY,
      });
    };
    const onPointerDown = (event: PointerEvent) => {
      draggingRef.current = true;
      pointerStartRef.current = { x: event.clientX, y: event.clientY };
    };
    const onPointerUp = (event: PointerEvent) => {
      draggingRef.current = false;
      const travel = Math.hypot(
        event.clientX - pointerStartRef.current.x,
        event.clientY - pointerStartRef.current.y,
      );
      // Touch users never move a hovering pointer, so a tap has to be the way
      // back to the controls.
      if (travel <= TAP_SLOP_PX) apply({ kind: "tap" });
    };
    const onPointerCancel = () => {
      draggingRef.current = false;
    };
    const onKeyDown = (event: KeyboardEvent) => {
      apply({ kind: "press", code: event.code });
    };
    const onWheel = () => apply({ kind: "wheel" });
    const onFocusIn = () => apply({ kind: "focus" });

    window.addEventListener("pointermove", onPointerMove, { passive: true });
    window.addEventListener("pointerdown", onPointerDown, { passive: true });
    window.addEventListener("pointerup", onPointerUp, { passive: true });
    window.addEventListener("pointercancel", onPointerCancel, {
      passive: true,
    });
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("wheel", onWheel, { passive: true });
    window.addEventListener("focusin", onFocusIn);
    const timer = window.setInterval(
      () => apply({ kind: "tick" }),
      CHROME_IDLE.tickMs,
    );

    return () => {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("pointercancel", onPointerCancel);
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("wheel", onWheel);
      window.removeEventListener("focusin", onFocusIn);
      window.clearInterval(timer);
    };
  }, []);

  // Leaving the immersive mode, or opening a panel, reveals the interface on
  // the same frame instead of waiting for the idle tick to notice.
  return !options.autoHide || options.pinned || visible;
}
