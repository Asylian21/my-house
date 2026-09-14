import { VertexBuffer } from '@babylonjs/core/Buffers/buffer';
import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { RawTexture } from '@babylonjs/core/Materials/Textures/rawTexture';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import { CreateBox } from '@babylonjs/core/Meshes/Builders/boxBuilder.pure';
import { Scene } from '@babylonjs/core/scene';
import { describe, expect, it } from 'vitest';
import { buildKitchenPendant } from '../lib/babylon-kitchen-pendant';
import { createKitchenTaskLight, KITCHEN_BROWSER_LIGHT_PREVIEW_GAIN, registerKitchenLightEmitter, setKitchenTaskLightingNightAlpha } from '../lib/babylon-interior-lighting';
import { ceilingElevationMm, INTERIOR_ROOMS, KITCHEN_DESIGN, KITCHEN_ISLAND, KITCHEN_RUN } from '../lib/twin-interior';
import { INTERIOR_LIGHTING, KITCHEN_ISLAND_LIGHT, KITCHEN_TASK_LIGHT, kitchenLightLuminance } from '../lib/twin-interior-lighting';

describe('kitchen task and island lighting', () => {
  it('lights the work areas while clearing the hood and keeping a high, centred island line', () => {
    const task = KITCHEN_TASK_LIGHT.geometry;
    expect(task.bodyCenterPlanMm[0] - task.dimensionsMm[0] / 2).toBeGreaterThan(KITCHEN_DESIGN.ovenTowerRectMm.x1);
    const hoodFront = (KITCHEN_DESIGN.hobRectMm.y0 + KITCHEN_DESIGN.hobRectMm.y1) / 2 + KITCHEN_DESIGN.hood.depthMm / 2;
    expect(task.bodyCenterPlanMm[1] - task.dimensionsMm[1] / 2).toBeGreaterThan(hoodFront);
    expect(task.bodyCenterPlanMm[1] + task.dimensionsMm[1] / 2).toBeLessThan(KITCHEN_RUN.rectMm.y0 + KITCHEN_RUN.upperCabinets.depthMm);
    const island = KITCHEN_ISLAND.worktopRectMm, pendant = KITCHEN_ISLAND_LIGHT.geometry;
    expect(pendant.bodyCenterPlanMm[0]).toBe((island.x0 + island.x1) / 2);
    expect(pendant.bodyCenterPlanMm[1]).toBe((island.y0 + island.y1) / 2);
    expect(pendant.bodyCenterPlanMm[2] - pendant.dimensionsMm[2] / 2).toBe(2200);
    expect(pendant.dimensionsMm[0]).toBeLessThan(island.x1 - island.x0);
    for (const fixture of INTERIOR_LIGHTING.fixtures) {
      const { light, geometry } = fixture;
      expect(light.positionPlanMm[2]).toBeLessThan(geometry.bodyCenterPlanMm[2] - geometry.dimensionsMm[2] / 2);
      expect(light.directionPlan).toEqual([0, 0, -1]);
      expect(kitchenLightLuminance(fixture) * Math.PI * light.sourceWidthMm * light.sourceHeightMm / 1e6).toBeCloseTo(light.lumens, 8);
    }
    expect(INTERIOR_LIGHTING.vendorPhotometryAvailable).toBe(false);
  });

  it('joins both suspension cables to the pendant and flush ceiling mounts, with no roof penetration', () => {
    const engine = new NullEngine(), scene = new Scene(engine);
    try {
      createKitchenTaskLight(scene);
      buildKitchenPendant({ scene, finish: (mesh, material) => { mesh.material = material; } });
      const room = INTERIOR_ROOMS.find(room => room.id === 'ROOM-1-03')!;
      const body = scene.getMeshByName(KITCHEN_ISLAND_LIGHT.geometry.sourceName)!;
      body.computeWorldMatrix(true);
      for (let i = 0; i < 2; i++) {
        const cable = scene.getMeshByName(`KITCHEN-RUN · ISLAND-LIGHT · jemný záves ${i + 1}`)!;
        const mount = scene.getMeshByName(`KITCHEN-RUN · ISLAND-LIGHT · kotvenie do šikmého stropu ${i + 1}`)!;
        cable.computeWorldMatrix(true); mount.computeWorldMatrix(true);
        expect(cable.getBoundingInfo().boundingBox.minimumWorld.y).toBeCloseTo(body.getBoundingInfo().boundingBox.maximumWorld.y, 5);
        const suspension = KITCHEN_ISLAND_LIGHT.suspension[i];
        expect(cable.getBoundingInfo().boundingBox.maximumWorld.y * 1000).toBeCloseTo((suspension.ceilingLeftMm + suspension.ceilingRightMm) / 2 - suspension.mountThicknessMm, 2);
        const positions = mount.getVerticesData(VertexBuffer.PositionKind)!;
        let contacts = 0;
        for (let v = 0; v < positions.length; v += 3) {
          const world = Vector3.TransformCoordinates(Vector3.FromArray(positions, v), mount.getWorldMatrix());
          const roof = ceilingElevationMm(room, world.x * 1000 + 15200);
          expect(world.y * 1000).toBeLessThanOrEqual(roof + 0.01);
          if (Math.abs(world.y * 1000 - roof) < 0.01) contacts++;
        }
        expect(contacts).toBeGreaterThan(0);
      }
      expect(scene.lights).toHaveLength(0);
    } finally { scene.dispose(); engine.dispose(); }
  });

  it('switches and dims both real rectangle lights and their dedicated diffusers together', () => {
    const engine = new NullEngine(), scene = new Scene(engine);
    // Seed local LTC placeholders: this geometry/power test performs no network request.
    const texture = () => RawTexture.CreateRGBATexture(new Uint8Array(64 * 64 * 4), 64, 64, scene, false, false);
    const ltc1 = texture(), ltc2 = texture();
    Object.assign(scene, { _ltcTextures: { LTC1: ltc1, LTC2: ltc2 } });
    try {
      createKitchenTaskLight(scene);
      const strip = new PBRMaterial('dedicated task diffuser', scene);
      registerKitchenLightEmitter(scene, KITCHEN_TASK_LIGHT.id, strip);
      buildKitchenPendant({ scene, finish: (mesh, material) => { mesh.material = material; } });
      const floor = CreateBox('1.03 Hlavný obytný priestor s kuchyňou · podlaha 1', { width: 2, height: 0.04, depth: 2 }, scene);
      floor.position.set(9.5, -0.02, -3.5);
      const unrelated = CreateBox('1.04 Pracovňa · podlaha 1', {}, scene);
      const mergedFloor = CreateBox('ArchViz | house | shared vinyl', { width: 20, depth: 20 }, scene);
      mergedFloor.metadata = { sourceName: floor.name };
      setKitchenTaskLightingNightAlpha(scene, 0);
      expect(scene.lights).toHaveLength(0);
      expect(strip.emissiveColor.r).toBe(0);
      setKitchenTaskLightingNightAlpha(scene, 1);
      expect(scene.lights).toHaveLength(2);
      const full = scene.lights.map(light => light.intensity);
      expect(full.every(value => Number.isFinite(value) && value > 0)).toBe(true);
      for (const light of scene.lights) {
        const fixture = INTERIOR_LIGHTING.fixtures.find(item => item.id === light.id)!;
        expect(light.intensity).toBe(kitchenLightLuminance(fixture) * KITCHEN_BROWSER_LIGHT_PREVIEW_GAIN);
        expect(light.canAffectMesh(floor)).toBe(true);
        expect(light.canAffectMesh(unrelated)).toBe(false);
        expect(light.canAffectMesh(mergedFloor)).toBe(false);
        expect(light.metadata.sourceLumens).toBe(fixture.light.lumens);
      }
      expect(strip.emissiveColor.r).toBe(1.2);
      setKitchenTaskLightingNightAlpha(scene, 0.5);
      expect(scene.lights.map(light => light.intensity)).toEqual(full.map(value => value / 2));
      setKitchenTaskLightingNightAlpha(scene, 0);
      expect(scene.lights.every(light => !light.isEnabled())).toBe(true);
      expect(strip.emissiveColor.r).toBe(0);
      for (const value of [-0.1, 1.1, NaN]) expect(() => setKitchenTaskLightingNightAlpha(scene, value)).toThrow();
      expect(scene.lights.every(light => !light.isEnabled())).toBe(true);
    } finally { ltc1.dispose(); ltc2.dispose(); scene.dispose(); engine.dispose(); }
  });
});
