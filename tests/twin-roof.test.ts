import { describe, expect, it } from "vitest";

import {
  ACTIVE_JOINED_ROOF_PARAMETERS,
  deriveJoinedRoofGeometry,
  mainFrontRoofHeightMm,
  mainGardenRoofHeightMm,
  roofHeightMm,
  wingInnerRoofHeightMm,
  wingOuterRoofHeightMm,
  type RoofTriangle,
  type RoofVertexMm,
} from "../lib/twin-roof";

const roof = deriveJoinedRoofGeometry();

describe("joined roof topology", () => {
  it("derives the exact active nine vertices, four faces and eight triangles", () => {
    expect(roof.vertices).toEqual([
      { id: "FRONT_WEST_EAVE", xMm: 6_440, yMm: 3_000, elevationMm: 3_125 },
      { id: "FRONT_EAST_EAVE", xMm: 28_040, yMm: 3_000, elevationMm: 3_125 },
      { id: "MAIN_WEST_RIDGE", xMm: 6_440, yMm: 7_100, elevationMm: 5_560 },
      { id: "ROOF_JUNCTION", xMm: 24_540, yMm: 7_100, elevationMm: 5_560 },
      { id: "GARDEN_WEST_EAVE", xMm: 6_440, yMm: 11_200, elevationMm: 3_125 },
      { id: "VALLEY_EAVE", xMm: 21_040, yMm: 11_200, elevationMm: 3_125 },
      {
        id: "WING_END_INNER_EAVE",
        xMm: 21_040,
        yMm: 22_085,
        elevationMm: 3_125,
      },
      { id: "WING_END_RIDGE", xMm: 24_540, yMm: 22_085, elevationMm: 5_560 },
      {
        id: "WING_END_OUTER_EAVE",
        xMm: 28_040,
        yMm: 22_085,
        elevationMm: 3_125,
      },
    ]);
    expect(roof.faces).toEqual([
      {
        id: "MAIN_FRONT",
        vertexIndices: [0, 1, 3, 2],
        triangleIndices: [0, 1],
        seamAxis: "X",
      },
      {
        id: "MAIN_GARDEN",
        vertexIndices: [2, 3, 5, 4],
        triangleIndices: [2, 3],
        seamAxis: "X",
      },
      {
        id: "WING_INNER",
        vertexIndices: [5, 3, 7, 6],
        triangleIndices: [4, 5],
        seamAxis: "Y",
      },
      {
        id: "WING_OUTER",
        vertexIndices: [3, 1, 8, 7],
        triangleIndices: [6, 7],
        seamAxis: "Y",
      },
    ]);
    expect(roof.triangles.map(({ vertexIndices }) => vertexIndices)).toEqual([
      [0, 1, 3],
      [0, 3, 2],
      [2, 3, 5],
      [2, 5, 4],
      [5, 3, 7],
      [5, 7, 6],
      [3, 1, 8],
      [3, 8, 7],
    ]);
    expect(roof.bounds).toEqual({
      minXmm: 6_440,
      maxXmm: 28_040,
      minYmm: 3_000,
      maxYmm: 22_085,
      minElevationMm: 3_125,
      maxElevationMm: 5_560,
    });
  });

  it("partitions the active L roof envelope including the 50 mm end overhang", () => {
    expect(roof.projectedAreaMm2).toBe(253_315_000);
    expect(roof.projectedAreaMm2 / 1_000_000).toBe(253.315);
    expect(roof.surfaceAreaMm2 / 1_000_000).toBeCloseTo(300.405497595, 9);
  });

  it("keeps every non-boundary triangle edge paired", () => {
    const incidence = edgeIncidence(roof.triangles);
    const counts = [...incidence.values()];
    expect(counts.filter((count) => count === 1)).toHaveLength(8);
    expect(counts.filter((count) => count === 2)).toHaveLength(8);
    expect(counts.every((count) => count === 1 || count === 2)).toBe(true);
    expect(roof.vertices.length - incidence.size + roof.triangles.length).toBe(1);

    expect(singletonEdges(incidence)).toEqual([
      "0:1",
      "0:2",
      "1:8",
      "2:4",
      "4:5",
      "5:6",
      "6:7",
      "7:8",
    ]);
  });
});

