import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Scene } from '@babylonjs/core/scene';
import type { TransformNode } from '@babylonjs/core/Meshes/transformNode';
import { expect, it } from 'vitest';
import { buildInterior } from '../lib/babylon-interior';
import type { AnimatedDoorRegistration } from '../lib/babylon-doors';
import { BATHROOM_FITOUT, INTERIOR_DOORS, INTERIOR_WALLS, OFFICE_FITOUT } from '../lib/twin-interior';
import { sceneXM, sceneZM } from '../lib/twin-render-frame';

it('renders revised office walls and the lobby mirror at their shared plan faces in C/B/B',()=>{
  const engine=new NullEngine();
  const scene=new Scene(engine);
  const material=new PBRMaterial('test',scene);
  const doors:AnimatedDoorRegistration[]=[];
  try {
    buildInterior({scene,livingLayout:'B',heatingLayout:'B',anisotropy:1,wall:material,soffit:material,glassFrame:material,chimneyMetal:material,timber:material,
      register:mesh=>mesh,realisticOnly:mesh=>mesh,castShadow:mesh=>mesh,registerAnimatedDoor:door=>doors.push(door)});
    for(const id of ['IW-STUDY-NORTH','C-ENTRY-OFFICE-EAST','C-ENTRY-OFFICE-RETURN']) {
      const r=INTERIOR_WALLS.find(w=>w.id===id)!.rectMm;
      const meshes=scene.meshes.filter(m=>m.name.startsWith(`Vnútorná stena ${id} ·`));
      expect(meshes,id).toHaveLength(id==='IW-STUDY-NORTH'?5:1);
      const boxes=meshes.map(mesh=>{
        mesh.computeWorldMatrix(true);
        expect(mesh.checkCollisions).toBe(mesh.metadata?.acousticMaterial!=='mineral-wool');
        const box=mesh.getBoundingInfo().boundingBox;
        // Every acoustic layer spans the complete wall length.
        expect(box.minimumWorld.x).toBeCloseTo(sceneXM(r.x0),5);
        expect(box.maximumWorld.x).toBeCloseTo(sceneXM(r.x1),5);
        return box;
      }).sort((a,b)=>a.minimumWorld.z-b.minimumWorld.z);
      expect(boxes[0].minimumWorld.z).toBeCloseTo(sceneZM(r.y1),5);
      expect(boxes.at(-1)!.maximumWorld.z).toBeCloseTo(sceneZM(r.y0),5);
      if(id==='IW-STUDY-NORTH'){
        // From shower to office: plaster, Leier, plaster, resilient lining cavity,
        // then one Silentboard. No additional full-wall collision solid.
        boxes.forEach((box,i)=>expect(box.maximumWorld.z-box.minimumWorld.z).toBeCloseTo([0.015,0.100,0.015,0.045,0.0125][i],5));
        boxes.slice(1).forEach((box,i)=>expect(box.minimumWorld.z).toBeCloseTo(boxes[i].maximumWorld.z,5));
        expect(meshes.filter(mesh=>mesh.metadata?.acousticMaterial==='gypsum-board')).toHaveLength(1);
        const cavity=meshes.find(mesh=>mesh.metadata?.acousticMaterial==='mineral-wool')!;
        expect(cavity.metadata).toMatchObject({acousticAssembly:'H200',acousticWall:'AK-03',acousticThicknessMm:45});
        expect(cavity.checkCollisions).toBe(false);
      }
    }
    const mirror=scene.meshes.find(m=>m.name.includes('MIRROR · vysoké zrkadlo'))!;
    mirror.computeWorldMatrix(true);
    expect(mirror.getBoundingInfo().boundingBox.maximumWorld.x).toBeCloseTo(sceneXM(23367-13),5);
    const obstacles=scene.meshes.filter(mesh=>mesh.checkCollisions && (
      mesh.name.startsWith('Vnútorná stena ') ||
      mesh.name.startsWith(OFFICE_FITOUT.id) || mesh.name.startsWith(BATHROOM_FITOUT.id)
    ) && !mesh.metadata?.doorId);
    for(const prefix of ['Vnútorná stena ',OFFICE_FITOUT.id,BATHROOM_FITOUT.id]) {
      expect(obstacles.filter(mesh=>mesh.name.startsWith(prefix)).length,prefix).toBeGreaterThan(0);
    }
    for(const obstacle of obstacles) obstacle.computeWorldMatrix(true);
    for(const id of ['DOOR-102-104','DOOR-102-105']) {
      const spec=INTERIOR_DOORS.find(door=>door.id===id)!;
      const registration=doors.find(door=>door.id===id)!;
      const leaf=scene.meshes.find(mesh=>mesh.metadata?.doorId===id&&mesh.name.includes('animované krídlo'))!;
      const hinge=leaf.parent as TransformNode;
      const movingParts=scene.meshes.filter(mesh=>mesh.parent===hinge);
      expect(movingParts.filter(part=>part.name.includes('kľučka'))).toHaveLength(2);
      expect(hinge.position.x).toBeCloseTo(sceneXM(spec.wallSpanMm[1]),6);
      expect(hinge.position.z).toBeCloseTo(sceneZM(id==='DOOR-102-104'?5481:6751.5),6);
      registration.apply(0,0);
      leaf.computeWorldMatrix(true);
      if(id==='DOOR-102-105') {
        expect(leaf.getBoundingInfo().boundingBox.centerWorld.z).toBeCloseTo(sceneZM(7101.5),6);
      }
      for(let step=0;step<=18;step++) {
        registration.apply(step/18,0);
        for(const part of movingParts) {
          part.computeWorldMatrix(true);
          for(const obstacle of obstacles) {
            expect(part.intersectsMesh(obstacle,true),`${id}: ${part.name} clears ${obstacle.name} at ${step*5} degrees`).toBe(false);
          }
        }
      }
      registration.apply(0,0);
    }
  } finally { scene.dispose();engine.dispose(); }
});
