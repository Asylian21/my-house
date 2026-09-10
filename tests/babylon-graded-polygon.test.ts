import { NullEngine } from "@babylonjs/core/Engines/nullEngine";
import { VertexBuffer } from "@babylonjs/core/Buffers/buffer";
import { Scene } from "@babylonjs/core/scene";
import { describe, expect, it } from "vitest";

import { createGradedPolygon } from "../lib/babylon-scene";
import { ROAD_CONTEXT, SITE_SURFACES, type Point2Mm } from "../lib/twin-site";
import { sceneXM, sceneZM } from "../lib/twin-render-frame";

const reserves = ROAD_CONTEXT.frontReserveSurfacePolygonsMm.map((ring, index) => ({
  name: `front reserve ${index + 1}`,
  ring,
  triangles: index === 0 ? 4 : 2,
  height: (point: Point2Mm) => -0.02 -
    ((point.y - ROAD_CONTEXT.frontAsphaltEdgeYmm) /
      Math.abs(ROAD_CONTEXT.frontAsphaltEdgeYmm)) * 0.015,
}));
const ramps = [SITE_SURFACES.driveway, SITE_SURFACES.entry, SITE_SURFACES.sideEntryApproach]
  .map((surface) => {
    const minY = Math.min(...surface.polygonMm.map((point) => point.y));
    const maxY = Math.max(...surface.polygonMm.map((point) => point.y));
    const minX = Math.min(...surface.polygonMm.map((point) => point.x));
    const maxX = Math.max(...surface.polygonMm.map((point) => point.x));
    const side = surface.id === SITE_SURFACES.sideEntryApproach.id;
    return {
      name: surface.accessOpeningId,
      ring: surface.polygonMm,
      triangles: side ? 4 : 2,
      height: (point: Point2Mm) => side
        ? -0.11 + ((maxX - point.x) / Math.max(1, maxX - minX)) * 0.095
        : point.y <= 0
          ? -0.11 + ((point.y - minY) / Math.max(1, -minY)) * 0.08
          : -0.03 + (point.y / Math.max(1, maxY)) * 0.015,
    };
  });

describe("walkable graded ground faces", () => {
  for (const fixture of [...reserves, ...ramps]) {
    it(`${fixture.name} faces upward with its real non-flat slope`, () => {
      const engine = new NullEngine();
      const scene = new Scene(engine);
      scene.useRightHandedSystem = true;
      try {
        // Input polygon orientation must not change which side is walkable.
        for (const ring of [fixture.ring, [...fixture.ring].reverse()]) {
          const mesh = createGradedPolygon(scene, fixture.name, ring, fixture.height);
          const positions = mesh.getVerticesData(VertexBuffer.PositionKind)!;
          const normals = mesh.getVerticesData(VertexBuffer.NormalKind)!;
          const indices = mesh.getIndices()!;
          const open = ring.length > 1 && ring[0].x === ring.at(-1)!.x && ring[0].y === ring.at(-1)!.y
            ? ring.slice(0, -1) : ring;
          expect(indices).toHaveLength(fixture.triangles * 3);
          expect(positions).toHaveLength(open.length * 3);
          open.forEach((point, vertex) => {
            expect(positions[vertex * 3]).toBeCloseTo(sceneXM(point.x), 5);
            expect(positions[vertex * 3 + 1]).toBeCloseTo(fixture.height(point), 6);
            expect(positions[vertex * 3 + 2]).toBeCloseTo(sceneZM(point.y), 5);
          });
          for (let offset = 0; offset < indices.length; offset += 3) {
            const ids = indices.slice(offset, offset + 3);
            const [a, b, c] = Array.from(ids, (vertex) => positions.slice(vertex * 3, vertex * 3 + 3));
            const u = b.map((value, axis) => value - a[axis]);
            const v = c.map((value, axis) => value - a[axis]);
            const cross = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
            // Babylon ground front winding uses the opposite of this RH cross;
            // the OBJ exporter then orients RH faces to the stored normals.
            expect(cross[1]).toBeLessThan(0);
            const length = Math.hypot(...cross);
            for (const vertex of ids) {
              const n = normals.slice(vertex * 3, vertex * 3 + 3);
              expect(n[1]).toBeGreaterThan(0.99);
              expect(Math.hypot(n[0], n[2])).toBeGreaterThan(0.004);
              expect(cross.reduce((sum, value, axis) => sum - value * n[axis], 0) / length)
                .toBeGreaterThan(0.999999);
            }
          }
          mesh.dispose();
        }
      } finally {
        scene.dispose();
        engine.dispose();
      }
    });
  }
});
