"use client";

import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from "react";
import {
  CarFront,
  CircleHelp,
  Command as CommandGlyph,
  Crosshair,
  Eye,
  Footprints,
  Fullscreen,
  LogOut,
  Plane,
  X,
  type LucideIcon,
} from "lucide-react";

import type {
  CameraPreset,
  TwinSceneController,
} from "@/lib/babylon-scene";
import {
  doorInteractionPromptLabel,
  type DoorInteractionSnapshot,
} from "@/lib/babylon-doors";
import type { FoundationStrip, LayerId, ViewMode } from "@/lib/twin-site";
import type {
  FlightCommand,
  NavigationMode,
  RenderQualityProfile,
} from "@/lib/twin-viewport-contract";
import { CAMERA_PRESETS, type CameraPresetId } from "@/lib/twin-commands";
import {
  WORKSPACE_MODE_OPTIONS,
  type ChromeContract,
  type WorkspaceMode,
} from "@/lib/twin-ui-mode";
import {
  GARAGE_VEHICLE,
  garageActionForState,
  garageActionLabel,
  garageParkingStatus,
  type GarageParkingState,
} from "@/lib/twin-garage";
import {
  DEFAULT_WALK_AVATAR_ID,
  WALK_AVATAR_STORAGE_KEY,
  isWalkAvatarId,
  walkAvatarOption,
  type WalkAvatarId,
} from "@/lib/twin-avatar";
import { COMMAND_ICONS } from "./hud-icons";

export interface BabylonViewportHandle {
  setCameraPreset: (preset: CameraPreset) => void;
  setNavigationMode: (mode: NavigationMode) => void;
  enterWalkthrough: (roomId?: string) => void;
  setWalkView: (view: "third" | "first") => void;
  setWalkAvatar: (id: WalkAvatarId) => Promise<void>;
  recoverWalkthrough: () => void;
  setFlightCommand: (command: FlightCommand, active: boolean) => void;
  nudgeFlight: (command: FlightCommand) => void;
  isGarageCinematicActive: () => boolean;
}

interface BabylonViewportProps {
  readonly foundations: readonly FoundationStrip[];
  readonly selectionId: string | null;
  readonly visibleLayers: Readonly<Record<LayerId, boolean>>;
  readonly viewMode: ViewMode;
  readonly navigationMode: NavigationMode;
  readonly workspace: WorkspaceMode;
  readonly chrome: ChromeContract;
  readonly chromeVisible: boolean;
  readonly helpOpen: boolean;
  readonly onSelect: (id: string) => void;
  readonly onNavigationModeChange: (mode: NavigationMode) => void;
  readonly onWorkspaceChange: (workspace: WorkspaceMode) => void;
  readonly onParcelOverviewRequest: () => void;
  readonly onCameraPreset: (preset: CameraPresetId) => void;
  readonly onOpenPalette: () => void;
  readonly onToggleHelp: () => void;
  readonly onWalkAvatarChange: (id: WalkAvatarId) => void;
  readonly onWalkViewChange: (view: "third" | "first") => void;
}

