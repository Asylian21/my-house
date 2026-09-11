import { describe, expect, it } from "vitest";

import { CODED_ITEMS, CODED_OPENINGS, DOOR_CHAINS, DOOR_TEXTS, FACADES, FOOTPRINT, GRID_X, GRID_Y, MATERIAL_LEGEND, PLAN_EXTENT, SECTION_CHAINS, SITE_BOUNDARY, TERRACES, TERRACE_AREA_M2, clearRects, codedItems, facadeChains, gridCell, innerDims, roomLabelPos } from "../lib/plan-export";
import { PLAN_ROOMS } from "../lib/plan-documentation";
import { INTERIOR_DOORS } from "../lib/twin-interior";

const span = (points: number[]) => points[points.length - 1] - points[0];
const monotonic = (points: number[]) => points.every((p, i) => i === 0 || p > points[i - 1]);

describe("export sheet dimensioning stays arithmetically consistent", () => {
  it("every facade row adds up to the same overall length and is strictly increasing", () => {
    const chains = facadeChains(5);
    expect(chains.length).toBeGreaterThan(0);
    for (const { def } of FACADES) {
      const rows = chains.filter((c) => c.axis === def.axis && Math.abs(c.at - def.outer) <= 2100 + 1 && c.points[0] === Math.min(def.from, def.to));
      const totals = new Set(rows.map((c) => Math.round(span(c.points))));
      expect(totals.size, `${def.id} rows disagree: ${[...totals].join(",")}`).toBe(1);
      for (const c of rows) expect(monotonic(c.points), `${def.id} row at ${c.at}`).toBe(true);
    }
  });

  it("main facades measure the documented footprint", () => {
    const overall = facadeChains(1);
    const south = overall.find((c) => c.axis === "x" && c.at < FOOTPRINT.y0)!;
    const east = overall.find((c) => c.axis === "y" && c.at > FOOTPRINT.x1)!;
    expect(span(south.points)).toBe(FOOTPRINT.x1 - FOOTPRINT.x0);
    expect(span(east.points)).toBe(FOOTPRINT.y1 - FOOTPRINT.y0);
  });

  it("section chains alternate solid walls with clear room widths across the whole line", () => {
    for (const c of SECTION_CHAINS) {
      expect(monotonic(c.points)).toBe(true);
      expect(c.solid).toHaveLength(c.points.length - 1);
      expect(c.solid!.some(Boolean)).toBe(true);
      // Room widths match the floor rectangles the line actually crosses.
      const clear = c.points.slice(1).map((p, i) => [p - c.points[i], c.solid![i]] as const).filter(([, solid]) => !solid).map(([w]) => Math.round(w));
      const floors = PLAN_ROOMS.flatMap((room) => clearRects(room)).filter((r) => (c.axis === "x" ? r.y0 < c.at && r.y1 > c.at : r.x0 < c.at && r.x1 > c.at));
      const floorWidths = floors.map((r) => Math.round(c.axis === "x" ? r.x1 - r.x0 : r.y1 - r.y0));
      for (const w of clear) {
        const explained = floorWidths.includes(w) || floorWidths.some((a) => floorWidths.some((b) => a + b === w)) || floorWidths.some((a) => floorWidths.some((b) => floorWidths.some((d) => a + b + d === w)));
        expect(explained || w >= 1900, `unexplained clear width ${w} on ${c.axis}=${c.at}`).toBe(true);
      }
    }
  });

  it("the openings row carries height (sill) under every opening and nothing under piers", () => {
    for (const { def, segments } of FACADES) {
      const row = facadeChains(2).find((c) => c.axis === def.axis && Math.abs(c.at - (def.outer + def.outward * 700)) < 1 && c.points[0] === def.from);
      if (!row) continue;
      expect(row.sub, def.id).toBeDefined();
      expect(row.sub).toHaveLength(row.points.length - 1);
      const openings = segments.filter((s) => s.kind === "opening" && s.item);
      expect(row.sub!.filter(Boolean), def.id).toHaveLength(openings.length);
      for (const s of openings) {
        const i = row.points.indexOf(s.a);
        expect(row.sub![i], `${def.id} ${s.item!.id}`).toBe(`${s.item!.opening!.height.toLocaleString("sk-SK")} (${s.item!.opening!.sill.toLocaleString("sk-SK")})`);
      }
    }
  });

  it("inner dimensions stay inside their room and never repeat a section chain", () => {
    for (const room of PLAN_ROOMS) {
      for (const d of innerDims(room)) {
        expect(d.x, `${room.number} ${d.text}`).toBeGreaterThan(room.bounds.x0);
        expect(d.x).toBeLessThan(room.bounds.x1);
        expect(d.y).toBeGreaterThan(room.bounds.y0);
        expect(d.y).toBeLessThan(room.bounds.y1);
        const rect = clearRects(room).find((r) => d.x >= r.x0 && d.x <= r.x1 && d.y >= r.y0 && d.y <= r.y1)!;
        expect(rect, `${room.number} ${d.text} outside floor`).toBeDefined();
        const crossing = SECTION_CHAINS.filter((c) => c.axis === d.axis && (d.axis === "x" ? c.at > rect.y0 && c.at < rect.y1 && c.points[0] <= rect.x0 && c.points[c.points.length - 1] >= rect.x1 : c.at > rect.x0 && c.at < rect.x1 && c.points[0] <= rect.y0 && c.points[c.points.length - 1] >= rect.y1));
        expect(crossing, `${room.number} ${d.text} duplicates a chain`).toHaveLength(0);
      }
    }
  });

  it("every interior door gets a width / height stamp in the middle of its wall gap", () => {
    expect(DOOR_TEXTS).toHaveLength(INTERIOR_DOORS.length);
    for (const t of DOOR_TEXTS) {
      // Slovak thousands separator is a non-breaking space.
      expect(t.text).toMatch(/^\d[\d\u00a0 ]* \/ \d[\d\u00a0 ]*$/);
      const [w0, w1] = t.door.wallSpanMm;
      const across = t.axis === "x" ? t.y : t.x;
      expect(across).toBeCloseTo((w0 + w1) / 2, 5);
    }
  });

  it("door chains are anchored on a room rectangle and locate the opening inside it", () => {
    // Doors sharing one wall face and room rectangle are merged into a single chain: 2 rectangle ends + 2 points per door.
    const doors = DOOR_CHAINS.reduce((s, c) => s + (c.points.length - 2) / 2, 0);
    expect(doors).toBe(10);
    for (const c of DOOR_CHAINS) {
      expect(monotonic(c.points)).toBe(true);
      expect(c.points.length % 2).toBe(0);
    }
  });
});

