import { describe, expect, it } from "vitest";

import {
  FIREPLACE_PIER,
  INTERIOR_DOORS,
  INTERIOR_ROOMS,
  INTERIOR_WALLS,
  KITCHEN_RUN,
  LIVING_DINING_FITOUT,
  ceilingElevationMm,
  roomAreaM2,
  roomAt,
  totalDocumentedFloorAreaM2,
  type RectMm,
} from "../lib/twin-interior";
import { HOUSE, SOURCES } from "../lib/twin-site";

const overlaps = (a: RectMm, b: RectMm) =>
  a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1;

const inside = (rect: RectMm, outer: RectMm) =>
  rect.x0 >= outer.x0 && rect.x1 <= outer.x1 && rect.y0 >= outer.y0 && rect.y1 <= outer.y1;

const lowerBar: RectMm = {
  x0: HOUSE.originMm.x,
  y0: HOUSE.originMm.y,
  x1: HOUSE.originMm.x + HOUSE.lowerBar.widthMm,
  y1: HOUSE.originMm.y + HOUSE.lowerBar.depthMm,
};
const wing: RectMm = {
  x0: HOUSE.originMm.x + HOUSE.wing.xMm,
  y0: HOUSE.originMm.y + HOUSE.wing.yMm,
  x1: HOUSE.originMm.x + HOUSE.wing.xMm + HOUSE.wing.widthMm,
  y1: HOUSE.originMm.y + HOUSE.wing.yMm + HOUSE.wing.depthMm,
};
// The wing column continues straight through the lower bar (corridor spine
// and kitchen bay cross the y = 11 200 line).
const wingColumn: RectMm = { x0: wing.x0, y0: lowerBar.y0, x1: wing.x1, y1: wing.y1 };
const insideFootprint = (rect: RectMm) =>
  inside(rect, lowerBar) || inside(rect, wing) || inside(rect, wingColumn);

