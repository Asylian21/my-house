import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Scene } from '@babylonjs/core/scene';
import { describe, expect, it } from 'vitest';
import { OFFICE_ACOUSTIC_ASSEMBLY, acousticMeshInfo, acousticWallLayers } from '../lib/acoustic-walls';
import { createConcept, DEFAULT_CONCEPT } from '../lib/floor-plan-concept';
import { ACTIVE_ACOUSTIC_WALLS, INTERIOR_DOORS, INTERIOR_RENDER_WALLS, INTERIOR_WALL_HEIGHT_MM } from '../lib/twin-interior';
import { PLAN_ITEM_BY_ID, unionBounds } from '../lib/plan-documentation';
import { INTERIOR_WALL_MESHES, WALL_SOLIDS, WALL_TYPES_USED, interiorWallClass } from '../lib/plan-export';
import { buildInterior } from '../lib/babylon-interior';
import { sceneXM, sceneZM } from '../lib/twin-render-frame';

describe('SA30 and H200 acoustic walls in C/B/B', () => {
  it('keeps the two approved footprints and the 1099 mm hallway opening', () => {
    expect(ACTIVE_ACOUSTIC_WALLS).toHaveLength(3);
    const south=ACTIVE_ACOUSTIC_WALLS.find(w=>w.mark==='AK-02')!;
    const north=ACTIVE_ACOUSTIC_WALLS.find(w=>w.mark==='AK-01')!;
    expect(south.rectMm).toEqual({x0:14943,x1:15243,y0:3504,y1:6552});
    expect(north.rectMm).toEqual({x0:14943,x1:15243,y0:7651,y1:10699});
    expect(north.rectMm.y0-south.rectMm.y1).toBe(1099);
    for(const wall of ACTIVE_ACOUSTIC_WALLS.filter(w=>w.assembly.code==='SA30')){
      expect(wall.layers.map(l=>l.rectMm.x1-l.rectMm.x0)).toEqual([100,100,100]);
      expect(wall.layers.map(l=>l.rectMm.x0)).toEqual([14943,15043,15143]);
      expect(unionBounds(wall.layers.map(l=>l.rectMm))).toEqual(wall.rectMm);
    }
    const historical=createConcept({...DEFAULT_CONCEPT,layout:'private'});
    expect(historical.walls.flatMap(acousticWallLayers)).toEqual([]);
  });

  it('exports whole 300 mm assemblies while hatching their 100 mm ceramic leaves as masonry', () => {
    for(const wall of ACTIVE_ACOUSTIC_WALLS.filter(w=>w.assembly.code==='SA30')){
      const item=PLAN_ITEM_BY_ID.get(wall.mark)!;
      expect(item.meshes).toHaveLength(3);
      expect(item.rect).toEqual(wall.rectMm);
      const solids=WALL_SOLIDS.filter(s=>s.id===wall.mark);
      expect(solids).toHaveLength(1);
      expect(solids[0].thickness).toBe(300);
      expect(solids[0].type.code).toBe('SA30');
    }
    const layers=INTERIOR_WALL_MESHES.filter(w=>acousticMeshInfo(w.mesh.name));
    expect(layers).toHaveLength(12);
    expect(layers.filter(w=>interiorWallClass(w.mesh,w.kind)==='partition')).toHaveLength(5);
    expect(layers.filter(w=>interiorWallClass(w.mesh,w.kind)==='mineral-wool')).toHaveLength(3);
    expect(WALL_TYPES_USED.find(w=>w.type.code==='SA30')?.range).toBe('300');
  });

  it('exports the H200 leaves on the correct room sides inside one 200 mm dimension', () => {
    const wall=ACTIVE_ACOUSTIC_WALLS.find(w=>w.mark==='AK-03')!;
    expect(wall.assembly).toBe(OFFICE_ACOUSTIC_ASSEMBLY);
    expect(wall.layers.map(l=>l.rectMm.y1-l.rectMm.y0)).toEqual([12.5,12.5,45,15,100,15]);
    expect(wall.layers.map(l=>l.rectMm.y0)).toEqual([6402,6414.5,6427,6472,6487,6587]);
    expect(unionBounds(wall.layers.map(l=>l.rectMm))).toEqual(wall.rectMm);
    const item=PLAN_ITEM_BY_ID.get('AK-03')!;
    expect(item.meshes).toHaveLength(6);
    expect(wall.layers.slice(0,2).map(l=>l.material)).toEqual(['gypsum-board','gypsum-board']);
    expect(OFFICE_ACOUSTIC_ASSEMBLY.requiredRwDb).toBe(51);
    expect(OFFICE_ACOUSTIC_ASSEMBLY).not.toHaveProperty('declaredRwDb');
    expect(item.rect).toEqual(wall.rectMm);
    expect(item.name).toContain('H200');
    expect(WALL_SOLIDS.filter(w=>w.id==='AK-03')).toMatchObject([{thickness:200,type:{code:'H200'}}]);
    expect(WALL_TYPES_USED.find(w=>w.type.code==='H200')?.range).toBe('200');
    expect(INTERIOR_WALL_MESHES.filter(w=>interiorWallClass(w.mesh,w.kind)==='plaster')).toHaveLength(2);
  });

  it('builds twelve real layers at the selected faces with solid leaves and noncollidable cavities', () => {
    const engine=new NullEngine(),scene=new Scene(engine),material=new PBRMaterial('test',scene);
    try {
      buildInterior({scene,livingLayout:'B',heatingLayout:'B',anisotropy:1,wall:material,soffit:material,glassFrame:material,chimneyMetal:material,timber:material,register:m=>m,realisticOnly:m=>m,castShadow:m=>m});
      const meshes=scene.meshes.filter(m=>m.metadata?.acousticAssembly);
      expect(meshes).toHaveLength(12);
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
        expect(mesh.checkCollisions).toBe(layer.material!=='mineral-wool');
      }
      expect(scene.meshes.some(m=>/^Vnútorná stena C-OPEN-HALL-[NS] · nosná/.test(m.name))).toBe(false);
      const door=INTERIOR_DOORS.find(d=>d.id==='DOOR-102-105')!;
      const leaf=scene.meshes.find(m=>m.metadata?.doorId===door.id&&m.name.endsWith(' · animované krídlo'))!;
      leaf.computeWorldMatrix(true);
      const leafBounds=leaf.getBoundingInfo().boundingBox;
      expect(leafBounds.centerWorld.z).toBeCloseTo(sceneZM(7101.5),5);
      expect(leafBounds.maximumWorld.z-leafBounds.minimumWorld.z).toBeCloseTo(.7,5);
      const jambs=scene.meshes.filter(m=>m.name.startsWith(`${door.label} · `)&&m.name.endsWith('zárubňa'));
      expect(jambs).toHaveLength(2);
      expect(jambs.reduce((sum,m)=>sum+m.position.z,0)/2).toBeCloseTo(leafBounds.centerWorld.z,5);
    } finally {scene.dispose();engine.dispose();}
  });
});
