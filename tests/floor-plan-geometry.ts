import { rect } from '../lib/floor-plan-concept';
import type { InteriorDoor, RectMm } from '../lib/twin-interior';

export const intersects = (a: RectMm, b: RectMm) => a.x0 < b.x1 && a.x1 > b.x0 && a.y0 < b.y1 && a.y1 > b.y0;
export const inside = (r: RectMm, x: number, y: number) => x >= r.x0 && x <= r.x1 && y >= r.y0 && y <= r.y1;
export const contains = (outer: RectMm, inner: RectMm) => inside(outer, inner.x0, inner.y0) && inside(outer, inner.x1, inner.y1);
export const check = (condition: boolean, message: string) => { if (!condition) throw new Error(message); };
export const opening = (d: InteriorDoor) => d.axis === 'X'
  ? rect(d.startMm, d.wallSpanMm[0], d.startMm + d.widthMm, d.wallSpanMm[1])
  : rect(d.wallSpanMm[0], d.startMm, d.wallSpanMm[1], d.startMm + d.widthMm);

export function openLeaf(d: InteriorDoor & { leafPlaneMm?: number }): RectMm {
  const exactPivot = d.hingeOffsetMm !== undefined;
  const plane = d.leafPlaneMm ?? (exactPivot ? (d.swing < 0 ? d.wallSpanMm[0] : d.wallSpanMm[1]) + d.swing * d.hingeOffsetMm! : (d.wallSpanMm[0] + d.wallSpanMm[1]) / 2);
  const inset = exactPivot && d.widthMm !== d.leafWidthMm ? 60 : 0;
  const hinge = d.startMm + (d.hinge === 1 ? d.widthMm - inset : inset);
  return d.axis === 'X'
    ? rect(hinge - 10, Math.min(plane, plane + d.swing * d.leafWidthMm), hinge + 10, Math.max(plane, plane + d.swing * d.leafWidthMm))
    : rect(Math.min(plane, plane + d.swing * d.leafWidthMm), hinge - 10, Math.max(plane, plane + d.swing * d.leafWidthMm), hinge + 10);
}

/** Exact quarter-disc test for a hinged leaf's complete swing, not only its open position. */
export function swingHits(d: InteriorDoor & { leafPlaneMm?: number }, obstacle: RectMm): boolean {
  const exactPivot = d.hingeOffsetMm !== undefined;
  const plane = d.leafPlaneMm ?? (exactPivot ? (d.swing < 0 ? d.wallSpanMm[0] : d.wallSpanMm[1]) + d.swing * d.hingeOffsetMm! : (d.wallSpanMm[0] + d.wallSpanMm[1]) / 2);
  const inset = exactPivot && d.widthMm !== d.leafWidthMm ? 60 : 0;
  const hinge = d.startMm + (d.hinge === 1 ? d.widthMm - inset : inset);
  const direction = d.hinge === -1 ? 1 : -1;
  const along = d.axis === 'X'
    ? [(obstacle.x0 - hinge) * direction, (obstacle.x1 - hinge) * direction]
    : [(obstacle.y0 - hinge) * direction, (obstacle.y1 - hinge) * direction];
  const across = d.axis === 'X'
    ? [(obstacle.y0 - plane) * d.swing, (obstacle.y1 - plane) * d.swing]
    : [(obstacle.x0 - plane) * d.swing, (obstacle.x1 - plane) * d.swing];
  if (Math.max(...along) <= 0 || Math.max(...across) <= 0) return false;
  return Math.hypot(Math.max(0, Math.min(...along)), Math.max(0, Math.min(...across))) < d.leafWidthMm;
}

type Segment = readonly [number, number, number, number];

/** Exterior edges of a union of rectangles, including the jambs of open doors. */
export function floorBoundary(floors: RectMm[]): Segment[] {
  const xs = [...new Set(floors.flatMap(r => [r.x0, r.x1]))].sort((a, b) => a - b);
  const ys = [...new Set(floors.flatMap(r => [r.y0, r.y1]))].sort((a, b) => a - b);
  const covered = (x: number, y: number) => floors.some(r => inside(r, x, y));
  const edges: Segment[] = [];
  for (const x of xs) for (let i = 1; i < ys.length; i++) {
    const y = (ys[i - 1] + ys[i]) / 2;
    if (covered(x - .1, y) !== covered(x + .1, y)) edges.push([x, ys[i - 1], x, ys[i]]);
  }
  for (const y of ys) for (let i = 1; i < xs.length; i++) {
    const x = (xs[i - 1] + xs[i]) / 2;
    if (covered(x, y - .1) !== covered(x, y + .1)) edges.push([xs[i - 1], y, xs[i], y]);
  }
  return edges;
}

/** A true 440 mm disc: exact distances to union boundaries and rectangular furniture. */
export function walkingPath(floors: RectMm[], obstacles: RectMm[], start: [number, number], goal: [number, number]): boolean {
  const edges = floorBoundary(floors), radiusSquared = 220 ** 2;
  const distanceSquared = (x: number, y: number, x0: number, y0: number, x1: number, y1: number) => {
    const nx = Math.max(x0, Math.min(x1, x)), ny = Math.max(y0, Math.min(y1, y));
    return (x - nx) ** 2 + (y - ny) ** 2;
  };
  const fits = (x: number, y: number) => floors.some(r => inside(r, x, y))
    && edges.every(([x0, y0, x1, y1]) => distanceSquared(x, y, x0, y0, x1, y1) >= radiusSquared)
    && obstacles.every(r => distanceSquared(x, y, r.x0, r.y0, r.x1, r.y1) >= radiusSquared);
  if (!fits(...start) || !fits(...goal)) return false;
  const queue: [number, number][] = [start], seen = new Set([start.join(':')]);
  for (let i = 0; i < queue.length; i++) {
    const [x, y] = queue[i];
    if (x === goal[0] && y === goal[1]) return true;
    for (const [dx, dy] of [[50, 0], [-50, 0], [0, 50], [0, -50]]) {
      const nx = x + dx, ny = y + dy, key = `${nx}:${ny}`;
      if (seen.has(key)) continue;
      seen.add(key);
      // Midpoint checks also guard a 50 mm step across a narrow obstruction.
      if (fits(nx, ny) && fits(x + dx / 2, y + dy / 2)) queue.push([nx, ny]);
    }
  }
  return false;
}