const MOVEMENT_ICONS: Readonly<Record<"flight" | "walk", LucideIcon>> = {
  flight: Plane,
  walk: Footprints,
};

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
    workspace,
    chrome,
    chromeVisible,
    helpOpen,
    onSelect,
    onNavigationModeChange,
    onWorkspaceChange,
    onParcelOverviewRequest,
    onCameraPreset,
    onOpenPalette,
    onToggleHelp,
    onWalkAvatarChange,
    onWalkViewChange,
  },
  ref,
) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const hudRef = useRef<HTMLDivElement>(null);
  const controllerRef = useRef<TwinSceneController | null>(null);
  const onSelectRef = useRef(onSelect);
  const navigationModeRef = useRef(navigationMode);
  const onNavigationModeChangeRef = useRef(onNavigationModeChange);
  const onWalkAvatarChangeRef = useRef(onWalkAvatarChange);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [quality, setQuality] = useState<RenderQualityProfile | null>(null);
  const [walkRoom, setWalkRoom] = useState("");
  const [walkRoomId, setWalkRoomId] = useState<string | null>(null);
  const [garageParkingState, setGarageParkingState] =
    useState<GarageParkingState>("away");
  const [walkView, setWalkView] = useState<"third" | "first">("third");
  const [walkBlocked, setWalkBlocked] = useState(false);
  const [doorInteraction, setDoorInteraction] =
    useState<DoorInteractionSnapshot | null>(null);
  const [walkAvatarId, setWalkAvatarId] = useState<WalkAvatarId>(
    DEFAULT_WALK_AVATAR_ID,
  );
  const [walkAvatarMessage, setWalkAvatarMessage] = useState("");

  onSelectRef.current = onSelect;
  navigationModeRef.current = navigationMode;
  onNavigationModeChangeRef.current = onNavigationModeChange;
  onWalkAvatarChangeRef.current = onWalkAvatarChange;

  const applyWalkAvatar = async (id: WalkAvatarId) => {
    const controller = controllerRef.current;
    if (!controller || controller.isGarageCinematicActive()) return;
    const option = walkAvatarOption(id);
    setWalkAvatarMessage(`Načítavam postavu ${option.label}.`);
    try {
      await controller.setWalkAvatar(id);
      setWalkAvatarId(id);
      onWalkAvatarChangeRef.current(id);
      setWalkAvatarMessage(`Postava ${option.label} je pripravená.`);
      try {
        window.localStorage.setItem(WALK_AVATAR_STORAGE_KEY, id);
      } catch {
        // A device-local preference is optional; the in-memory choice remains.
      }
    } catch {
      const current = walkAvatarOption(controller.getWalkAvatar());
      setWalkAvatarId(current.id);
      onWalkAvatarChangeRef.current(current.id);
      setWalkAvatarMessage(
        `Postavu ${option.label} sa nepodarilo načítať. Zostáva ${current.label}.`,
      );
    }
  };

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
      onWalkViewChange(view);
    },
    async setWalkAvatar(id) {
      await applyWalkAvatar(id);
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
    isGarageCinematicActive() {
      return controllerRef.current?.isGarageCinematicActive() ?? false;
    },
  }));

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
            onWalkAvatarChangeRef.current(storedAvatarId);
            void createdController.setWalkAvatar(storedAvatarId);
          }
        } catch {
          // The choice remains fully usable when browser storage is blocked.
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
      setWalkRoomId(null);
      setWalkBlocked(false);
      setDoorInteraction(null);
      return;
    }
    const read = () => {
      const room = controllerRef.current?.getWalkRoom();
      setWalkRoom(
        room ? `${room.number} · ${room.name}` : "Exteriér · terasa a záhrada",
      );
      setWalkRoomId(room?.id ?? null);
      setWalkBlocked(controllerRef.current?.isWalkBlocked() ?? false);
      setDoorInteraction(controllerRef.current?.getDoorInteraction() ?? null);
      setGarageParkingState(
        controllerRef.current?.getGarageParkingState() ?? "away",
      );
    };
    read();
    const timer = window.setInterval(read, 200);
    return () => window.clearInterval(timer);
  }, [status, navigationMode]);

  const setMode = (mode: NavigationMode) => {
    const controller = controllerRef.current;
    if (controller?.isGarageCinematicActive()) return false;
    controller?.setNavigationMode(mode);
    onNavigationModeChangeRef.current(mode);
    return true;
  };

  const applyPreset = (preset: CameraPreset) => {
    if (controllerRef.current?.isGarageCinematicActive()) return;
    if (preset === "parcels") onParcelOverviewRequest();
    if (!setMode("orbit")) return;
    controllerRef.current?.setCameraPreset(preset);
  };

  const toggleWalkView = () => {
    if (controllerRef.current?.isGarageCinematicActive()) return;
    const next = walkView === "third" ? "first" : "third";
    controllerRef.current?.setWalkView(next);
    setWalkView(next);
    onWalkViewChange(next);
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

  const doorPromptStatus = doorInteraction
    ? doorInteractionPromptLabel(doorInteraction)
    : "";

  const garageAction = garageActionForState(garageParkingState);
  const garageStatus = garageParkingStatus(garageParkingState);
  /** The garage cinematic owns the camera; every control waits it out. */
  const sceneBusy = !garageAction;

  const requestGarageVehicleAction = () => {
    if (!garageAction) return;
    const controller = controllerRef.current;
    if (!controller?.requestGarageVehicleAction(garageAction)) return;
    setGarageParkingState(controller.getGarageParkingState());
  };

  const experience = workspace === "experience";
  const contextTitle =
    navigationMode === "walk"
      ? walkRoom || "Interiér 1.NP"
      : navigationMode === "flight"
        ? "Voľný prelet"
        : "Dom 6012/26";
  const contextMeta =
    navigationMode === "walk"
      ? `${walkAvatarOption(walkAvatarId).label} · WASD · E dvere`
      : navigationMode === "flight"
        ? "WASD pohyb · Q/E výška · Shift turbo"
        : "Březí u Mikulova · 753 m²";

  // Focusing the current selection is contextual: it belongs to the inspector,
  // the F key and the palette, not to a permanent slot over the render.
  const presets = CAMERA_PRESETS.filter((preset) => !preset.contextual);

  useEffect(() => {
    const hud = hudRef.current;
    if (!hud || navigationMode === "orbit") return;
    // The scene reads WASD from the canvas, so a pointer click anywhere in the
    // interface has to hand the keyboard straight back or movement dies on the
    // first tap. Keyboard activation reports detail 0 and keeps its place.
    const restoreCanvasFocus = (event: MouseEvent) => {
      if (event.detail === 0) return;
      canvasRef.current?.focus({ preventScroll: true });
    };
    hud.addEventListener("click", restoreCanvasFocus);
    return () => hud.removeEventListener("click", restoreCanvasFocus);
  }, [navigationMode, status]);

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
            ? "Prechádzka domom s voliteľnou postavou. Postavu vyberiete v paneli príkazov pod Command K, kde nájdete aj všetkých dvanásť miestností. W A S D ovládajú chôdzu v smere kamery, ťahaním otáčate kameru okolo postavy, Shift je beh, E alebo dotyk na výzvu otvorí a zavrie blízke dvere alebo dvierka spotrebičov, koliesko približuje, V prepína pohľad z očí, R vystredí kameru alebo vyslobodí postavu a Escape ukončí prechádzku. Všetkých 18 dverových systémov aj obe dvierka spotrebičov majú animovaný pohyb a fyzickú kolíziu."
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
            toggleWalkView();
          }
          if (event.key.toLowerCase() === "r" && navigationMode === "walk") {
            event.preventDefault();
            controllerRef.current?.recoverWalkthrough();
          }
        }}
      />

      <span className="sr-only" aria-live="polite">
        {walkAvatarMessage}
      </span>

      {status === "ready" && (
        <div
          ref={hudRef}
          className="hud"
          data-autohide={chrome.autoHide}
          data-visible={chromeVisible}
          data-pad={chrome.virtualPad}
        >
          <div className="hud-row hud-row-top">
            <div className="hud-slot hud-start">
              {experience ? (
                <div className="context-pill glass hud-fade">
                  <span className="context-dot" aria-hidden="true" />
                  <span className="context-copy">
                    <strong>{contextTitle}</strong>
                    <small>{contextMeta}</small>
                  </span>
                </div>
              ) : (
                <div className="truth-card glass hud-fade">
                  <div className="truth-live">
                    <i aria-hidden="true" />
                    AKTUÁLNY KATASTER · ROHOVÁ
                  </div>
                  <strong>6012/26</strong>
                  <div className="truth-meta">
                    <span>753 m²</span>
                    <i aria-hidden="true" />
                    <span>EPSG:5514</span>
                  </div>
                  <small>ČÚZK · overené 24. 8. 2026</small>
                </div>
              )}
            </div>
            <div className="hud-slot hud-center" />
            <div className="hud-slot hud-end">
              <div className="hud-controls hud-fade">
                <div
                  className="segmented glass"
                  role="group"
                  aria-label="Režim pracovného priestoru"
                >
                  {WORKSPACE_MODE_OPTIONS.map((option) => {
                    const Icon = COMMAND_ICONS[option.id];
                    return (
                      <button
                        key={option.id}
                        type="button"
                        aria-pressed={workspace === option.id}
                        aria-label={`${option.label} · ${option.tagline}`}
                        onClick={() => onWorkspaceChange(option.id)}
                      >
                        <Icon size={16} strokeWidth={1.8} aria-hidden="true" />
                        <span>{option.label}</span>
                      </button>
                    );
                  })}
                </div>
                <button
                  type="button"
                  className="hud-icon-button glass"
                  aria-label="Ovládanie a klávesové skratky"
                  aria-expanded={helpOpen}
                  onClick={onToggleHelp}
                >
                  <CircleHelp size={18} />
                </button>
                <button
                  type="button"
                  className="hud-icon-button glass"
                  aria-label="Zobraziť na celej obrazovke"
                  onClick={() => {
                    if (document.fullscreenElement) void document.exitFullscreen();
                    else void document.documentElement.requestFullscreen();
                  }}
                >
                  <Fullscreen size={18} />
                </button>
              </div>
              {helpOpen && (
                <aside className="help-sheet" aria-label="Ovládanie modelu">
                  <header>
                    <strong>Ovládanie modelu</strong>
                    <button
                      type="button"
                      aria-label="Zavrieť pomoc"
                      onClick={onToggleHelp}
                    >
                      <X size={16} />
                    </button>
                  </header>
                  <dl>
                    <div>
                      <dt>Príkazy</dt>
                      <dd>⌘K</dd>
                    </div>
                    <div>
                      <dt>Prepnúť režim</dt>
                      <dd>M</dd>
                    </div>
                    <div>
                      <dt>Orbit a zoom</dt>
                      <dd>ťahanie · koliesko</dd>
                    </div>
                    <div>
                      <dt>Pohľady</dt>
                      <dd>1 · 2 · 3 · 4 · 5 · F</dd>
                    </div>
                    <div>
                      <dt>Voľný prelet</dt>
                      <dd>H · WASD · Q/E</dd>
                    </div>
                    <div>
                      <dt>Prechádzka</dt>
                      <dd>G · WASD</dd>
                    </div>
                    <div>
                      <dt>Dvere a dvierka</dt>
                      <dd>E</dd>
                    </div>
                    <div>
                      <dt>Pohľad z očí</dt>
                      <dd>V</dd>
                    </div>
                    <div>
                      <dt>Vystrediť postavu</dt>
                      <dd>R</dd>
                    </div>
                    <div>
                      <dt>Rýchlosť</dt>
                      <dd>Shift · Alt</dd>
                    </div>
                    <div>
                      <dt>Späť do orbitu</dt>
                      <dd>Esc</dd>
                    </div>
                  </dl>
                </aside>
              )}
            </div>
          </div>

          <div className="hud-row hud-row-middle">
            {chrome.reticle && <span className="reticle" aria-hidden="true" />}
          </div>

          <div className="hud-row hud-row-bottom">
            <div className="hud-slot hud-start">
              {/* Provenance has one home: the evidence rail in Documentation.
                  A floating copy of it over the render was the duplication
                  that made the old interface feel noisy. */}
              <div
                className="touch-pad"
                data-enabled={chrome.virtualPad}
                data-vertical={navigationMode === "flight"}
                role="group"
                aria-label={
                  navigationMode === "walk"
                    ? "Dotykové ovládanie chôdze"
                    : "Dotykové ovládanie voľného preletu"
                }
              >
                {(
                  [
                    ["forward", "↑", "Kráčať dopredu", "Letieť dopredu"],
                    ["left", "←", "Kráčať doľava", "Letieť doľava"],
                    ["backward", "↓", "Kráčať dozadu", "Letieť dozadu"],
                    ["right", "→", "Kráčať doprava", "Letieť doprava"],
                    ["up", "+", "Stúpať", "Stúpať"],
                    ["down", "−", "Klesať", "Klesať"],
                  ] as const
                )
                  .filter(
                    ([command]) =>
                      navigationMode === "flight" ||
                      (command !== "up" && command !== "down"),
                  )
                  .map(([command, glyph, walkLabel, flightLabel]) => (
                    <button
                      key={command}
                      type="button"
                      className={`touch-${command}`}
                      disabled={sceneBusy}
                      aria-label={
                        navigationMode === "walk" ? walkLabel : flightLabel
                      }
                      onPointerDown={(event) =>
                        holdFlightCommand(command, true, event)
                      }
                      onPointerUp={(event) =>
                        holdFlightCommand(command, false, event)
                      }
                      onPointerCancel={(event) =>
                        holdFlightCommand(command, false, event)
                      }
                      onLostPointerCapture={(event) =>
                        holdFlightCommand(command, false, event)
                      }
                      onClick={(event) => {
                        event.stopPropagation();
                        if (event.detail === 0)
                          controllerRef.current?.nudgeFlight(command);
                      }}
                    >
                      <span aria-hidden="true">{glyph}</span>
                    </button>
                  ))}
              </div>
            </div>

            <div className="hud-slot hud-center">
              {walkRoomId === GARAGE_VEHICLE.roomId && (
                <div
                  className="vehicle-cta glass hud-fade"
                  role="region"
                  aria-label="Ovládanie auta v garáži"
                  aria-busy={sceneBusy}
                  data-busy={sceneBusy}
                >
                  <span className="sr-only" aria-live="polite">
                    {garageStatus}
                  </span>
                  <span className="vehicle-icon" aria-hidden="true">
                    <CarFront size={18} strokeWidth={1.8} />
                  </span>
                  <span className="vehicle-copy">
                    <small>ŠKODA SUPERB COMBI IV · GARÁŽ 1.12</small>
                    <strong>{garageStatus}</strong>
                  </span>
                  <button
                    type="button"
                    disabled={sceneBusy}
                    aria-label={
                      garageAction ? garageActionLabel(garageAction) : garageStatus
                    }
                    onClick={(event) => {
                      event.stopPropagation();
                      requestGarageVehicleAction();
                    }}
                  >
                    {garageAction ? garageActionLabel(garageAction) : "Prebieha…"}
                  </button>
                </div>
              )}

              {navigationMode === "walk" && doorInteraction && (
                <button
                  type="button"
                  className="door-prompt glass"
                  aria-keyshortcuts="E"
                  aria-disabled={!doorInteraction.action}
                  aria-busy={
                    doorInteraction.phase === "OPENING" ||
                    doorInteraction.phase === "CLOSING"
                  }
                  data-blocked={Boolean(doorInteraction.blockedMessage)}
                  data-phase={doorInteraction.phase.toLowerCase()}
                  aria-label={`${doorPromptStatus}. ${doorInteraction.label}`}
                  onClick={(event) => {
                    event.stopPropagation();
                    if (!doorInteraction.action) return;
                    const controller = controllerRef.current;
                    const restoreCanvasFocus = event.detail !== 0;
                    controller?.toggleDoorInteraction(restoreCanvasFocus);
                    setDoorInteraction(controller?.getDoorInteraction() ?? null);
                  }}
                >
                  <kbd aria-hidden="true">E</kbd>
                  <span className="door-prompt-copy">
                    <strong>{doorPromptStatus}</strong>
                    <small>{doorInteraction.label}</small>
                  </span>
                  <span className="sr-only" aria-live="polite">
                    {doorPromptStatus}. {doorInteraction.label}.
                  </span>
                </button>
              )}

              <div
                className="dock glass hud-fade"
                role="toolbar"
                aria-label="Kamera a navigácia"
              >
                {chrome.cameraPresets && (
                  <div className="dock-group">
                    {presets.map((preset) => {
                      const Icon = COMMAND_ICONS[preset.icon];
                      return (
                        <button
                          key={preset.id}
                          type="button"
                          className="dock-button"
                          aria-label={`${preset.label} · ${preset.detail}`}
                          aria-keyshortcuts={preset.shortcut}
                          onClick={() => onCameraPreset(preset.id)}
                        >
                          <Icon size={17} strokeWidth={1.7} />
                          <span>{preset.label}</span>
                          <kbd className="key">{preset.shortcut}</kbd>
                        </button>
                      );
                    })}
                  </div>
                )}

                {experience && (
                  <>
                    {chrome.cameraPresets && (
                      <span className="dock-divider" aria-hidden="true" />
                    )}
                    <div className="dock-group">
                      {(["flight", "walk"] as const).map((mode) => {
                        const Icon = MOVEMENT_ICONS[mode];
                        const activeMode = navigationMode === mode;
                        const label = mode === "flight" ? "Prelet" : "Prechádzka";
                        return (
                          <button
                            key={mode}
                            type="button"
                            className="dock-button"
                            data-accent="true"
                            aria-pressed={activeMode}
                            aria-keyshortcuts={mode === "flight" ? "H" : "G"}
                            aria-label={
                              activeMode
                                ? `Ukončiť ${label.toLowerCase()}`
                                : mode === "flight"
                                  ? "Spustiť voľný 3D prelet"
                                  : "Prejsť sa interiérom domu"
                            }
                            disabled={sceneBusy}
                            onClick={() => {
                              if (activeMode) {
                                setMode("orbit");
                                return;
                              }
                              if (mode === "walk") {
                                if (controllerRef.current?.isGarageCinematicActive())
                                  return;
                                onNavigationModeChangeRef.current("walk");
                                controllerRef.current?.enterWalkthrough();
                                return;
                              }
                              setMode("flight");
                            }}
                          >
                            <Icon size={17} strokeWidth={1.7} />
                            <span>{label}</span>
                            <kbd className="key">
                              {mode === "flight" ? "H" : "G"}
                            </kbd>
                          </button>
                        );
                      })}
                    </div>
                  </>
                )}

                {navigationMode === "walk" && (
                  <>
                    <span className="dock-divider" aria-hidden="true" />
                    <div className="dock-group">
                      <button
                        type="button"
                        className="dock-button"
                        disabled={sceneBusy}
                        aria-keyshortcuts="V"
                        aria-label={
                          walkView === "third"
                            ? "Prepnúť na pohľad z očí"
                            : "Prepnúť na pohľad tretej osoby"
                        }
                        onClick={toggleWalkView}
                      >
                        <Eye size={17} strokeWidth={1.7} />
                        <span>
                          {walkView === "third" ? "Z očí" : "Tretia osoba"}
                        </span>
                        <kbd className="key">V</kbd>
                      </button>
                      <button
                        type="button"
                        className="dock-button"
                        disabled={sceneBusy}
                        aria-keyshortcuts="R"
                        aria-label={
                          walkBlocked
                            ? "Vyslobodiť zaseknutú postavu"
                            : "Vystrediť kameru za postavou"
                        }
                        onClick={(event) => {
                          event.stopPropagation();
                          controllerRef.current?.recoverWalkthrough();
                        }}
                      >
                        <Crosshair size={17} strokeWidth={1.7} />
                        <span>{walkBlocked ? "Vyslobodiť" : "Vystrediť"}</span>
                        <kbd className="key">R</kbd>
                      </button>
                    </div>
                  </>
                )}

                {experience && navigationMode !== "orbit" && (
                  <>
                    <span className="dock-divider" aria-hidden="true" />
                    <button
                      type="button"
                      className="dock-button"
                      disabled={sceneBusy}
                      aria-label="Ukončiť a vrátiť sa k obehu okolo modelu"
                      onClick={() => setMode("orbit")}
                    >
                      <LogOut size={17} strokeWidth={1.7} />
                      <span>Ukončiť</span>
                      <kbd className="key">Esc</kbd>
                    </button>
                  </>
                )}

                <span className="dock-divider" aria-hidden="true" />
                <button
                  type="button"
                  className="dock-command"
                  aria-label="Otvoriť príkazy modelu"
                  aria-keyshortcuts="Meta+K Control+K"
                  onClick={onOpenPalette}
                >
                  <CommandGlyph size={15} strokeWidth={1.9} />
                  <span>Príkazy</span>
                  <kbd className="key">K</kbd>
                </button>
              </div>
            </div>

            <div className="hud-slot hud-end">
              {chrome.surveyOverlays && (
                <div
                  className="survey-compass glass hud-fade"
                  aria-label="Smer kladnej osi Y lokálneho pôdorysu"
                >
                  <span>Y</span>
                  <i aria-hidden="true" />
                  <small>+ do parcely</small>
                </div>
              )}
              {chrome.surveyOverlays && quality && (
                <div
                  className="render-readout glass hud-fade"
                  aria-label={`Retina render ${qualityRatio}-násobné rozlíšenie, MSAA ${quality.msaaSamples}-krát`}
                >
                  <span>RETINA</span>
                  <small>
                    {qualityRatio}× · MSAA {quality.msaaSamples}×
                  </small>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {status === "loading" && (
        <div className="viewport-state" role="status">
          <span className="drawing-loader" aria-hidden="true" />
          <strong>Skladám digitálne dvojča</strong>
          <small>Kataster · dom · základy · komunikácia · siete</small>
        </div>
      )}
      {status === "error" && (
        <div className="viewport-state" role="alert">
          <strong>3D zobrazenie nie je dostupné</strong>
          <small>Model a parametre môžete ďalej používať cez Prieskumník.</small>
        </div>
      )}
    </div>
  );
});
