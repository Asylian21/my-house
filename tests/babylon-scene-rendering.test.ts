import { NullEngine } from "@babylonjs/core/Engines/nullEngine";
import { VertexBuffer } from "@babylonjs/core/Buffers/buffer";
import { Scene } from "@babylonjs/core/scene";
import { describe, expect, it } from "vitest";

import {
  PARCEL_LABEL_RENDERING_GROUP_ID,
  TwinSceneController,
  createFlatPolygonWithHoles,
  createRoofFace,
  createTwinRenderScene,
  setSelectionHighlightForNavigation,
} from "../lib/babylon-scene";
import {
  CADASTRAL_PARCELS,
  GARDEN_POOL,
  PARCEL_LAWN_INTERIOR_CUTOUTS_MM,
  POOL_TECHNOLOGY_SHAFT,
  sjtskToLocalMm,
} from "../lib/twin-site";
import { sceneXM, sceneZM } from "../lib/twin-render-frame";
import {
  deriveJoinedRoofRenderPlan,
  type JoinedRoofGeometry,
} from "../lib/twin-roof";
import { HOUSE } from "../lib/twin-active-house";

describe("active and archived roof mesh bounds", () => {
  for(const [label,archiveRoof,overhang] of [
    ['active',false,0],
    ['archive',true,50],
  ] as const) {
    it(`keeps the ${label} geometric boundary at its own facade offset`, () => {
      const engine=new NullEngine();
      const scene=createTwinRenderScene(engine);
      // Exercise the actual lazy roof input used by prototype-only extractors,
      // including the explicit archive selection used by the browser scene.
      const shell=Object.assign(Object.create(TwinSceneController.prototype),{archiveRoof});
      const roof=shell.roof as JoinedRoofGeometry;
      try {
        const meshes=roof.faces.map(face=>createRoofFace(scene,face.id,face.vertexIndices.map(i=>roof.vertices[i])));
        meshes.forEach(mesh=>mesh.computeWorldMatrix(true));
        const northWorldZ=Math.min(...meshes.map(mesh=>mesh.getBoundingInfo().boundingBox.minimumWorld.z));
        expect(northWorldZ).toBeCloseTo(sceneZM(HOUSE.porches.wingEnd.frontYmm+overhang),6);
        const visible=deriveJoinedRoofRenderPlan(roof).topFaces.map(face=>createRoofFace(scene,face.id+'-finish',face.vertices));
        visible.forEach(mesh=>mesh.computeWorldMatrix(true));
        expect(Math.min(...visible.map(mesh=>mesh.getBoundingInfo().boundingBox.minimumWorld.z)))
          .toBeCloseTo(sceneZM(HOUSE.porches.wingEnd.frontYmm),6);
      } finally {scene.dispose();engine.dispose();}
    });
  }
});

function pointInTriangle(
  point: readonly [number, number],
  a: readonly [number, number],
  b: readonly [number, number],
  c: readonly [number, number],
) {
  const cross = (
    p1: readonly [number, number],
    p2: readonly [number, number],
    p3: readonly [number, number],
  ) =>
    (p2[0] - p1[0]) * (p3[1] - p1[1]) -
    (p2[1] - p1[1]) * (p3[0] - p1[0]);
  const ab = cross(a, b, point);
  const bc = cross(b, c, point);
  const ca = cross(c, a, point);
  return !(
    (ab < -1e-9 || bc < -1e-9 || ca < -1e-9) &&
    (ab > 1e-9 || bc > 1e-9 || ca > 1e-9)
  );
}

describe("Babylon scene depth occlusion", () => {
  it("keeps house depth when the late parcel-label group renders", () => {
    const engine = new NullEngine({
      renderHeight: 64,
      renderWidth: 64,
      textureSize: 64,
    });
    const scene = createTwinRenderScene(engine);

    try {
      expect(
        scene.getAutoClearDepthStencilSetup(PARCEL_LABEL_RENDERING_GROUP_ID),
      ).toMatchObject({ autoClear: false });
    } finally {
      scene.dispose();
      engine.dispose();
    }
  });

  it("disables x-ray selection glow for both immersive cameras", () => {
    const highlight = { isEnabled: true };

    setSelectionHighlightForNavigation(highlight, "walk");
    expect(highlight.isEnabled).toBe(false);

    setSelectionHighlightForNavigation(highlight, "flight");
    expect(highlight.isEnabled).toBe(false);

    setSelectionHighlightForNavigation(highlight, "orbit");
    expect(highlight.isEnabled).toBe(true);
  });

  it("removes the transparent pool footprint from the grass triangles", () => {
    const engine = new NullEngine();
    const scene = new Scene(engine);
    scene.useRightHandedSystem = true;
    const subjectParcel = CADASTRAL_PARCELS.find((parcel) => parcel.isSubject);
    expect(subjectParcel).toBeDefined();

    const lawn = createFlatPolygonWithHoles(
      scene,
      "parcel lawn regression fixture",
      subjectParcel!.sjtskRingMm.map(sjtskToLocalMm),
      PARCEL_LAWN_INTERIOR_CUTOUTS_MM,
      -0.065,
    );

    try {
      const positions = lawn.getVerticesData(VertexBuffer.PositionKind);
      const indices = lawn.getIndices();
      expect(positions).not.toBeNull();
      expect(indices).not.toBeNull();

      // Match the production RHS scene: Babylon ground faces use this X/Z
      // winding. The realistic lawn material culls the opposite side, so a
      // positive cross-product here would make the entire lawn invisible.
      for (let offset = 0; offset < indices!.length; offset += 3) {
        const [a, b, c] = [
          indices![offset],
          indices![offset + 1],
          indices![offset + 2],
        ].map((index) => [
          positions![index * 3],
          positions![index * 3 + 2],
        ] as const);
        const facingY =
          (b[1] - a[1]) * (c[0] - a[0]) -
          (b[0] - a[0]) * (c[1] - a[1]);
        expect(facingY).toBeLessThan(0);
      }

      const covers = (pointMm: { readonly x: number; readonly y: number }) => {
        const point = [sceneXM(pointMm.x), sceneZM(pointMm.y)] as const;
        for (let offset = 0; offset < indices!.length; offset += 3) {
          const triangle = [
            indices![offset],
            indices![offset + 1],
            indices![offset + 2],
          ].map((index) => [
            positions![index * 3],
            positions![index * 3 + 2],
          ] as const);
          if (pointInTriangle(point, triangle[0], triangle[1], triangle[2])) {
            return true;
          }
        }
        return false;
      };

      expect(covers(GARDEN_POOL.centerMm)).toBe(false);
      expect(
        covers({
          x:
            (POOL_TECHNOLOGY_SHAFT.hatch.footprintMm.x0 +
              POOL_TECHNOLOGY_SHAFT.hatch.footprintMm.x1) /
            2,
          y:
            (POOL_TECHNOLOGY_SHAFT.hatch.footprintMm.y0 +
              POOL_TECHNOLOGY_SHAFT.hatch.footprintMm.y1) /
            2,
        }),
      ).toBe(false);
      expect(covers({ x: 25_000, y: 18_000 })).toBe(true);
    } finally {
      scene.dispose();
      engine.dispose();
    }
  });
});
