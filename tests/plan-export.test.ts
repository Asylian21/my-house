import { describe, expect, it } from "vitest";

import { CODED_ITEMS, CODED_OPENINGS, DOOR_CHAINS, DOOR_TEXTS, FACADES, FOOTPRINT, GRID_X, GRID_Y, MATERIAL_LEGEND, PLAN_EXTENT, SECTION_CHAINS, SHELL_WALL_MESHES, SITE_BOUNDARY, TERRACES, TERRACE_AREA_M2, clearRects, codedItems, facadeChains, gridCell, innerDims, roomLabelPos } from "../lib/plan-export";
import { PLAN_ROOMS, exteriorWallLayer } from "../lib/plan-documentation";
import { INTERIOR_DOORS, INTERIOR_WALLS } from "../lib/twin-interior";

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
    expect(MATERIAL_LEGEND.map((e) => e.cls)).toEqual(["exterior", "insulation", "bearing", "partition", "board"]);
    expect(MATERIAL_LEGEND[0].codes).toBe("SO30, SO50");
    expect(MATERIAL_LEGEND[1].codes).toBe("TI20");
    for (const e of MATERIAL_LEGEND) expect(e.text).toMatch(/hr\. \d/);
  });
});

describe("exterior walls are drawn in their real build-up (300 masonry + 200 insulation)", () => {
  const cut = SHELL_WALL_MESHES.filter((m) => m.z0 <= 0);
  const layers = cut.filter((m) => / · úsek \d+ · /.test(m.name));
  const across = (m: (typeof cut)[number]) => Math.round(Math.min(m.rect.x1 - m.rect.x0, m.rect.y1 - m.rect.y0));

  it("every insulated facade segment has a 200 mm insulation layer on the outer face and masonry behind it", () => {
    const insulation = layers.filter((m) => exteriorWallLayer(m) === "insulation");
    expect(insulation.length).toBeGreaterThan(20);
    for (const m of insulation) expect(across(m), m.name).toBe(200);
    for (const m of layers.filter((l) => exteriorWallLayer(l) === "masonry")) expect(across(m), m.name).toBeGreaterThanOrEqual(300);
    // Outer faces of the insulation are the documented footprint faces.
    expect(insulation.filter((m) => m.rect.y0 === 3000).length).toBeGreaterThan(5);
    expect(insulation.filter((m) => m.rect.x1 === 28040).length).toBeGreaterThan(3);
    expect(insulation.filter((m) => m.rect.y1 === 11200).length).toBeGreaterThan(2);
    expect(insulation.filter((m) => m.rect.x0 === 6440).length).toBeGreaterThan(2);
    expect(insulation.filter((m) => m.rect.x0 === 21040).length).toBeGreaterThan(1);
  });

  it("free-standing terrace piers stay solid 500 mm masonry without insulation", () => {
    const solid = layers.filter((m) => exteriorWallLayer(m) === "solid").map((m) => m.rect);
    expect(solid).toEqual(expect.arrayContaining([
      { x0: 21040, y0: 21535, x1: 21540, y1: 22035 }, // porch corner pillar
      { x0: 27510, y0: 19535, x1: 28040, y1: 22035 }, // east wall end along the porch
      { x0: 6440, y0: 10670, x1: 8440, y1: 11200 }, // long garden arm of the L support
      { x0: 6440, y0: 10200, x1: 6970, y1: 11200 }, // short west arm of the L support
    ]));
    // The erased rear return in the client sketch is now a clear side passage.
    expect(cut.some(({rect:r}) => r.x0 < 6940 && r.x1 > 6440 && r.y0 < 10200 && r.y1 > 9247)).toBe(false);
    const insulated = layers.filter((m) => exteriorWallLayer(m) === "insulation").map((m) => m.rect);
    for (const pier of solid) expect(insulated.some((r) => r.x0 < pier.x1 && r.x1 > pier.x0 && r.y0 < pier.y1 && r.y1 > pier.y0), JSON.stringify(pier)).toBe(false);
  });

  it("the insulation wraps the outer corners and the masonry stops behind it", () => {
    const rect = (name: RegExp) => cut.find((m) => name.test(m.name))!.rect;
    expect(rect(/^Južná fasáda · úsek 1 · murivo$/).x0).toBe(6640);
    expect(rect(/^Južná fasáda · úsek 1 · izolácia$/).x0).toBe(6440);
    expect(rect(/^Východná fasáda · úsek 1 · murivo$/).y0).toBe(3200);
    expect(rect(/^Garážový štít · úsek 1 · murivo$/).y0).toBe(3200);
    expect(rect(/^Záhradná fasáda · úsek 3 · murivo$/).x0).toBe(10842);
    expect(rect(/^Záhradná fasáda · úsek 3 · izolácia$/).x0).toBe(10640);
    expect(rect(/^Západná stena krídla · úsek 3 · murivo$/).y1).toBe(19335);
    expect(rect(/^Krytá terasa · murovaný pilier pri rohu · izolácia$/)).toEqual({ x0: 21040, y0: 19335, x1: 22040, y1: 19535 });
    expect(rect(/^Krytá terasa · plná zadná stena · izolácia$/)).toEqual({ x0: 24040, y0: 19335, x1: 27840, y1: 19535 });
  });

  it("the loggia's east junction is closed: masonry corner up to the spine wall and a flush insulation cheek", () => {
    const corner = cut.find((m) => m.name === "Lodžia · zadná stena · roh pri stene spálne")!;
    const cheek = cut.find((m) => m.name === "Lodžia · východná bočná stena · izolácia")!;
    const spine = INTERIOR_WALLS.find((w) => w.id === "C-GARAGE-SPINE-N")!.rectMm;
    expect(corner.rect).toEqual({ x0: 10640, y0: 8747, x1: spine.x0, y1: 9247 });
    expect(cheek.rect).toEqual({ x0: 10640, y0: 9247, x1: spine.x0, y1: 11200 });
    expect(cut.some((m) => m.name === "Lodžia · východná bočná stena")).toBe(false);
  });

  it("facade dimension rows treat both layers of a segment as one wall and keep the piers as walls", () => {
    for (const { def, segments } of FACADES) {
      for (let i = 1; i < segments.length; i++) expect(segments[i].a, `${def.id} segment ${i}`).toBeGreaterThanOrEqual(segments[i - 1].b - 1);
    }
    const east = FACADES.find((f) => f.def.id === "E")!.segments;
    expect(east.filter((s) => s.a >= 19535).map((s) => s.kind)).toEqual(["wall"]);
    const west = FACADES.find((f) => f.def.id === "W")!.segments;
    expect(west.find((s) => s.a === 9247)).toMatchObject({ b: 10200, kind: "open" });
    expect(west.find((s) => s.a === 10200)).toMatchObject({ b: 11200, kind: "wall" });
  });
});
