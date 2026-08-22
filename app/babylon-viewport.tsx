"use client";

import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from "react";
import type {
  CameraPreset,
  TwinSceneController,
} from "@/lib/babylon-scene";
import type { FoundationStrip, LayerId, ViewMode } from "@/lib/twin-site";
import type {
  FlightCommand,
  NavigationMode,
  PersonCameraView,
  RenderQualityProfile,
} from "@/lib/twin-viewport-contract";
import { INTERIOR_ROOMS } from "@/lib/twin-interior";

export interface BabylonViewportHandle {
  setCameraPreset: (preset: CameraPreset) => void;
  setNavigationMode: (mode: NavigationMode) => void;
  enterWalkthrough: (roomId?: string) => void;
  setFlightCommand: (command: FlightCommand, active: boolean) => void;
  nudgeFlight: (command: FlightCommand) => void;
  setPersonRunning: (active: boolean) => void;
  cyclePersonView: () => PersonCameraView | undefined;
  togglePersonShoulder: () => -1 | 1 | undefined;
  lockPersonLook: () => boolean;
  releasePersonLook: () => boolean;
  isPersonLookLocked: () => boolean;
  consumePersonEscape: () => boolean;
}

interface BabylonViewportProps {
  foundations: readonly FoundationStrip[];
  selectionId: string | null;
  visibleLayers: Readonly<Record<LayerId, boolean>>;
  viewMode: ViewMode;
  navigationMode: NavigationMode;
  onSelect: (id: string) => void;
  onNavigationModeChange: (mode: NavigationMode) => void;
  onPersonModeRequest: () => void;
}

export const BabylonViewport = forwardRef<
  BabylonViewportHandle,
  BabylonViewportProps
