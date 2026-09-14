import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Scene } from '@babylonjs/core/scene';
import { describe, expect, it } from 'vitest';
import { buildInterior } from '../lib/babylon-interior';
import { INTERIOR_DOORS, INTERIOR_ROOMS, INTERIOR_WALLS, OFFICE_FITOUT } from '../lib/twin-interior';
import { OFFICE_FITOUT as historicalOffice } from '../lib/twin-interior-baseline';
import { PLAN_ITEM_BY_ID } from '../lib/plan-documentation';
import { sceneXM, sceneZM } from '../lib/twin-render-frame';
import { contains, intersects, swingHits } from './floor-plan-geometry';

describe('client-selected AlzaErgo ET1 NewGen desk in C/B/B', () => {
  it('fits the exact 1400 × 800 top without moving the workstation axis or blocking the entry', () => {
    const { desk, chair, cabinet, clearEntryRectMm } = OFFICE_FITOUT;
    const r = desk.footprintMm;
    expect(r).toEqual({ x0: 23542, y0: 3704, x1: 24342, y1: 5104 });
    expect(desk.topThicknessMm).toBe(18);
    expect(desk.topElevationMm).toBe(750);
    expect(desk.facing).toBe('WEST');
    expect((r.y0 + r.y1) / 2).toBe(desk.monitor.centerMm.y);
    expect(chair.centerMm.y).toBe(desk.monitor.centerMm.y);
    expect(desk.monitor.widthMm).toBeLessThan(r.y1 - r.y0);
    expect(chair.footprintMm.x0 - r.x1).toBe(120);
    expect(clearEntryRectMm.y0 - r.y1).toBe(296);
    const office = INTERIOR_ROOMS.find(room => room.id === 'ROOM-1-04')!;
    expect(office.rectsMm.some(room => contains(room, r))).toBe(true);
    for (const obstacle of [...INTERIOR_WALLS.map(w => w.rectMm), chair.footprintMm, cabinet.footprintMm, clearEntryRectMm]) {
      expect(intersects(obstacle, r)).toBe(false);
    }
    const door = INTERIOR_DOORS.find(d => d.id === 'DOOR-102-104')!;
    expect(swingHits({ ...door, startMm: door.startMm + (door.frameInsetMm ?? 60), widthMm: door.leafWidthMm, leafPlaneMm: door.wallSpanMm[1] }, r)).toBe(false);
    expect(historicalOffice.desk.footprintMm.y1 - historicalOffice.desk.footprintMm.y0).toBe(1800);
  });

  it('renders the real top and collision envelope at the same millimetre coordinates', () => {
    const engine = new NullEngine({ renderWidth: 64, renderHeight: 64, textureSize: 64 });
    const scene = new Scene(engine);
    const mat = new PBRMaterial('test', scene);
    try {
      buildInterior({ scene, anisotropy: 1, wall: mat, soffit: mat, glassFrame: mat,
        chimneyMetal: mat, timber: mat, register: m => m, realisticOnly: m => m, castShadow: m => m });
      const meshes = scene.meshes.filter(m => m.name.startsWith(`${OFFICE_FITOUT.id} · DESK ·`));
      const top = meshes.find(m => m.name.includes('čierna doska'))!;
      const guard = meshes.find(m => m.metadata?.walkCollisionOnly)!;
      for (const mesh of [top, guard]) {
        mesh.computeWorldMatrix(true);
        const b = mesh.getBoundingInfo().boundingBox;
        expect(b.minimumWorld.x).toBeCloseTo(sceneXM(23542), 5);
        expect(b.maximumWorld.x).toBeCloseTo(sceneXM(24342), 5);
        expect(b.minimumWorld.z).toBeCloseTo(sceneZM(5104), 5);
        expect(b.maximumWorld.z).toBeCloseTo(sceneZM(3704), 5);
      }
      const b = top.getBoundingInfo().boundingBox;
      expect(b.maximumWorld.y).toBeCloseTo(0.750, 6);
      expect(b.minimumWorld.y).toBeCloseTo(0.732, 6);
      expect(top.material?.name).toBe('real-office-desk-black-laminate');
      expect(guard.checkCollisions).toBe(true);
      expect(meshes.filter(m => m.name.includes('pätka T'))).toHaveLength(2);
      expect(meshes.filter(m => /stĺp \d ·/.test(m.name))).toHaveLength(6);
      for (const mesh of meshes.filter(m => m !== guard)) {
        mesh.computeWorldMatrix(true);
        const bounds = mesh.getBoundingInfo().boundingBox;
        expect(bounds.minimumWorld.x).toBeGreaterThanOrEqual(b.minimumWorld.x - 0.00001);
        expect(bounds.maximumWorld.x).toBeLessThanOrEqual(b.maximumWorld.x + 0.00001);
        expect(bounds.minimumWorld.z).toBeGreaterThanOrEqual(b.minimumWorld.z - 0.00001);
        expect(bounds.maximumWorld.z).toBeLessThanOrEqual(b.maximumWorld.z + 0.00001);
      }
    } finally { scene.dispose(); engine.dispose(); }
  });

  it('keeps the exported 2D geometry and product information in sync with the 3D top', () => {
    const item = PLAN_ITEM_BY_ID.get(`${OFFICE_FITOUT.id}-DESK`)!;
    expect(item.nominal).toEqual(OFFICE_FITOUT.desk.footprintMm);
    expect(item.product?.source).toContain('d13366453');
    const top = item.meshes.find(m => m.name.includes('čierna doska'))!;
    expect(top).toBeDefined();
    expect(top.rect).toEqual(OFFICE_FITOUT.desk.footprintMm);
    expect(top.z1 - top.z0).toBe(18);
  });
});
