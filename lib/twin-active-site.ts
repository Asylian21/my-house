import * as c3 from './twin-site';
import { ACTIVE_HOUSE_PLACEMENT, siteToHouseFrameMm } from './twin-house-placement';
import type { Point2Mm, FenceRunMm, PhysicalFenceRunMm } from './twin-site';

// Original C3 recipes remain available in twin-site and historical snapshots.
export * from './twin-site';
export { sjtskToLocalMm, ACTIVE_HOUSE_PLACEMENT, ACTIVE_LOCAL_ORIGIN_SJTSK_MM } from './twin-house-placement';

const rebase = siteToHouseFrameMm;
const ring = (points: readonly Point2Mm[]) => points.map(rebase);
const rings = (polygons: readonly (readonly Point2Mm[])[]) => polygons.map(ring);
const road = c3.ROAD_CONTEXT;
const frontAccessXs = new Set<number>([
  ...c3.SITE_SURFACES.driveway.polygonMm.map(p => p.x),
  ...c3.SITE_SURFACES.entry.polygonMm.map(p => p.x),
]);

export const ROAD_CONTEXT = Object.freeze({
  ...road,
  frontParcelEdgeMm: ring(road.frontParcelEdgeMm),
  frontOppositeParcelEdgeMm: ring(road.frontOppositeParcelEdgeMm),
  frontReservePolygonMm: ring(road.frontReservePolygonMm),
  // Straight garage/entry approaches follow the house through the street verge.
  frontReserveSurfacePolygonsMm: road.frontReserveSurfacePolygonsMm.map(points =>
    points.map(p => frontAccessXs.has(p.x) ? p : rebase(p))),
  frontagePolygonMm: ring(road.frontagePolygonMm),
  cornerParcelEdgeMm: ring(road.cornerParcelEdgeMm),
  cornerAsphaltEdgeMm: ring(road.cornerAsphaltEdgeMm),
  cornerReservePolygonMm: ring(road.cornerReservePolygonMm),
  cornerReserveSurfacePolygonsMm: rings(road.cornerReserveSurfacePolygonsMm),
  cornerOuterEdgeMm: ring(road.cornerOuterEdgeMm),
  cornerPolygonMm: ring(road.cornerPolygonMm),
  cornerCarriagewayPolygonMm: ring(road.cornerCarriagewayPolygonMm),
  visualReference: { ...road.visualReference,
    vergeClustersMm: road.visualReference.vergeClustersMm.map(p => ({ ...p, ...rebase(p) })),
  },
  streetLighting: { ...road.streetLighting, polesMm: ring(road.streetLighting.polesMm) },
  sideCurbAccessMm: {
    transitionStart: rebase({ x: 34270, y: 8750 }),
    gateStart: rebase({ x: 34268, y: 9250 }),
    gateEnd: rebase({ x: 34262, y: 11050 }),
    transitionEnd: rebase({ x: 34260, y: 11550 }),
  },
});

const fence = c3.SITE_FENCE;
function rebaseFenceRun<T extends FenceRunMm | PhysicalFenceRunMm>(run: T) {
  return { ...run, pointsMm: run.pointsMm.map((p, i) => {
    // The front fence changes length at its cadastral end, retaining facade/gate fixings.
    if (run.id.endsWith('FRONT-LEFT') && i === run.pointsMm.length - 1) return p;
    if (run.id.endsWith('FRONT-RIGHT') && i === 0) return p;
    return rebase(p);
  }) };
}
const sideGate = fence.sidePedestrianGate;
export const SITE_FENCE = Object.freeze({
  ...fence,
  annotatedCenterlineRuns: fence.annotatedCenterlineRuns.map(rebaseFenceRun),
  fixedRuns: fence.fixedRuns.map(rebaseFenceRun),
  // Rigid translation preserves the 100 mm inset and shared side/rear miters.
  physicalFixedRuns: fence.physicalFixedRuns.map(rebaseFenceRun),
  vehicleGate: { ...fence.vehicleGate,
    availableStackPocketMm: fence.vehicleGate.availableStackPocketMm + ACTIVE_HOUSE_PLACEMENT.translationMm.x,
  },
  sidePedestrianGate: { ...sideGate,
    startMm: rebase(sideGate.startMm), endMm: rebase(sideGate.endMm),
    physicalStartMm: rebase(sideGate.physicalStartMm), physicalEndMm: rebase(sideGate.physicalEndMm),
    terminalFrameCenterMm: rebase(sideGate.terminalFrameCenterMm),
    supportPostCentersMm: ring(sideGate.supportPostCentersMm),
  },
});

const approach = c3.SITE_SURFACES.sideEntryApproach;
const eastFaceX = c3.HOUSE.facades.east.faceXmm;
const approachBoundaryX = Math.min(...approach.privatePolygonMm.filter(p => p.x > eastFaceX + 2000).map(p => p.x));
const approachPoint = (p: Point2Mm): Point2Mm => {
  const fraction = Math.max(0, Math.min(1, (p.x - (eastFaceX - 2)) / (approachBoundaryX - (eastFaceX - 2))));
  return { x: p.x - ACTIVE_HOUSE_PLACEMENT.translationMm.x * fraction, y: p.y };
};
const privateApproach = approach.privatePolygonMm.map(approachPoint);
export const SITE_SURFACES = Object.freeze({
  ...c3.SITE_SURFACES,
  sideEntryApproach: { ...approach,
    polygonMm: approach.polygonMm.map(approachPoint),
    privatePolygonMm: privateApproach,
    roadReservePolygonMm: ring(approach.roadReservePolygonMm),
    areaM2: c3.polygonAreaM2(approach.polygonMm.map(approachPoint)),
    streetConnection: { ...approach.streetConnection, privateAreaM2: c3.polygonAreaM2(privateApproach) },
  },
});

export const UTILITY_ROUTES = c3.UTILITY_ROUTES.map(route => ({ ...route,
  pointsMm: route.pointsMm.map(p => {
    if (route.status === 'EXISTING_CONTEXT') return rebase(p);
    // Keep internal water/sewer junctions together and taper only the street lead-ins.
    const fraction = route.id === 'UTIL-ELECTRICITY'
      ? Math.max(0, 1 - p.x / 7236)
      : Math.max(0, Math.min(1, -p.y / 1689));
    return { x: p.x - ACTIVE_HOUSE_PLACEMENT.translationMm.x * fraction, y: p.y };
  }),
}));

export const PARCEL_LAWN_INTERIOR_CUTOUTS_MM = Object.freeze([
  privateApproach,
  ...c3.PARCEL_LAWN_INTERIOR_CUTOUTS_MM.slice(1),
]);
