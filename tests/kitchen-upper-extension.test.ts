import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { Ray } from '@babylonjs/core/Culling/ray';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import type { AbstractMesh } from '@babylonjs/core/Meshes/abstractMesh';
import { Scene } from '@babylonjs/core/scene';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { buildInterior } from '../lib/babylon-interior';
import { buildOpening, type OpeningBuildContext } from '../lib/babylon-openings';
import type { AnimatedDoorRegistration } from '../lib/babylon-doors';
import { HOUSE } from '../lib/twin-active-house';
import { INTERIOR_DOORS, KITCHEN_DESIGN, KITCHEN_ISLAND, KITCHEN_RUN, type RectMm } from '../lib/twin-interior';
import { SCENE_CENTER_MM, sceneXM, sceneZM } from '../lib/twin-render-frame';

type Bounds = RectMm & { bottom: number; top: number };
const bounds = (mesh: AbstractMesh): Bounds => {
  mesh.computeWorldMatrix(true);
  const b = mesh.getBoundingInfo().boundingBox;
  return {
    x0: b.minimumWorld.x * 1000 + SCENE_CENTER_MM.x,
    x1: b.maximumWorld.x * 1000 + SCENE_CENTER_MM.x,
    y0: SCENE_CENTER_MM.y - b.maximumWorld.z * 1000,
    y1: SCENE_CENTER_MM.y - b.minimumWorld.z * 1000,
    bottom: b.minimumWorld.y * 1000,
    top: b.maximumWorld.y * 1000,
  };
};
const overlaps = (a: Bounds, b: Bounds) =>
  a.x0 < b.x1 - .1 && a.x1 > b.x0 + .1 && a.y0 < b.y1 - .1 && a.y1 > b.y0 + .1
  && a.bottom < b.top - .1 && a.top > b.bottom + .1;

