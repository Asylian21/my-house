"use client";

import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import type {
  CameraPreset,
  TwinSceneController,
} from "@/lib/babylon-scene";
import type { FoundationStrip, LayerId, ViewMode } from "@/lib/twin-site";

export interface BabylonViewportHandle {
  setCameraPreset: (preset: CameraPreset) => void;
}

interface BabylonViewportProps {
  foundations: readonly FoundationStrip[];
  selectionId: string | null;
  visibleLayers: Readonly<Record<LayerId, boolean>>;
  viewMode: ViewMode;
  onSelect: (id: string) => void;
}

export const BabylonViewport = forwardRef<
  BabylonViewportHandle,
  BabylonViewportProps
>(function BabylonViewport(
  { foundations, selectionId, visibleLayers, viewMode, onSelect },
  ref,
) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const controllerRef = useRef<TwinSceneController | null>(null);
  const onSelectRef = useRef(onSelect);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  onSelectRef.current = onSelect;

  useImperativeHandle(ref, () => ({
    setCameraPreset(preset) {
      controllerRef.current?.setCameraPreset(preset);
    },
  }), []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let active = true;
    let observer: ResizeObserver | undefined;

    void import("@/lib/babylon-scene")
      .then(({ createTwinScene }) => {
        if (!active) return;
        const controller = createTwinScene(canvas, (id) => onSelectRef.current(id));
        controllerRef.current = controller;
        observer = new ResizeObserver(() => controller.resize());
        observer.observe(canvas);
        setStatus("ready");
      })
      .catch(() => {
        if (active) setStatus("error");
      });

    return () => {
      active = false;
      observer?.disconnect();
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

  return (
    <div
      className="canvas-region"
      role="region"
      aria-label="3D model parcely, domu, základov, komunikácie a inžinierskych sietí"
      aria-describedby="canvas-instructions"
    >
      <p id="canvas-instructions" className="sr-only">
        Interaktívny technický model. Ťahaním model otáčate, kolieskom alebo
        gestom priblížite. Kláves 1 nastaví axonometriu, 2 pôdorys a F zameria
        vybraný prvok. Kláves 4 otvorí záhradný prezentačný pohľad.
      </p>
      <canvas
        ref={canvasRef}
        className="scene-canvas"
        tabIndex={0}
        aria-label="Ovládanie 3D modelu"
        onKeyDown={(event) => {
          if (event.key === "1") controllerRef.current?.setCameraPreset("axonometric");
          if (event.key === "2") controllerRef.current?.setCameraPreset("top");
          if (event.key === "3") controllerRef.current?.setCameraPreset("street");
          if (event.key === "4") controllerRef.current?.setCameraPreset("garden");
          if (event.key.toLowerCase() === "f") controllerRef.current?.setCameraPreset("focus");
        }}
      />
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
