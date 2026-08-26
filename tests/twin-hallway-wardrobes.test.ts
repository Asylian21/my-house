import { describe, expect, it } from "vitest";

import {
  HALLWAY_BUILT_IN_WARDROBES,
  INTERIOR_DOORS,
  INTERIOR_ROOMS,
  type RectMm,
} from "../lib/twin-interior";
import { SOURCES } from "../lib/twin-site";
import { WALK_COLLISION_ELLIPSOID_M } from "../lib/twin-viewport-contract";

const overlaps = (left: RectMm, right: RectMm) =>
  left.x0 < right.x1
  && left.x1 > right.x0
  && left.y0 < right.y1
  && left.y1 > right.y0;

const containsPoint = (rect: RectMm, point: { x: number; y: number }) =>
  point.x >= rect.x0
  && point.x <= rect.x1
  && point.y >= rect.y0
  && point.y <= rect.y1;

function openLeafRect(door: (typeof INTERIOR_DOORS)[number]): RectMm {
  const frameMm = 60;
  const leafThicknessMm = 40;
  const [wallFrom, wallTo] = door.wallSpanMm;
  const hingeAlongMm = door.hinge < 0
    ? door.startMm + frameMm
    : door.startMm + door.widthMm - frameMm;
  const hingeAcrossMm = door.swing < 0 ? wallFrom : wallTo;
  const centerAcrossMm = hingeAcrossMm + door.swing * (door.leafWidthMm / 2 + 10);
  const centerAlongMm = hingeAlongMm
    + (door.hinge < 0 ? 1 : -1) * (leafThicknessMm / 2 + 8);
  return door.axis === "X"
    ? {
        x0: centerAlongMm - leafThicknessMm / 2,
        x1: centerAlongMm + leafThicknessMm / 2,
        y0: centerAcrossMm - (door.leafWidthMm + 20) / 2,
        y1: centerAcrossMm + (door.leafWidthMm + 20) / 2,
      }
    : {
        x0: centerAcrossMm - (door.leafWidthMm + 20) / 2,
        x1: centerAcrossMm + (door.leafWidthMm + 20) / 2,
        y0: centerAlongMm - leafThicknessMm / 2,
        y1: centerAlongMm + leafThicknessMm / 2,
      };
}

function hasHallwayPath(
  roomRects: readonly RectMm[],
  obstacles: readonly RectMm[],
  start: { x: number; y: number },
  goal: { x: number; y: number },
) {
  const radiusMm = WALK_COLLISION_ELLIPSOID_M.x * 1000;
  const diagonalMm = radiusMm / Math.SQRT2;
  const probeOffsets = [
    [0, 0],
    [radiusMm, 0],
    [-radiusMm, 0],
    [0, radiusMm],
    [0, -radiusMm],
    [diagonalMm, diagonalMm],
    [diagonalMm, -diagonalMm],
    [-diagonalMm, diagonalMm],
    [-diagonalMm, -diagonalMm],
  ] as const;
  const insideHallway = (point: { x: number; y: number }) =>
    roomRects.some((rect) => containsPoint(rect, point));
  const walkable = (point: { x: number; y: number }) =>
    probeOffsets.every(([dx, dy]) => insideHallway({ x: point.x + dx, y: point.y + dy }))
    && obstacles.every((rect) => (
      point.x <= rect.x0 - radiusMm
      || point.x >= rect.x1 + radiusMm
      || point.y <= rect.y0 - radiusMm
      || point.y >= rect.y1 + radiusMm
    ));

  const bounds = roomRects.reduce(
    (value, rect) => ({
      x0: Math.min(value.x0, rect.x0),
      y0: Math.min(value.y0, rect.y0),
      x1: Math.max(value.x1, rect.x1),
      y1: Math.max(value.y1, rect.y1),
    }),
    { x0: Infinity, y0: Infinity, x1: -Infinity, y1: -Infinity },
  );
  const stepMm = 50;
  const pointAt = (xIndex: number, yIndex: number) => ({
    x: bounds.x0 + xIndex * stepMm,
    y: bounds.y0 + yIndex * stepMm,
  });
  const indexFor = (point: { x: number; y: number }) => ({
    x: Math.round((point.x - bounds.x0) / stepMm),
    y: Math.round((point.y - bounds.y0) / stepMm),
  });
  const key = (point: { x: number; y: number }) => `${point.x}:${point.y}`;
  const startIndex = indexFor(start);
  const goalIndex = indexFor(goal);
  if (!walkable(pointAt(startIndex.x, startIndex.y))) return false;
  if (!walkable(pointAt(goalIndex.x, goalIndex.y))) return false;

  const queue = [startIndex];
  const visited = new Set([key(startIndex)]);
  for (let cursor = 0; cursor < queue.length; cursor += 1) {
    const current = queue[cursor];
    if (current.x === goalIndex.x && current.y === goalIndex.y) return true;
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]] as const) {
      const next = { x: current.x + dx, y: current.y + dy };
      const nextKey = key(next);
      if (visited.has(nextKey)) continue;
      const point = pointAt(next.x, next.y);
      if (
        point.x < bounds.x0
        || point.x > bounds.x1
        || point.y < bounds.y0
        || point.y > bounds.y1
        || !walkable(point)
      ) continue;
      visited.add(nextKey);
      queue.push(next);
    }
  }
  return false;
}

