import { NullEngine } from "@babylonjs/core/Engines/nullEngine";
import { Vector3 } from "@babylonjs/core/Maths/math.vector";
import { UniversalCamera } from "@babylonjs/core/Cameras/universalCamera";
import { Scene } from "@babylonjs/core/scene";
import { afterEach, describe, expect, it } from "vitest";

import { buildGarageSuperbVehicle } from "../lib/babylon-garage-vehicle";
import { GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM } from "../lib/twin-superb-combi";

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
    });
    expect(visual.wheelSpins).toHaveLength(4);
    expect(visual.frontSteering).toHaveLength(2);

    const names = scene.meshes.map(({ name }) => name);
    expect(names.filter((name) => name.includes("bočné sklo"))).toHaveLength(6);
    expect(names.filter((name) => name.includes("pneumatika 235/40 R19"))).toHaveLength(4);
    expect(names.filter((name) => name.includes("strešná lyžina"))).toHaveLength(2);
    expect(names).toEqual(
      expect.arrayContaining([
        expect.stringContaining("lisovaná karoséria Modern Solid"),
        expect.stringContaining("predĺžená lakovaná strecha Combi"),
        expect.stringContaining("akustické čelné sklo"),
        expect.stringContaining("vyhrievané sklo piatych dverí"),
        expect.stringContaining("Matrix LED modul"),
        expect.stringContaining("kryštalické zadné svetlo C"),
      ]),
    );

    const colliders = scene.meshes.filter(
      ({ metadata }) => metadata?.vehicleCollider === true,
    );
    expect(colliders).toHaveLength(2);
    expect(colliders.every(({ isVisible }) => !isVisible)).toBe(true);
    expect(colliders.every(({ checkCollisions }) => checkCollisions)).toBe(true);
    const lowerCollider = colliders.find(({ name }) =>
      name.includes("spodný kolízny obal"),
    )!;
    const lowerBounds = lowerCollider.getBoundingInfo().boundingBox;
    expect(lowerBounds.maximum.x - lowerBounds.minimum.x).toBeCloseTo(
      GARAGE_SUPERB_REFERENCE_DIMENSIONS_MM.length / 1_000,
      6,
    );

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
