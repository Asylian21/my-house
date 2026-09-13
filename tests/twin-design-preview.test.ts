import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { Scene } from '@babylonjs/core/scene';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { describe, expect, it } from 'vitest';
import { buildInterior } from '../lib/babylon-interior';
import { sourceRestBounds } from '../lib/babylon-archviz';
import { designFromSearch, designHref, PREVIEW_DESIGN } from '../lib/twin-design-selection';
import { LIVING_LAYOUTS, houseFluesForLiving, livingWalkArrival } from '../lib/twin-living-layouts';
import { KITCHEN_RUN } from '../lib/twin-interior';
import generated from '../lib/plan-geometry.generated.json';

describe('current C / B / B web preview', () => {
  it('keeps main links on B/B and preserves alternative choices only within archive links', () => {
    expect(designFromSearch(new URLSearchParams(), PREVIEW_DESIGN)).toEqual(PREVIEW_DESIGN);
    for (const livingLayout of ['A','B'] as const) for (const heatingLayout of ['A','B'] as const) {
      const design={livingLayout,heatingLayout};
      for(const path of ['/navrh-3d','/koncept-2d','/3d','/podorys','/docs/manual'] as const) {
        const url=new URL(designHref(path,design),'http://localhost');
        expect(url.searchParams.get('variant')).toBe('c');
        expect(designFromSearch(url.searchParams)).toEqual(PREVIEW_DESIGN);
        expect(url.pathname).toBe(path);
        const archived=new URL(designHref(path,design,true),'http://localhost');
        expect(archived.pathname).toBe(path==='/3d'||path==='/navrh-3d'?'/archiv/3d':'/archiv/podorys');
        expect(designFromSearch(archived.searchParams)).toEqual(design);
        expect(archived.searchParams.get('view')).toBe(path==='/docs/manual'?'manual':null);
      }
    }
    expect(designFromSearch(new URLSearchParams('living=B&heating=B'))).toEqual(PREVIEW_DESIGN);
    expect(designFromSearch(new URLSearchParams('living=invalid&heating=invalid'))).toEqual({livingLayout:'A',heatingLayout:'A'});
  });

  it('places the roof penetration over the selected stove and arrives outside the sofa and worktop', () => {
    for(const id of ['A','B'] as const) {
      expect(houseFluesForLiving(id)[0].centerMm).toEqual(LIVING_LAYOUTS[id].stove.centerMm);
      expect(houseFluesForLiving(id)[0].id).toBe(LIVING_LAYOUTS[id].stove.flue.id);
    }
    const {standing}=livingWalkArrival('B')!;
    expect(LIVING_LAYOUTS.B.fitout.sofa.mainRectMm.x0-standing.x).toBeGreaterThan(300);
    expect(standing.y-KITCHEN_RUN.peninsulaRectMm.y1-KITCHEN_RUN.peninsulaOverhangMm).toBeGreaterThan(300);
  });

  it('matches every current interior part to the measured 2D B/B geometry within 0.02 mm', () => {
    const engine=new NullEngine();
    const scene=new Scene(engine);
    scene.useRightHandedSystem=true;
    const material=new PBRMaterial('preview-parity',scene);
    try {
      buildInterior({scene,...PREVIEW_DESIGN,anisotropy:1,wall:material,soffit:material,glassFrame:material,chimneyMetal:material,timber:material,
        register:mesh=>mesh,realisticOnly:mesh=>mesh,castShadow:mesh=>mesh});
      const plan=generated.meshes.filter(m=>(!m.layout||m.layout==='B')&&(!m.heatingLayout||m.heatingLayout==='B'));
      const byName=new Map<string,typeof plan>();
      for(const part of plan) byName.set(part.name,[...(byName.get(part.name)??[]),part]);
      let checked=0;
      for(const mesh of scene.meshes.filter(m=>m.isVisible&&m.visibility>0&&!m.metadata?.walkCollisionOnly&&!m.metadata?.navigationGuard&&m.getTotalVertices()>0)) {
        const {minimum:min,maximum:max}=sourceRestBounds(mesh);
        const actual=[min.x*1000+15200,10800-max.z*1000,max.x*1000+15200,10800-min.z*1000,min.y*1000,max.y*1000];
        const candidates=byName.get(mesh.name)??[];
        const matches=candidates.some(p=>[p.rect.x0,p.rect.y0,p.rect.x1,p.rect.y1,p.z0,p.z1].every((n,i)=>Math.abs(n-actual[i])<.02));
        expect(matches,`${mesh.name}: ${actual.join(', ')}`).toBe(true);
        checked++;
      }
      expect(checked).toBeGreaterThan(1000);
      expect(scene.meshes.some(m=>m.name.startsWith('TECHNICAL-PLUS19-'))).toBe(false);
      expect(scene.meshes.some(m=>m.name.startsWith(LIVING_LAYOUTS.A.stove.id))).toBe(false);
    } finally {scene.dispose();engine.dispose();}
  });
});
