"use client";

import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from "react";
import { Bot, Shield, UserRound, type LucideIcon } from "lucide-react";
import type {
  CameraPreset,
  TwinSceneController,
} from "@/lib/babylon-scene";
import type { FoundationStrip, LayerId, ViewMode } from "@/lib/twin-site";
import type {
  FlightCommand,
  NavigationMode,
  RenderQualityProfile,
} from "@/lib/twin-viewport-contract";
import { INTERIOR_ROOMS } from "@/lib/twin-interior";
import {
  DEFAULT_WALK_AVATAR_ID,
  WALK_AVATARS,
  WALK_AVATAR_STORAGE_KEY,
  isWalkAvatarId,
  walkAvatarOption,
  type WalkAvatarIcon,
  type WalkAvatarId,
} from "@/lib/twin-avatar";

const WALK_AVATAR_ICONS: Readonly<Record<WalkAvatarIcon, LucideIcon>> = {
  person: UserRound,
  shield: Shield,
  robot: Bot,
};

export interface BabylonViewportHandle {
  setCameraPreset: (preset: CameraPreset) => void;
  setNavigationMode: (mode: NavigationMode) => void;
  enterWalkthrough: (roomId?: string) => void;
  setWalkView: (view: "third" | "first") => void;
  setWalkAvatar: (id: WalkAvatarId) => Promise<void>;
  recoverWalkthrough: () => void;
  setFlightCommand: (command: FlightCommand, active: boolean) => void;
  nudgeFlight: (command: FlightCommand) => void;
}

