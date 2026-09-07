import { readFileSync } from 'node:fs';
import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Scene } from '@babylonjs/core/scene';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { buildLivingDiningFitout, createInteriorMaterials, type InteriorBuildContext } from '../lib/babylon-interior';
import { matchingSource, sourceRestBounds } from '../lib/babylon-archviz';
import { LIVING_DINING_FITOUT } from '../lib/twin-interior';
import { sceneXM, sceneZM } from '../lib/twin-render-frame';

describe('tailored living-room sofa',()=>{
  let engine:NullEngine, scene:Scene;
  beforeAll(()=>{
    engine=new NullEngine();scene=new Scene(engine);
    const material=(name:string)=>new PBRMaterial(name,scene);
    const context:InteriorBuildContext={scene,anisotropy:1,
      wall:material('wall'),soffit:material('soffit'),glassFrame:material('frame'),
      chimneyMetal:material('metal'),timber:material('timber'),
      register:()=>{},realisticOnly:()=>{},castShadow:()=>{},
    };
    buildLivingDiningFitout(context,createInteriorMaterials(context));
  });
  afterAll(()=>{scene.dispose();engine.dispose();});

  it('has flat seats, softened edges and upholstery entirely inside the original sofa envelope',()=>{
    const parts=scene.meshes.filter(mesh=>mesh.name.includes('SOFA-L · TAILORED'));
    const seats=parts.filter(mesh=>mesh.name.includes('sedák'));
    expect(seats).toHaveLength(4);
    for(const seat of seats){
      const positions=seat.getVerticesData('position')!,normals=seat.getVerticesData('normal')!;
      const flatTop=[];
      for(let i=0;i<positions.length;i+=3)if(normals[i+1]>.999)flatTop.push([positions[i],positions[i+2]]);
      const b=seat.getBoundingInfo().boundingBox;
      // A real planar sitting surface covers most of each cushion, unlike a capsule.
      for(const [axis,dimension] of [[0,b.extendSize.x*2],[1,b.extendSize.z*2]] as const){
        const coords=flatTop.map(p=>p[axis]);
        expect(Math.max(...coords)-Math.min(...coords)).toBeGreaterThan(dimension*.85);
      }
      seat.computeWorldMatrix(true);
      expect(seat.getBoundingInfo().boundingBox.maximumWorld.y).toBeCloseTo(LIVING_DINING_FITOUT.sofa.seatHeightMm/1000,4);
      expect((seat.material as PBRMaterial).roughness).toBe(.99);
    }
    const {mainRectMm:main,chaiseRectMm:chaise}=LIVING_DINING_FITOUT.sofa;
    for(const part of parts){
      part.computeWorldMatrix(true);
      const b=part.getBoundingInfo().boundingBox;
      expect(b.minimumWorld.x,part.name).toBeGreaterThanOrEqual(sceneXM(chaise.x0)-.001);
      expect(b.maximumWorld.x,part.name).toBeLessThanOrEqual(sceneXM(main.x1)+.001);
      expect(b.minimumWorld.z,part.name).toBeGreaterThanOrEqual(sceneZM(main.y1)-.001);
      expect(b.maximumWorld.z,part.name).toBeLessThanOrEqual(sceneZM(main.y0)+.001);
      expect(part.checkCollisions).toBe(false);
      expect(part.isPickable).toBe(true);
    }
    const guards=scene.meshes.filter(m=>m.name.startsWith('LIVING-103-SOFA-L')&&m.metadata?.walkCollisionOnly);
    expect(guards).toHaveLength(3); // Two sofa volumes and the separate coffee-table envelope.
    expect(guards.every(m=>m.checkCollisions&&!m.isVisible)).toBe(true);
  });

  it('rejects the shipped capsule upholstery without losing the still-valid rug and table exports',()=>{
    const sources=scene.meshes.map(mesh=>({mesh,...sourceRestBounds(mesh)}));
    const obsolete:string[]=[];
    const retained:string[]=[];
    for(const file of ['01','02','03','04']){
      const bytes=readFileSync(new URL(`../public/assets/archviz/dom-interior-${file}.glb`,import.meta.url));
      const gltf=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString()) as {
        nodes:{extras?:{source_name?:string;source_id?:string;source_bounds_mm?:string}}[];
      };
      for(const {extras} of gltf.nodes){
        const name=extras?.source_name;
        if(!name?.startsWith('LIVING-103-SOFA-L'))continue;
        if(/vankúš|podrúčka|chrbtové jadro|skrytá nízka báza/.test(name)){
          expect(matchingSource(sources,extras!),name).toBeNull();
          obsolete.push(name);
        }else if(/koberec|oválny konferenčný stolík/.test(name)){
          expect(matchingSource(sources,extras!),name).not.toBeNull();
          retained.push(name);
        }
      }
    }
    expect(obsolete.length).toBeGreaterThanOrEqual(10);
    expect(retained).toHaveLength(3);
  });
});
