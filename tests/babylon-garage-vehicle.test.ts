import { NullEngine } from "@babylonjs/core/Engines/nullEngine";
import { Vector3 } from "@babylonjs/core/Maths/math.vector";
import { UniversalCamera } from "@babylonjs/core/Cameras/universalCamera";
import { Scene } from "@babylonjs/core/scene";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import { afterEach, describe, expect, it } from "vitest";

import { buildGarageSuperbVehicle } from "../lib/babylon-garage-vehicle";
import { GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM } from "../lib/twin-superb-combi";

const boundsOf = (meshes: readonly AbstractMesh[]) => {
  for (const mesh of meshes) mesh.computeWorldMatrix(true);
  const boxes = meshes.map((mesh) => mesh.getBoundingInfo().boundingBox);
  const minimum = {
    x: Math.min(...boxes.map(({ minimumWorld }) => minimumWorld.x)),
    y: Math.min(...boxes.map(({ minimumWorld }) => minimumWorld.y)),
    z: Math.min(...boxes.map(({ minimumWorld }) => minimumWorld.z)),
  };
  const maximum = {
    x: Math.max(...boxes.map(({ maximumWorld }) => maximumWorld.x)),
    y: Math.max(...boxes.map(({ maximumWorld }) => maximumWorld.y)),
    z: Math.max(...boxes.map(({ maximumWorld }) => maximumWorld.z)),
  };
  return {
    x: maximum.x - minimum.x,
    y: maximum.y - minimum.y,
    z: maximum.z - minimum.z,
  };
};

