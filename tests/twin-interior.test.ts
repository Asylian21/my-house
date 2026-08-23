import { describe, expect, it } from "vitest";

import {
  BATHROOM_FITOUT,
  FIREPLACE_PIER,
  INTERIOR_DOORS,
  INTERIOR_ROOMS,
  INTERIOR_WALLS,
  KITCHEN_RUN,
  LIVING_DINING_FITOUT,
  TECHNICAL_HEATING_FITOUT,
  WC_FITOUT,
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
    const tolerance: Record<string, number> = {
      "1.02": 0.8,
      "1.03": 3,
      "1.05": 0.2,
      // Client revision transfers 0.48 m² from 1.07 to 1.06 while the
      // documentedAreaM2 fields retain the original D1.1.002 legend values.
      "1.06": 0.5,
      "1.07": 0.5,
    };
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
    expect(KITCHEN_RUN.designSourceId).toBe(SOURCES.clientKitchenRevision20260823.id);
    expect(KITCHEN_RUN.eastReturnSourceId).toBe(SOURCES.clientKitchenLRevision20260823.id);
    expect(inside(KITCHEN_RUN.fridgeUnitRectMm, KITCHEN_RUN.rectMm)).toBe(true);
    expect(KITCHEN_RUN.fridgeUnitRectMm).toEqual({ x0: 22791, y0: 10949, x1: 23391, y1: 11550 });
    expect(KITCHEN_RUN.fridgeUnitRectMm.x1 - KITCHEN_RUN.fridgeUnitRectMm.x0).toBe(600);
    expect(KITCHEN_RUN.fridgeCabinetHeightMm).toBe(2250);
    expect(KITCHEN_RUN.peninsulaRectMm.y0 - KITCHEN_RUN.fridgeUnitRectMm.y1).toBeGreaterThanOrEqual(900);
    expect(KITCHEN_RUN.fridgeUnitRectMm.x1).toBeLessThan(KITCHEN_RUN.sinkCenterXmm);
    expect(roomAt({
      x: (KITCHEN_RUN.fridgeUnitRectMm.x0 + KITCHEN_RUN.fridgeUnitRectMm.x1) / 2,
      y: (KITCHEN_RUN.fridgeUnitRectMm.y0 + KITCHEN_RUN.fridgeUnitRectMm.y1) / 2,
    })?.number).toBe("1.03");
    const technicalDoor = INTERIOR_DOORS.find((door) => door.id === "DOOR-103-107")!;
    expect(technicalDoor.startMm - KITCHEN_RUN.fridgeUnitRectMm.x1).toBeGreaterThanOrEqual(2400);
    expect(KITCHEN_RUN.ovenCenterXmm).toBe(KITCHEN_RUN.hobCenterXmm);
    expect(KITCHEN_RUN.ovenCenterXmm - 280).toBeGreaterThan(KITCHEN_RUN.peninsulaRectMm.x0);
    expect(KITCHEN_RUN.ovenCenterXmm + 280).toBeLessThan(KITCHEN_RUN.peninsulaRectMm.x1);
    const eastReturn = KITCHEN_RUN.eastReturnRectMm;
    const eastWindow = HOUSE.facades.east.openings.find((opening) => opening.id === "EAST-04")!;
    expect(inside(eastReturn, INTERIOR_ROOMS.find((room) => room.number === "1.03")!.rectsMm[0])).toBe(true);
    expect(eastReturn.x1 - eastReturn.x0).toBe(600);
    expect(eastReturn.y1 - eastReturn.y0).toBe(994);
    expect(eastReturn.x1).toBe(INTERIOR_ROOMS.find((room) => room.number === "1.03")!.rectsMm[0].x1);
    expect(eastReturn.y1).toBe(KITCHEN_RUN.peninsulaRectMm.y0);
    expect(eastReturn.x0 - (technicalDoor.startMm + technicalDoor.widthMm)).toBeGreaterThanOrEqual(250);
    expect(eastWindow.startYmm - eastReturn.y1).toBeGreaterThanOrEqual(150);
    expect(overlaps(eastReturn, KITCHEN_RUN.peninsulaRectMm)).toBe(false);
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

  it("fits the wood boiler and 1 000 l accumulator into room 1.07 without blocking either access", () => {
    const fitout = TECHNICAL_HEATING_FITOUT;
    const technicalRoom = INTERIOR_ROOMS.find((room) => room.id === fitout.roomId)!;
    const technicalDoor = INTERIOR_DOORS.find((door) => door.id === "DOOR-103-107")!;
    const eastDoor = HOUSE.facades.east.openings.find(
      (opening) => opening.id === fitout.exteriorAccessOpeningId,
    )!;
    const cornersInsideTechnicalRoom = (rect: RectMm) => [
      { x: rect.x0, y: rect.y0 },
      { x: rect.x1, y: rect.y0 },
      { x: rect.x0, y: rect.y1 },
      { x: rect.x1, y: rect.y1 },
    ].every((point) => roomAt(point)?.id === technicalRoom.id);

    expect(fitout.sourceId).toBe(SOURCES.clientTechnicalHeatingRevision20260823.id);
    expect(fitout.architecturalSourceId).toBe(SOURCES.floorPlan.id);
    expect(fitout.status).toBe("CLIENT_DESIGN_CONCEPT");
    expect(technicalRoom.number).toBe("1.07");

    const boiler = fitout.boiler;
    expect(cornersInsideTechnicalRoom(boiler.footprintMm)).toBe(true);
    expect(boiler.footprintMm.x1 - boiler.footprintMm.x0).toBe(800);
    expect(boiler.footprintMm.y1 - boiler.footprintMm.y0).toBe(900);
    expect(boiler.heightMm).toBe(1450);
    expect(boiler.front).toBe("NORTH");
    expect(cornersInsideTechnicalRoom(boiler.serviceRectMm)).toBe(true);
    expect(boiler.serviceRectMm.x1 - boiler.serviceRectMm.x0).toBe(900);
    expect(boiler.serviceRectMm.y1 - boiler.serviceRectMm.y0).toBe(900);
    expect(overlaps(boiler.footprintMm, boiler.serviceRectMm)).toBe(false);
    expect(boiler.serviceRectMm.y1).toBeLessThan(eastDoor.startYmm);
    expect(boiler.heightMm).toBeLessThan(technicalRoom.clearHeightMm);

    const tank = fitout.accumulator;
    const tankRadiusMm = tank.outerDiameterMm / 2;
    const tankBounds: RectMm = {
      x0: tank.centerMm.x - tankRadiusMm,
      y0: tank.centerMm.y - tankRadiusMm,
      x1: tank.centerMm.x + tankRadiusMm,
      y1: tank.centerMm.y + tankRadiusMm,
    };
    expect(tank.nominalVolumeL).toBe(1000);
    expect(tank.outerDiameterMm).toBe(1000);
    expect(tank.heightMm).toBe(2100);
    expect(cornersInsideTechnicalRoom(tankBounds)).toBe(true);
    expect(tank.heightMm).toBeLessThan(technicalRoom.clearHeightMm);
    expect(overlaps(tankBounds, boiler.footprintMm)).toBe(false);
    expect(overlaps(tankBounds, boiler.serviceRectMm)).toBe(false);
    expect(tank.centerMm).toEqual({ x: 25026, y: 9912 });
    const technicalWestBay = technicalRoom.rectsMm[0];
    expect(tankBounds.x0 - technicalWestBay.x0).toBeGreaterThanOrEqual(300);
    expect(technicalWestBay.x1 - tankBounds.x1).toBeGreaterThanOrEqual(300);
    expect(technicalDoor.startMm - tankBounds.x1).toBeGreaterThanOrEqual(350);
    const openTechnicalLeafSouthEdge =
      technicalDoor.wallSpanMm[0] - technicalDoor.leafWidthMm - 20;
    expect(openTechnicalLeafSouthEdge - tankBounds.y1).toBeGreaterThanOrEqual(250);
    expect(technicalDoor.swing).toBe(-1);
  });

  it("expands room 1.06 by 300 mm and fits a wall-hung WC plus compact basin", () => {
    const fitout = WC_FITOUT;
    const wc = INTERIOR_ROOMS.find((room) => room.id === fitout.roomId)!;
    const technicalRoom = INTERIOR_ROOMS.find((room) => room.id === "ROOM-1-07")!;
    const wcRect = wc.rectsMm[0];
    const technicalWestBay = technicalRoom.rectsMm[0];
    const partition = INTERIOR_WALLS.find((wall) => wall.id === "IW-WC-EAST")!;
    const wcDoor = INTERIOR_DOORS.find((door) => door.id === "DOOR-102-106")!;
    const insideWc = (rect: RectMm) => [
      { x: rect.x0, y: rect.y0 },
      { x: rect.x1, y: rect.y0 },
      { x: rect.x0, y: rect.y1 },
      { x: rect.x1, y: rect.y1 },
    ].every((point) => roomAt(point)?.id === wc.id);

    expect(fitout.sourceId).toBe(SOURCES.clientWcRevision20260823.id);
    expect(fitout.status).toBe("CLIENT_DESIGN_CONCEPT");
    expect(fitout.expansionMm).toBe(300);
    expect(wcRect).toEqual({ x0: 22783, y0: 9112, x1: 24082, y1: 10712 });
    expect(wcRect.x1 - wcRect.x0).toBe(1299);
    expect(roomAreaM2(wc)).toBeCloseTo(2.0784, 4);
    expect(roomAreaM2(technicalRoom)).toBeCloseTo(9.247247, 6);
    expect(partition.rectMm).toEqual({ x0: 24082, y0: 9112, x1: 24221, y1: 10712 });
    expect(partition.rectMm.x0).toBe(wcRect.x1);
    expect(partition.rectMm.x1).toBe(technicalWestBay.x0);
    expect(partition.rectMm.x1 - partition.rectMm.x0).toBe(139);

    expect(insideWc(fitout.toilet.footprintMm)).toBe(true);
    expect(insideWc(fitout.toilet.concealedCisternRectMm)).toBe(true);
    expect(fitout.toilet.facing).toBe("WEST");
    expect(fitout.toilet.seatElevationMm).toBe(450);
    expect(fitout.toilet.footprintMm.x1 - fitout.toilet.footprintMm.x0).toBe(520);
    expect(fitout.toilet.footprintMm.y1 - fitout.toilet.footprintMm.y0).toBe(370);
    expect(wcDoor.startMm - fitout.toilet.footprintMm.y1).toBeGreaterThanOrEqual(150);

    expect(insideWc(fitout.basin.footprintMm)).toBe(true);
    expect(fitout.basin.facing).toBe("SOUTH");
    expect(fitout.basin.rimElevationMm).toBe(850);
    expect(fitout.basin.footprintMm.x1 - fitout.basin.footprintMm.x0).toBe(450);
    expect(fitout.basin.footprintMm.y1 - fitout.basin.footprintMm.y0).toBe(320);
    expect(overlaps(fitout.toilet.footprintMm, fitout.basin.footprintMm)).toBe(false);

    const openDoorLeafEastEdge = wcDoor.wallSpanMm[1] + wcDoor.leafWidthMm + 20;
    expect(fitout.toilet.footprintMm.x0 - openDoorLeafEastEdge).toBeGreaterThanOrEqual(50);
    expect(fitout.basin.footprintMm.x0 - openDoorLeafEastEdge).toBeGreaterThanOrEqual(90);
    expect(insideWc(fitout.clearFloorRectMm)).toBe(true);
    expect(fitout.clearFloorRectMm.x1 - fitout.clearFloorRectMm.x0).toBeGreaterThanOrEqual(750);
    expect(fitout.clearFloorRectMm.y1 - fitout.clearFloorRectMm.y0).toBeGreaterThanOrEqual(650);
    expect(overlaps(fitout.clearFloorRectMm, fitout.toilet.footprintMm)).toBe(false);
    expect(overlaps(fitout.clearFloorRectMm, fitout.basin.footprintMm)).toBe(false);
  });

  it("fits the window-end shower and one built-in bathroom wall into room 1.05", () => {
    const fitout = BATHROOM_FITOUT;
    const bathroom = INTERIOR_ROOMS.find((room) => room.id === fitout.roomId)!;
    const bathroomDoor = INTERIOR_DOORS.find((door) => door.id === "DOOR-102-105")!;
    const eastWindow = HOUSE.facades.east.openings.find((opening) => opening.id === "EAST-02")!;
    const insideBathroom = (rect: RectMm) => [
      { x: rect.x0, y: rect.y0 },
      { x: rect.x1 - 1, y: rect.y0 },
      { x: rect.x0, y: rect.y1 - 1 },
      { x: rect.x1 - 1, y: rect.y1 - 1 },
    ].every((point) => roomAt(point)?.id === bathroom.id);

    expect(fitout.sourceId).toBe(SOURCES.clientBathroomBuiltInRevision20260823.id);
    expect(fitout.architecturalSourceId).toBe(SOURCES.floorPlan.id);
    expect(fitout.status).toBe("CLIENT_DESIGN_CONCEPT");
    expect(roomAreaM2(bathroom)).toBeCloseTo(8.339778, 6);

    expect(insideBathroom(fitout.shower.footprintMm)).toBe(true);
    expect(fitout.shower.footprintMm.x1 - fitout.shower.footprintMm.x0).toBeGreaterThanOrEqual(1200);
    expect(fitout.shower.footprintMm.y1 - fitout.shower.footprintMm.y0).toBe(900);
    expect(inside(fitout.shower.glassPanelMm, fitout.shower.footprintMm)).toBe(true);
    expect(inside(fitout.shower.linearDrainMm, fitout.shower.footprintMm)).toBe(true);
    expect(fitout.shower.clearEntryWidthMm).toBeGreaterThanOrEqual(600);
    expect(eastWindow.sillMm).toBe(1750);
    expect(inside(fitout.shower.footprintMm, bathroom.rectsMm[1])).toBe(true);
    expect(fitout.shower.footprintMm.x1).toBe(bathroom.rectsMm[1].x1);
    expect(fitout.shower.footprintMm.y0).toBeLessThan(eastWindow.startYmm + eastWindow.widthMm);
    expect(fitout.shower.footprintMm.y1).toBeGreaterThan(eastWindow.startYmm);

    const builtIn = fitout.builtIn;
    expect(insideBathroom(builtIn.footprintMm)).toBe(true);
    expect(inside(builtIn.footprintMm, bathroom.rectsMm[0])).toBe(true);
    expect(builtIn.footprintMm.x0).toBe(bathroom.rectsMm[0].x0);
    expect(builtIn.footprintMm.x1).toBe(bathroom.rectsMm[0].x1);
    expect(builtIn.footprintMm.y1).toBe(bathroom.rectsMm[0].y1);
    expect(builtIn.footprintMm.x1 - builtIn.footprintMm.x0).toBe(2616);
    expect(builtIn.footprintMm.y1 - builtIn.footprintMm.y0).toBe(650);
    expect(builtIn.facing).toBe("SOUTH");
    expect(builtIn.heightMm).toBeLessThan(bathroom.clearHeightMm);
    expect(builtIn.overheadCabinetBottomMm).toBeGreaterThan(builtIn.counterHeightMm);

    expect(inside(builtIn.basin.footprintMm, builtIn.footprintMm)).toBe(true);
    expect(builtIn.basin.footprintMm.x1 - builtIn.basin.footprintMm.x0).toBeGreaterThanOrEqual(1100);
    expect(builtIn.basin.footprintMm.y1 - builtIn.basin.footprintMm.y0).toBeGreaterThanOrEqual(450);
    expect(builtIn.basin.finish).toBe("MATTE_BLACK");
    expect(builtIn.basin.rimElevationMm).toBe(builtIn.counterHeightMm);

    expect(builtIn.appliances.map((appliance) => appliance.kind)).toEqual(["WASHER", "DRYER"]);
    expect(builtIn.appliances.map((appliance) => appliance.finish)).toEqual(["WHITE", "WHITE"]);
    for (const appliance of builtIn.appliances) {
      expect(inside(appliance.footprintMm, builtIn.footprintMm), appliance.kind).toBe(true);
      expect(appliance.footprintMm.x1 - appliance.footprintMm.x0, appliance.kind).toBe(600);
      expect(appliance.footprintMm.y1 - appliance.footprintMm.y0, appliance.kind).toBe(600);
    }
    expect(overlaps(builtIn.appliances[0].footprintMm, builtIn.appliances[1].footprintMm)).toBe(false);
    expect(builtIn.appliances[0].footprintMm.x1).toBeLessThan(builtIn.appliances[1].footprintMm.x0);

    expect(insideBathroom(fitout.clearFloorRectMm)).toBe(true);
    expect(fitout.clearFloorRectMm.x1 - fitout.clearFloorRectMm.x0).toBeGreaterThanOrEqual(2600);
    expect(fitout.clearFloorRectMm.y1 - fitout.clearFloorRectMm.y0).toBeGreaterThanOrEqual(850);
    expect(roomAt(bathroom.standingPointMm)?.id).toBe(bathroom.id);
    expect(inside(fitout.clearFloorRectMm, bathroom.rectsMm[0])).toBe(true);
    expect(bathroom.standingPointMm.x).toBeGreaterThan(fitout.clearFloorRectMm.x0);
    expect(bathroom.standingPointMm.x).toBeLessThan(fitout.clearFloorRectMm.x1);
    expect(bathroom.standingPointMm.y).toBeGreaterThan(fitout.clearFloorRectMm.y0);
    expect(bathroom.standingPointMm.y).toBeLessThan(fitout.clearFloorRectMm.y1);
    expect(insideBathroom(fitout.applianceServiceRectMm)).toBe(true);
    expect(fitout.applianceServiceRectMm.y1 - fitout.applianceServiceRectMm.y0).toBe(900);

    for (const [label, rect] of [
      ["sprcha", fitout.shower.footprintMm],
      ["vstavaná stena", builtIn.footprintMm],
    ] as const) {
      expect(overlaps(rect, fitout.clearFloorRectMm), `${label} × voľný stred`).toBe(false);
    }
    expect(overlaps(fitout.shower.footprintMm, builtIn.footprintMm)).toBe(false);

    const leafRect: RectMm = {
      x0: bathroomDoor.wallSpanMm[1],
      x1: bathroomDoor.wallSpanMm[1] + bathroomDoor.leafWidthMm + 20,
      y0: bathroomDoor.startMm + 60,
      y1: bathroomDoor.startMm + 100,
    };
    expect(overlaps(leafRect, fitout.shower.footprintMm)).toBe(false);
    expect(overlaps(leafRect, builtIn.footprintMm)).toBe(false);
  });
});
