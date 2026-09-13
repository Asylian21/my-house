import {
  CADASTRAL_PARCELS,
  HOUSE,
  SITE_AXIS,
  SUBJECT_PARCEL_SJTSK_ORIGIN_MM,
  sjtskToLocalMm as c3ToLocalMm,
  type Point2Mm,
} from './twin-site';

const parcel = CADASTRAL_PARCELS.find(p => p.isSubject)!.sjtskRingMm.map(c3ToLocalMm);
const eastEdge = parcel.slice(0, -1).map((a, i) => ({ a, b: parcel[i + 1] }))
  .filter(({ a, b }) => Math.abs(b.y - a.y) > 10_000)
  .sort((a, b) => b.a.x + b.b.x - a.a.x - a.b.x)[0];
const edgeDx = eastEdge.b.x - eastEdge.a.x;
const edgeDy = eastEdge.b.y - eastEdge.a.y;
const edgeLength = Math.hypot(edgeDx, edgeDy);
const normalX = Math.abs(edgeDy) / edgeLength;
const normalY = -edgeDx * Math.sign(edgeDy) / edgeLength;
const originalEastSetbackMm = Math.min(...HOUSE.footprintMm.map(p =>
  (eastEdge.a.x - p.x) * normalX + (eastEdge.a.y - p.y) * normalY));

/** Client placement correction, 13 Sep 2026. Translate, never resize the house. */
export const ACTIVE_HOUSE_PLACEMENT = Object.freeze({
  id: 'CLIENT-PLACEMENT-20260913',
  status: 'CLIENT_REQUESTED_SETBACK' as const,
  reference: 'C3',
  streetSetbackMm: 3000,
  eastSetbackMm: 3000,
  originalEastSetbackMm,
  translationMm: Object.freeze({ x: (originalEastSetbackMm - 3000) / normalX, y: 0 }),
});

/** Keep architectural coordinates stable; express fixed site features in the moved house frame. */
export function siteToHouseFrameMm(point: Point2Mm): Point2Mm {
  return { x: point.x - ACTIVE_HOUSE_PLACEMENT.translationMm.x, y: point.y };
}

export function sjtskToLocalMm(point: Point2Mm): Point2Mm {
  // Apply the fractional placement AFTER the existing cadastral mm rounding.
  return siteToHouseFrameMm(c3ToLocalMm(point));
}

/** National-grid origin for the active house frame; the original legal datum stays intact. */
export const ACTIVE_LOCAL_ORIGIN_SJTSK_MM = Object.freeze({
  x: SUBJECT_PARCEL_SJTSK_ORIGIN_MM.x + ACTIVE_HOUSE_PLACEMENT.translationMm.x * SITE_AXIS.ux,
  y: SUBJECT_PARCEL_SJTSK_ORIGIN_MM.y + ACTIVE_HOUSE_PLACEMENT.translationMm.x * SITE_AXIS.uy,
});
