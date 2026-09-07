import { describe, expect, it } from 'vitest';
import { BED_LENGTH, createVestibuleConcept as createConcept, DEFAULT_CONCEPT, normalizeConcept, rect } from '../lib/floor-plan-concept';
import { INTERIOR_ROOMS, INTERIOR_WALLS, type RectMm } from '../lib/twin-interior';
import { HOUSE } from '../lib/twin-site';

const overlaps = (a:RectMm,b:RectMm) => a.x0<b.x1 && a.x1>b.x0 && a.y0<b.y1 && a.y1>b.y0;
const contains = (r:RectMm,x:number,y:number) => x>=r.x0 && x<=r.x1 && y>=r.y0 && y<=r.y1;

describe('2D conceptual reconfiguration',()=>{
  it('leaves the source envelope and every load-bearing wall intact',()=>{
    const before=JSON.stringify({HOUSE,INTERIOR_ROOMS,INTERIOR_WALLS});
    for(const expansion of [0,300,600]) {
      const model=createConcept({...DEFAULT_CONCEPT,expansion});
      for(const wall of INTERIOR_WALLS.filter(w=>w.role==='LOAD_BEARING')) {
        expect(model.walls.find(w=>w.id===wall.id)?.rectMm).toEqual(wall.rectMm);
      }
    }
    expect(JSON.stringify({HOUSE,INTERIOR_ROOMS,INTERIOR_WALLS})).toBe(before);
  });
  it('transfers room area without overlap or loss and keeps the original entrance',()=>{
    const baseline=createConcept(DEFAULT_CONCEPT);
    for(let expansion=0;expansion<=600;expansion+=50) {
      const model=createConcept({...DEFAULT_CONCEPT,expansion});
      expect(model.bedroomArea+model.kidGardenArea).toBeCloseTo(baseline.bedroomArea+baseline.kidGardenArea,8);
      expect(model.bedroomArea-baseline.bedroomArea).toBeCloseTo(expansion*2958/1e6,8);
      const room=model.rooms.find(r=>r.number==='1.10')!;
      for(const r of room.rectsMm) for(const other of model.rooms.filter(r=>r.number!=='1.10')) for(const o of other.rectsMm) expect(overlaps(r,o)).toBe(false);
      const entry=model.doors.find(d=>d.id==='DOOR-102-110')!;
      expect(entry.wallSpanMm).toEqual([15003,15143]);
      expect(model.vestibule[1].x1-model.vestibule[1].x0).toBe(999);
    }
  });
  it('fits the actual bed length without blocking glazing, wardrobes, or open entrance leaves',()=>{
    for(const expansion of [0,600]) for(const bedWidth of [1600,1800,2200]) for(const wardrobe of [false,true]) {
      const model=createConcept({...DEFAULT_CONCEPT,expansion,bedWidth,wardrobe});
      expect(model.bed.x1-model.bed.x0).toBe(BED_LENGTH);
      expect(model.bed.y1-model.bed.y0).toBe(bedWidth);
      expect(model.sideClearance).toBeGreaterThanOrEqual(900);
      expect(model.footClearance).toBeGreaterThanOrEqual(1060);
      expect(overlaps(model.bed,rect(11840,10699,14340,11200))).toBe(false);
      expect(overlaps(model.bed,rect(14273,7591,15073,7611))).toBe(false);
      if(wardrobe) expect(overlaps(model.bed,model.wardrobeRect)).toBe(false);
    }
  });
  it('connects the bedroom to its bathroom entirely inside the suite',()=>{
    // Flood-fill a 440 mm wide walking envelope on a 50 mm grid.
    // The shared hall and garage are deliberately excluded from traversable floor.
    for(const expansion of [0,600]) {
      const model=createConcept({...DEFAULT_CONCEPT,expansion,bedWidth:2200,garageConnected:false});
      const floors=[...model.vestibule,...model.rooms.filter(r=>['1.10','1.11'].includes(r.number)).flatMap(r=>r.rectsMm)];
      for(const door of model.doors.filter(d=>['DOOR-102-110','DOOR-102-111'].includes(d.id))) floors.push(door.axis==='X'?rect(door.startMm,door.wallSpanMm[0],door.startMm+door.widthMm,door.wallSpanMm[1]):rect(door.wallSpanMm[0],door.startMm,door.wallSpanMm[1],door.startMm+door.widthMm));
      const obstacles=[model.bed,model.wardrobeRect,rect(13980,3600,14780,5300),rect(15370,3550,16170,4000),rect(15945,4710,16355,5310)];
      const fits=(x:number,y:number)=>Array.from({length:16},(_,i)=>{const a=i*Math.PI/8;return [x+220*Math.cos(a),y+220*Math.sin(a)];}).every(([px,py])=>floors.some(r=>contains(r,px,py))&&!obstacles.some(r=>contains(r,px,py)));
      const queue:[[number,number]]=[[13900,7200]], seen=new Set(['13900:7200']);let reached=false;
      for(let i=0;i<queue.length;i++) {
        const [x,y]=queue[i];
        if(Math.abs(x-15450)<=50&&Math.abs(y-4450)<=50){reached=true;break;}
        for(const [dx,dy] of [[50,0],[-50,0],[0,50],[0,-50]]) {
          const nx=x+dx,ny=y+dy,key=`${nx}:${ny}`;
          if(!seen.has(key)&&fits(nx,ny)){seen.add(key);queue.push([nx,ny]);}
        }
      }
      expect(reached,`private path at expansion ${expansion}`).toBe(true);
    }
  });
  it('makes the garage compromise explicit and closes the old street-bedroom bathroom door',()=>{
    const connected=createConcept(DEFAULT_CONCEPT), disconnected=createConcept({...DEFAULT_CONCEPT,garageConnected:false});
    expect(connected.doors.some(d=>d.id==='DOOR-102-112')).toBe(true);
    expect(disconnected.doors.some(d=>d.id==='DOOR-102-112')).toBe(false);
    expect(disconnected.walls.some(w=>w.id==='CLOSED-GARAGE')).toBe(true);
    expect(connected.doors.some(d=>d.id==='DOOR-108-111')).toBe(false);
    expect(createConcept(DEFAULT_CONCEPT,true).doors.some(d=>d.id==='DOOR-108-111')).toBe(true);
    expect(createConcept(DEFAULT_CONCEPT,true).bedroomArea).toBeCloseTo(12.2851);
  });
  it('normalizes invalid settings without producing impossible dimensions',()=>{
    expect(normalizeConcept({expansion:Infinity,bedWidth:-200})).toEqual({...DEFAULT_CONCEPT,bedWidth:1600});
    expect(normalizeConcept({expansion:9999,bedWidth:4000})).toEqual({...DEFAULT_CONCEPT,expansion:600,bedWidth:2200});
  });
});
