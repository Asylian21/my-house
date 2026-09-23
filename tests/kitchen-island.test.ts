import { readFileSync } from 'node:fs';
import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import { Ray } from '@babylonjs/core/Culling/ray';
import { Scene } from '@babylonjs/core/scene';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { buildInterior } from '../lib/babylon-interior';
import { matchingSource, sourceRestBounds } from '../lib/babylon-archviz';
import { INTERIOR_DOORS, KITCHEN_DESIGN, KITCHEN_ISLAND, KITCHEN_RUN, type RectMm } from '../lib/twin-interior';
import { KITCHEN_RUN as archivedKitchen } from '../lib/twin-interior-baseline';
import { LIVING_LAYOUTS } from '../lib/twin-living-layouts';
import { PLAN_ITEM_BY_ID } from '../lib/plan-documentation';
import { swingHits } from './floor-plan-geometry';

const bounds=(mesh:Scene['meshes'][number]):RectMm=>{
  mesh.computeWorldMatrix(true);
  const b=mesh.getBoundingInfo().boundingBox;
  return {x0:b.minimumWorld.x*1000+15200,x1:b.maximumWorld.x*1000+15200,
    y0:10800-b.maximumWorld.z*1000,y1:10800-b.minimumWorld.z*1000};
};
const expectBounds=(actual:RectMm,expected:RectMm)=>{
  for(const key of ['x0','x1','y0','y1'] as const)expect(actual[key]).toBeCloseTo(expected[key],1);
};
const contains=(outer:RectMm,inner:RectMm)=>inner.x0>=outer.x0&&inner.x1<=outer.x1&&inner.y0>=outer.y0&&inner.y1<=outer.y1;
const overlaps=(a:RectMm,b:RectMm)=>a.x0<b.x1&&a.x1>b.x0&&a.y0<b.y1&&a.y1>b.y0;

