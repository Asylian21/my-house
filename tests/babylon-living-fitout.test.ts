import { readFileSync } from 'node:fs';
import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Scene } from '@babylonjs/core/scene';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { buildLivingDiningFitout, buildLivingFireplace, createInteriorMaterials, type InteriorBuildContext } from '../lib/babylon-interior';
import { matchingSource, sourceRestBounds } from '../lib/babylon-archviz';
import { LIVING_DINING_FITOUT, type RectMm } from '../lib/twin-interior';
import { LIVING_LAYOUTS } from '../lib/twin-living-layouts';
import { sceneXM, sceneZM } from '../lib/twin-render-frame';

const buildContext=(scene:Scene):InteriorBuildContext=>{
  const material=(name:string)=>new PBRMaterial(name,scene);
  return {scene,anisotropy:1,
    wall:material('wall'),soffit:material('soffit'),glassFrame:material('frame'),
    chimneyMetal:material('metal'),timber:material('timber'),
    register:()=>{},realisticOnly:()=>{},castShadow:()=>{},
  };
};
/** Plan-mm bounds of a mesh after its world matrix is applied. */
const planBounds=(mesh:Scene['meshes'][number]):RectMm=>{
  mesh.computeWorldMatrix(true);
  const b=mesh.getBoundingInfo().boundingBox;
  return {x0:b.minimumWorld.x*1000+15200,x1:b.maximumWorld.x*1000+15200,y0:10800-b.maximumWorld.z*1000,y1:10800-b.minimumWorld.z*1000};
};
const within=(rect:RectMm,outer:RectMm,tolerance=1)=>rect.x0>=outer.x0-tolerance&&rect.x1<=outer.x1+tolerance&&rect.y0>=outer.y0-tolerance&&rect.y1<=outer.y1+tolerance;

