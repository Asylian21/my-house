import { NullEngine } from "@babylonjs/core/Engines/nullEngine";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import type { TransformNode } from "@babylonjs/core/Meshes/transformNode";
import { Scene } from "@babylonjs/core/scene";
import { describe, expect, it } from "vitest";

import { buildInterior } from "../lib/babylon-interior";
import type { AnimatedDoorRegistration } from "../lib/babylon-doors";
import {
  CHILDRENS_BEDROOM_FITOUTS,
  FIREPLACE_STOVE,
  GARAGE_FITOUT,
  INTERIOR_DOORS,
  TECHNICAL_HEATING_FITOUT,
} from "../lib/twin-interior";

describe("Babylon interior fit-out", () => {
  it("builds the required room objects and measured collision envelopes", () => {
    const engine = new NullEngine({
      renderHeight: 256,
      renderWidth: 256,
      textureSize: 256,
    });
    const scene = new Scene(engine);
    const material = (name: string) => new PBRMaterial(name, scene);
    const doors: AnimatedDoorRegistration[] = [];
    try {
      buildInterior({
        scene,
        anisotropy: 1,
        wall: material("test-wall"),
        soffit: material("test-soffit"),
        glassFrame: material("test-glass-frame"),
        chimneyMetal: material("test-chimney-metal"),
        timber: material("test-timber"),
        register: (mesh: AbstractMesh) => mesh,
        realisticOnly: (mesh: AbstractMesh) => mesh,
        castShadow: (mesh: AbstractMesh) => mesh,
        registerAnimatedDoor: (door) => doors.push(door),
      });

      expect(doors.map(({ id }) => id).sort()).toEqual(
        INTERIOR_DOORS.map(({ id }) => id).sort(),
      );
      expect(doors).toHaveLength(11);
      for (const door of doors) {
        const leaf = scene.meshes.find(
          (mesh) =>
            mesh.metadata?.doorId === door.id &&
            mesh.name.includes("animované krídlo"),
        );
        expect(leaf, `${door.id} has one moving leaf`).toBeDefined();
        expect(leaf?.checkCollisions).toBe(true);
        expect(leaf?.isPickable).toBe(true);
        expect(leaf?.metadata).toMatchObject({
          doorId: door.id,
          doorMotion: "HINGED",
          dynamicCameraOccluder: true,
        });
        const handles = scene.meshes.filter(
          (mesh) =>
            mesh.parent === leaf?.parent && mesh.name.includes("kľučka"),
        );
        expect(handles, `${door.id} has a lever on both faces`).toHaveLength(2);
        door.apply(1, 1);
        expect(
          Math.abs((leaf?.parent as TransformNode | null)?.rotation.y ?? 0),
        ).toBeCloseTo(
          Math.PI / 2,
          8,
        );
        expect(
          door.canOpen?.({
            position: door.interactionPoint,
            facing: { x: 1, z: 0 },
          }),
        ).toBe(false);
        expect(
          door.canClose?.({
            position: {
              x: door.interactionPoint.x + 5,
              z: door.interactionPoint.z + 5,
            },
            facing: { x: 1, z: 0 },
          }),
        ).toBe(true);
        door.apply(0, 0);
      }

      for (const fitout of CHILDRENS_BEDROOM_FITOUTS) {
        const roomMeshes = scene.meshes.filter((mesh) => mesh.name.startsWith(fitout.id));
        for (const required of ["· BED ·", "· WARDROBE ·", "· DESK ·", "· CHAIR ·"]) {
          expect(
            roomMeshes.some((mesh) => mesh.name.includes(required)),
            `${fitout.id} renders ${required}`,
          ).toBe(true);
        }

        const guards = roomMeshes.filter((mesh) => mesh.metadata?.walkCollisionOnly === true);
        expect(guards.map((guard) => guard.name)).toEqual(expect.arrayContaining([
          expect.stringContaining("· BED · navigačný obrys"),
          expect.stringContaining("· WARDROBE · navigačný obrys"),
          expect.stringContaining("· DESK · navigačný obrys"),
          expect.stringContaining("· CHAIR · navigačný obrys pojazdu"),
        ]));
        expect(guards).toHaveLength(4);
        for (const guard of guards) {
          expect(guard.checkCollisions).toBe(true);
          expect(guard.isVisible).toBe(false);
        }
      }

      const heatingMeshes = scene.meshes.filter((mesh) =>
        mesh.name.startsWith(TECHNICAL_HEATING_FITOUT.id),
      );
      for (const required of [
        "· WOOD-PELLET-BOILER ·",
        "· PELLET-HOPPER ·",
        "· PELLET-AUGER ·",
        "· PELLET-FEED-HOSE ·",
        "· PELLET-BURNER ·",
        "· BUFFER-TANK-1000L ·",
      ]) {
        expect(
          heatingMeshes.some((mesh) => mesh.name.includes(required)),
          `technical heating renders ${required}`,
        ).toBe(true);
      }

      const hose = heatingMeshes.find((mesh) => mesh.name.includes("· PELLET-FEED-HOSE ·"));
      expect(hose?.getTotalVertices()).toBeGreaterThan(0);
      expect(
        heatingMeshes.find((mesh) => mesh.name.includes("kombinované teleso"))?.isPickable,
      ).toBe(true);
      expect(
        heatingMeshes.find((mesh) => mesh.name.includes("zásobník peliet približne"))
          ?.isPickable,
      ).toBe(true);

      const heatingGuards = heatingMeshes.filter(
        (mesh) => mesh.metadata?.walkCollisionOnly === true,
      );
      expect(heatingGuards).toHaveLength(1);
      expect(heatingGuards[0].name).toContain("· WOOD-PELLET-ASSEMBLY · navigačný obrys");
      expect(heatingGuards[0].checkCollisions).toBe(true);
      expect(heatingGuards[0].isVisible).toBe(false);
      const garageMeshes = scene.meshes.filter((mesh) => mesh.name.startsWith(GARAGE_FITOUT.id));
      for (const required of [
        "· UTILITY-SINK ·",
        "· GARAGE-RACK ·",
        "· GARAGE-SHELF ·",
        "· REAR-SHELF ·",
        "· PEGBOARD ·",
        "· GARAGE-CLUTTER ·",
        "· LONG-TOOL ·",
        "· MOWER ·",
      ]) {
        expect(
          garageMeshes.some((mesh) => mesh.name.includes(required)),
          `garage renders ${required}`,
        ).toBe(true);
      }

      expect(
        garageMeshes.find((mesh) => mesh.name.includes("hlboká nerezová pracovná vaňa"))
          ?.metadata,
      ).toMatchObject({
        designSourceId: GARAGE_FITOUT.sourceId,
        plumbingStatus: GARAGE_FITOUT.plumbingStatus,
      });
      expect(
        garageMeshes.filter((mesh) => mesh.name.includes("kartónová krabica")),
      ).toHaveLength(GARAGE_FITOUT.storageRack.cardboardBoxCount);
      expect(
        garageMeshes.filter((mesh) => mesh.name.includes("plastový box")),
      ).toHaveLength(GARAGE_FITOUT.storageRack.plasticBinCount);
      expect(
        garageMeshes.filter((mesh) => mesh.name.includes("plechovka farby")),
      ).toHaveLength(GARAGE_FITOUT.storageRack.paintCanCount);
      expect(
        garageMeshes.filter((mesh) => /· MOWER · gumové koleso \d/.test(mesh.name)),
      ).toHaveLength(4);
      expect(
        garageMeshes.find((mesh) => mesh.name.includes("· MOWER · sklopná oceľová rukoväť"))
          ?.getTotalVertices(),
      ).toBeGreaterThan(0);

      const garageGuards = garageMeshes.filter(
        (mesh) => mesh.metadata?.walkCollisionOnly === true,
      );
      expect(garageGuards.map((guard) => guard.name)).toEqual(expect.arrayContaining([
        expect.stringContaining("· UTILITY-SINK · navigačný obrys"),
        expect.stringContaining("· GARAGE-RACK · navigačný obrys"),
        expect.stringContaining("· MOWER · navigačný obrys"),
      ]));
      expect(garageGuards).toHaveLength(3);
      expect(garageMeshes.filter((mesh) => mesh.checkCollisions)).toEqual(garageGuards);
      for (const guard of garageGuards) {
        expect(guard.checkCollisions).toBe(true);
        expect(guard.isVisible).toBe(false);
      }
    } finally {
      scene.dispose();
      engine.dispose();
    }
  });

  it("renders only the new cylindrical stove, curved glass and coaxial top connection", () => {
    const engine = new NullEngine({
      renderHeight: 256,
      renderWidth: 256,
      textureSize: 256,
    });
    const scene = new Scene(engine);
    const material = (name: string) => new PBRMaterial(name, scene);
    try {
      buildInterior({
        scene,
        anisotropy: 1,
        wall: material("test-wall"),
        soffit: material("test-soffit"),
        glassFrame: material("test-glass-frame"),
        chimneyMetal: material("test-chimney-metal"),
        timber: material("test-timber"),
        register: (mesh: AbstractMesh) => mesh,
        realisticOnly: (mesh: AbstractMesh) => mesh,
        castShadow: (mesh: AbstractMesh) => mesh,
      });

      const meshes = scene.meshes.filter((mesh) => mesh.name.startsWith(FIREPLACE_STOVE.id));
      const find = (marker: string) => meshes.find((mesh) => mesh.name.includes(marker));
      const body = find("· BODY ·");
      const glass = find("· CURVED-GLASS ·");

      expect(body).toBeDefined();
      expect(body?.checkCollisions).toBe(true);
      expect(body?.metadata).toMatchObject({
        designSourceId: FIREPLACE_STOVE.sourceId,
        fireplaceShape: "CYLINDRICAL",
        cameraOccluder: true,
      });
      body?.computeWorldMatrix(true);
      expect((body?.getBoundingInfo().boundingBox.extendSizeWorld.x ?? 0) * 2).toBeCloseTo(
        FIREPLACE_STOVE.bodyDiameterMm * 0.001,
        3,
      );
      expect((body?.getBoundingInfo().boundingBox.extendSizeWorld.z ?? 0) * 2).toBeCloseTo(
        FIREPLACE_STOVE.bodyDiameterMm * 0.001,
        3,
      );

      expect(glass).toBeDefined();
      expect(glass?.getTotalVertices()).toBeGreaterThan(100);
      expect(find("· FIRE-GLOW ·")).toBeDefined();
      expect(find("· DOOR-HANDLE ·")).toBeDefined();
      expect(find("· FLUE-COLLAR ·")).toBeDefined();
      expect(meshes.filter((mesh) => mesh.checkCollisions)).toEqual([body]);
      expect(
        scene.lights.some((light) => light.name.includes(`${FIREPLACE_STOVE.id} · FIRE-LIGHT`)),
      ).toBe(true);
      expect(
        scene.meshes.some((mesh) =>
          /komínový pilier|dymovod do komína|koleno dymovodu|Krbové kachle vedľa dverí/.test(
            mesh.name,
          ),
        ),
      ).toBe(false);
    } finally {
      scene.dispose();
      engine.dispose();
    }
  });
});