describe("green-marked hallway wardrobes", () => {
  it("fills the two exact 601 mm corridor niches with flush full-height oak cabinetry", () => {
    const hallway = INTERIOR_ROOMS.find((room) => room.id === "ROOM-1-02")!;
    expect(HALLWAY_BUILT_IN_WARDROBES).toHaveLength(2);
    expect(new Set(HALLWAY_BUILT_IN_WARDROBES.map(({ id }) => id)).size).toBe(2);

    const expected = [
      {
        nicheRectIndex: 5,
        footprintMm: { x0: 20942, y0: 7902, x1: 21543, y1: 10699 },
        facing: "EAST",
        spanMm: 2797,
        doorCount: 4,
        clearDepthMm: 1096,
        reededPanelIndices: [1, 2],
      },
      {
        nicheRectIndex: 2,
        footprintMm: { x0: 16142, y0: 5561, x1: 16743, y1: 6420 },
        facing: "WEST",
        spanMm: 859,
        doorCount: 2,
        clearDepthMm: 999,
        reededPanelIndices: [],
      },
    ] as const;

    for (const [index, wardrobe] of HALLWAY_BUILT_IN_WARDROBES.entries()) {
      const contract = expected[index];
      expect(wardrobe).toMatchObject({
        sourceId: SOURCES.clientHallwayWardrobesRevision20260825.id,
        architecturalSourceId: SOURCES.floorPlan.id,
        status: "CLIENT_DESIGN_CONCEPT",
        roomId: hallway.id,
        nicheRectIndex: contract.nicheRectIndex,
        footprintMm: contract.footprintMm,
        facing: contract.facing,
        heightMm: 2550,
        doorCount: contract.doorCount,
      });
      expect(hallway.rectsMm[wardrobe.nicheRectIndex]).toEqual(wardrobe.footprintMm);
      expect(wardrobe.footprintMm.x1 - wardrobe.footprintMm.x0).toBe(601);
      expect(wardrobe.footprintMm.y1 - wardrobe.footprintMm.y0).toBe(contract.spanMm);
      expect(hallway.clearHeightMm - wardrobe.heightMm).toBe(50);
      expect(wardrobe.style).toMatchObject({
        finish: "BOOKMATCHED_WARM_OAK_WITH_SMOKED_REEDED_ACCENT",
        opening: "HANDLELESS_COPLANAR_SOFT_CLOSE_SLIDING",
        panelRevealMm: 8,
        plinthHeightMm: 80,
        ledCctK: 2700,
        reededPanelIndices: contract.reededPanelIndices,
        reededGrooveCountPerPanel: 5,
      });

      const clearance = wardrobe.frontClearanceRectMm;
      expect(clearance.x1 - clearance.x0).toBe(contract.clearDepthMm);
      expect(clearance.y0).toBe(wardrobe.footprintMm.y0);
      expect(clearance.y1).toBe(wardrobe.footprintMm.y1);
      expect(overlaps(clearance, wardrobe.footprintMm)).toBe(false);
      expect(hallway.rectsMm.some((rect) => (
        clearance.x0 >= rect.x0
        && clearance.y0 >= rect.y0
        && clearance.x1 <= rect.x1
        && clearance.y1 <= rect.y1
      ))).toBe(true);
      if (wardrobe.facing === "EAST") {
        expect(clearance.x0).toBe(wardrobe.footprintMm.x1);
      } else {
        expect(clearance.x1).toBe(wardrobe.footprintMm.x0);
      }
      expect(contract.clearDepthMm - WALK_COLLISION_ELLIPSOID_M.x * 2000)
        .toBeGreaterThanOrEqual(550);
      for (const door of INTERIOR_DOORS) {
        expect(
          overlaps(openLeafRect(door), wardrobe.footprintMm),
          `${wardrobe.id} clears the fully open ${door.id} leaf`,
        ).toBe(false);
      }
    }
  });

  it("keeps a 220 mm-radius avatar connected through the complete L-shaped hallway", () => {
    const hallway = INTERIOR_ROOMS.find((room) => room.id === "ROOM-1-02")!;
    const obstacles = HALLWAY_BUILT_IN_WARDROBES.map(({ footprintMm }) => footprintMm);
    const westApproach = { x: 14500, y: 6000 };
    for (const goal of [
      { x: 16500, y: 7100 },
      { x: 22000, y: 5700 },
      { x: 22000, y: 11000 },
    ]) {
      expect(hasHallwayPath(hallway.rectsMm, obstacles, westApproach, goal)).toBe(true);
    }
  });
});