>(function BabylonViewport(
  {
    foundations,
    selectionId,
    visibleLayers,
    viewMode,
    navigationMode,
    onSelect,
    onNavigationModeChange,
    onPersonModeRequest,
  },
  ref,
) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const controllerRef = useRef<TwinSceneController | null>(null);
  const onSelectRef = useRef(onSelect);
  const navigationModeRef = useRef(navigationMode);
  const onNavigationModeChangeRef = useRef(onNavigationModeChange);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [quality, setQuality] = useState<RenderQualityProfile | null>(null);
  const [walkRoom, setWalkRoom] = useState<string>("");
  const [personView, setPersonView] =
    useState<PersonCameraView>("shoulder");
  const [personShoulder, setPersonShoulder] = useState<-1 | 1>(1);
  const [personLookState, setPersonLookState] =
    useState<"paused" | "locking" | "locked" | "error">("paused");
  const [personRunning, setPersonRunning] = useState(false);

  onSelectRef.current = onSelect;
  navigationModeRef.current = navigationMode;
  onNavigationModeChangeRef.current = onNavigationModeChange;

  useImperativeHandle(ref, () => ({
    setCameraPreset(preset) {
      controllerRef.current?.setCameraPreset(preset);
    },
    setNavigationMode(mode) {
      controllerRef.current?.setNavigationMode(mode);
    },
    enterWalkthrough(roomId) {
      controllerRef.current?.enterWalkthrough(roomId);
    },
    setFlightCommand(command, active) {
      controllerRef.current?.setFlightCommand(command, active);
    },
    nudgeFlight(command) {
      controllerRef.current?.nudgeFlight(command);
    },
    setPersonRunning(active) {
      controllerRef.current?.setPersonRunning(active);
    },
    cyclePersonView() {
      return controllerRef.current?.cyclePersonView();
    },
    togglePersonShoulder() {
      return controllerRef.current?.togglePersonShoulder();
    },
    lockPersonLook() {
      return controllerRef.current?.lockPersonLook() ?? false;
    },
    releasePersonLook() {
      return controllerRef.current?.releasePersonLook() ?? false;
    },
    isPersonLookLocked() {
      return controllerRef.current?.isPersonLookLocked() ?? false;
    },
    consumePersonEscape() {
      return controllerRef.current?.consumePersonEscape() ?? false;
    },
  }), []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let active = true;
    let observer: ResizeObserver | undefined;
    let dprQuery: MediaQueryList | undefined;
    let controller: TwinSceneController | null = null;
    const onWindowResize = () => controller?.resize();
    const onDprChange = () => {
      controller?.resize();
      dprQuery?.removeEventListener("change", onDprChange);
      dprQuery = window.matchMedia(
        `(resolution: ${window.devicePixelRatio}dppx)`,
      );
      dprQuery.addEventListener("change", onDprChange);
    };

    void import("@/lib/babylon-scene")
      .then(async ({ createTwinScene }) => {
        if (!active) return;
        const createdController = createTwinScene(
          canvas,
          (id) => onSelectRef.current(id),
          (mode) => onNavigationModeChangeRef.current(mode),
          (profile) => setQuality(profile),
        );
        controller = createdController;
        controllerRef.current = createdController;
        if (import.meta.env?.DEV) {
          (window as unknown as Record<string, unknown>).twinDebug =
            createdController;
        }
        createdController.setNavigationMode(navigationModeRef.current);
        observer = new ResizeObserver(() => createdController.resize());
        observer.observe(canvas);
        window.addEventListener("resize", onWindowResize);
        dprQuery = window.matchMedia(
          `(resolution: ${window.devicePixelRatio}dppx)`,
        );
        dprQuery.addEventListener("change", onDprChange);
        await createdController.whenReady();
        if (!active) return;
        setStatus("ready");
      })
      .catch(() => {
        if (active) setStatus("error");
      });

    return () => {
      active = false;
      observer?.disconnect();
      window.removeEventListener("resize", onWindowResize);
      dprQuery?.removeEventListener("change", onDprChange);
      controllerRef.current?.dispose();
      controllerRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (status === "ready") {
      controllerRef.current?.update({
        foundations,
        selectionId,
        visibleLayers,
        viewMode,
      });
    }
  }, [status, foundations, selectionId, visibleLayers, viewMode]);

  useEffect(() => {
    if (status === "ready") {
      controllerRef.current?.setNavigationMode(navigationMode);
    }
  }, [status, navigationMode]);

  useEffect(() => {
    if (status !== "ready" || navigationMode !== "walk") {
      setWalkRoom("");
      setPersonLookState("paused");
      setPersonRunning(false);
      return;
    }
    const read = () => {
      const controller = controllerRef.current;
      const room = controller?.getWalkRoom();
      setWalkRoom(room ? `${room.number} · ${room.name}` : "Exteriér · terasa a záhrada");
      setPersonView(controller?.getPersonCameraView() ?? "shoulder");
      setPersonShoulder(controller?.getPersonShoulderSide() ?? 1);
      setPersonLookState(controller?.getPersonLookState() ?? "paused");
    };
    read();
    const timer = window.setInterval(read, 200);
    return () => window.clearInterval(timer);
  }, [status, navigationMode]);

  const setMode = (mode: NavigationMode) => {
    controllerRef.current?.setNavigationMode(mode);
    onNavigationModeChangeRef.current(mode);
  };

  const applyPreset = (preset: CameraPreset) => {
    setMode("orbit");
    controllerRef.current?.setCameraPreset(preset);
  };

  const holdFlightCommand = (
    command: FlightCommand,
    active: boolean,
    event: ReactPointerEvent<HTMLButtonElement>,
  ) => {
    event.stopPropagation();
    if (active) {
      // Keep focus on the canvas so its blur handler cannot cancel the first
      // held touch command while the button takes pointer capture.
      event.preventDefault();
      event.currentTarget.setPointerCapture(event.pointerId);
    }
    controllerRef.current?.setFlightCommand(command, active);
  };

  const qualityRatio = quality
    ? quality.pixelRatio.toLocaleString("sk-SK", {
        minimumFractionDigits: quality.pixelRatio % 1 === 0 ? 0 : 1,
        maximumFractionDigits: 1,
      })
    : null;

  return (
    <div
      className="canvas-region"
      role="region"
      aria-label="3D model parcely, domu, základov, komunikácie a inžinierskych sietí"
      aria-describedby="canvas-instructions"
    >
      <p id="canvas-instructions" className="sr-only">
        {navigationMode === "flight"
          ? "Voľný 3D prelet. Ťahaním sa rozhliadate, W A S D ovládajú vodorovný pohyb, E a Q výšku, Shift zrýchľuje, Alt spomaľuje a Escape ukončí prelet."
          : navigationMode === "walk"
            ? "Režim postavy. Kliknutie do scény zapne voľný rozhľad myšou, ťahanie zostáva dostupné na trackpade a dotyku. W A S D ovládajú pohyb, Shift beh, V mení pohľad, Q prepína rameno a Escape uvoľní kurzor."
            : "Interaktívny technický model. Ťahaním model otáčate, pravým alebo Control ťahaním posúvate a trackpadom, kolieskom alebo pinch gestom plynulo približujete k ukazovateľu. Klávesy 1 až 4 nastavia pohľady, F zameria výber, H spustí voľný 3D prelet a G režim postavy."}
      </p>
      <canvas
        ref={canvasRef}
        className="scene-canvas"
        tabIndex={0}
        aria-label="Ovládanie 3D modelu"
        aria-describedby="canvas-instructions"
        onKeyDown={(event) => {
          if (event.key === "1") applyPreset("axonometric");
          if (event.key === "2") applyPreset("top");
          if (event.key === "3") applyPreset("street");
          if (event.key === "4") applyPreset("garden");
          if (event.key.toLowerCase() === "f") applyPreset("focus");
          if (event.key.toLowerCase() === "h") {
            event.preventDefault();
            setMode(navigationMode === "flight" ? "orbit" : "flight");
          }
          if (event.key.toLowerCase() === "g") {
            event.preventDefault();
            onPersonModeRequest();
          }
        }}
      />
      {status === "ready" && quality && (
        <div
          className="render-quality-badge"
          aria-label={`Retina render ${qualityRatio}-násobné rozlíšenie, MSAA ${quality.msaaSamples}-krát`}
        >
          <span>RETINA</span>
          <small>{qualityRatio}× · MSAA {quality.msaaSamples}×</small>
        </div>
      )}
      {status === "ready" && navigationMode === "walk" && (
        <div className={`flight-hud walk-hud ${personLookState === "locked" ? "is-look-locked" : ""}`}>
          <div className="walk-status" role="status" aria-live="polite">
            <span>POSTAVA · {walkRoom || "INTERIÉR 1.NP"}</span>
            <strong className="walk-fine-copy">WASD pohyb · trackpad / myš kamera</strong>
            <strong className="walk-coarse-copy">Tlačidlá pohyb · ťahanie kamerou</strong>
            <small>
              {personLookState === "locked"
                ? "Voľný rozhľad aktívny · Esc uvoľní kurzor"
                : personLookState === "error"
                  ? "Voľný rozhľad sa nepodarilo zapnúť · ťahanie zostáva aktívne"
                  : "Shift beh · šípky kamera · V pohľad · Q rameno"}
            </small>
          </div>
          <div className="walk-actions" role="group" aria-label="Kamera postavy">
            <button
              type="button"
              aria-keyshortcuts="V"
              onClick={(event) => {
                event.stopPropagation();
                const next = controllerRef.current?.cyclePersonView();
                if (next) setPersonView(next);
              }}
            >
              Pohľad: {personView === "shoulder" ? "za postavou" : personView === "close" ? "blízko" : "z očí"}
            </button>
            {personView !== "first-person" && (
              <button
                type="button"
                aria-label={personShoulder < 0 ? "Kamera je na ľavom ramene, prepnúť na pravé" : "Kamera je na pravom ramene, prepnúť na ľavé"}
                aria-keyshortcuts="Q"
                onClick={(event) => {
                  event.stopPropagation();
                  const next = controllerRef.current?.togglePersonShoulder();
                  if (next) setPersonShoulder(next);
                }}
              >
                Rameno: {personShoulder < 0 ? "ľavé" : "pravé"}
              </button>
            )}
            {personLookState !== "locked" && (
              <button
                type="button"
                className="walk-look-control"
                disabled={personLookState === "locking"}
                onClick={(event) => {
                  event.stopPropagation();
                  controllerRef.current?.lockPersonLook();
                }}
              >
                {personLookState === "locking" ? "Zapínam rozhľad…" : "Zapnúť voľný rozhľad"}
              </button>
            )}
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                onPersonModeRequest();
              }}
            >
              Ukončiť režim
            </button>
          </div>
          <details className="walk-relocate">
            <summary>Premiestniť sa</summary>
            <div className="walk-rooms" role="group" aria-label="Prejsť do miestnosti">
              {INTERIOR_ROOMS.map((room) => (
                <button
                  key={room.id}
                  type="button"
                  aria-label={`Prejsť do ${room.number} ${room.name}`}
                  onClick={(event) => {
                    event.stopPropagation();
                    controllerRef.current?.enterWalkthrough(room.id);
                    event.currentTarget
                      .closest("details")
                      ?.removeAttribute("open");
                  }}
                >
                  <strong>{room.number}</strong>
                  <small>{room.name}</small>
                </button>
              ))}
            </div>
          </details>
        </div>
      )}
      {status === "ready" && (navigationMode === "flight" || navigationMode === "walk") && (
        <>
          {navigationMode === "flight" && (
          <div className="flight-hud" role="status" aria-live="polite">
            <span>PRELET · HELIKOPTÉROVÁ KAMERA</span>
            <strong>WASD pohyb · Q/E výška</strong>
            <small>Ťahanie rozhľad · Shift turbo · Alt presne · Esc koniec</small>
          </div>
          )}
          <div
            className="flight-control-pad"
            role="group"
            aria-label={navigationMode === "walk" ? "Dotykové ovládanie postavy" : "Dotykové ovládanie voľného preletu"}
          >
            {(navigationMode === "walk"
              ? ([
                  ["forward", "↑", "Ísť dopredu"],
                  ["left", "←", "Ísť doľava"],
                  ["backward", "↓", "Ísť dozadu"],
                  ["right", "→", "Ísť doprava"],
                ] as const)
              : ([
                  ["forward", "↑", "Letieť dopredu"],
                  ["left", "←", "Letieť doľava"],
                  ["backward", "↓", "Letieť dozadu"],
                  ["right", "→", "Letieť doprava"],
                  ["up", "+", "Stúpať"],
                  ["down", "−", "Klesať"],
                ] as const)
            ).map(([command, glyph, label]) => (
              <button
                type="button"
                key={command}
                className={`flight-command flight-${command}`}
                aria-label={label}
                onPointerDown={(event) => holdFlightCommand(command, true, event)}
                onPointerUp={(event) => holdFlightCommand(command, false, event)}
                onPointerCancel={(event) => holdFlightCommand(command, false, event)}
                onLostPointerCapture={(event) => holdFlightCommand(command, false, event)}
                onClick={(event) => {
                  event.stopPropagation();
                  if (event.detail === 0) controllerRef.current?.nudgeFlight(command);
                }}
              >
                <span aria-hidden="true">{glyph}</span>
              </button>
            ))}
            {navigationMode === "walk" && (
              <button
                type="button"
                className={`flight-command flight-run ${personRunning ? "active" : ""}`}
                aria-label={personRunning ? "Vypnúť beh" : "Zapnúť beh"}
                aria-pressed={personRunning}
                onClick={(event) => {
                  event.stopPropagation();
                  const next = !personRunning;
                  setPersonRunning(next);
                  controllerRef.current?.setPersonRunning(next);
                }}
              >
                <span aria-hidden="true">⇧</span>
              </button>
            )}
            <button
              type="button"
              className="flight-exit"
              aria-label={navigationMode === "walk" ? "Ukončiť režim postavy" : "Ukončiť voľný prelet"}
              onClick={(event) => {
                event.stopPropagation();
                if (navigationMode === "walk") onPersonModeRequest();
                else setMode("orbit");
              }}
            >
              Ukončiť
            </button>
          </div>
        </>
      )}
      {status === "loading" && (
        <div className="viewport-state" role="status">
          <span className="drawing-loader" aria-hidden="true" />
          <strong>Skladám digitálne dvojča</strong>
          <small>Kataster · dom · základy · komunikácia · siete</small>
        </div>
      )}
      {status === "error" && (
        <div className="viewport-state error-state" role="alert">
          <strong>3D zobrazenie nie je dostupné</strong>
          <small>Model a parametre môžete ďalej používať cez Prieskumník.</small>
        </div>
      )}
    </div>
  );
});
