import type { DeckZone, TerraceZoneRectMm } from "./twin-site";

/** Surface construction derived from the shared terrace footprint, in mm. */
export const DECK_BOARD_LAYOUT = Object.freeze({
  revision: "continuous-zone-grid-1",
  widthMm: 145,
  jointMm: 8,
  thicknessMm: 28,
  topMm: 20,
  minimumCutWidthMm: 40,
});

export interface DeckBoardMm extends TerraceZoneRectMm {
  readonly row: number;
  readonly segment: number;
}

function unionIntervals(intervals: readonly (readonly [number, number])[]) {
  const result: [number, number][] = [];
  for (const [start, end] of [...intervals].sort((a, b) => a[0] - b[0])) {
    const prior = result.at(-1);
    if (prior && start <= prior[1]) prior[1] = Math.max(prior[1], end);
    else result.push([start, end]);
  }
  return result;
}

/**
 * Use one row lattice for the whole zone. Rectangles describe its footprint,
 * not separate starts of the decking: their shared edges must not open gaps.
 * Sweep X strips so a row crossing a notch remains exactly inside the union.
 */
export function planDeckBoards(zone: DeckZone): DeckBoardMm[] {
  if (!zone.rectsMm.length) return [];
  const rects = zone.rectsMm;
  for (const r of rects) {
    if (![r.x0, r.y0, r.x1, r.y1].every(Number.isFinite) || r.x0 >= r.x1 || r.y0 >= r.y1) {
      throw new Error(`Invalid deck footprint: ${zone.id}`);
    }
  }
  const xs = [...new Set(rects.flatMap((r) => [r.x0, r.x1]))].sort((a, b) => a - b);
  const strips = xs.slice(0, -1).map((x0, index) => {
    const x1 = xs[index + 1];
    return { x0, x1, intervals: unionIntervals(rects
      .filter((r) => r.x0 <= x0 && r.x1 >= x1)
      .map((r) => [r.y0, r.y1] as const)) };
  });
  const { widthMm, jointMm, minimumCutWidthMm } = DECK_BOARD_LAYOUT;
  const yOrigin = Math.min(...rects.map((r) => r.y0)) + jointMm;
  const yLimit = Math.max(...rects.map((r) => r.y1));
  // Shift the common lattice only when an edge would leave a fragile rip.
  // This is an authored construction rule, not a measurement of installed boards.
  // Keep the leading perimeter joint and choose the smallest adequate shift.
  let shift: number | undefined;
  for (let candidate = 0; candidate <= widthMm - minimumCutWidthMm; candidate++) {
    let minimum = Infinity;
    for (let y = yOrigin - candidate; y < yLimit; y += widthMm + jointMm) {
      for (const strip of strips) for (const [start, end] of strip.intervals) {
        const cut = Math.min(y + widthMm, end) - Math.max(y, start, yOrigin);
        if (cut > 0) minimum = Math.min(minimum, cut);
      }
    }
    if (minimum >= minimumCutWidthMm && minimum < Infinity) { shift = candidate; break; }
  }
  if (shift === undefined) throw new Error(`Deck footprint needs a reviewed edge-board layout: ${zone.id}`);
  const boards: DeckBoardMm[] = [];
  for (let y = yOrigin - shift, row = 0; y < yLimit; y += widthMm + jointMm, row++) {
    const spans = new Map<string, { y0: number; y1: number; xs: [number, number][] }>();
    for (const strip of strips) {
      for (const [start, end] of strip.intervals) {
        const y0 = Math.max(y, start, yOrigin), y1 = Math.min(y + widthMm, end);
        if (y1 <= y0) continue;
        const key = `${y0}:${y1}`;
        const span = spans.get(key) ?? { y0, y1, xs: [] };
        span.xs.push([strip.x0, strip.x1]);
        spans.set(key, span);
      }
    }
    let boardIndex = 0;
    for (const span of [...spans.values()].sort((a, b) => a.y0 - b.y0 || a.y1 - b.y1)) {
      for (const [x0, x1] of unionIntervals(span.xs)) {
        const count = Math.max(1, Math.ceil((x1 - x0) / 3_600));
        const boundaries = [x0];
        for (let segment = 1; segment < count; segment++) {
          const stagger = (((row + segment) % 3) - 1) * 170;
          boundaries.push(x0 + ((x1 - x0) * segment) / count + stagger);
        }
        boundaries.push(x1);
        for (let segment = 0; segment < count; segment++) {
          boards.push({
            x0: boundaries[segment] + (segment > 0 ? jointMm / 2 : 0),
            x1: boundaries[segment + 1] - (segment < count - 1 ? jointMm / 2 : 0),
            y0: span.y0, y1: span.y1, row, segment: boardIndex++,
          });
        }
      }
    }
  }
  return boards;
}
