import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Scene } from '@babylonjs/core/scene';
import { describe, expect, it } from 'vitest';
import { ACOUSTIC_ASSEMBLY, acousticMeshInfo, acousticWallLayers } from '../lib/acoustic-walls';
import { createConcept, DEFAULT_CONCEPT } from '../lib/floor-plan-concept';
import { ACTIVE_ACOUSTIC_WALLS, INTERIOR_RENDER_WALLS, INTERIOR_WALL_HEIGHT_MM } from '../lib/twin-interior';
import { PLAN_ITEM_BY_ID, unionBounds } from '../lib/plan-documentation';
import { INTERIOR_WALL_MESHES, WALL_SOLIDS, WALL_TYPES_USED, interiorWallClass } from '../lib/plan-export';
import { buildInterior } from '../lib/babylon-interior';
import { sceneXM, sceneZM } from '../lib/twin-render-frame';

describe('SA30 acoustic wall revision in C/B/B', () => {
  it('keeps the two approved footprints and the 1099 mm hallway opening', () => {
    expect(ACTIVE_ACOUSTIC_WALLS).toHaveLength(2);
    const south=ACTIVE_ACOUSTIC_WALLS.find(w=>w.mark==='AK-02')!;
    const north=ACTIVE_ACOUSTIC_WALLS.find(w=>w.mark==='AK-01')!;
    expect(south.rectMm).toEqual({x0:14943,x1:15243,y0:3504,y1:6552});
    expect(north.rectMm).toEqual({x0:14943,x1:15243,y0:7651,y1:10699});
    expect(north.rectMm.y0-south.rectMm.y1).toBe(1099);
    for(const wall of ACTIVE_ACOUSTIC_WALLS){
      expect(wall.layers.map(l=>l.rectMm.x1-l.rectMm.x0)).toEqual([100,100,100]);
      expect(wall.layers.map(l=>l.rectMm.x0)).toEqual([14943,15043,15143]);
      expect(unionBounds(wall.layers.map(l=>l.rectMm))).toEqual(wall.rectMm);
    }
    const historical=createConcept({...DEFAULT_CONCEPT,layout:'private'});
    expect(historical.walls.flatMap(acousticWallLayers)).toEqual([]);
  });

  it('exports whole 300 mm assemblies while hatching their 100 mm ceramic leaves as masonry', () => {
    for(const wall of ACTIVE_ACOUSTIC_WALLS){
      const item=PLAN_ITEM_BY_ID.get(wall.mark)!;
      expect(item.meshes).toHaveLength(3);
      expect(item.rect).toEqual(wall.rectMm);
      const solids=WALL_SOLIDS.filter(s=>s.id===wall.mark);
      expect(solids).toHaveLength(1);
      expect(solids[0].thickness).toBe(300);
      expect(solids[0].type.code).toBe('SA30');
    }
    const layers=INTERIOR_WALL_MESHES.filter(w=>acousticMeshInfo(w.mesh.name));
    expect(layers).toHaveLength(6);
    expect(layers.filter(w=>interiorWallClass(w.mesh,w.kind)==='partition')).toHaveLength(4);
    expect(layers.filter(w=>interiorWallClass(w.mesh,w.kind)==='mineral-wool')).toHaveLength(2);
    expect(WALL_TYPES_USED.find(w=>w.type.code==='SA30')?.range).toBe('300');
  });

  it('builds six real layers at the approved faces and keeps collision on both masonry leaves', () => {
    const engine=new NullEngine(),scene=new Scene(engine),material=new PBRMaterial('test',scene);
    try {
      buildInterior({scene,livingLayout:'B',heatingLayout:'B',anisotropy:1,wall:material,soffit:material,glassFrame:material,chimneyMetal:material,timber:material,register:m=>m,realisticOnly:m=>m,castShadow:m=>m});
      const meshes=scene.meshes.filter(m=>m.metadata?.acousticAssembly===ACOUSTIC_ASSEMBLY.code);
      expect(meshes).toHaveLength(6);
      for(const wall of INTERIOR_RENDER_WALLS)for(const layer of acousticWallLayers(wall)){
        const mesh=meshes.find(m=>m.metadata.sourceWallId===wall.id&&m.metadata.acousticLayer===layer.id)!;
        expect(mesh).toBeDefined();
        mesh.computeWorldMatrix(true);
        const b=mesh.getBoundingInfo().boundingBox,r=layer.rectMm;
        expect(b.minimumWorld.x).toBeCloseTo(sceneXM(r.x0),5);
        expect(b.maximumWorld.x).toBeCloseTo(sceneXM(r.x1),5);
        expect(b.minimumWorld.z).toBeCloseTo(sceneZM(r.y1),5);
        expect(b.maximumWorld.z).toBeCloseTo(sceneZM(r.y0),5);
        expect(b.minimumWorld.y).toBeCloseTo(0,5);
        expect(b.maximumWorld.y).toBeCloseTo(INTERIOR_WALL_HEIGHT_MM/1000,5);
        expect(mesh.checkCollisions).toBe(layer.material==='masonry');
      }
      expect(scene.meshes.some(m=>/^Vnútorná stena C-OPEN-HALL-[NS] · nosná/.test(m.name))).toBe(false);
    } finally {scene.dispose();engine.dispose();}
  });
});