describe('client kitchen upper row, open sideboard and visible extractor', () => {
  let engine: NullEngine, scene: Scene;
  const doors: AnimatedDoorRegistration[] = [];
  const prefix = 'KITCHEN-RUN · ';
  const mesh = (name: string) => {
    const found = scene.getMeshByName(prefix + name);
    expect(found, name).not.toBeNull();
    return found!;
  };
  const extensions = () => scene.meshes.filter(m => m.metadata?.kitchenPart === 'upper-extension');
  beforeAll(() => {
    engine = new NullEngine();
    scene = new Scene(engine);
    scene.useRightHandedSystem = true;
    const material = new PBRMaterial('kitchen-clearance-test', scene);
    const identity = (m: AbstractMesh) => m;
    buildInterior({
      scene, anisotropy: 1, livingLayout: 'B', heatingLayout: 'B',
      wall: material, soffit: material, glassFrame: material, chimneyMetal: material, timber: material,
      register: identity, realisticOnly: identity, castShadow: identity,
      registerAnimatedDoor: door => doors.push(door),
    });
    const window = HOUSE.facades.east.openings.find(o => o.id === 'EAST-04')!;
    const context: OpeningBuildContext = {
      scene, materials: new Proxy({} as OpeningBuildContext['materials'], { get: () => material }),
      register: identity, realisticOnly: identity, castShadow: identity, appearance: identity,
    };
    buildOpening(context, {
      name: window.id, axis: 'X', faceMm: HOUSE.facades.east.faceXmm,
      centerMm: window.startYmm + window.widthMm / 2, widthMm: window.widthMm,
      heightMm: window.heightMm, sillMm: window.sillMm, outward: 1, wallThicknessMm: 530,
      kind: 'window', frameMaterial: material, curtains: true,
    });
    scene.meshes.forEach(m => m.computeWorldMatrix(true));
  });
  afterAll(() => { scene.dispose(); engine.dispose(); });

  it('ends the five matching oak upper fronts exactly at the main run with real recessed joints', () => {
    const upper = KITCHEN_DESIGN.upperExtension;
    const fronts = scene.meshes.filter(m => m.name.startsWith(prefix + 'horné skrinky · nadstavba · dubové čelo'));
    expect(fronts).toHaveLength(5);
    const oak = mesh('FRIDGE-600 · dubový blok 2026').material as PBRMaterial;
    expect(oak.albedoTexture?.name).toContain('living-natural-oak-albedo.jpg');
    const ordered = fronts.map(m => ({ m, b: bounds(m) })).sort((a, b) => a.b.x0 - b.b.x0);
    for (const { m, b } of ordered) {
      expect(m.material).toBe(oak);
      expect(b.bottom).toBeCloseTo(upper.bottomMm, 1);
      expect(b.top).toBeCloseTo(upper.topMm, 1);
      expect(b.y1).toBeCloseTo(upper.rectMm.y1, 1);
      expect(b.y1 - b.y0).toBeCloseTo(22, 1);
    }
    expect(ordered[0].b.x0 - upper.rectMm.x0).toBeCloseTo(2, 1);
    expect(upper.rectMm.x1 - ordered.at(-1)!.b.x1).toBeCloseTo(2, 1);
    for (let i = 1; i < ordered.length; i++) expect(ordered[i].b.x0 - ordered[i - 1].b.x1).toBeCloseTo(4, 1);
    const backing = bounds(mesh('horné skrinky · nadstavba · tmavé pozadie škár'));
    expect(ordered[0].b.y0 - backing.y1).toBeGreaterThan(1);
    const carcass = bounds(mesh('horné skrinky · nadstavba · zapustený korpus'));
    expect(carcass.x0).toBeCloseTo(KITCHEN_RUN.rectMm.x0, 1);
    expect(carcass.x1).toBeCloseTo(KITCHEN_RUN.rectMm.x1, 1);
    expect(ordered.at(-1)!.b.x1).toBeCloseTo(KITCHEN_RUN.rectMm.x1 - 2, 1);
  });

  it('leaves the whole area over the doorway and east sideboard open, without a bridge or cupboard stub', () => {
    const east = KITCHEN_DESIGN.eastStorageRectMm;
    const openVolume: Bounds = {
      x0: KITCHEN_RUN.rectMm.x1 + .5, x1: east.x1 + .5,
      y0: KITCHEN_RUN.rectMm.y0 - .5, y1: east.y1 + .5, bottom: 900.1, top: 5000,
    };
    const backsplash = mesh('L-RETURN-EAST · obklad pri stene 2026');
    const blockers = scene.meshes.filter(m => m.isVisible && m.name.startsWith(prefix)
      && !m.metadata?.coordinationOnly && m !== backsplash && overlaps(bounds(m), openVolume));
    expect(blockers.map(m => m.name)).toEqual([]);
    expect(scene.meshes.some(m => m.metadata?.kitchenPart === 'east-upper-tower' || m.name.includes('ľavé zakončenie'))).toBe(false);
    const stone = bounds(backsplash), window = HOUSE.facades.east.openings.find(o => o.id === 'EAST-04')!;
    expect(stone.y0).toBeCloseTo(east.y0 + 10, 1);
    expect(stone.y1).toBeCloseTo(window.startYmm - 20, 1);
    expect(stone.bottom).toBeCloseTo(900, 1);
    expect(stone.top).toBeCloseTo(1080, 1);
    const countertop = mesh('L-RETURN-EAST · minerálna doska pri okne');
    for (const y of [east.y0 + 100, window.startYmm - 100, window.startYmm + 300]) {
      const hit = scene.pickWithRay(new Ray(new Vector3(sceneXM((east.x0 + east.x1) / 2), 2.8, sceneZM(y)), Vector3.Down(), 2),
        m => m.isVisible && m.name.startsWith(prefix) && !m.metadata?.coordinationOnly);
      expect(hit?.pickedMesh, `unobstructed worktop at Y=${y}`).toBe(countertop);
      expect(hit!.pickedPoint!.y).toBeCloseTo(.9, 3);
    }
  });

  it('keeps the scanned oak grain vertical at its physical scale on both front and side panels', () => {
    const panels = [
      { panel: mesh('horné skrinky · nadstavba · dubové čelo 1'), normal: new Vector3(0, 0, -1) },
      { panel: mesh('horné skrinky · nadstavba · zapustený korpus'), normal: new Vector3(1, 0, 0) },
    ];
    for (const { panel, normal } of panels) {
      const oak = panel.material as PBRMaterial;
      expect(oak.albedoTexture?.name).toBe('/assets/textures/kitchen/living-natural-oak-albedo.jpg');
      expect(oak.bumpTexture?.name).toBe('/assets/textures/kitchen/living-natural-oak-normal.jpg');
      expect(oak.bumpTexture?.gammaSpace).toBe(false);
      const positions = panel.getVerticesData('position')!, normals = panel.getVerticesData('normal')!, uvs = panel.getVerticesData('uv')!;
      const world = panel.computeWorldMatrix(true);
      const face = [];
      for (let i = 0; i < positions.length / 3; i++) {
        const n = Vector3.TransformNormal(Vector3.FromArray(normals, i * 3), world).normalize();
        if (Vector3.Dot(n, normal) > .99) face.push({
          world: Vector3.TransformCoordinates(Vector3.FromArray(positions, i * 3), world),
          uv: new Vector3(uvs[i * 2], uvs[i * 2 + 1], 1),
        });
      }
      expect(face, panel.name).toHaveLength(4);
      let checkedVerticalEdges = 0;
      for (const a of face) for (const b of face) {
        const rise = b.world.y - a.world.y;
        if (rise < .3 || Math.abs(a.world.x - b.world.x) > 1e-6 || Math.abs(a.world.z - b.world.z) > 1e-6) continue;
        checkedVerticalEdges++;
        for (const texture of [oak.albedoTexture!, oak.bumpTexture!]) {
          // Match the shader's matrix * vec4(U, V, 1, 0), so this catches
          // both side-face UV rotation and a later material-level rotation.
          const matrix = texture.getTextureMatrix();
          const sampleA = Vector3.TransformNormal(a.uv, matrix), sampleB = Vector3.TransformNormal(b.uv, matrix);
          expect(sampleB.x - sampleA.x, `${panel.name}: vertical grain must not advance along U`).toBeCloseTo(0, 6);
          expect(sampleB.y - sampleA.y, `${panel.name}: 1.83 m physical veneer repeat`).toBeCloseTo(rise / 1.83, 6);
        }
      }
      expect(checkedVerticalEdges, panel.name).toBe(2);
    }
  });

  it('clears the complete rendered utility door swing, jambs and human-height approach', () => {
    const spec = INTERIOR_DOORS.find(d => d.id === 'DOOR-103-107')!;
    const door = doors.find(d => d.id === spec.id)!;
    expect(door).toBeDefined();
    const moving = scene.meshes.filter(m => m.metadata?.doorId === spec.id);
    const frames = scene.meshes.filter(m => m.name.startsWith(spec.label) && !m.metadata?.doorId);
    expect(moving.length).toBeGreaterThanOrEqual(3);
    const added = extensions().map(m => ({ name: m.name, b: bounds(m) }));
    for (const frame of frames) for (const item of added) expect(overlaps(bounds(frame), item.b), `${frame.name} / ${item.name}`).toBe(false);
    try {
      // Actual transformed leaf and handles, including intermediate opening angles.
      for (let step = 0; step <= 180; step++) {
        door.apply(step / 180, 0);
        for (const leaf of moving) for (const item of added)
          expect(overlaps(bounds(leaf), item.b), `${leaf.name} / ${item.name} at ${step / 2} degrees`).toBe(false);
      }
    } finally { door.apply(0, 0); }
    const passages: Bounds[] = [
      { x0: spec.startMm + 60, x1: spec.startMm + spec.widthMm - 60, y0: spec.wallSpanMm[1], y1: KITCHEN_ISLAND.worktopRectMm.y0, bottom: 0, top: 2100 },
      { x0: KITCHEN_ISLAND.worktopRectMm.x1 + 1, x1: KITCHEN_ISLAND.eastReturnWorktopRectMm.x0 - 1, y0: KITCHEN_RUN.rectMm.y1, y1: KITCHEN_ISLAND.worktopRectMm.y1, bottom: 0, top: 2100 },
    ];
    for (const passage of passages) for (const item of added) expect(overlaps(passage, item.b), item.name).toBe(false);
  });

  it('stays below the rendered cathedral underside and outside the window, sill and curtains', () => {
    const windowMeshes = scene.meshes.filter(m => m.name.startsWith('EAST-04'));
    expect(windowMeshes.length).toBeGreaterThan(8);
    for (const added of extensions()) for (const window of windowMeshes)
      expect(overlaps(bounds(added), bounds(window)), `${added.name} / ${window.name}`).toBe(false);
    const fronts = extensions().filter(m => m.name.includes('nadstavba · dubové čelo'));
    for (const front of fronts) {
      const b = bounds(front);
      for (const x of [b.x0 + 1, b.x1 - 1]) {
        const hit = scene.pickWithRay(new Ray(new Vector3(sceneXM(x), b.top / 1000 + .0001, sceneZM((b.y0 + b.y1) / 2)), Vector3.Up(), 3),
          m => m.name.startsWith('1.03 · šikmý SDK podhľad'));
        expect(hit?.hit, `${front.name} has a modeled ceiling above`).toBe(true);
        expect(hit!.pickedPoint!.y * 1000 - b.top, front.name).toBeGreaterThan(20);
      }
    }
  });

  it('shows an actual metal canopy and graphite front, with open filter recesses above the hob', () => {
    const canopy = mesh('odsávač · integrovaná spodná kazeta');
    const cb = bounds(canopy), front = mesh('odsávač · grafitové čelo 2026');
    expect(front.material).toBe(mesh('OVEN-ELEVATED · rúra so zasúvacím krídlom').material);
    expect((front.material as PBRMaterial).clearCoat.isEnabled).toBe(true);
    expect(cb.x0).toBeLessThan(KITCHEN_DESIGN.hobRectMm.x0);
    expect(cb.x1).toBeGreaterThan(KITCHEN_DESIGN.hobRectMm.x1);
    expect(cb.bottom - 905).toBeCloseTo(615, 1);
    expect(cb.top).toBeCloseTo(1600, 1);
    expect((canopy.material as PBRMaterial).metallic).toBeGreaterThan(.8);
    const fb = bounds(mesh('odsávač · filtre'));
    const sampleX = KITCHEN_RUN.extractorCenterXmm + 100;
    // This ray passes between modeled slats into the recess. A solid fake
    // canopy or the old oak box would be hit before the recessed filter back.
    const filterHit = scene.pickWithRay(new Ray(new Vector3(sceneXM(sampleX), 1.45, sceneZM(fb.y0 + 18)), Vector3.Up(), .3),
      m => m.isVisible && m.name.startsWith(prefix) && !m.metadata?.coordinationOnly);
    expect(filterHit?.pickedMesh?.name).toBe(prefix + 'odsávač · filtre');
    expect(filterHit!.pickedPoint!.y * 1000 - cb.bottom).toBeCloseTo(30, 1);
    const frontBounds = bounds(front);
    const frontHit = scene.pickWithRay(new Ray(new Vector3(sceneXM(sampleX), 1.56, sceneZM(12000)), new Vector3(0, 0, 1), 1),
      m => m.isVisible && m.name.startsWith(prefix) && !m.metadata?.coordinationOnly);
    expect(frontHit?.pickedMesh).toBe(front);
    expect(frontBounds.top - frontBounds.bottom).toBeGreaterThanOrEqual(64.9);
    const outlet = bounds(mesh('odsávač · horná vratná mriežka'));
    expect(outlet.bottom).toBeCloseTo(KITCHEN_DESIGN.upperExtension.topMm, 1);
    expect(mesh('odsávač · servisná obálka').metadata.returnElevationMm).toBeCloseTo(outlet.bottom, 1);
    const returnHit = scene.pickWithRay(new Ray(new Vector3(sceneXM(sampleX), outlet.top / 1000 + .01, sceneZM((outlet.y0 + outlet.y1) / 2)), Vector3.Up(), 3),
      m => m.isVisible && (m.name.startsWith(prefix) || m.name.startsWith('1.03 · šikmý SDK podhľad')));
    expect(returnHit?.pickedMesh?.name).toContain('šikmý SDK podhľad');
    expect(returnHit!.distance).toBeGreaterThan(.1);
  });
});