describe('tailored living-room sofa',()=>{
  let engine:NullEngine, scene:Scene;
  beforeAll(()=>{
    engine=new NullEngine();scene=new Scene(engine);
    const context=buildContext(scene);
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

describe('living layout B built from the same builders',()=>{
  let engine:NullEngine, sceneA:Scene, sceneB:Scene;
  beforeAll(()=>{
    engine=new NullEngine();
    for(const [layout,make] of [['A',(s:Scene)=>{sceneA=s;}],['B',(s:Scene)=>{sceneB=s;}]] as const){
      const scene=new Scene(engine);make(scene);
      const context=buildContext(scene),materials=createInteriorMaterials(context);
      buildLivingFireplace(context,materials,LIVING_LAYOUTS[layout].stove);
      buildLivingDiningFitout(context,materials,LIVING_LAYOUTS[layout]);
    }
  });
  afterAll(()=>{sceneA.dispose();sceneB.dispose();engine.dispose();});

  it('produces the same set of parts for both layouts, with variant B turned into its own envelopes',()=>{
    // Chair rows S/N (A) correspond to W/E (B): kitchen or wall side first.
    const names=(scene:Scene)=>scene.meshes.map(m=>m.name.replace(LIVING_LAYOUTS.A.stove.id,'STOVE').replace(LIVING_LAYOUTS.B.stove.id,'STOVE').replace(/pri krbe|pri presklení terasy/,'tower-0').replace(/pri zadnom okne|pri východnej stene/,'tower-1').replace(/DINING-CHAIR-[SW](\d)/,'CHAIR-ROW0-$1').replace(/DINING-CHAIR-[NE](\d)/,'CHAIR-ROW1-$1')).sort();
    expect(names(sceneB)).toEqual(names(sceneA));
    const B=LIVING_LAYOUTS.B, {sofa,tvWall,dining}=B.fitout;
    const visible=sceneB.meshes.filter(m=>m.isVisible&&!m.metadata?.walkCollisionOnly&&!m.metadata?.navigationGuard);
    const sofaEnvelope:RectMm={x0:Math.min(sofa.mainRectMm.x0,sofa.chaiseRectMm.x0),x1:Math.max(sofa.mainRectMm.x1,sofa.chaiseRectMm.x1),y0:sofa.mainRectMm.y0,y1:Math.max(sofa.mainRectMm.y1,sofa.chaiseRectMm.y1)};
    for(const part of visible.filter(m=>m.name.includes('SOFA-L · TAILORED')))expect(within(planBounds(part),sofaEnvelope),part.name).toBe(true);
    // The TV wall faces south: its carcass sits on the gable and only the screen, console and soundbar protrude into the room.
    for(const part of visible.filter(m=>m.name.startsWith('LIVING-103-TV-WALL'))){
      const bounds=planBounds(part);
      expect(within(bounds,{...tvWall.rectMm,y0:tvWall.rectMm.y0-120}),part.name).toBe(true);
      if(/skriňa/.test(part.name))expect(bounds.y0,part.name).toBeGreaterThanOrEqual(tvWall.rectMm.y0-1);
    }
    // The six-seat dining table runs north–south with three chairs on each long side and two pendants on its axis.
    const top=visible.find(m=>m.name.endsWith('klasický dubový stôl · doska'))!;
    const topBounds=planBounds(top);
    expect(topBounds.x1-topBounds.x0).toBeCloseTo(dining.tableDepthMm,0);
    expect(topBounds.y1-topBounds.y0).toBeCloseTo(dining.tableLengthMm,0);
    const seats=visible.filter(m=>/DINING-CHAIR-.. · klasický čalúnený sedák$/.test(m.name));
    expect(seats).toHaveLength(6);
    for(const seat of seats){
      const bounds=planBounds(seat);
      expect(bounds.y0).toBeGreaterThan(topBounds.y0);expect(bounds.y1).toBeLessThan(topBounds.y1);
      expect(Math.min(topBounds.x1,bounds.x1)-Math.max(topBounds.x0,bounds.x0),seat.name).toBeCloseTo(330,0);
    }
    const shades=visible.filter(m=>/závesné svietidlo \d · klasické tienidlo$/.test(m.name)).map(planBounds);
    expect(shades).toHaveLength(2);
    for(const shade of shades)expect((shade.x0+shade.x1)/2).toBeCloseTo(dining.tableCenterMm.x,0);
    expect(Math.abs((shades[0].y0+shades[0].y1)/2-(shades[1].y0+shades[1].y1)/2)).toBeCloseTo(dining.tableLengthMm/2,0);
    const shadesA=sceneA.meshes.filter(m=>/závesné svietidlo \d · klasické tienidlo$/.test(m.name)).map(planBounds);
    expect(shadesA).toHaveLength(2);
    expect(Math.abs((shadesA[0].x0+shadesA[0].x1)/2-(shadesA[1].x0+shadesA[1].x1)/2)).toBeCloseTo(LIVING_LAYOUTS.A.fitout.dining.tableLengthMm/2,0);
    // The stove is turned 45° toward the room: the curved glass door looks south-east from the centre.
    const glass=planBounds(visible.find(m=>m.name.startsWith(B.stove.id)&&m.name.includes('CURVED-GLASS'))!);
    expect((glass.x0+glass.x1)/2).toBeGreaterThan(B.stove.centerMm.x+60);
    expect((glass.y0+glass.y1)/2).toBeLessThan(B.stove.centerMm.y-60);
    const glassA=planBounds(sceneA.meshes.find(m=>m.name.startsWith(LIVING_LAYOUTS.A.stove.id)&&m.name.includes('CURVED-GLASS'))!);
    expect((glassA.x0+glassA.x1)/2).toBeGreaterThan(LIVING_LAYOUTS.A.stove.centerMm.x+60);
    expect(Math.abs((glassA.y0+glassA.y1)/2-LIVING_LAYOUTS.A.stove.centerMm.y)).toBeLessThan(30); // arc tessellation only
    for(const part of visible.filter(m=>m.name.startsWith(B.stove.id)&&!/FLUE|dymovod|svetlo|light/i.test(m.name))){
      const bounds=planBounds(part);
      expect(within(bounds,{x0:B.stove.footprintMm.x0-40,x1:B.stove.footprintMm.x1+100,y0:B.stove.footprintMm.y0-100,y1:B.stove.footprintMm.y1+40}),part.name).toBe(true);
    }
    for(const table of visible.filter(m=>/oválny konferenčný stolík/.test(m.name)))expect(within(planBounds(table),B.rugRectMm),table.name).toBe(true);
  });
});
