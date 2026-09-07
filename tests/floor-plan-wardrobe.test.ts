import { describe, expect, it } from 'vitest';
import { area, createConcept, DEFAULT_CONCEPT as BASE_DEFAULT, rect } from '../lib/floor-plan-concept';
import { INTERIOR_ROOMS, INTERIOR_WALLS, type RectMm } from '../lib/twin-interior';
import { HOUSE } from '../lib/twin-site';

const DEFAULT_CONCEPT={...BASE_DEFAULT,layout:'wardrobe' as const};
const intersects=(a:RectMm,b:RectMm)=>a.x0<b.x1&&a.x1>b.x0&&a.y0<b.y1&&a.y1>b.y0;
const inside=(r:RectMm,x:number,y:number)=>x>=r.x0&&x<=r.x1&&y>=r.y0&&y<=r.y1;
describe('walk-through wardrobe study B',()=>{
  it('has real storage, exact clearances and no extra private hall',()=>{
    const m=createConcept(DEFAULT_CONCEPT);
    expect(m.privateHallArea).toBe(0);
    expect(m.vestibule).toEqual([]);
    expect(m.dressingAisle).toBe(1400);
    expect(area([m.dressing!])).toBeCloseTo(7.72);
    expect(m.storageLength).toBe(2860);
    expect(m.storageRuns[1].x0-m.storageRuns[0].x1).toBe(1000);
    for(const bank of m.storageRuns){expect(bank.y1-bank.y0).toBe(600);expect(m.doors.every(d=>d.axis!=='X'||d.startMm+d.widthMm<=bank.x0||d.startMm>=bank.x1)).toBe(true);}
    expect(m.bedroomArea).toBeCloseTo(11.6379);
    expect(m.sideClearance).toBe(607);
    expect(m.footClearance).toBe(1660);
  });
  it('preserves the canonical model but explicitly identifies the changed bearing walls',()=>{
    const before=JSON.stringify({HOUSE,INTERIOR_ROOMS,INTERIOR_WALLS});
    const m=createConcept(DEFAULT_CONCEPT);
    expect(m.structuralChanges.map(w=>w.id)).toEqual(['IW-GARAGE-NORTH','IW-GARAGE-LOGGIA']);
    for(const old of INTERIOR_WALLS.filter(w=>w.role==='LOAD_BEARING'&&!m.structuralChanges.some(c=>c.id===w.id))) expect(m.walls.find(w=>w.id===old.id)?.rectMm).toEqual(old.rectMm);
    expect(JSON.stringify({HOUSE,INTERIOR_ROOMS,INTERIOR_WALLS})).toBe(before);
  });
  it('keeps rooms, cabinets, windows and doors valid throughout the controls',()=>{
    for(let expansion=0;expansion<=600;expansion+=50) for(const wardrobeDepth of [2000,2200]) {
      const m=createConcept({...DEFAULT_CONCEPT,expansion,wardrobeDepth});
      for(let i=0;i<m.rooms.length;i++)for(let j=i+1;j<m.rooms.length;j++)for(const a of m.rooms[i].rectsMm)for(const b of m.rooms[j].rectsMm)expect(intersects(a,b),`${m.rooms[i].number}/${m.rooms[j].number}`).toBe(false);
      for(const r of m.storageRuns) expect(inside(m.dressing!,r.x0,r.y0)&&inside(m.dressing!,r.x1,r.y1)).toBe(true);
      const east=m.doors.find(d=>d.id==='B-HALL-DRESSING')!;
      expect(east.startMm).toBeGreaterThanOrEqual(6560);
      expect(east.startMm+east.widthMm).toBeLessThanOrEqual(Math.min(7601,m.dressing!.y1));
      const bedDoor=m.doors.find(d=>d.id==='B-DRESSING-BED')!;
      expect(bedDoor.motion).toBe('POCKET_SLIDING');
      expect(bedDoor.startMm+bedDoor.widthMm+850).toBeLessThan(m.suiteRight);
      expect(m.frontWindowStart).toBeGreaterThan(m.suiteRight+140);
      expect(m.frontWindowStart+750).toBeLessThan(17140);
      expect(m.suiteRight+140).toBeLessThan(15840);
      const zone=m.rooms.find(r=>r.number==='1.10')!.rectsMm[0];
      expect(inside(zone,m.bed.x0,m.bed.y0)&&inside(zone,m.bed.x1,m.bed.y1)).toBe(true);
    }
  });
  it('makes the smaller bedroom and optional terrace conversion measurable',()=>{
    const normal=createConcept(DEFAULT_CONCEPT);
    const tight=createConcept({...DEFAULT_CONCEPT,wardrobeDepth:2200,bedWidth:2200});
    expect(tight.sideClearance).toBe(307);
    expect(normal.garageDepth).toBe(7195);
    expect(area(normal.rooms.find(r=>r.number==='1.12')!.rectsMm)).toBeCloseTo(28.04611);
    expect(normal.convertedTerraceArea).toBeCloseTo(5.659896);
    const terrace=createConcept({...DEFAULT_CONCEPT,encloseLoggia:false,garageConnected:false});
    expect(terrace.garageDepth).toBe(5245);
    expect(terrace.convertedTerraceArea).toBe(0);
    expect(terrace.doors.some(d=>d.id==='B-GARAGE-DRESSING')).toBe(false);
  });
  it('provides a 440mm walking path from bedside through the wardrobe into the bathroom',()=>{
    for(const expansion of [0,600]) {
      const m=createConcept({...DEFAULT_CONCEPT,expansion,garageConnected:false});
      const floors=m.rooms.filter(r=>['1.10','1.11','1.14'].includes(r.number)).flatMap(r=>r.rectsMm);
      const privateDoors=m.doors.filter(d=>['B-DRESSING-BED','B-DRESSING-BATH'].includes(d.id));
      for(const d of privateDoors)floors.push(rect(d.startMm,d.wallSpanMm[0],d.startMm+d.widthMm,d.wallSpanMm[1]));
      const bathDoor=privateDoors.find(d=>d.id==='B-DRESSING-BATH')!;
      const obstacles=[...m.storageRuns,m.bed,...Object.values(m.fixtures),rect(bathDoor.startMm-10,4674,bathDoor.startMm+10,5474)];
      const offsets=Array.from({length:16},(_,i)=>[220*Math.cos(i*Math.PI/8),220*Math.sin(i*Math.PI/8)]);
      const fits=(x:number,y:number)=>offsets.every(([dx,dy])=>floors.some(r=>inside(r,x+dx,y+dy))&&!obstacles.some(r=>inside(r,x+dx,y+dy)));
      const queue:[number,number][]=[[14000,9000]], seen=new Set(['14000:9000']);let reached=false;
      for(let i=0;i<queue.length;i++) {
        const [x,y]=queue[i];
        if(Math.abs(x-13200)<=50&&Math.abs(y-4400)<=50){reached=true;break;}
        for(const [dx,dy] of [[50,0],[-50,0],[0,50],[0,-50]]){const nx=x+dx,ny=y+dy,key=`${nx}:${ny}`;if(!seen.has(key)&&fits(nx,ny)){seen.add(key);queue.push([nx,ny]);}}
      }
      expect(reached).toBe(true);
    }
  });
});
