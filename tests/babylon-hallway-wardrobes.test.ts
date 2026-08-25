import { NullEngine } from "@babylonjs/core/Engines/nullEngine";
import { PBRMaterial } from "@babylonjs/core/Materials/PBR/pbrMaterial";
import type { AbstractMesh } from "@babylonjs/core/Meshes/abstractMesh";
import { Scene } from "@babylonjs/core/scene";
import { describe, expect, it } from "vitest";

import { buildInterior } from "../lib/babylon-interior";
import { HALLWAY_BUILT_IN_WARDROBES } from "../lib/twin-interior";

describe("Babylon hallway built-in wardrobes", () => {
  it("renders premium oak fronts, integrated light and one smooth collision guard per niche", () => {
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

      for (const wardrobe of HALLWAY_BUILT_IN_WARDROBES) {
        const meshes = scene.meshes.filter((mesh) => mesh.name.startsWith(wardrobe.id));
        const carcase = meshes.find((mesh) => mesh.name.includes("· CARCASE ·"));
        expect(carcase?.metadata).toMatchObject({
          fitoutId: wardrobe.id,
          designSourceId: wardrobe.sourceId,
          architecturalSourceId: wardrobe.architecturalSourceId,
          roomId: wardrobe.roomId,
          furnitureKind: "HALLWAY_BUILT_IN_WARDROBE",
          embeddedInArchitecturalNiche: true,
          facing: wardrobe.facing,
          finish: wardrobe.style.finish,
          opening: wardrobe.style.opening,
          cameraOccluder: true,
        });
        expect(carcase?.isPickable).toBe(true);

        const fronts = meshes.filter((mesh) => mesh.name.includes("· DOOR ·"));
        expect(fronts).toHaveLength(wardrobe.doorCount);
        for (const [index, front] of fronts.entries()) {
          const isReeded = wardrobe.style.reededPanelIndices.includes(index);
          expect(front.metadata).toMatchObject({
            fitoutId: wardrobe.id,
            panelIndex: index,
            veneerPattern: "BOOKMATCHED_VERTICAL_GRAIN",
            handleless: true,
            reededAccent: isReeded,
          });
          expect(front.isPickable).toBe(true);
          expect(front.material?.name).toBe(
            isReeded
              ? "real-hallway-wardrobe-smoked-oak"
              : "real-hallway-wardrobe-warm-oak",
          );
        }

        expect(meshes.filter((mesh) => mesh.name.includes("· REEDED-ACCENT ·")))
          .toHaveLength(
            wardrobe.style.reededPanelIndices.length
              * wardrobe.style.reededGrooveCountPerPanel,
          );
        expect(meshes.filter((mesh) => mesh.name.includes("· LED ·")))
          .toHaveLength(wardrobe.style.ledEdges.length);
        expect(meshes.some((mesh) => mesh.name.includes("· PLINTH ·"))).toBe(true);
        expect(meshes.some((mesh) => mesh.name.includes("horná tieňová škára"))).toBe(true);

        const guards = meshes.filter((mesh) => mesh.metadata?.walkCollisionOnly === true);
        expect(guards).toHaveLength(1);
        expect(guards[0].name).toContain("· WARDROBE · hladký navigačný obrys niky");
        expect(guards[0].checkCollisions).toBe(true);
        expect(guards[0].isVisible).toBe(false);
        expect(meshes.filter((mesh) => mesh.checkCollisions)).toEqual(guards);
      }
    } finally {
      scene.dispose();
      engine.dispose();
    }
  });
});
