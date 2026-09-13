import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Scene } from '@babylonjs/core/scene';
import { expect, it } from 'vitest';
import { buildInterior } from '../lib/babylon-interior';
import { INTERIOR_WALLS } from '../lib/twin-interior';
import { sceneXM, sceneZM } from '../lib/twin-render-frame';

it('renders revised office walls and the lobby mirror at their shared plan faces in C/B/B',()=>{
  const engine=new NullEngine();
  const scene=new Scene(engine);
  const material=new PBRMaterial('test',scene);
  try {
    buildInterior({scene,livingLayout:'B',heatingLayout:'B',anisotropy:1,wall:material,soffit:material,glassFrame:material,chimneyMetal:material,timber:material,
      register:mesh=>mesh,realisticOnly:mesh=>mesh,castShadow:mesh=>mesh});
    for(const id of ['IW-STUDY-NORTH','C-ENTRY-OFFICE-EAST','C-ENTRY-OFFICE-RETURN']) {
      const r=INTERIOR_WALLS.find(w=>w.id===id)!.rectMm;
      const mesh=scene.meshes.find(m=>m.name.startsWith(`Vnútorná stena ${id} ·`))!;
      expect(mesh,id).toBeDefined();
      mesh.computeWorldMatrix(true);
      const box=mesh.getBoundingInfo().boundingBox;
      expect(box.minimumWorld.x).toBeCloseTo(sceneXM(r.x0),5);
      expect(box.maximumWorld.x).toBeCloseTo(sceneXM(r.x1),5);
      expect(box.minimumWorld.z).toBeCloseTo(sceneZM(r.y1),5);
      expect(box.maximumWorld.z).toBeCloseTo(sceneZM(r.y0),5);
      expect(mesh.checkCollisions).toBe(true);
    }
    const mirror=scene.meshes.find(m=>m.name.includes('MIRROR · vysoké zrkadlo'))!;
    mirror.computeWorldMatrix(true);
    expect(mirror.getBoundingInfo().boundingBox.maximumWorld.x).toBeCloseTo(sceneXM(23367-13),5);
  } finally { scene.dispose();engine.dispose(); }
});