describe("Babylon Superb Combi visual", () => {
  let engine: NullEngine | null = null;
  let scene: Scene | null = null;

  afterEach(() => {
    scene?.dispose();
    engine?.dispose();
    scene = null;
    engine = null;
  });

  it("builds a closed, detailed estate with four production-size wheels", () => {
    engine = new NullEngine();
    scene = new Scene(engine);
    scene.activeCamera = new UniversalCamera(
      "superb-test-camera",
      new Vector3(6, 2, -8),
      scene,
    );

    const visual = buildGarageSuperbVehicle(scene, {
      realisticOnly: () => undefined,
      castShadow: () => undefined,
      register: () => undefined,
    });
    visual.root.setEnabled(true);
    scene.render();

    expect(visual.root.metadata).toMatchObject({
      vehicleGeneration: "SUPERB-IV-COMBI",
      productionDimensionsMm: GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM,
      visualLengthScale: 1,
      visualReference: "skoda-superb-combi-official-technical-sheet-2024-06-03-and-client-photos-2026-08-25",
      referenceViews: ["side-profile", "front-three-quarter"],
      bodyConstruction: "curved-loft-conforming-panels",
    });
    expect(visual.wheelSpins).toHaveLength(4);
    expect(visual.frontSteering).toHaveLength(2);

    const names = scene.meshes.map(({ name }) => name);
    expect(
      names.filter((name) => name.includes("bočné presklenie kabíny")),
    ).toHaveLength(2);
    expect(names.filter((name) => name.includes("pneumatika 235/40 R19"))).toHaveLength(4);
    expect(names.filter((name) => name.includes("strešná lyžina"))).toHaveLength(2);
    expect(names).toEqual(
      expect.arrayContaining([
        expect.stringContaining("lisovaná karoséria Modern Solid"),
        expect.stringContaining("akustické čelné sklo"),
        expect.stringContaining("vyhrievané sklo piatych dverí"),
        expect.stringContaining("Matrix LED modul"),
        expect.stringContaining("kryštalické zadné svetlo C"),
        expect.stringContaining("chrómové orámovanie presklenia"),
      ]),
    );

    const byPart = (part: string) =>
      scene!.meshes.filter(({ metadata }) => metadata?.vehiclePart === part);
    expect(byPart("body-shell")).toHaveLength(1);
    expect(byPart("side-glass")).toHaveLength(2);
    expect(byPart("windshield")).toHaveLength(1);
    expect(byPart("rear-window")).toHaveLength(1);
    expect(byPart("window-pillar")).toHaveLength(4);
    expect(byPart("window-chrome-surround")).toHaveLength(2);
    expect(byPart("external-mirror")).toHaveLength(2);
    expect(byPart("door-handle")).toHaveLength(4);
    expect(byPart("door-seam")).toHaveLength(6);
    expect(byPart("roof-rail")).toHaveLength(2);
    expect(byPart("rocker-trim")).toHaveLength(2);
    expect(byPart("wheel-well")).toHaveLength(4);
    expect(byPart("wheel-arch")).toHaveLength(4);
    expect(byPart("front-grille")).toHaveLength(1);
    expect(byPart("front-grille-slat")).toHaveLength(13);
    expect(byPart("headlamp")).toHaveLength(2);
    expect(byPart("headlamp-module")).toHaveLength(6);
    expect(byPart("drl")).toHaveLength(2);
    expect(byPart("lower-intake")).toHaveLength(1);
    expect(byPart("side-intake")).toHaveLength(2);
    expect(byPart("rear-lamp")).toHaveLength(2);
    expect(byPart("rear-wrap-lamp")).toHaveLength(2);
    expect(byPart("rear-light-guide")).toHaveLength(4);
    expect(byPart("tire")).toHaveLength(4);
    expect(byPart("rim")).toHaveLength(4);
    expect(byPart("wheel-spoke")).toHaveLength(40);

    for (const tire of byPart("tire")) {
      const size = boundsOf([tire]);
      expect(size.x).toBeCloseTo(0.671, 2);
      expect(size.y).toBeCloseTo(0.671, 2);
      expect(size.z).toBeCloseTo(0.235, 2);
    }

    const visibleEnvelope = boundsOf(
      scene.meshes.filter(
        (mesh) =>
          mesh.isEnabled() &&
          mesh.isVisible &&
          mesh.metadata?.vehicleCollider !== true &&
          mesh.getTotalVertices() > 0,
      ),
    );
    expect(visibleEnvelope.x).toBeCloseTo(
      GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.length / 1_000,
      1,
    );
    expect(visibleEnvelope.y).toBeCloseTo(
      GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.height / 1_000,
      1,
    );
    expect(visibleEnvelope.z).toBeCloseTo(
      GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.mirrorWidth / 1_000,
      1,
    );

    const colliders = scene.meshes.filter(
      ({ metadata }) => metadata?.vehicleCollider === true,
    );
    expect(colliders).toHaveLength(2);
    expect(colliders.every(({ isVisible }) => !isVisible)).toBe(true);
    expect(colliders.every(({ checkCollisions }) => checkCollisions)).toBe(true);
    expect(scene.meshes.filter(({ checkCollisions }) => checkCollisions)).toEqual(
      colliders,
    );
    expect(colliders.every(({ parent }) => parent === visual.root)).toBe(true);
    expect(
      colliders.every(
        ({ metadata }) =>
          metadata?.cameraOccluder === true &&
          metadata?.dynamicCameraOccluder === true,
      ),
    ).toBe(true);
    const lowerCollider = colliders.find(({ name }) =>
      name.includes("spodný kolízny obal"),
    )!;
    const lowerBounds = lowerCollider.getBoundingInfo().boundingBox;
    expect(lowerBounds.maximum.x - lowerBounds.minimum.x).toBeCloseTo(
      GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.length / 1_000,
      6,
    );
    for (const collider of colliders) {
      const size = boundsOf([collider]);
      expect(size.x).toBeLessThanOrEqual(4.902 + 1e-6);
      expect(size.y).toBeLessThanOrEqual(1.482 + 1e-6);
      expect(size.z).toBeLessThanOrEqual(1.849 + 1e-6);
    }

    for (const mesh of scene.meshes.filter((candidate) => candidate.getTotalVertices() > 0)) {
      mesh.computeWorldMatrix(true);
      const bounds = mesh.getBoundingInfo().boundingBox;
      expect(
        [
          ...bounds.minimumWorld.asArray(),
          ...bounds.maximumWorld.asArray(),
        ].every(Number.isFinite),
        mesh.name,
      ).toBe(true);
    }
  });
});