describe("joined roof architectural edges", () => {
  it("exposes the exact ridges, valley, hip and four gutter runs", () => {
    expect(roof.ridges).toEqual([
      {
        id: "MAIN_RIDGE",
        kind: "RIDGE",
        startVertexIndex: 2,
        endVertexIndex: 3,
      },
      {
        id: "WING_RIDGE",
        kind: "RIDGE",
        startVertexIndex: 3,
        endVertexIndex: 7,
      },
    ]);
    expect(roof.valley).toEqual({
      id: "JOIN_VALLEY",
      kind: "VALLEY",
      startVertexIndex: 5,
      endVertexIndex: 3,
    });
    expect(roof.hip).toEqual({
      id: "JOIN_HIP",
      kind: "HIP",
      startVertexIndex: 3,
      endVertexIndex: 1,
    });
    expect(roof.gutters.map(({ startVertexIndex, endVertexIndex }) => [
      startVertexIndex,
      endVertexIndex,
    ])).toEqual([
      [0, 1],
      [4, 5],
      [5, 6],
      [1, 8],
    ]);
    expect(roof.gutters.map((gutter) => lineLengthMm(gutter, roof.vertices))).toEqual([
      21_600,
      14_600,
      10_885,
      19_085,
    ]);
  });

  it("has only the west and active 22085 mm roof-end gables", () => {
    expect(roof.gables).toEqual([
      {
        id: "MAIN_WEST_GABLE",
        vertexIndices: [0, 2, 4],
        plane: { axis: "X", coordinateMm: 6_440 },
      },
      {
        id: "WING_END_GABLE",
        vertexIndices: [6, 7, 8],
        plane: { axis: "Y", coordinateMm: 22_085 },
      },
    ]);
    expect(
      roof.gables.some(
        ({ plane }) => plane.axis === "X" && plane.coordinateMm === 28_040,
      ),
    ).toBe(false);
    expect(ACTIVE_JOINED_ROOF_PARAMETERS.wingEndYmm).toBe(22_085);
  });
});

describe("joined roof plane continuity", () => {
  it("meets exactly at the valley eave, four-face junction and hip eave", () => {
    expect(mainGardenRoofHeightMm(11_200)).toBe(3_125);
    expect(wingInnerRoofHeightMm(21_040)).toBe(3_125);

    expect(mainFrontRoofHeightMm(7_100)).toBe(5_560);
    expect(mainGardenRoofHeightMm(7_100)).toBe(5_560);
    expect(wingInnerRoofHeightMm(24_540)).toBe(5_560);
    expect(wingOuterRoofHeightMm(24_540)).toBe(5_560);

    expect(mainFrontRoofHeightMm(3_000)).toBe(3_125);
    expect(wingOuterRoofHeightMm(28_040)).toBe(3_125);
  });

  it("places every face vertex on its declared plane", () => {
    for (const face of roof.faces) {
      for (const vertexIndex of face.vertexIndices) {
        const point = roof.vertices[vertexIndex];
        expect(
          roofHeightMm(face.id, point.xMm, point.yMm),
          `${face.id}:${point.id}`,
        ).toBeCloseTo(point.elevationMm, 10);
      }
    }
  });
});

