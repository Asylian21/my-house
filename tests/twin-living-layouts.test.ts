import { describe, expect, it } from "vitest";

import {
  DEFAULT_LIVING_LAYOUT_ID,
  FIREPLACE_STOVE_B,
  LIVING_DINING_FITOUT_B,
  LIVING_LAYOUTS,
  LIVING_LAYOUT_IDS,
  PENINSULA_WORKTOP_EDGE_YMM,
  coffeeTableRectMm,
  diningChairSeatRectMm,
  diningTableRectMm,
  normalizeLivingLayout,
} from "../lib/twin-living-layouts";
import {
  FIREPLACE_STOVE,
  INTERIOR_ROOMS,
  KITCHEN_RUN,
  LIVING_DINING_FITOUT,
  type RectMm,
} from "../lib/twin-interior-baseline";
import { HOUSE, SOURCES } from "../lib/twin-site";

const overlaps = (a: RectMm, b: RectMm) => a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1;
const inside = (rect: RectMm, outer: RectMm) =>
  rect.x0 >= outer.x0 && rect.x1 <= outer.x1 && rect.y0 >= outer.y0 && rect.y1 <= outer.y1;
const living = INTERIOR_ROOMS.find((room) => room.number === "1.03")!;
const livingMain = living.rectsMm[0];
const porch = HOUSE.porches.wingEnd;
/** Inner face of the garden gable of the wing (the room rectangle runs under the wall). */
const gableInnerFaceYmm = porch.glazingFaceYmm - 500;
const usable: RectMm = { ...livingMain, y1: gableInnerFaceYmm };

