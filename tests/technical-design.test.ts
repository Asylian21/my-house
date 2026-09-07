import { describe, expect, it } from 'vitest';
import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { Scene } from '@babylonjs/core/scene';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import { buildOpening, type OpeningBuildContext } from '../lib/babylon-openings';
import type { AnimatedDoorRegistration } from '../lib/babylon-doors';
import { HOUSE } from '../lib/twin-active-house';
import { SCENE_CENTER_MM } from '../lib/twin-render-frame';
import { INTERIOR_ROOMS, roomAreaM2 } from '../lib/twin-interior';
import { BATHROOM_FITOUT, TECHNICAL_HEATING_FITOUT as heating, WC_FITOUT } from '../lib/technical-design';
import generated from '../lib/plan-geometry.generated.json';
import { contains, floorBoundary, inside, intersects } from './floor-plan-geometry';
import { hull } from '../scripts/plan-documentation/extract';

type Point=[number,number];
const distance=(p:Point,a:Point,b:Point)=>{
  const dx=b[0]-a[0],dy=b[1]-a[1],t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy||1)));
  return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy);
};
function discHits(p:Point,r:number,poly:Point[]){
  let inside=false;
  for(let i=0,j=poly.length-1;i<poly.length;j=i++){
    const a=poly[i],b=poly[j];
    if(distance(p,a,b)<r-.5)return true;
    if((a[1]>p[1])!==(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])inside=!inside;
  }
  return inside;
}
function polysOverlap(a:Point[],b:Point[]){
  for(const p of [a,b])for(let i=0;i<p.length;i++){
    const v=p[i],w=p[(i+1)%p.length],nx=-(w[1]-v[1]),ny=w[0]-v[0];
    const aa=a.map(q=>q[0]*nx+q[1]*ny),bb=b.map(q=>q[0]*nx+q[1]*ny);
    if(Math.min(Math.max(...aa),Math.max(...bb))-Math.max(Math.min(...aa),Math.min(...bb))<=.1*Math.hypot(nx,ny))return false;
  }
  return true;
}