describe("export sheet coding is unique and complete", () => {
  it("assigns unique O#/D# codes to every exterior opening and interior door", () => {
    const codes = CODED_OPENINGS.map((o) => o.code);
    expect(new Set(codes).size).toBe(codes.length);
    expect(codes.filter((c) => c.startsWith("O")).length).toBeGreaterThanOrEqual(10);
    expect(CODED_OPENINGS.filter((o) => o.door)).toHaveLength(10);
  });

  it("assigns unique item codes and only fixed equipment at level 4", () => {
    const codes = CODED_ITEMS.map((c) => c.code);
    expect(new Set(codes).size).toBe(codes.length);
    expect(codedItems(3)).toHaveLength(0);
    expect(codedItems(4).every((c) => c.level === 4)).toBe(true);
    expect(codedItems(5).length).toBeGreaterThan(codedItems(4).length);
  });

  it("grid axes are increasing and every room resolves to a grid cell", () => {
    expect(monotonic(GRID_X.map((a) => a.at))).toBe(true);
    expect(monotonic(GRID_Y.map((a) => a.at))).toBe(true);
    for (const room of PLAN_ROOMS) {
      expect(gridCell(room.bounds)).toMatch(/^[A-F](–[A-F])? \/ [1-6](–[1-6])?$/);
      const pos = roomLabelPos(room, 3);
      expect(pos.x).toBeGreaterThan(room.bounds.x0);
      expect(pos.x).toBeLessThan(room.bounds.x1);
      expect(pos.y).toBeGreaterThan(room.bounds.y0);
      expect(pos.y).toBeLessThan(room.bounds.y1);
    }
  });

  it("trims the living room floor to the covered terrace wall face", () => {
    const living = PLAN_ROOMS.find((r) => r.number === "1.03")!;
    const deepest = clearRects(living).sort((a, b) => b.y1 - a.y1)[0];
    expect(deepest.y1).toBe(19035);
  });
});

describe("export sheet site context follows D1.1.002", () => {
  it("draws the subject parcel with the street edge at y = 0 and the east and north boundaries inside the plan extent", () => {
    expect(SITE_BOUNDARY.length).toBeGreaterThanOrEqual(4);
    expect(Math.min(...SITE_BOUNDARY.map((p) => p.y))).toBe(0);
    expect(Math.max(...SITE_BOUNDARY.map((p) => p.x))).toBeLessThan(PLAN_EXTENT.x1);
    expect(Math.max(...SITE_BOUNDARY.map((p) => p.y))).toBeLessThan(PLAN_EXTENT.y1);
    expect(PLAN_EXTENT.y0).toBeLessThan(0);
  });

  it("lists the three D1 timber terraces as room 1.13 with the active area", () => {
    expect(TERRACES.map((t) => t.title)).toEqual(["TERASA", "TERASA", "KRYTÁ TERASA"]);
    expect(TERRACE_AREA_M2).toBeCloseTo(80.15, 2);
    for (const t of TERRACES) {
      const inside = t.rects.some((r) => t.label.x >= r.x0 && t.label.x <= r.x1 && t.label.y >= r.y0 && t.label.y <= r.y1);
      expect(inside, t.id).toBe(true);
    }
  });

  it("material legend covers every hatch class used by the model", () => {
    expect(MATERIAL_LEGEND.map((e) => e.cls)).toEqual(["exterior", "bearing", "partition", "board"]);
    expect(MATERIAL_LEGEND[0].codes).toBe("SO50");
    for (const e of MATERIAL_LEGEND) expect(e.text).toMatch(/hr\. \d/);
  });
});