describe('freestanding kitchen island in the active C/B/B design',()=>{
  let engine:NullEngine,scene:Scene;
  beforeAll(()=>{
    engine=new NullEngine();scene=new Scene(engine);
    const material=(name:string)=>new PBRMaterial(name,scene);
    buildInterior({scene,anisotropy:1,livingLayout:'B',heatingLayout:'B',
      wall:material('wall'),soffit:material('soffit'),glassFrame:material('frame'),
      chimneyMetal:material('metal'),timber:material('timber'),
      register:mesh=>mesh,realisticOnly:mesh=>mesh,castShadow:mesh=>mesh});
    scene.meshes.forEach(mesh=>mesh.computeWorldMatrix(true));
  });
  afterAll(()=>{scene.dispose();engine.dispose();});

  it('aligns with the opposite back worktop and retains the full wall-side run with a 900 mm passage',()=>{
    const top=KITCHEN_ISLAND.worktopRectMm;
    expect(top.x1-top.x0).toBe(2640);
    expect(top.y1-top.y0).toBe(920);
    expect(top.x1).toBe(KITCHEN_RUN.rectMm.x1+20);
    expect(KITCHEN_RUN.eastReturnRectMm.y1).toBe(archivedKitchen.peninsulaRectMm.y1);
    expect(KITCHEN_ISLAND.eastReturnWorktopRectMm.y1).toBe(archivedKitchen.peninsulaRectMm.y1+archivedKitchen.peninsulaOverhangMm);
    expect(KITCHEN_ISLAND.eastReturnWorktopRectMm.y1).toBe(top.y1);
    expect(KITCHEN_ISLAND.eastReturnWorktopRectMm.x0-top.x1).toBe(900);
    expect(KITCHEN_ISLAND.workAisleMm).toBe(1150);
    expect(top.x1-KITCHEN_DESIGN.sinkBowlRectMm.x1).toBeGreaterThanOrEqual(1300);
    expect(KITCHEN_DESIGN.sinkBowlRectMm.x0-top.x0).toBeGreaterThanOrEqual(700);
    expect(LIVING_LAYOUTS.B.fitout.sofa.mainRectMm.y0-top.y1).toBe(800);
    // Historical source remains the connected peninsula, without imposing its old appliance positions.
    expect(archivedKitchen.peninsulaRectMm.x1).toBe(27541);
  });

  it('uses the finished stone outlines for both visible 3D surfaces and their collision guards',()=>{
    const islandTop=scene.getMeshByName('KITCHEN-RUN · pracovná doska ostrovčeka · minerálny povrch')!;
    const islandGuard=scene.getMeshByName('KITCHEN-RUN · navigačný obrys ostrovčeka')!;
    const returnTop=scene.getMeshByName('KITCHEN-RUN · L-RETURN-EAST · minerálna doska pri okne')!;
    const returnGuard=scene.getMeshByName('KITCHEN-RUN · L-RETURN-EAST · hladký navigačný obrys')!;
    const backTop=scene.getMeshByName('KITCHEN-RUN · nika · minerálna pracovná doska')!;
    expect(bounds(islandTop).x1).toBeCloseTo(bounds(backTop).x1,1);
    expect(bounds(returnTop).y1).toBeCloseTo(bounds(islandTop).y1,1);
    for(const [top,guard,outline] of [[islandTop,islandGuard,KITCHEN_ISLAND.worktopRectMm],
      [returnTop,returnGuard,KITCHEN_ISLAND.eastReturnWorktopRectMm]] as const){
      expectBounds(bounds(top),outline);expectBounds(bounds(guard),outline);
      expect(guard.checkCollisions).toBe(true);expect(guard.isVisible).toBe(false);
    }
    for(const passage of [{x0:26022,x1:26920,y0:12700,y1:14200},
      {x0:24000,x1:26000,y0:11731,y1:12879}]){
      const blockers=scene.meshes.filter(mesh=>{
        if(!mesh.checkCollisions||mesh.metadata?.walkSurface)return false;
        const r=bounds(mesh),b=mesh.getBoundingInfo().boundingBox;
        return b.maximumWorld.y>.1&&b.minimumWorld.y<2&&overlaps(r,passage);
      });
      expect(blockers.map(mesh=>mesh.name)).toEqual([]);
    }
  });

  it('moves cooking to the wall and recesses the island sink through both the stone and cabinet',()=>{
    const hob=scene.getMeshByName('KITCHEN-RUN · varná doska · indukcia 800')!;
    expectBounds(bounds(hob),KITCHEN_DESIGN.hobRectMm);
    expect(contains(KITCHEN_DESIGN.backWorktopRectMm,KITCHEN_DESIGN.hobRectMm)).toBe(true);
    expect(overlaps(bounds(hob),KITCHEN_ISLAND.worktopRectMm)).toBe(false);
    expect(contains(KITCHEN_ISLAND.worktopRectMm,KITCHEN_DESIGN.sinkBowlRectMm)).toBe(true);
    const sink=KITCHEN_DESIGN.sinkBowlRectMm;
    const sample=(x:number,y:number)=>scene.pickWithRay(new Ray(
      new Vector3((x-15200)/1000,1,(10800-y)/1000),Vector3.Down(),1),
      mesh=>mesh.isVisible&&mesh.name.startsWith('KITCHEN-RUN')&&!mesh.metadata?.coordinationOnly);
    // A ray into the bowl must meet its recessed floor, not a painted black patch on a solid worktop.
    const bowlHit=sample(sink.x0+150,sink.y0+150);
    expect(bowlHit?.pickedMesh?.name).toContain('drez · zapustené dno');
    expect(bowlHit?.pickedPoint?.y).toBeCloseTo(.703,3);
    const stoneHit=sample(sink.x1+100,sink.y0+150);
    expect(stoneHit?.pickedMesh?.name).toContain('pracovná doska ostrovčeka');
    expect(stoneHit?.pickedPoint?.y).toBeCloseTo(.9,3);
    expect(.9-bowlHit!.pickedPoint!.y).toBeGreaterThan(.19);
    expect(.9-bowlHit!.pickedPoint!.y).toBeLessThanOrEqual(KITCHEN_DESIGN.sinkDepthMm/1000);
  });

  it('places a retracting-door oven at working height',()=>{
    const oven=scene.getMeshByName('KITCHEN-RUN · OVEN-ELEVATED · rúra so zasúvacím krídlom')!;
    const b=oven.getBoundingInfo().boundingBox;
    expect(b.minimumWorld.y*1000).toBeCloseTo(850,1);
    expect(b.maximumWorld.y*1000).toBeCloseTo(1445,1);
    expect(bounds(oven).x0).toBeGreaterThanOrEqual(KITCHEN_DESIGN.ovenTowerRectMm.x0);
    expect(bounds(oven).x1).toBeLessThanOrEqual(KITCHEN_DESIGN.ovenTowerRectMm.x1);
    expect(KITCHEN_DESIGN.oven.door).toBe('fully-retracting');
    expect(scene.meshes.some(mesh=>mesh.name.includes('OVEN-UNDER-HOB'))).toBe(false);
  });

  it('puts the dishwasher at the window end, separated from the sink, without obstructing the bypass or technical door',()=>{
    const dishwasher=KITCHEN_DESIGN.dishwasherRectMm,opened=KITCHEN_DESIGN.dishwasherOpenRectMm;
    const sinkModule=KITCHEN_DESIGN.islandModules.find(m=>m.kind==='sink-waste')!;
    const separatingModules=KITCHEN_DESIGN.islandModules.filter(m=>m.x0>=sinkModule.x1&&m.x1<=dishwasher.x0);
    expect(dishwasher.x1-dishwasher.x0).toBe(600);
    expect(dishwasher.x1).toBe(KITCHEN_RUN.peninsulaRectMm.x1-20);
    expect(dishwasher.x0-sinkModule.x1).toBe(600);
    expect(separatingModules).toHaveLength(1);
    expect(separatingModules[0].kind).toBe('drawers');
    expect(KITCHEN_RUN.dishwasherXmm).toEqual([dishwasher.x0,dishwasher.x1]);
    expect(contains(KITCHEN_RUN.peninsulaRectMm,dishwasher)).toBe(true);
    const front=scene.meshes.filter(mesh=>/^KITCHEN-RUN · DISHWASHER · umývačka \d+$/.test(mesh.name));
    expect(front).toHaveLength(1);
    const frontBounds=bounds(front[0]);
    expect(frontBounds.x0).toBeCloseTo(dishwasher.x0+2,1);
    expect(frontBounds.x1).toBeCloseTo(dishwasher.x1-2,1);
    expect(frontBounds.y0).toBeLessThan(KITCHEN_RUN.peninsulaRectMm.y0);
    expect(opened.x0).toBe(dishwasher.x0);
    expect(opened.x1).toBe(dishwasher.x1);
    expect(opened.y1).toBe(dishwasher.y0);
    expect(opened.y1-opened.y0).toBe(600);
    expect(opened.y0-KITCHEN_RUN.rectMm.y1).toBe(580);
    const backTop=bounds(scene.getMeshByName('KITCHEN-RUN · nika · minerálna pracovná doska')!);
    // The open door leaves an appliance-use zone to the stone, not a second through-route.
    expect(opened.y0-backTop.y1).toBeCloseTo(560,1);
    const oven=bounds(scene.getMeshByName('KITCHEN-RUN · OVEN-ELEVATED · rúra so zasúvacím krídlom')!);
    expect(oven.x1).toBeLessThan(opened.x0);
    expect(swingHits(INTERIOR_DOORS.find(door=>door.id==='DOOR-103-107')!,opened)).toBe(false);
    expect(overlaps(opened,{x0:KITCHEN_ISLAND.worktopRectMm.x1,x1:KITCHEN_ISLAND.eastReturnWorktopRectMm.x0,
      y0:KITCHEN_RUN.rectMm.y1,y1:KITCHEN_ISLAND.worktopRectMm.y1})).toBe(false);
  });

  it('uses textured natural oak throughout the cabinet elevations with one satin dark-stone finish across all three tops',()=>{
    const fronts=[
      'FRIDGE-600 · dubový blok 2026','OVEN-TOWER · horné dvierka 2026',
      'nika · zásuvky 1','horné skrinky · matná nika 2026',
      'ostrovček · zásuvková skrinka 1','DISHWASHER · umývačka 4',
      'ostrovček · plytké úložisko 1','L-RETURN-EAST · dvierka 1',
    ].map(name=>scene.getMeshByName(`KITCHEN-RUN · ${name}`)!.material as PBRMaterial);
    expect(fronts.every(front=>front===fronts[0])).toBe(true);
    expect(fronts[0].albedoTexture?.name).toContain('living-natural-oak-albedo.jpg');
    const tops=[
      'nika · minerálna pracovná doska','pracovná doska ostrovčeka · minerálny povrch',
      'L-RETURN-EAST · minerálna doska pri okne',
    ].map(name=>scene.getMeshByName(`KITCHEN-RUN · ${name}`)!.material as PBRMaterial);
    expect(tops.every(top=>top===tops[0])).toBe(true);
    expect(tops[0]).not.toBe(fronts[0]);
    expect(tops[0].albedoTexture?.name).toContain('stone-dark-albedo.jpg');
    expect(Math.max(tops[0].albedoColor.r,tops[0].albedoColor.g,tops[0].albedoColor.b)).toBeLessThan(.25);
    expect(tops[0].metallic).toBe(0);
    expect(tops[0].roughness).toBeGreaterThanOrEqual(.35);
  });

  it('fits the concealed canopy in its wall cabinet and leaves the cathedral ceiling free of an island chimney',()=>{
    const hood=scene.getMeshByName('KITCHEN-RUN · odsávač · servisná obálka')!;
    const r=bounds(hood),b=hood.getBoundingInfo().boundingBox;
    expect(r.x1-r.x0).toBeCloseTo(880,1);
    const cabinet={x0:KITCHEN_DESIGN.backModules[1],x1:KITCHEN_DESIGN.backModules[2],
      y0:KITCHEN_RUN.rectMm.y0,y1:KITCHEN_RUN.rectMm.y0+KITCHEN_RUN.upperCabinets.depthMm};
    expect(cabinet.x1-cabinet.x0).toBe(990);
    expect(contains(cabinet,r)).toBe(true);
    expect(b.minimumWorld.y).toBeCloseTo(1.52,3);
    expect(b.maximumWorld.y*1000).toBeLessThan(KITCHEN_RUN.upperCabinets.topMm);
    expect((r.x0+r.x1)/2).toBeCloseTo(KITCHEN_RUN.hobCenterXmm,1);
    expect((r.y0+r.y1)/2).toBeCloseTo((KITCHEN_DESIGN.hobRectMm.y0+KITCHEN_DESIGN.hobRectMm.y1)/2,1);
    const canopy=bounds(scene.getMeshByName('KITCHEN-RUN · odsávač · integrovaná spodná kazeta')!);
    expectBounds(canopy,r);
    expect(contains(cabinet,canopy)).toBe(true);
    expect(hood.metadata.ventilation).toBe('recirculation-with-top-return');
    const outlet=scene.getMeshByName('KITCHEN-RUN · odsávač · horná vratná mriežka')!;
    expect(outlet.getBoundingInfo().boundingBox.minimumWorld.y*1000).toBeCloseTo(KITCHEN_DESIGN.upperExtension.topMm,1);
    const extractors=scene.meshes.filter(mesh=>/KITCHEN-RUN.*odsávač/.test(mesh.name));
    expect(extractors.every(mesh=>!overlaps(bounds(mesh),KITCHEN_ISLAND.worktopRectMm))).toBe(true);
    expect(scene.meshes.some(mesh=>/KITCHEN-RUN.*komín/.test(mesh.name))).toBe(false);
  });

  it('documents the same island outline and rejects all old kitchen parts from ArchViz assets',()=>{
    const item=PLAN_ITEM_BY_ID.get('kitchen-island')!;
    expect(item.name).toBe('Kuchynský ostrovček');
    const top=item.meshes.find(mesh=>mesh.name.includes('pracovná doska'))!;
    expectBounds(top.rect,KITCHEN_ISLAND.worktopRectMm);
    expect(item.note).toMatch(/2\s640 × 920 mm/);
    const wallRun=PLAN_ITEM_BY_ID.get('kitchen-return')!;
    expectBounds(wallRun.meshes.find(mesh=>mesh.name.includes('doska pri okne'))!.rect,KITCHEN_ISLAND.eastReturnWorktopRectMm);
    const sources=scene.meshes.map(mesh=>({mesh,...sourceRestBounds(mesh)}));
    const oldKitchenParts:string[]=[];
    for(const file of ['01','02','03','04']){
      const bytes=readFileSync(new URL(`../public/assets/archviz/dom-interior-${file}.glb`,import.meta.url));
      const gltf=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString());
      for(const {extras} of gltf.nodes){
        const name=extras?.source_name;
        if(!name?.startsWith('KITCHEN-RUN'))continue;
        oldKitchenParts.push(name);
        expect(matchingSource(sources,extras),name).toBeNull();
      }
    }
    expect(oldKitchenParts.length).toBeGreaterThan(0);
  });
});