interface BabylonViewportProps {
  foundations: readonly FoundationStrip[];
  selectionId: string | null;
  visibleLayers: Readonly<Record<LayerId, boolean>>;
  viewMode: ViewMode;
  navigationMode: NavigationMode;
  onSelect: (id: string) => void;
  onNavigationModeChange: (mode: NavigationMode) => void;
  onParcelOverviewRequest: () => void;
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
    onParcelOverviewRequest,
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
  const [walkView, setWalkView] = useState<"third" | "first">("third");
  const [walkBlocked, setWalkBlocked] = useState(false);
  const [walkHudCollapsed, setWalkHudCollapsed] = useState(false);
  const [walkAvatarId, setWalkAvatarId] = useState<WalkAvatarId>(
    DEFAULT_WALK_AVATAR_ID,
  );
  const [pendingWalkAvatarId, setPendingWalkAvatarId] =
    useState<WalkAvatarId | null>(null);
  const [walkAvatarMessage, setWalkAvatarMessage] = useState("");
  const [walkAvatarError, setWalkAvatarError] = useState("");
  const avatarPointerSelectionRef = useRef<WalkAvatarId | null>(null);

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
    setWalkView(view) {
      controllerRef.current?.setWalkView(view);
      setWalkView(view);
    },
    async setWalkAvatar(id) {
      await controllerRef.current?.setWalkAvatar(id);
      setWalkAvatarId(id);
    },
    recoverWalkthrough() {
      controllerRef.current?.recoverWalkthrough();
    },
    setFlightCommand(command, active) {
      controllerRef.current?.setFlightCommand(command, active);
    },
    nudgeFlight(command) {
      controllerRef.current?.nudgeFlight(command);
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
        try {
          const storedAvatarId = window.localStorage.getItem(
            WALK_AVATAR_STORAGE_KEY,
          );
          if (isWalkAvatarId(storedAvatarId)) {
            setWalkAvatarId(storedAvatarId);
            void createdController.setWalkAvatar(storedAvatarId);
          }
        } catch {
          // The picker remains fully usable when browser storage is blocked.
        }
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
      setWalkBlocked(false);
      return;
    }
    const read = () => {
      const room = controllerRef.current?.getWalkRoom();
      setWalkRoom(room ? `${room.number} · ${room.name}` : "Exteriér · terasa a záhrada");
      setWalkBlocked(controllerRef.current?.isWalkBlocked() ?? false);
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
    if (preset === "parcels") onParcelOverviewRequest();
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

  const chooseWalkAvatar = async (
    id: WalkAvatarId,
    restoreCanvasFocus: boolean,
  ) => {
    const controller = controllerRef.current;
    if (!controller || pendingWalkAvatarId || id === walkAvatarId) {
      if (restoreCanvasFocus) {
        canvasRef.current?.focus({ preventScroll: true });
      }
      return;
    }
    const option = walkAvatarOption(id);
    setPendingWalkAvatarId(id);
    setWalkAvatarError("");
    setWalkAvatarMessage(`Načítavam postavu ${option.label}.`);
    try {
      await controller.setWalkAvatar(id);
      setWalkAvatarId(id);
      setWalkAvatarMessage(`Postava ${option.label} je pripravená.`);
      try {
        window.localStorage.setItem(WALK_AVATAR_STORAGE_KEY, id);
      } catch {
        // A device-local preference is optional; the in-memory choice remains.
      }
    } catch {
      const current = walkAvatarOption(controller.getWalkAvatar());
      setWalkAvatarId(current.id);
      setWalkAvatarMessage("");
      setWalkAvatarError(
        `Postavu ${option.label} sa nepodarilo načítať. Zostáva ${current.label}.`,
      );
    } finally {
      setPendingWalkAvatarId(null);
      if (restoreCanvasFocus) {
        window.requestAnimationFrame(() =>
          canvasRef.current?.focus({ preventScroll: true }),
        );
      }
    }
  };

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
            ? "Prechádzka domom s voliteľnou postavou. V paneli môžete vybrať Michelle, Vanguard alebo Robo. W A S D ovládajú chôdzu v smere kamery, ťahaním otáčate kameru okolo postavy, Shift je beh, koliesko približuje, V prepína pohľad z očí, R vystredí kameru alebo vyslobodí postavu, steny zastavia pohyb, otvorené dvere a presklené steny terás sú priechodné, Escape ukončí prechádzku."
            : "Interaktívny technický model. Ťahaním model otáčate, kolieskom alebo gestom priblížite. Klávesy 1 až 5 nastavia pohľady, F zameria výber, H spustí voľný 3D prelet a G prechádzku interiérom."}
      </p>
      <canvas
        ref={canvasRef}
        className="scene-canvas"
        tabIndex={0}
        aria-label="Ovládanie 3D modelu"
        onKeyDown={(event) => {
          if (event.key === "1") applyPreset("axonometric");
          if (event.key === "2") applyPreset("top");
          if (event.key === "3") applyPreset("street");
          if (event.key === "4") applyPreset("garden");
          if (event.key === "5") applyPreset("parcels");
          if (event.key.toLowerCase() === "f") applyPreset("focus");
          if (event.key.toLowerCase() === "h") {
            event.preventDefault();
            setMode(navigationMode === "flight" ? "orbit" : "flight");
          }
          if (event.key.toLowerCase() === "g") {
            event.preventDefault();
            if (navigationMode === "walk") setMode("orbit");
            else controllerRef.current?.enterWalkthrough();
          }
          if (event.key.toLowerCase() === "v" && navigationMode === "walk") {
            event.preventDefault();
            const next = walkView === "third" ? "first" : "third";
            controllerRef.current?.setWalkView(next);
            setWalkView(next);
          }
          if (event.key.toLowerCase() === "r" && navigationMode === "walk") {
            event.preventDefault();
            controllerRef.current?.recoverWalkthrough();
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
        <div
          className={`flight-hud walk-hud${walkHudCollapsed ? " is-collapsed" : ""}`}
          role="region"
          aria-label="Postava, miestnosti a ovládanie prechádzky"
        >
          <span className="sr-only" aria-live="polite">
            Aktuálna zóna: {walkRoom || "Interiér 1.NP"}
          </span>
          <button
            type="button"
            className="walk-hud-toggle"
            aria-expanded={!walkHudCollapsed}
            aria-controls="walk-hud-content"
            aria-label={`${walkHudCollapsed ? "Rozbaliť" : "Zbaliť"} panel postavy, miestností a ovládania prechádzky`}
            onClick={(event) => {
              event.stopPropagation();
              setWalkHudCollapsed((collapsed) => !collapsed);
              // Pointer users can continue with WASD immediately. Keyboard
              // users keep focus on the toggle so Enter can reopen it.
              if (event.detail !== 0) canvasRef.current?.focus({ preventScroll: true });
            }}
          >
            <span className="walk-hud-title">
              {walkHudCollapsed
                ? `POSTAVA · ${walkAvatarOption(walkAvatarId).label.toUpperCase()}`
                : `PRECHÁDZKA · ${walkRoom || "INTERIÉR 1.NP"}`}
            </span>
            <small>{walkHudCollapsed ? "Rozbaliť" : "Zbaliť"}</small>
            <span className="walk-hud-chevron" aria-hidden="true" />
          </button>
          <div
            id="walk-hud-content"
            className="walk-hud-content"
            hidden={walkHudCollapsed}
          >
            <fieldset
              className="walk-avatar-picker"
              aria-busy={pendingWalkAvatarId !== null}
            >
              <legend>Vyber postavu</legend>
              <div className="walk-avatar-options">
                {WALK_AVATARS.map((option) => {
                  const Icon = WALK_AVATAR_ICONS[option.icon];
                  const checked =
                    (pendingWalkAvatarId ?? walkAvatarId) === option.id;
                  return (
                    <label
                      key={option.id}
                      className={`walk-avatar-option${checked ? " is-selected" : ""}${pendingWalkAvatarId === option.id ? " is-loading" : ""}`}
                      title={option.description}
                      onPointerDown={() => {
                        avatarPointerSelectionRef.current = option.id;
                      }}
                    >
                      <input
                        type="radio"
                        name="walk-avatar"
                        value={option.id}
                        checked={checked}
                        disabled={pendingWalkAvatarId !== null}
                        onChange={() => {
                          const pointerSelection =
                            avatarPointerSelectionRef.current === option.id;
                          avatarPointerSelectionRef.current = null;
                          void chooseWalkAvatar(option.id, pointerSelection);
                        }}
                      />
                      <span className="walk-avatar-icon" aria-hidden="true">
                        <Icon size={18} strokeWidth={1.8} />
                      </span>
                      <span className="walk-avatar-copy">
                        <strong>{option.label}</strong>
                        <small>{option.tagline}</small>
                      </span>
                      <span className="walk-avatar-check" aria-hidden="true" />
                    </label>
                  );
                })}
              </div>
              <span className="sr-only" aria-live="polite">
                {walkAvatarMessage}
              </span>
              {walkAvatarError && (
                <small className="walk-avatar-error" role="alert">
                  {walkAvatarError}
                </small>
              )}
            </fieldset>
            <strong>WASD chôdza · ťahanie otáča kameru · Shift beh</strong>
            <small>Koliesko priblíženie · Alt pomaly · V {walkView === "third" ? "pohľad z očí" : "tretia osoba"} · R vyslobodiť · Esc koniec</small>
            <div className="walk-rooms" role="group" aria-label="Prejsť do miestnosti">
              <button
                type="button"
                className={`walk-recover${walkBlocked ? " is-needed" : ""}`}
                aria-label={walkBlocked ? "Vyslobodiť zaseknutú postavu" : "Vystrediť kameru za postavou"}
                onClick={(event) => {
                  event.stopPropagation();
                  controllerRef.current?.recoverWalkthrough();
                }}
              >
                {walkBlocked ? "Vyslobodiť" : "Vystrediť"}
              </button>
              {INTERIOR_ROOMS.map((room) => (
                <button
                  key={room.id}
                  type="button"
                  aria-label={`Prejsť do ${room.number} ${room.name}`}
                  onClick={(event) => {
                    event.stopPropagation();
                    controllerRef.current?.enterWalkthrough(room.id);
                  }}
                >
                  {room.number}
                </button>
              ))}
            </div>
          </div>
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
            aria-label={navigationMode === "walk" ? "Dotykové ovládanie chôdze" : "Dotykové ovládanie voľného preletu"}
          >
            {([
              ["forward", "↑", "Letieť dopredu"],
              ["left", "←", "Letieť doľava"],
              ["backward", "↓", "Letieť dozadu"],
              ["right", "→", "Letieť doprava"],
              ["up", "+", "Stúpať"],
              ["down", "−", "Klesať"],
            ] as const)
              .filter(([command]) => navigationMode === "flight" || (command !== "up" && command !== "down"))
              .map(([command, glyph, label]) => (
              <button
                key={command}
                className={`flight-command flight-${command}`}
                aria-label={
                  navigationMode === "walk"
                    ? label.replace("Letieť", "Kráčať")
                    : label
                }
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
            <button
              className="flight-exit"
              onClick={(event) => {
                event.stopPropagation();
                setMode("orbit");
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
