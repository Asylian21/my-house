import { describe, expect, it } from "vitest";
import { DECK_BOARD_LAYOUT, planDeckBoards } from "../lib/deck-boards";
import { POOL_SURROUND_DECK, POOL_TECHNOLOGY_SHAFT, TERRACE_ZONES_D1, type TerraceZoneRectMm } from "../lib/twin-site";

function overlap(a: TerraceZoneRectMm, b: TerraceZoneRectMm) {
  return Math.max(0, Math.min(a.x1, b.x1) - Math.max(a.x0, b.x0))
    * Math.max(0, Math.min(a.y1, b.y1) - Math.max(a.y0, b.y0));
}

describe("continuous terrace board layout", () => {
  it("does not turn footprint decomposition edges into construction gaps", () => {
    const whole = { id: "whole", label: "", rectsMm: [{ x0: 0, y0: 0, x1: 6000, y1: 2000 }] };
    const split = { ...whole, rectsMm: [
      { x0: 0, y0: 0, x1: 2100, y1: 500 }, { x0: 2100, y0: 0, x1: 6000, y1: 500 },
      { x0: 0, y0: 500, x1: 6000, y1: 2000 },
    ] };
    expect(planDeckBoards(split)).toEqual(planDeckBoards(whole));
    expect(planDeckBoards({ ...split, rectsMm: [...split.rectsMm].reverse() })).toEqual(planDeckBoards(whole));
    expect(planDeckBoards({ ...whole, rectsMm: [...whole.rectsMm, ...split.rectsMm] })).toEqual(planDeckBoards(whole));
  });

  it("closes the measured 49 and 37 mm accidental slots beside the hatch", () => {
    const boards = planDeckBoards(POOL_SURROUND_DECK);
    const openAt = (from: number, to: number) => Array.from({ length: to - from }, (_, i) => from + i + .5)
      .filter((y) => !boards.some((b) => b.x0 < 13000 && b.x1 > 13000 && b.y0 <= y && b.y1 >= y));
    expect(openAt(16859, 16908)).toEqual([]);
    // The only remaining opening is the regular 8 mm row joint.
    expect(openAt(17971, 18008)).toEqual(Array.from({ length: 8 }, (_, i) => 17996.5 + i));
  });

  it.each([...TERRACE_ZONES_D1, POOL_SURROUND_DECK])("preserves $id footprint without overlapping boards", (zone) => {
    const boards = planDeckBoards(zone);
    expect(boards.length).toBeGreaterThan(0);
    for (const [i, board] of boards.entries()) {
      const area = (board.x1 - board.x0) * (board.y1 - board.y0);
      expect(area).toBeGreaterThan(0);
      expect(board.y1 - board.y0).toBeLessThanOrEqual(145);
      expect(board.y1 - board.y0).toBeGreaterThanOrEqual(40);
      expect(zone.rectsMm.reduce((sum, rect) => sum + overlap(board, rect), 0)).toBeCloseTo(area, 5);
      for (const other of boards.slice(i + 1)) expect(overlap(board, other)).toBe(0);
    }
  });

  it("retains the exact hatch opening and source deck elevation", () => {
    const hatch = POOL_TECHNOLOGY_SHAFT.hatch.footprintMm;
    expect((hatch.x1 - hatch.x0) * (hatch.y1 - hatch.y0)).toBe(900 * 1100);
    for (const b of planDeckBoards(POOL_SURROUND_DECK)) expect(overlap(b, hatch)).toBe(0);
    expect(DECK_BOARD_LAYOUT).toMatchObject({ widthMm: 145, jointMm: 8, thicknessMm: 28, topMm: 20 });
  });
});
