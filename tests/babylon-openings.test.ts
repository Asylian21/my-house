import { NullEngine } from "@babylonjs/core/Engines/nullEngine";
import type { Material } from "@babylonjs/core/Materials/material";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import { Scene } from "@babylonjs/core/scene";
import { describe, expect, it } from "vitest";

import {
  buildOpening,
  resolveFacadeOpeningStyle,
  type OpeningBuildContext,
} from "../lib/babylon-openings";
import { HOUSE } from "../lib/twin-site";

describe("Babylon facade openings", () => {
  it("builds the office fixed glazing as one pane in an ultra-slim frame", () => {
    const engine = new NullEngine({
      renderHeight: 256,
      renderWidth: 256,
      textureSize: 256,
    });
    const scene = new Scene(engine);
    const material = (name: string) => new PBRMaterial(name, scene);
    const frame = material("test-frame");
    const context: OpeningBuildContext = {
      scene,
      materials: {
        glass: material("test-glass"),
        technicalGlass: material("test-technical-glass"),
        sillInterior: material("test-sill-interior"),
        sillExterior: material("test-sill-exterior"),
        handle: material("test-handle"),
        doorLeaf: material("test-door"),
        curtain: material("test-curtain"),
        track: material("test-track"),
      },
      register: (mesh: AbstractMesh) => mesh,
      realisticOnly: (mesh: AbstractMesh) => mesh,
      castShadow: (mesh: AbstractMesh) => mesh,
      appearance: (mesh: AbstractMesh, _technical: Material, realistic: Material) => {
        mesh.material = realistic;
        return mesh;
      },
    };

    try {
      const name = "Výplň otvoru FRONT-07";
      const officeWindow = HOUSE.facades.front.openings.find(
        ({ id }) => id === "FRONT-07",
      )!;
      const style = resolveFacadeOpeningStyle(officeWindow, "FRONT-ENTRY");
      expect(style).toEqual({ kind: "fixed", frameWidthMm: 35 });
      const built = buildOpening(context, {
        name,
        axis: "Z",
        faceMm: 3000,
        centerMm: officeWindow.startXmm + officeWindow.widthMm / 2,
        widthMm: officeWindow.widthMm,
        heightMm: officeWindow.heightMm,
        sillMm: officeWindow.sillMm,
        outward: -1,
        wallThicknessMm: 530,
        kind: style.kind,
        frameMaterial: frame,
        frameWidthMm: style.frameWidthMm,
        entityId: "HOUSE-DESIGN",
        curtains: false,
      });

      expect(built.map(({ name: meshName }) => meshName)).toEqual([
        `${name} · pevné izolačné dvojsklo`,
      ]);
      expect(built[0].checkCollisions).toBe(true);

      const openingMeshes = scene.meshes.filter((mesh) => mesh.name.startsWith(name));
      expect(openingMeshes.some(({ name: meshName }) =>
        /krídlo|stredový stĺpik|kľučka|rozeta/.test(meshName),
      )).toBe(false);

      const leftFrame = openingMeshes.find(({ name: meshName }) =>
        meshName.endsWith("rám ľavý stĺpik"),
      )!;
      const bottomFrame = openingMeshes.find(({ name: meshName }) =>
        meshName.endsWith("rám spodný priečnik"),
      )!;
      expect(leftFrame.getBoundingInfo().boundingBox.extendSize.x * 2).toBeCloseTo(0.035, 6);
      expect(bottomFrame.getBoundingInfo().boundingBox.extendSize.y * 2).toBeCloseTo(0.035, 6);
    } finally {
      scene.dispose();
      engine.dispose();
    }
  });
});
