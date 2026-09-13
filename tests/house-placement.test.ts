import { describe, expect, it } from 'vitest';
import * as baseline from '../lib/twin-site';
import * as site from '../lib/twin-active-site';
import { HOUSE, SIDE_ENTRY_APPROACH, PARCEL_LAWN_INTERIOR_CUTOUTS_MM } from '../lib/twin-active-house';
import { SITE_BOUNDARY } from '../lib/plan-export';
import { ACTIVE_HOUSE_PLACEMENT, ACTIVE_LOCAL_ORIGIN_SJTSK_MM } from '../lib/twin-house-placement';

const distanceToLine = (p: baseline.Point2Mm, a: baseline.Point2Mm, b: baseline.Point2Mm) =>
  Math.abs((b.y - a.y) * p.x - (b.x - a.x) * p.y + b.x * a.y - b.y * a.x)
    / Math.hypot(b.x - a.x, b.y - a.y);
const samePoint = (a: baseline.Point2Mm, b: baseline.Point2Mm) => {
  expect(a.x).toBeCloseTo(b.x, 7);
  expect(a.y).toBeCloseTo(b.y, 7);
};

describe('client placement: street and right boundary at 3 m', () => {
  it('moves the complete house relative to the unaltered cadastral polygon', () => {
    expect(HOUSE.footprintMm).toEqual(baseline.HOUSE.footprintMm);
    const subject = site.CADASTRAL_PARCELS.find(p => p.isSubject)!;
    expect(subject).toBe(baseline.CADASTRAL_PARCELS.find(p => p.isSubject));
    const previous = subject.sjtskRingMm.map(baseline.sjtskToLocalMm);
    expect(site.polygonAreaM2(SITE_BOUNDARY)).toBeCloseTo(baseline.polygonAreaM2(previous), 9);
    for (let i = 0; i < previous.length; i++) {
      expect(previous[i].x - SITE_BOUNDARY[i].x).toBeCloseTo(77.913405454, 7);
      expect(previous[i].y).toBe(SITE_BOUNDARY[i].y);
    }
    const east = SITE_BOUNDARY.filter(p => p.x > 30000 && p.y >= 3000);
    expect(east).toHaveLength(2);
    const distances = HOUSE.footprintMm.map(p => distanceToLine(p, east[0], east[1]));
    expect(Math.min(...distances)).toBeCloseTo(3000, 8);
    expect(Math.min(...HOUSE.footprintMm.map(p => p.y))).toBe(3000);
  });

  it('exports the moved national-grid origin without rewriting the C3 datum', () => {
    const delta = ACTIVE_HOUSE_PLACEMENT.translationMm.x;
    const dx = ACTIVE_LOCAL_ORIGIN_SJTSK_MM.x - baseline.SUBJECT_PARCEL_SJTSK_ORIGIN_MM.x;
    const dy = ACTIVE_LOCAL_ORIGIN_SJTSK_MM.y - baseline.SUBJECT_PARCEL_SJTSK_ORIGIN_MM.y;
    expect(dx * site.SITE_AXIS.ux + dy * site.SITE_AXIS.uy).toBeCloseTo(delta, 5);
    expect(dx * site.SITE_AXIS.vx + dy * site.SITE_AXIS.vy).toBeCloseTo(0, 5);
    expect(HOUSE.placement.status).toBe('CLIENT_REQUESTED_SETBACK');
  });

  it('keeps cadastral fencing at its 100 mm physical inset and attached gate at the house', () => {
    for (const run of site.SITE_FENCE.physicalFixedRuns) {
      if (run.id.includes('FRONT')) continue;
      const referenceId = run.referenceRunIds[0];
      const reference = site.SITE_FENCE.fixedRuns.find(r => r.id === referenceId)!;
      for (const p of run.pointsMm) {
        expect(distanceToLine(p, reference.pointsMm[0], reference.pointsMm[1])).toBeCloseTo(100, 0);
      }
    }
    expect(site.SITE_FENCE.houseClosure).toEqual(baseline.SITE_FENCE.houseClosure);
    samePoint(site.SITE_FENCE.vehicleGate.leafClosureEndMm, HOUSE.originMm);
    samePoint(site.SITE_FENCE.physicalFixedRuns.find(r => r.id.endsWith('FRONT-RIGHT'))!.pointsMm[0],
      site.SITE_FENCE.houseClosure.endMm);
    const gate = site.SITE_FENCE.sidePedestrianGate;
    samePoint(site.SITE_FENCE.physicalFixedRuns.find(r => r.id.endsWith('EAST-UPPER'))!.pointsMm[1], gate.physicalStartMm);
    samePoint(site.SITE_FENCE.physicalFixedRuns.find(r => r.id.endsWith('EAST-LOWER'))!.pointsMm[0], gate.physicalEndMm);
  });

  it('joins the road, side access and lawn cutout while retaining front entry widths', () => {
    const delta = ACTIVE_HOUSE_PLACEMENT.translationMm.x;
    for (let i = 0; i < site.ROAD_CONTEXT.cornerParcelEdgeMm.length; i++) {
      samePoint(site.ROAD_CONTEXT.cornerParcelEdgeMm[i], SITE_BOUNDARY[i]);
    }
    const sideCurb = site.ROAD_CONTEXT.sideCurbAccessMm;
    expect(sideCurb.gateStart.x).toBeCloseTo(34268 - delta, 8);
    expect(SIDE_ENTRY_APPROACH.roadReservePolygonMm.some(p => p.x === sideCurb.gateStart.x)).toBe(true);
    expect(PARCEL_LAWN_INTERIOR_CUTOUTS_MM[0]).toBe(SIDE_ENTRY_APPROACH.privatePolygonMm);
    expect(site.SITE_SURFACES.driveway).toBe(baseline.SITE_SURFACES.driveway);
    expect(site.SITE_SURFACES.entry).toBe(baseline.SITE_SURFACES.entry);
    const middleReserve = site.ROAD_CONTEXT.frontReserveSurfacePolygonsMm[1];
    expect(Math.min(...middleReserve.map(p => p.x))).toBe(10690);
    expect(Math.max(...middleReserve.map(p => p.x))).toBe(21415);
  });
});