describe('Service core dimensional and access contracts',()=>{
  it('has a continuous 550 mm access path to storage and tank, including linings, nozzles and raised bases',()=>{
    const floors=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-07')!.rectsMm,edges=floorBoundary([...floors]);
    const obstacles=generated.meshes.filter(m=>(m.name.startsWith('TECHNICAL')||m.name.startsWith('1.07 ·'))&&m.z0<1850&&m.z1>20
      &&(!m.name.includes('BUFFER-TANK')||/hrdlo|teplomer|ciferník/.test(m.name)));
    const rectDistance=(p:Point,r:typeof obstacles[number]['rect'])=>Math.hypot(Math.max(r.x0-p[0],0,p[0]-r.x1),Math.max(r.y0-p[1],0,p[1]-r.y1));
    const routes:Point[][]=[[[26500,10350],[26050,9560],[25955,9490],[25605,9355],[25480,9275],[25310,9210],[25280,9200]],[[26500,10350],[26170,10020]]];
    // Distance is 1-Lipschitz: a 0.5 mm margin and samples <=1 mm apart
    // also protect every point between samples, rather than only grid nodes.
    for(const route of routes)for(let i=1;i<route.length;i++){
      const a=route[i-1],b=route[i],steps=Math.ceil(Math.hypot(a[0]-b[0],a[1]-b[1]));
      for(let j=0;j<=steps;j++){
        const p:Point=[a[0]+(b[0]-a[0])*j/steps,a[1]+(b[1]-a[1])*j/steps];
        const clear=Math.min(Math.hypot(p[0]-heating.accumulator.centerMm.x,p[1]-heating.accumulator.centerMm.y)-heating.accumulator.outerDiameterMm/2,
          ...obstacles.map(m=>rectDistance(p,m.rect)),...edges.map(([x0,y0,x1,y1])=>distance(p,[x0,y0],[x1,y1])));
        expect(floors.some(r=>inside(r,...p))&&clear>=275.5,`550 mm route blocked at ${p}; radius clearance ${clear}`).toBe(true);
      }
    }
  });
  it('enlarges the WC without overlapping room floors or reducing full-size laundry appliances',()=>{
    const wc=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-06')!;
    expect(roomAreaM2(wc)).toBeCloseTo(2.7522,6);
    const tech=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-07')!;
    expect(roomAreaM2(tech)).toBeCloseTo(9.335177,6);
    const floors=INTERIOR_ROOMS.flatMap(r=>r.rectsMm.map(rect=>({id:r.id,rect})));
    floors.forEach((a,i)=>floors.slice(i+1).forEach(b=>expect(intersects(a.rect,b.rect),`${a.id}/${b.id}`).toBe(false)));
    for(const a of BATHROOM_FITOUT.builtIn.appliances){
      expect(a.footprintMm.x1-a.footprintMm.x0).toBe(600);
      expect(a.footprintMm.y1-a.footprintMm.y0).toBe(600);
      expect(contains(BATHROOM_FITOUT.builtIn.footprintMm,a.footprintMm)).toBe(true);
    }
    const sanitary=generated.meshes.filter(m=>m.name.startsWith(WC_FITOUT.id));
    expect(sanitary.length).toBeGreaterThan(10);
    for(const m of sanitary)expect(intersects(WC_FITOUT.clearFloorRectMm,m.rect),m.name).toBe(false);
  });
  it('keeps the real boiler assembly inside the catalogue envelope and the tank body at its verified size',()=>{
    const boiler=generated.meshes.filter(m=>m.name.startsWith(heating.id)&&!m.name.includes('BUFFER-TANK'));
    expect(boiler.length).toBeGreaterThan(30);
    for(const m of boiler){
      expect(contains(heating.boiler.assemblyFootprintMm,m.rect),m.name).toBe(true);
      expect(m.z1,m.name).toBeLessThanOrEqual(1441.1);
    }
    const tank=generated.meshes.find(m=>m.name.endsWith('akumulačná nádrž 1000 l'))!;
    expect(tank.rect.x1-tank.rect.x0).toBe(1106);
    expect(tank.rect.y1-tank.rect.y0).toBe(1106);
    expect(generated.meshes.find(m=>m.name.endsWith('horné izolované veko'))!.z1).toBe(1913);
  });
  it('opens both transport leaves outward through a collision-free sweep and passes the upright insulated tank',()=>{
    const engine=new NullEngine({renderWidth:128,renderHeight:128,textureSize:128,deterministicLockstep:false,lockstepMaxSteps:1}),scene=new Scene(engine);
    scene.useRightHandedSystem=true;
    const material=new PBRMaterial('transport-test',scene),doors:AnimatedDoorRegistration[]=[];
    const identity:OpeningBuildContext['register']=mesh=>mesh;
    const context:OpeningBuildContext={scene,materials:new Proxy({} as OpeningBuildContext['materials'],{get:()=>material}),register:identity,realisticOnly:identity,castShadow:identity,appearance:mesh=>mesh,registerAnimatedDoor:d=>doors.push(d)};
    try{
      const opening=HOUSE.facades.east.openings.find(o=>o.id==='EAST-03')!;
      buildOpening(context,{name:opening.id,axis:'X',faceMm:HOUSE.facades.east.faceXmm,centerMm:opening.startYmm+opening.widthMm/2,widthMm:opening.widthMm,heightMm:opening.heightMm,sillMm:0,outward:1,wallThicknessMm:530,kind:'door',frameMaterial:material,curtains:false,interaction:{id:opening.id,label:'Transport',layout:'DOUBLE_LEAF_OUTWARD'}});
      expect(doors).toHaveLength(1);
      const leaves=scene.meshes.filter(m=>m.metadata?.dynamicCameraOccluder&&m.name.includes('transportné krídlo'));
      expect(leaves).toHaveLength(2);
      const shape=(mesh:typeof leaves[number])=>{
        const matrix=mesh.computeWorldMatrix(true),v=mesh.getVerticesData('position')!,points:Point[]=[];let bottom=Infinity,top=-Infinity;
        for(let i=0;i<v.length;i+=3){const p=Vector3.TransformCoordinates(new Vector3(v[i],v[i+1],v[i+2]),matrix);points.push([p.x*1000+SCENE_CENTER_MM.x,SCENE_CENTER_MM.y-p.z*1000]);bottom=Math.min(bottom,p.y*1000);top=Math.max(top,p.y*1000);}
        return {name:mesh.name,polygon:hull(points) as Point[],bottom,top};
      };
      const frames=scene.meshes.filter(m=>m.name.includes('zárubňa')).map(shape);
      for(let step=0;step<=180;step++){
        doors[0].apply(step/180,0);
        for(const leaf of leaves.map(shape))for(const frame of frames){
          if(leaf.top>frame.bottom+.1&&leaf.bottom<frame.top-.1)expect(polysOverlap(leaf.polygon,frame.polygon),`${leaf.name}/${frame.name} at ${step/2} degrees`).toBe(false);
        }
      }
      expect(leaves.map(shape).every(s=>Math.max(...s.polygon.map(p=>p[0]))>HOUSE.facades.east.faceXmm)).toBe(true);
      const staticObstacles=generated.meshes.filter(m=>m.z1>100.1&&m.z0<2013&&m.rect.x1>24000&&m.rect.y1>9000&&m.rect.y0<11200&&!m.name.includes('EAST-03')&&!m.name.includes('BUFFER-TANK')).map(m=>({name:m.name,polygon:m.polygon.split(' ').map(pair=>{const [x,y]=pair.split(',').map(Number);return [x,-y] as Point;})}));
      const openDoorObstacles=scene.meshes.map(shape).filter(m=>m.top>100.1&&m.bottom<2013);
      const route:Point[]=[[29000,10200],[26120,10200],[26000,10100],[25104,10100],[25104,10020]];
      for(let i=1;i<route.length;i++){
        const a=route[i-1],b=route[i],steps=Math.ceil(Math.hypot(a[0]-b[0],a[1]-b[1])/10);
        for(let j=0;j<=steps;j++){
          const p:Point=[a[0]+(b[0]-a[0])*j/steps,a[1]+(b[1]-a[1])*j/steps];
          for(const obstacle of [...staticObstacles,...openDoorObstacles])expect(discHits(p,553,obstacle.polygon),`Tank at ${p} hits ${obstacle.name}`).toBe(false);
        }
      }
    }finally{scene.dispose();engine.dispose();}
  },30000);
});
