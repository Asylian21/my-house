import { describe, expect, it } from 'vitest';
import { createConcept, DEFAULT_CONCEPT, rect } from '../lib/floor-plan-concept';
import { createExperiment } from '../lib/floor-plan-experiment';
import { createGarageEnvelope } from '../lib/floor-plan-garage';
import { GARAGE_DEPTH_REVISION, HOUSE } from '../lib/twin-site';
import { contains, intersects, opening, openLeaf, swingHits, walkingPath } from './floor-plan-geometry';

describe('shared garden recess in all floor-plan variants',()=>{
  it('fills the entire insulation corner between the garage back wall and bedroom cheek',()=>{
    const {insulation}=createGarageEnvelope();
    // Sample both arms and the formerly uninsulated 202 × 200 mm junction.
    for(let x=10550;x<10842;x+=20)for(let y=9057;y<9400;y+=20){
      if(x<10640&&y>=9247)continue; // Open loggia outside the L-shaped band.
      const layers=insulation.filter(r=>r.x0<x&&r.x1>x&&r.y0<y&&r.y1>y);
      expect(layers,`insulation at ${x}, ${y}`).toHaveLength(1);
    }
  });
  it('retains the source pillar, side opening and recessed wall with a usable garden door',()=>{
    const variants=[
      createConcept(DEFAULT_CONCEPT,true),
      ...(['vestibule','wardrobe','nested','private'] as const).map(layout=>createConcept({...DEFAULT_CONCEPT,layout})),
      createExperiment(),
    ];
    for(const m of variants){
      expect(m.gardenRecess).toBe(true);
      expect(m.loggia.depth).toBe(1953);
      expect(m.loggia.pier).toEqual(rect(6440,10700,7840,11200));
      expect(m.loggia.openingWidth).toBe(2800);
      expect(m.loggia.pierReturn.y0-m.loggia.bounds.y0).toBe(HOUSE.facades.west.loggiaOpening.widthMm);
      expect(m.loggia.bounds.x1).toBe(HOUSE.porches.gardenLoggia.eastInnerXmm);
      expect(m.garageBackOpening.y0).toBe(GARAGE_DEPTH_REVISION.revisedGarageRearInnerFaceYmm);
      for(const floor of m.rooms.flatMap(room=>room.rectsMm))expect(intersects(floor,m.loggia.bounds)).toBe(false);
      expect(swingHits(m.gardenDoor,m.car)).toBe(false);
      expect(contains(m.garageThreshold,rect(m.car.x0,m.car.y0,m.car.x1,3504))).toBe(true);
      const floors=[...m.rooms.find(room=>room.number==='1.12')!.rectsMm,opening(m.gardenDoor),m.loggia.bounds];
      expect(walkingPath(floors,[m.car,openLeaf(m.gardenDoor),...m.garageShelves,m.loggia.pier,m.loggia.pierReturn],[10300,6200],[9550,10200])).toBe(true);
    }
  });
  it('only encloses the garden recess when explicitly selected in a proposed layout',()=>{
    for(const layout of ['wardrobe','nested','private'] as const){
      const retained=createConcept({...DEFAULT_CONCEPT,layout});
      const enclosed=createConcept({...DEFAULT_CONCEPT,layout,gardenRecess:false});
      expect(retained.garageDepth).toBe(5245);
      expect(enclosed.garageDepth).toBe(7195);
      expect(enclosed.gardenRecess).toBe(false);
      expect(enclosed.garageBackOpening.y1).toBe(HOUSE.porches.gardenLoggia.faceYmm);
      for(const number of ['1.08','1.09','1.10','1.11','1.14'])expect(enclosed.rooms.find(room=>room.number===number)).toEqual(retained.rooms.find(room=>room.number===number));
    }
    expect(createConcept({...DEFAULT_CONCEPT,gardenRecess:false},true).gardenRecess).toBe(true);
    expect(createConcept({...DEFAULT_CONCEPT,layout:'vestibule',gardenRecess:false}).gardenRecess).toBe(true);
  });
});