describe("switchable living-room layouts of room 1.03", () => {
  it("keeps variant A identical to the active model data and normalises the URL value", () => {
    expect(LIVING_LAYOUT_IDS).toEqual(["A", "B"]);
    expect(DEFAULT_LIVING_LAYOUT_ID).toBe("A");
    expect(LIVING_LAYOUTS.A.fitout).toBe(LIVING_DINING_FITOUT);
    expect(LIVING_LAYOUTS.A.stove).toBe(FIREPLACE_STOVE);
    expect(LIVING_LAYOUTS.B.fitout).toBe(LIVING_DINING_FITOUT_B);
    expect(LIVING_LAYOUTS.B.stove).toBe(FIREPLACE_STOVE_B);
    expect(LIVING_LAYOUTS.B.sourceId).toBe(SOURCES.clientLivingVariantB20260911.id);
    expect(SOURCES.clientLivingVariantB20260911.kind).toBe("CLIENT_REVISION");
    for (const value of ["b", "B", " b"]) expect(normalizeLivingLayout(value.trim())).toBe("B");
    for (const value of ["a", "A", "", "x", null, undefined]) expect(normalizeLivingLayout(value)).toBe("A");
    expect(diningTableRectMm(LIVING_DINING_FITOUT.dining)).toEqual({ x0: 23800, x1: 25800, y0: 14580, y1: 15480 });
    // Both variants seat six at the same 2 000 × 900 table.
    for (const layout of Object.values(LIVING_LAYOUTS)) {
      expect(layout.fitout.dining.tableLengthMm).toBe(2000);
      expect(layout.fitout.dining.tableDepthMm).toBe(900);
      expect(layout.fitout.dining.chairs).toHaveLength(6);
      expect(layout.notes.join(" ")).toMatch(/13 800 mm/);
    }
    // A's rug keeps the bounds of the shipped ArchViz asset; the north chairs' rear legs
    // (145 mm behind the seat centre, Ø55) stand on the floor just short of it.
    const A = LIVING_LAYOUTS.A;
    expect(A.rugRectMm).toEqual({ x0: 22520, y0: 15580, x1: 27190, y1: 18880 });
    for (const chair of A.fitout.dining.chairs.filter((chair) => chair.facing === "SOUTH")) {
      expect(chair.centerMm.y + 145 + 28).toBeLessThanOrEqual(A.rugRectMm.y0);
    }
    for (const rect of A.coffeeTables.map(coffeeTableRectMm)) expect(inside(rect, A.rugRectMm)).toBe(true);
    expect(PENINSULA_WORKTOP_EDGE_YMM).toBe(HOUSE.facades.wingWest.opening.startYmm + HOUSE.facades.wingWest.opening.widthMm);
  });

  it("places every variant B piece inside the usable living room without collisions", () => {
    const B = LIVING_LAYOUTS.B;
    const { tvWall, sofa, dining } = B.fitout;
    const table = diningTableRectMm(dining);
    const seats = dining.chairs.map((chair) => diningChairSeatRectMm(dining, chair));
    const tables = B.coffeeTables.map(coffeeTableRectMm);
    const pieces: [string, RectMm][] = [
      ["tv", tvWall.rectMm],
      ["sofa", sofa.mainRectMm],
      ["chaise", sofa.chaiseRectMm],
      ["table", table],
      ...seats.map((seat, i) => [`seat-${i}`, seat] as [string, RectMm]),
      ...tables.map((rect, i) => [`coffee-${i}`, rect] as [string, RectMm]),
      ["stove", B.stove.footprintMm],
      ["kitchen-back", KITCHEN_RUN.rectMm],
      ["peninsula", KITCHEN_RUN.peninsulaRectMm],
      ["east-return", KITCHEN_RUN.eastReturnRectMm],
    ];
    for (const [name, rect] of pieces) {
      if (name.startsWith("kitchen") || name === "peninsula" || name === "east-return") continue;
      expect(inside(rect, usable), name).toBe(true);
    }
    // The L modules share a corner, chairs tuck under the table and the two
    // ovals nest at different heights (as in variant A), so their plan boxes may touch.
    const allowedOverlaps = new Set(["sofa/chaise", "chaise/sofa", "coffee-0/coffee-1", ...seats.map((_, i) => `table/seat-${i}`)]);
    for (const [nameA, a] of pieces) {
      for (const [nameB, b] of pieces) {
        if (nameA === nameB || allowedOverlaps.has(`${nameA}/${nameB}`) || allowedOverlaps.has(`${nameB}/${nameA}`)) continue;
        expect(overlaps(a, b), `${nameA} vs ${nameB}`).toBe(false);
      }
    }
    // Coffee tables stay on the rug and the rug stays clear of the TV wall and the dining zone.
    for (const rect of tables) expect(inside(rect, B.rugRectMm)).toBe(true);
    expect(overlaps(B.rugRectMm, tvWall.rectMm)).toBe(false);
    expect(overlaps(B.rugRectMm, table)).toBe(false);
    expect(inside(B.coffeeTableGuardRectMm, B.rugRectMm)).toBe(true);
    for (const rect of tables) expect(inside(rect, B.coffeeTableGuardRectMm)).toBe(true);
  });

  it("gives variant B sensible clearances, sight lines and a fixed kitchen", () => {
    const B = LIVING_LAYOUTS.B;
    const { tvWall, sofa, dining } = B.fitout;
    const table = diningTableRectMm(dining);
    const glazing = porch.glazing;
    const eastWindow = HOUSE.facades.east.openings.find((o) => o.id === "EAST-04")!;
    const terraceDoor = HOUSE.facades.wingWest.opening;

    // TV wall on the solid gable: 100 mm reveal to the fixed pane, flush with the east wall, facing the sofa.
    expect(tvWall.facing).toBe("SOUTH");
    expect(tvWall.rectMm.y1).toBe(gableInnerFaceYmm);
    expect(tvWall.rectMm.x0 - (glazing.startXmm + glazing.widthMm)).toBe(100);
    expect(tvWall.rectMm.x1).toBe(livingMain.x1);
    expect(tvWall.rectMm.y1 - tvWall.rectMm.y0).toBe(LIVING_DINING_FITOUT.tvWall.rectMm.x1 - LIVING_DINING_FITOUT.tvWall.rectMm.x0);
    const [bay0, bay1] = tvWall.centralBayMm;
    expect(bay0).toBeGreaterThan(tvWall.rectMm.x0);
    expect(bay1).toBeLessThan(tvWall.rectMm.x1);
    expect(bay1 - bay0).toBeGreaterThan(tvWall.tv.widthMm);
    // Screen centred on the sofa axis; viewing distance from the sofa front 2.5–2.7 m
    // (≈ 3.2 m to the eyes, a 37° angle on the 98″ screen) after the sofa moved with the peninsula.
    expect(Math.abs((bay0 + bay1) / 2 - (sofa.mainRectMm.x0 + sofa.mainRectMm.x1) / 2)).toBeLessThanOrEqual(5);
    expect(tvWall.rectMm.y0 - sofa.mainRectMm.y1).toBeGreaterThanOrEqual(2500);
    expect(tvWall.rectMm.y0 - sofa.mainRectMm.y1).toBeLessThanOrEqual(2700);
    const eyeDistanceMm = tvWall.rectMm.y0 - sofa.mainRectMm.y1 + 650;
    const viewingAngleDeg = (2 * Math.atan(tvWall.tv.widthMm / 2 / eyeDistanceMm) * 180) / Math.PI;
    expect(viewingAngleDeg).toBeGreaterThanOrEqual(30);
    expect(viewingAngleDeg).toBeLessThanOrEqual(40);

    // Sofa: same module sizes as A, main module facing north, chaise along the east wall.
    expect(sofa.facing).toBe("NORTH");
    expect(sofa.mainRectMm.x1 - sofa.mainRectMm.x0).toBe(LIVING_DINING_FITOUT.sofa.mainRectMm.y1 - LIVING_DINING_FITOUT.sofa.mainRectMm.y0);
    expect(sofa.mainRectMm.y1 - sofa.mainRectMm.y0).toBe(LIVING_DINING_FITOUT.sofa.mainRectMm.x1 - LIVING_DINING_FITOUT.sofa.mainRectMm.x0);
    expect(sofa.chaiseRectMm.y1 - sofa.chaiseRectMm.y0).toBe(LIVING_DINING_FITOUT.sofa.chaiseRectMm.x1 - LIVING_DINING_FITOUT.sofa.chaiseRectMm.x0);
    expect(sofa.chaiseRectMm.x1).toBe(sofa.mainRectMm.x1);
    expect(sofa.chaiseRectMm.y0).toBe(sofa.mainRectMm.y0);
    expect(livingMain.x1 - sofa.chaiseRectMm.x1).toBe(200);
    // Walkway of a full metre between the peninsula worktop edge (flush with the terrace-door reveal) and the sofa back.
    const worktopFrontYmm = KITCHEN_RUN.peninsulaRectMm.y1 + KITCHEN_RUN.peninsulaOverhangMm;
    expect(worktopFrontYmm).toBe(PENINSULA_WORKTOP_EDGE_YMM);
    expect(sofa.mainRectMm.y0 - worktopFrontYmm).toBe(1000);
    expect(sofa.mainRectMm.y0 - KITCHEN_RUN.peninsulaRectMm.y1).toBeGreaterThanOrEqual(1200);
    // The chaise does not block the east window and stays clear of the tech-room door approach.
    expect(sofa.chaiseRectMm.y0).toBeGreaterThan(eastWindow.startYmm + eastWindow.widthMm);
    // Sofa, rug and coffee tables stay south of the TV wall with room to walk along it.
    expect(tvWall.rectMm.y0 - B.rugRectMm.y1).toBeGreaterThanOrEqual(250);
    for (const rect of B.coffeeTables.map(coffeeTableRectMm)) {
      expect(tvWall.rectMm.y0 - 120 - rect.y1).toBeGreaterThanOrEqual(250);
      expect(rect.y0 - sofa.mainRectMm.y1).toBeGreaterThanOrEqual(400);
    }

    // Dining along the west wall: three chairs per long side, pull-back room by the wall and
    // a metre-wide route between the table and the sofa (still 900+ behind a seated diner).
    expect(dining.axis).toBe("Y");
    expect(table.x1 - table.x0).toBe(900);
    expect(table.y1 - table.y0).toBe(2000);
    expect(table.x0 - livingMain.x0).toBeGreaterThanOrEqual(950);
    expect(sofa.mainRectMm.x0 - table.x1).toBeGreaterThanOrEqual(1000);
    expect(sofa.mainRectMm.x0 - (table.x1 + dining.chairSeatDepthMm - 330)).toBeGreaterThanOrEqual(900);
    expect(table.y0).toBeGreaterThan(terraceDoor.startYmm + terraceDoor.widthMm);
    expect(table.y0 - worktopFrontYmm).toBeGreaterThanOrEqual(1500);
    expect(table.y1).toBeLessThan(B.stove.footprintMm.y0);
    expect(new Set(dining.chairs.map((chair) => chair.facing))).toEqual(new Set(["EAST", "WEST"]));
    expect(dining.chairs.filter((chair) => chair.facing === "EAST")).toHaveLength(3);
    for (const chair of dining.chairs) {
      const seat = diningChairSeatRectMm(dining, chair);
      const tuck = Math.min(seat.x1, table.x1) - Math.max(seat.x0, table.x0);
      expect(tuck, chair.id).toBe(330);
      expect(seat.y0, chair.id).toBeGreaterThan(table.y0);
      expect(seat.y1, chair.id).toBeLessThan(table.y1);
    }
    for (const facing of ["EAST", "WEST"] as const) {
      const ys = dining.chairs.filter((chair) => chair.facing === facing).map((chair) => chair.centerMm.y).sort((a, b) => a - b);
      expect(ys[1] - ys[0]).toBe(650);
      expect(ys[2] - ys[1]).toBe(650);
      expect(ys[1]).toBe(dining.tableCenterMm.y);
    }

    // Stove in the north-west corner, turned to the room, clear of the fixed pane and the gable pier.
    expect(B.stove.facing).toBe("SOUTH_EAST");
    expect(B.stove.facingAngleDeg).toBe(-45);
    expect(B.stove.footprintMm.x0 - livingMain.x0).toBe(FIREPLACE_STOVE.footprintMm.x0 - livingMain.x0);
    expect(gableInnerFaceYmm - B.stove.footprintMm.y1).toBe(160);
    expect(B.stove.footprintMm.x1).toBeLessThan(glazing.startXmm + 100);
    expect(B.stove.flue.id).not.toBe(FIREPLACE_STOVE.flue.id);
    expect(B.stove.flue.terminationElevationMm).toBe(FIREPLACE_STOVE.flue.terminationElevationMm);

    // Kitchen is shared; the notes say so and quote the key clearances.
    expect(B.notes.join(" ")).toMatch(/priechod 1 000 mm/);
    expect(B.notes.join(" ")).toMatch(/957 mm/);
    expect(B.notes.join(" ")).toMatch(/1 041 mm/);
    expect(B.notes.join(" ")).toMatch(/pre šesť osôb/);
    expect(B.notes.join(" ")).toMatch(/rovnaké/);
    expect(B.notes.join(" ")).toMatch(/346 mm/);
    expect(LIVING_LAYOUTS.A.notes.join(" ")).toMatch(/pre šesť osôb/);
    expect(LIVING_LAYOUTS.A.notes.join(" ")).toMatch(/650 mm/);
    expect(LIVING_LAYOUTS.A.notes.length).toBeGreaterThanOrEqual(3);
  });
});
