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
  type OpeningSpec,
} from "../lib/babylon-openings";
import type { AnimatedDoorRegistration } from "../lib/babylon-doors";
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

  it("registers all six exterior pedestrian doors with physical moving leaves", () => {
    const engine = new NullEngine({
      renderHeight: 256,
      renderWidth: 256,
      textureSize: 256,
    });
    const scene = new Scene(engine);
    const material = (name: string) => new PBRMaterial(name, scene);
    const frame = material("test-frame");
    const doors: AnimatedDoorRegistration[] = [];
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
      registerAnimatedDoor: (door) => doors.push(door),
    };

    const build = (
      spec: Omit<OpeningSpec, "frameMaterial" | "curtains">,
    ) =>
      buildOpening(context, { ...spec, frameMaterial: frame, curtains: false });
    try {
      const front = HOUSE.facades.front.openings.find(
        ({ id }) => id === "FRONT-ENTRY",
      )!;
      build({
        name: front.id,
        axis: "Z",
        faceMm: HOUSE.facades.front.faceYmm,
        centerMm: front.startXmm + front.widthMm / 2,
        widthMm: front.widthMm,
        heightMm: front.heightMm,
        sillMm: front.sillMm,
        outward: -1,
        wallThicknessMm: 530,
        kind: "door",
        interaction: { id: front.id, label: front.id },
      });
      for (const opening of HOUSE.facades.garden.openings.filter(
        ({ id }) => id === "GARDEN-02" || id === "GARDEN-03",
      )) {
        build({
          name: opening.id,
          axis: "Z",
          faceMm: HOUSE.facades.garden.faceYmm,
          centerMm: opening.startXmm + opening.widthMm / 2,
          widthMm: opening.widthMm,
          heightMm: opening.heightMm,
          sillMm: opening.sillMm,
          outward: 1,
          wallThicknessMm: 530,
          kind: "sliding",
          interaction: { id: opening.id, label: opening.id },
        });
      }
      const east = HOUSE.facades.east.openings.find(
        ({ id }) => id === "EAST-03",
      )!;
      build({
        name: east.id,
        axis: "X",
        faceMm: HOUSE.facades.east.faceXmm,
        centerMm: east.startYmm + east.widthMm / 2,
        widthMm: east.widthMm,
        heightMm: east.heightMm,
        sillMm: east.sillMm,
        outward: 1,
        wallThicknessMm: 530,
        kind: "door",
        interaction: { id: east.id, label: east.id },
      });
      const wing = HOUSE.facades.wingWest.opening;
      build({
        name: wing.id,
        axis: "X",
        faceMm: HOUSE.facades.wingWest.faceXmm,
        centerMm: wing.startYmm + wing.widthMm / 2,
        widthMm: wing.widthMm,
        heightMm: wing.heightMm,
        sillMm: wing.sillMm,
        outward: -1,
        wallThicknessMm: 500,
        kind: "sliding",
        interaction: { id: wing.id, label: wing.id },
      });
      const loggia = HOUSE.porches.gardenLoggia.backDoor;
      build({
        name: loggia.id,
        axis: "Z",
        faceMm: HOUSE.porches.gardenLoggia.backFaceYmm,
        centerMm: loggia.startXmm + loggia.widthMm / 2,
        widthMm: loggia.widthMm,
        heightMm: loggia.heightMm,
        sillMm: loggia.sillMm,
        outward: 1,
        wallThicknessMm: 530,
        kind: "door",
        interaction: { id: loggia.id, label: loggia.id },
      });

      expect(doors.map(({ id }) => id).sort()).toEqual([
        "EAST-03",
        "FRONT-ENTRY",
        "GARDEN-02",
        "GARDEN-03",
        "LOGGIA-DOOR",
        "WING-WEST-01",
      ]);
      expect(doors.filter(({ kind }) => kind === "HINGED")).toHaveLength(3);
      expect(doors.filter(({ kind }) => kind === "SLIDING")).toHaveLength(3);
      for (const door of doors) {
        const movingLeaf = scene.meshes.find(
          (mesh) =>
            mesh.metadata?.doorId === door.id && mesh.checkCollisions,
        );
        expect(movingLeaf, `${door.id} has a moving collision leaf`).toBeDefined();
        expect(movingLeaf?.checkCollisions).toBe(true);
        expect(movingLeaf?.metadata).toMatchObject({
          doorId: door.id,
          dynamicCameraOccluder: true,
        });
        expect(
          door.canOpen?.({
            position: door.interactionPoint,
            facing: { x: 1, z: 0 },
          }),
        ).toBe(false);
        door.apply(1, 1);
        movingLeaf?.computeWorldMatrix(true);
        door.apply(0, 0);
      }

      const frontDoor = doors.find(({ id }) => id === "FRONT-ENTRY")!;
      const frontRosettes = scene.meshes.filter((mesh) =>
        mesh.name.includes("FRONT-ENTRY · rozeta kľučky"),
      );
      const rotations = frontRosettes.map((mesh) => mesh.rotation.clone());
      frontDoor.apply(0.35, 1);
      expect(frontRosettes).toHaveLength(2);
      frontRosettes.forEach((mesh, index) =>
        expect(mesh.rotation.equals(rotations[index])).toBe(true),
      );
    } finally {
      scene.dispose();
      engine.dispose();
    }
  });
});