describe("joined roof standing seams", () => {
  it("clips all seams to their individual roof polygons", () => {
    expect(roof.seamSegments).toHaveLength(100);
    expect(
      countSeams("MAIN_FRONT"),
    ).toBe(28);
    expect(countSeams("MAIN_GARDEN")).toBe(24);
    expect(countSeams("WING_INNER")).toBe(21);
    expect(countSeams("WING_OUTER")).toBe(27);

    for (const seam of roof.seamSegments) {
      expect(seam.start.elevationMm).toBeCloseTo(
        roofHeightMm(seam.faceId, seam.start.xMm, seam.start.yMm),
        10,
      );
      expect(seam.end.elevationMm).toBeCloseTo(
        roofHeightMm(seam.faceId, seam.end.xMm, seam.end.yMm),
        10,
      );
      if (seam.axis === "X") {
        expect(seam.start.xMm).toBe(seam.coordinateMm);
        expect(seam.end.xMm).toBe(seam.coordinateMm);
        expect(seam.start.yMm).toBeLessThan(seam.end.yMm);
      } else {
        expect(seam.start.yMm).toBe(seam.coordinateMm);
        expect(seam.end.yMm).toBe(seam.coordinateMm);
        expect(seam.start.xMm).toBeLessThan(seam.end.xMm);
      }
    }
  });

  it("terminates the last main seams at the hip and valley", () => {
    const front = seam("MAIN_FRONT", 27_320);
    expect(front.start).toEqual({ xMm: 27_320, yMm: 3_000, elevationMm: 3_125 });
    expect(front.end.xMm).toBe(27_320);
    expect(front.end.yMm).toBeCloseTo(3_843.4285714285716, 10);
    expect(front.end.elevationMm).toBeCloseTo(3_625.914285714286, 10);

    const garden = seam("MAIN_GARDEN", 24_280);
    expect(garden.start.xMm).toBe(24_280);
    expect(garden.start.yMm).toBe(7_100);
    expect(garden.start.elevationMm).toBe(5_560);
    expect(garden.end.yMm).toBeCloseTo(7_404.571428571428, 10);
    expect(garden.end.elevationMm).toBeCloseTo(5_379.114285714286, 10);
  });

  it("starts the wing seams on the hip and valley instead of crossing them", () => {
    const outer = seam("WING_OUTER", 3_300);
    expect(outer.start.xMm).toBeCloseTo(27_783.90243902439, 10);
    expect(outer.start.yMm).toBe(3_300);
    expect(outer.start.elevationMm).toBeCloseTo(3_303.170731707317, 10);
    expect(outer.end).toEqual({ xMm: 28_040, yMm: 3_300, elevationMm: 3_125 });

    const inner = seam("WING_INNER", 7_620);
    expect(inner.start.xMm).toBeCloseTo(24_096.09756097561, 10);
    expect(inner.start.yMm).toBe(7_620);
    expect(inner.start.elevationMm).toBeCloseTo(5_251.170731707317, 10);
    expect(inner.end).toEqual({ xMm: 24_540, yMm: 7_620, elevationMm: 5_560 });
  });
});

function edgeIncidence(triangles: readonly RoofTriangle[]): Map<string, number> {
  const incidence = new Map<string, number>();
  for (const { vertexIndices } of triangles) {
    for (const [start, end] of [
      [vertexIndices[0], vertexIndices[1]],
      [vertexIndices[1], vertexIndices[2]],
      [vertexIndices[2], vertexIndices[0]],
    ]) {
      const key = start < end ? `${start}:${end}` : `${end}:${start}`;
      incidence.set(key, (incidence.get(key) ?? 0) + 1);
    }
  }
  return incidence;
}

function singletonEdges(incidence: ReadonlyMap<string, number>): readonly string[] {
  return [...incidence]
    .filter(([, count]) => count === 1)
    .map(([edge]) => edge)
    .sort((left, right) => left.localeCompare(right, "en", { numeric: true }));
}

function lineLengthMm(
  line: { readonly startVertexIndex: number; readonly endVertexIndex: number },
  vertices: readonly RoofVertexMm[],
): number {
  const start = vertices[line.startVertexIndex];
  const end = vertices[line.endVertexIndex];
  return Math.hypot(end.xMm - start.xMm, end.yMm - start.yMm);
}

function countSeams(faceId: string): number {
  return roof.seamSegments.filter((candidate) => candidate.faceId === faceId).length;
}

function seam(faceId: string, coordinateMm: number) {
  const found = roof.seamSegments.find(
    (candidate) =>
      candidate.faceId === faceId && candidate.coordinateMm === coordinateMm,
  );
  expect(found).toBeDefined();
  return found!;
}
