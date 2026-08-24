import { NullEngine } from "@babylonjs/core/Engines/nullEngine";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import { Scene } from "@babylonjs/core/scene";
import { describe, expect, it } from "vitest";

import { buildInterior } from "../lib/babylon-interior";
import { CHILDRENS_BEDROOM_FITOUTS, TECHNICAL_HEATING_FITOUT } from "../lib/twin-interior";

describe("Babylon interior fit-out", () => {
  it("builds the required room objects and measured collision envelopes", () => {
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
    } finally {
      scene.dispose();
      engine.dispose();
    }
  });
});
