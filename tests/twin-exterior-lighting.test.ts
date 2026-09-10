import { describe, expect, it } from 'vitest';
import { EXTERIOR_LIGHTING, EXTERIOR_LIGHTING_SOURCE_GEOMETRY } from '../lib/twin-exterior-lighting';
import { HOUSE } from '../lib/twin-active-house';
import { GARDEN_POOL } from '../lib/twin-site';

describe('shared authored exterior lighting', () => {
  it('retains the five existing fixture bodies and two brackets independently of export order', () => {
    const fixtures = EXTERIOR_LIGHTING.fixtures;
    expect(fixtures.map(f => f.id)).toEqual([
      'EXT-TERRACE-WALL-01', 'EXT-TERRACE-WALL-02',
      'EXT-POOL-WALL-01', 'EXT-POOL-WALL-02', 'EXT-POOL-WALL-03',
    ]);
    // Golden current builder positions/dimensions, not values recomputed by the new factory.
    expect(fixtures.map(f => f.geometry.bodyCenterPlanMm)).toEqual([
      [22600, 19610, 3935], [26400, 19610, 3935],
      [13590, 16092, -652], [14740, 16092, -652], [15890, 16092, -652],
    ]);
    expect(fixtures.map(f => [f.geometry.diameterMm, f.geometry.lengthMm, f.geometry.tessellation]))
      .toEqual([[70, 170, 24], [70, 170, 24], [135, 22, 24], [135, 22, 24], [135, 22, 24]]);
    expect(fixtures.flatMap(f => f.geometry.bracket ? [f.geometry.bracket] : []).map(b => [b.centerPlanMm, b.sizePlanMm]))
      .toEqual([[[22600, 19579, 3935], [24, 48, 30]], [[26400, 19579, 3935], [24, 48, 30]]]);
    expect(fixtures.slice(0, 2).every(f => f.parentSourceId === HOUSE.porches.wingEnd.id)).toBe(true);
    expect(fixtures.slice(2).every(f => f.parentSourceId === GARDEN_POOL.id)).toBe(true);
  });

  it('aims down/inward and keeps finite proxy sources clear of their own original cap', () => {
    for (const fixture of EXTERIOR_LIGHTING.fixtures) {
      const { light, geometry } = fixture;
      expect(Math.hypot(...light.directionPlan)).toBe(1);
      const displacement = light.positionPlanMm.map((v, i) => v - geometry.capCenterPlanMm[i]);
      const clearance = displacement.reduce((s, v, i) => s + v * light.directionPlan[i], 0) - light.sourceRadiusMm;
      expect(clearance).toBe(2);
      expect(light.sourceRadiusMm).toBeLessThanOrEqual(geometry.diameterMm / 2);
      if (fixture.kind === 'terrace-wall-downlight') {
        expect(light.directionPlan).toEqual([0, 0, -1]);
        expect(light.positionPlanMm[2]).toBe(3828);
      } else {
        expect(light.directionPlan).toEqual([0, -1, 0]);
        expect(light.positionPlanMm[1]).toBe(16024);
        expect(light.positionPlanMm[1]).toBeGreaterThan(GARDEN_POOL.centerMm.y - GARDEN_POOL.waterWidthMm / 2);
        expect(light.positionPlanMm[2] + light.sourceRadiusMm).toBeLessThan(EXTERIOR_LIGHTING_SOURCE_GEOMETRY.pool.waterSurfaceElevationMm);
      }
    }
  });

  it('serializes explicit authored cone photometry and preserves the lumen-to-candela convention', () => {
    const contract = JSON.parse(JSON.stringify(EXTERIOR_LIGHTING)) as typeof EXTERIOR_LIGHTING;
    expect(contract.provenance).toBe('AUTHORED_VISUALIZATION_PROPOSAL');
    expect(contract.coordinateSystem).toBe('PLAN_XY_ELEVATION_Z_MM');
    expect(contract.photometricConvention).toBe('UE_CONE_SOLID_ANGLE_LUMENS');
    expect([contract.vendorPhotometryAvailable, contract.iesProfileAvailable, contract.permitOrAsBuiltClaim]).toEqual([false, false, false]);
    expect(contract.fixtures.map(f => [f.light.nominalConeLumens, f.light.temperatureK])).toEqual([[300, 2700], [300, 2700], [400, 4000], [400, 4000], [400, 4000]]);
    for (const { light } of contract.fixtures) {
      const solidAngle = 2 * Math.PI * (1 - Math.cos(light.outerConeHalfAngleDeg * Math.PI / 180));
      expect(light.peakCandela * solidAngle).toBeCloseTo(light.nominalConeLumens, 10);
      expect(light.innerConeHalfAngleDeg).toBeGreaterThan(0);
      expect(light.outerConeHalfAngleDeg).toBeGreaterThan(light.innerConeHalfAngleDeg);
      expect(light.outerConeHalfAngleDeg).toBeLessThan(90);
      expect([light.dayMultiplier, light.nightMultiplier, light.castsShadows]).toEqual([0, 1, true]);
    }
  });
});