describe("interior of 1.NP traced from D1.1.002", () => {
  it("lists the twelve legend rooms whose documented areas sum to the D1 floor area", () => {
    expect(INTERIOR_ROOMS.map((room) => room.number)).toEqual([
      "1.01", "1.02", "1.03", "1.04", "1.05", "1.06",
      "1.07", "1.08", "1.09", "1.10", "1.11", "1.12",
    ]);
    expect(totalDocumentedFloorAreaM2()).toBeCloseTo(HOUSE.floorAreaM2, 2);
  });

  it("reproduces the legend areas from the traced wall faces", () => {
    // 1.02 and 1.03 are measured differently in the legend (the corridor
    // spine and the kitchen bay are counted once, not per room); the vector
    // trace stays the geometry of record and the deviation is visible here.
    const tolerance: Record<string, number> = { "1.02": 0.8, "1.03": 3, "1.05": 0.2 };
    for (const room of INTERIOR_ROOMS) {
      const area = roomAreaM2(room);
      expect(Math.abs(area - room.documentedAreaM2), room.number).toBeLessThan(
        tolerance[room.number] ?? 0.05,
      );
    }
    // 1.03 legend = 6 000 × 8 075 clear span; the trace adds the kitchen bay.
    const living = INTERIOR_ROOMS.find((room) => room.number === "1.03")!;
    expect(roomAreaM2(living)).toBeGreaterThan(living.documentedAreaM2);
  });

  it("keeps every room and wall inside the D1 footprint with no overlaps", () => {
    const rects = INTERIOR_ROOMS.flatMap((room) =>
      room.rectsMm.map((rect) => ({ rect, owner: room.number })),
    );
    for (const { rect, owner } of rects) {
      expect(insideFootprint(rect), `${owner} inside footprint`).toBe(true);
      expect(rect.x1 > rect.x0 && rect.y1 > rect.y0, `${owner} non-degenerate`).toBe(true);
    }
    for (let a = 0; a < rects.length; a += 1) {
      for (let b = a + 1; b < rects.length; b += 1) {
        if (rects[a].owner === rects[b].owner) continue;
        expect(overlaps(rects[a].rect, rects[b].rect), `${rects[a].owner} × ${rects[b].owner}`).toBe(false);
      }
    }
    for (const wall of INTERIOR_WALLS) {
      expect(insideFootprint(wall.rectMm), wall.id).toBe(true);
      for (const { rect, owner } of rects) {
        expect(overlaps(wall.rectMm, rect), `${wall.id} × ${owner}`).toBe(false);
      }
    }
    // The 347 × 500 pier stands inside 1.03 against its west wall.
    const living = INTERIOR_ROOMS.find((room) => room.number === "1.03")!;
    expect(inside(FIREPLACE_PIER.rectMm, living.rectsMm[0])).toBe(true);
    expect(FIREPLACE_PIER.rectMm.x0).toBe(living.rectsMm[0].x0);
  });

  it("uses the plan wall thicknesses (140 partitions, 190–300 load-bearing)", () => {
    for (const wall of INTERIOR_WALLS) {
      const thickness = Math.min(
        wall.rectMm.x1 - wall.rectMm.x0,
        wall.rectMm.y1 - wall.rectMm.y0,
      );
      if (wall.role === "PARTITION") {
        expect(thickness, wall.id).toBeGreaterThanOrEqual(97);
        expect(thickness, wall.id).toBeLessThanOrEqual(250);
      } else {
        expect(thickness, wall.id).toBeGreaterThanOrEqual(190);
        expect(thickness, wall.id).toBeLessThanOrEqual(530);
      }
    }
  });

  it("places every door in a clear wall gap between its two rooms", () => {
    for (const door of INTERIOR_DOORS) {
      const [wallFrom, wallTo] = door.wallSpanMm;
      const opening: RectMm =
        door.axis === "X"
          ? { x0: door.startMm, x1: door.startMm + door.widthMm, y0: wallFrom, y1: wallTo }
          : { x0: wallFrom, x1: wallTo, y0: door.startMm, y1: door.startMm + door.widthMm };
      for (const wall of INTERIOR_WALLS) {
        expect(overlaps(opening, wall.rectMm), `${door.id} blocked by ${wall.id}`).toBe(false);
      }
      expect(door.leafWidthMm).toBeLessThan(door.widthMm);
      expect(door.heightMm).toBe(2100);
      const from = INTERIOR_ROOMS.find((room) => room.id === door.fromRoomId)!;
      const to = INTERIOR_ROOMS.find((room) => room.id === door.toRoomId)!;
      // A room touches the door when its rectangles, taken together, line
      // the full clear opening on one face of the wall.
      const touches = (roomRects: readonly RectMm[]) => {
        const lining = roomRects.filter((rect) =>
          door.axis === "X"
            ? (Math.abs(rect.y1 - wallFrom) < 2 || Math.abs(rect.y0 - wallTo) < 2) &&
              rect.x0 < opening.x1 && rect.x1 > opening.x0
            : (Math.abs(rect.x1 - wallFrom) < 2 || Math.abs(rect.x0 - wallTo) < 2) &&
              rect.y0 < opening.y1 && rect.y1 > opening.y0,
        );
        const start = door.startMm;
        const end = door.startMm + door.widthMm;
        const covered = lining
          .map((rect) => (door.axis === "X" ? [rect.x0, rect.x1] : [rect.y0, rect.y1]))
          .sort((a, b) => a[0] - b[0]);
        let cursor = start;
        for (const [from, to] of covered) {
          if (from > cursor + 1) break;
          cursor = Math.max(cursor, to);
        }
        return cursor >= end - 1;
      };
      expect(touches(from.rectsMm), `${door.id} from ${from.number}`).toBe(true);
      expect(touches(to.rectsMm), `${door.id} to ${to.number}`).toBe(true);
    }
  });

  it("gives 1.03 the 2 750 / 4 850 vault and every other room its flat SDK height", () => {
    const living = INTERIOR_ROOMS.find((room) => room.number === "1.03")!;
    expect(living.ceiling).toBe("VAULTED_TO_RIDGE");
    expect(ceilingElevationMm(living, 21543)).toBe(2750);
    expect(ceilingElevationMm(living, 24540)).toBe(4850);
    expect(ceilingElevationMm(living, 27541)).toBeCloseTo(2750, -1);
    for (const room of INTERIOR_ROOMS) {
      if (room === living) continue;
      expect(room.ceiling).toBe("FLAT");
      expect(ceilingElevationMm(room, 10000)).toBe(room.clearHeightMm);
      expect(room.clearHeightMm).toBe(2600);
    }
  });

  it("resolves walk positions to rooms and keeps the kitchen inside 1.03", () => {
    expect(roomAt({ x: 24540, y: 17200 })?.number).toBe("1.03");
    expect(roomAt({ x: 22090, y: 7100 })?.number).toBe("1.02");
    expect(roomAt({ x: 10300, y: 5000 })?.number).toBe("1.12");
    expect(roomAt({ x: 24540, y: 21000 })).toBeNull();
    for (const room of INTERIOR_ROOMS) {
      expect(roomAt(room.standingPointMm)?.id, room.number).toBe(room.id);
    }
    expect(roomAt({ x: (KITCHEN_RUN.rectMm.x0 + KITCHEN_RUN.rectMm.x1) / 2, y: 11200 })?.number).toBe("1.03");
    expect(KITCHEN_RUN.barStoolCount).toBe(0);
  });

  it("lays out the client living and dining concept between the fireplace, glazing and kitchen", () => {
    const fitout = LIVING_DINING_FITOUT;
    const living = INTERIOR_ROOMS.find((room) => room.number === "1.03")!;
    const livingMain = living.rectsMm[0];
    const tvWall = fitout.tvWall.rectMm;
    const rearGlazing = HOUSE.porches.wingEnd.glazing;
    const rearInnerFaceYmm = HOUSE.porches.wingEnd.glazingFaceYmm - 500;

    expect(fitout.sourceId).toBe(SOURCES.clientRevision20260823.id);
    expect(fitout.status).toBe("CLIENT_DESIGN_CONCEPT");
    expect(tvWall.x0).toBe(livingMain.x0);
    expect(tvWall.x1).toBeLessThan(rearGlazing.startXmm);
    expect(tvWall.y0 - FIREPLACE_PIER.rectMm.y1).toBeGreaterThanOrEqual(300);
    expect(rearInnerFaceYmm - tvWall.y1).toBeGreaterThanOrEqual(250);
    expect(inside(tvWall, livingMain)).toBe(true);

    const [bayY0, bayY1] = fitout.tvWall.centralBayYmm;
    expect(bayY0).toBeGreaterThan(tvWall.y0);
    expect(bayY1).toBeLessThan(tvWall.y1);
    expect(bayY1 - bayY0).toBeGreaterThan(fitout.tvWall.tv.widthMm);
    expect(fitout.tvWall.tv.diagonalIn).toBe(98);
    expect(fitout.tvWall.tv.widthMm / fitout.tvWall.tv.heightMm).toBeCloseTo(16 / 9, 2);

    const { mainRectMm, chaiseRectMm } = fitout.sofa;
    expect(inside(mainRectMm, livingMain)).toBe(true);
    expect(inside(chaiseRectMm, livingMain)).toBe(true);
    expect(mainRectMm.y1).toBeLessThan(rearInnerFaceYmm);
    expect(chaiseRectMm.x0 - (rearGlazing.startXmm + rearGlazing.widthMm)).toBeGreaterThanOrEqual(400);
    expect(overlaps(mainRectMm, chaiseRectMm)).toBe(true);
    expect(mainRectMm.y1 - mainRectMm.y0).toBeGreaterThan(mainRectMm.x1 - mainRectMm.x0);
    expect(chaiseRectMm.x1 - chaiseRectMm.x0).toBeGreaterThan(chaiseRectMm.y1 - chaiseRectMm.y0);
    expect(mainRectMm.x0 - tvWall.x1).toBeGreaterThanOrEqual(4000);
    expect(mainRectMm.x0 - tvWall.x1).toBeLessThanOrEqual(4500);

    const tableRect: RectMm = {
      x0: fitout.dining.tableCenterMm.x - fitout.dining.tableLengthMm / 2,
      x1: fitout.dining.tableCenterMm.x + fitout.dining.tableLengthMm / 2,
      y0: fitout.dining.tableCenterMm.y - fitout.dining.tableDepthMm / 2,
      y1: fitout.dining.tableCenterMm.y + fitout.dining.tableDepthMm / 2,
    };
    expect(inside(tableRect, livingMain)).toBe(true);
    expect(KITCHEN_RUN.peninsulaRectMm.y1).toBeLessThan(tableRect.y0);
    expect(tableRect.y1).toBeLessThan(mainRectMm.y0);
    expect(tableRect.x0 - tvWall.x1).toBeGreaterThanOrEqual(1200);
    expect(fitout.dining.tableLengthMm).toBe(1400);
    expect(fitout.dining.tableDepthMm).toBe(800);
    expect(fitout.dining.tableLengthMm * fitout.dining.tableDepthMm).toBeLessThanOrEqual(1_120_000);
    expect(fitout.dining.chairs).toHaveLength(4);
    expect(new Set(fitout.dining.chairs.map((chair) => chair.id)).size).toBe(4);
    expect(new Set(fitout.dining.chairs.map((chair) => chair.facing))).toEqual(
      new Set(["NORTH", "SOUTH"]),
    );
    const southChairs = fitout.dining.chairs.filter((chair) => chair.facing === "NORTH");
    const northChairs = fitout.dining.chairs.filter((chair) => chair.facing === "SOUTH");
    expect(tableRect.y0 - Math.max(...southChairs.map((chair) => chair.centerMm.y))).toBe(350);
    expect(Math.min(...northChairs.map((chair) => chair.centerMm.y)) - tableRect.y1).toBe(350);
    for (const chair of fitout.dining.chairs) {
      expect(roomAt(chair.centerMm)?.id, chair.id).toBe(living.id);
    }

    expect(overlaps(tableRect, mainRectMm)).toBe(false);
    expect(overlaps(tableRect, chaiseRectMm)).toBe(false);
    expect(overlaps(tvWall, mainRectMm)).toBe(false);
    expect(overlaps(tvWall, chaiseRectMm)).toBe(false);
    expect(overlaps(mainRectMm, chaiseRectMm)).toBe(true);
    expect(overlaps(tableRect, {
      x0: living.standingPointMm.x - 220,
      x1: living.standingPointMm.x + 220,
      y0: living.standingPointMm.y - 220,
      y1: living.standingPointMm.y + 220,
    })).toBe(false);
  });
});
