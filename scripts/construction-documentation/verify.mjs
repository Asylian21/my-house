import { readFile,writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { chromium } from 'playwright';
import { CUTS, openingRows,sectionRoof,sectionGarageGable,sectionRoomSpans,sectionDimensionPoints,terraceIntervals,sectionPorchEnvelope } from './render.mjs';
import { foundationViewPoint } from './foundation-axon.mjs';
import { derivePartitionLoads,verifyPartitionLoads } from './partition-loads.mjs';

const out=resolve(import.meta.dirname,'../../output/pdf/construction-cbb');
const d=JSON.parse(await readFile(resolve(out,'model-snapshot.json'),'utf8'));
const register=JSON.parse(await readFile(resolve(out,'drawing-register.json'),'utf8'));
for(const [file,hash] of Object.entries(d.provenance.files))assert.equal(createHash('sha256').update(await readFile(resolve(import.meta.dirname,'../..',file))).digest('hex'),hash,`Changed source after export: ${file}`);
assert.equal(CUTS.length,3);
assert.equal(new Set(register.map(s=>s.id)).size,register.length);
assert(register.every(s=>s.status==='NOT_FOR_CONSTRUCTION'));
assert(!('foundations' in d),'Archived foundation solids must not be current design input');
assert.equal(d.design.livingLayout,'B');
assert.equal(d.design.heatingLayout,'B');
assert.equal(d.clientBrief.datum.elevationM,184.2);
assert.equal(d.clientBrief.datum.finishedFloorAboveRoadMm,null,'Street datum must not silently become FFL');
assert.equal(d.elevations.floor.absoluteM,null);
assert.equal(d.elevations.roofEdge.absoluteM,null);
assert.equal(d.clientBrief.foundations.requestedUpperStrip.widthMm,350);
assert.equal(d.clientBrief.foundations.requestedUpperStrip.heightMm,600);
assert.equal(d.clientBrief.foundations.slab.selectedThicknessMm,null);
assert.equal(d.clientBrief.foundations.requestedRibs.reinforcement,null);
assert.equal(d.clientBrief.foundations.permanentConcreteBlocks,false);
assert.equal(d.clientBrief.services.drilledSlabPenetrations,false);
assert.equal(d.clientBrief.roof.atticUse,'STORAGE_ONLY');
assert.equal(d.clientBrief.roof.floorStructure,'TIMBER');
assert.equal(d.clientBrief.roof.concreteFloorSlab,false);
assert.equal(d.clientBrief.roof.concreteFloorTopping,false);
assert.equal(d.clientBrief.foundations.system,'MONOLITHIC_CAST_IN_PLACE');
const ax=d.foundationIllustration;
assert.equal(register.find(s=>s.id==='D1.1.ZA-03')?.scale,'axonometria');
assert.equal(ax.perimeterWidthMm,350);
assert.equal(ax.upperHeightMm,600);
assert.equal(ax.absoluteElevations,null);
assert.equal(ax.asBuiltOffsetMm,null);
assert.equal(ax.excavation.designDepthMm,null,'A reported lower strip depth is not an excavation design');
assert.equal(ax.excavation.widthMm,null);
assert.equal(ax.lowerStrip.widthMm,null);
assert.equal(ax.lowerStrip.bottomElevationMm,null);
assert.equal(ax.graphicWidthIsDesign,false);
assert.equal(ax.foundationLoadApproval,false);
assert.equal(d.clientBrief.foundations.reportedCastScope.includesLoggia,true);
assert.equal(d.clientBrief.foundations.reportedCastScope.includesCoveredTerrace,true);
assert.equal(ax.castExtentEvidence.evidence,'CLIENT_REPORTED');
assert.equal(ax.castExtentEvidence.surveyVerified,false);
assert.equal(ax.castExtentEvidence.measuredBoundaryMm,null);
assert.equal(ax.castExtentEvidence.existingRibLayout,null);
assert.deepEqual(ax.castOutline,d.house.footprintMm.slice(0,-1).map(p=>[p.x,p.y]),'The declared cast extent includes the whole L, with loggia and covered terrace');
assert.equal(Math.max(...ax.castOutline.map(p=>p[1])),d.house.porches.wingEnd.frontYmm);
assert.equal(Math.max(...ax.perimeterAxis.map(p=>p[1])),21685,'Use the outer terrace edge, never NN.inner as a masonry face');
assert.equal(ax.ribs.length,7);
assert.deepEqual(ax.ribs.find(r=>r.id==='R4').points,[[21393,19185],[27691,19185]]);
assert.deepEqual(ax.ribs.find(r=>r.id==='R5').points,[[6794,8897],[10993,8897]]);
assert.deepEqual(ax.ribs.find(r=>r.id==='R6').points,[[10993,8897],[10993,10849]]);
const partitionRib=ax.ribs.find(r=>r.id==='R7');
assert.deepEqual(partitionRib.points,[[15093,3354],[15093,10849]]);
assert.equal(partitionRib.sourceKind,'OWN_WEIGHT_PARTITION_SUPPORT');
assert.deepEqual(partitionRib.loadedIntervalsMm.slice().sort((a,b)=>a.from-b.from),[{code:'AK-02',from:3504,to:6552},{code:'AK-01',from:7651,to:10699}]);
verifyPartitionLoads(d.partitionLoads);
assert.deepEqual(d.partitionLoads,derivePartitionLoads(d),'Stored load values must reproduce from the exact exported model');
assert.equal(d.partitionLoads.totals.unplasteredKg,2781.3);
assert.equal(d.partitionLoads.totals.bricksOnlyKg,2743.2);
for(const wall of d.partitionLoads.walls){
  assert.equal(wall.heightMm,3125,'Use the real masonry height, not the suspended ceiling');
  assert.equal(wall.lengthMm,3048);
  assert.equal(wall.unplastered.kgPerM,456.25);
  assert.equal(wall.bricksOnly.kgPerM,450);
  assert.deepEqual(wall.leaves.map(l=>l.centerlineMm[0][0]-partitionRib.points[0][0]),[-100,100]);
}
const streetW=foundationViewPoint([6440,3000]),streetE=foundationViewPoint([28040,3000]),gardenE=foundationViewPoint([28040,22035]);
assert(streetE[0]>streetW[0]);assert.equal(streetE[1],streetW[1],'Street edge should be horizontal');
assert(gardenE[1]<streetE[1],'Garden and long wing should extend above the street');
assert(gardenE[0]>streetE[0],'Long wing remains on the right');
assert.equal(ax.view.reflected,false);
assert.equal(Math.max(...ax.closedOutline.map(p=>p[1])),d.house.porches.wingEnd.glazingFaceYmm,'The covered terrace is not enclosed house');
assert(ax.closedOutline.some(p=>p[0]===d.house.porches.gardenLoggia.eastInnerXmm&&p[1]===d.house.porches.gardenLoggia.backFaceYmm),'Keep the garage loggia recess');
for(const r of ax.ribs){
  assert.equal(r.designWidthMm,null);assert.equal(r.designReinforcement,null);assert.equal(r.foundationSupport,null);
  if(r.sourceKind==='MODEL_LOAD_BEARING_WALL')assert(r.sourceIds.every(id=>d.walls.some(w=>w.id===id&&w.role==='LOAD_BEARING')));
  else if(r.sourceKind==='FACADE_BOUNDARY')assert(r.sourceIds.every(id=>d.facades.some(f=>f.def.id===id)));
  else if(r.sourceKind==='PARTITION_BOUNDARY_COORDINATION'){
    assert.equal(r.id,'R6');assert.equal(r.sourceKind,'PARTITION_BOUNDARY_COORDINATION');
    assert(r.sourceIds.every(id=>d.walls.some(w=>w.id===id&&w.role==='PARTITION')));
  }
  else {
    assert.equal(r.id,'R7');assert.equal(r.sourceKind,'OWN_WEIGHT_PARTITION_SUPPORT');
    assert(r.sourceIds.every(id=>d.walls.some(w=>w.id===id&&w.role==='PARTITION')));
    assert(r.sourceIds.every(id=>d.partitionLoads.walls.some(w=>w.wallId===id)));
  }
  if(r.sourceKind==='MODEL_LOAD_BEARING_WALL')assert(!r.sourceIds.some(id=>ax.notRoofLoadBearingWalls.includes(id)),'SA30 own-weight support must not turn it into a roof or ceiling bearing wall');
}
assert.equal(d.foundationFloorLevelMm,null,'An unknown strip/slab/floor joint cannot determine FFL');
assert.equal(d.entryProposal.status,'COORDINATION_PROPOSAL');
assert.equal(d.entryProposal.doorCode,'D2');
assert.equal(d.entryProposal.minimumStepCount,1);
assert.equal(d.entryProposal.stepHeightMm,150);
assert.equal(d.entryProposal.absoluteElevations,null,'A 150 mm local step is not an absolute site level');
const landing=d.entryProposal.landingRectMm;
assert.equal(landing.y1,d.surfaces.entry.streetConnection.houseFaceYmm);
assert(landing.y0>=d.surfaces.entry.streetConnection.cadastralBoundaryYmm);
assert.equal(landing.x1-landing.x0,1500);
assert.equal(landing.y1-landing.y0,1500);
assert.deepEqual(d.clientBrief.services.heatedRoomExclusions,['1.07','1.12']);
assert.equal(d.roofParameters.wingEndYmm,d.house.porches.wingEnd.frontYmm);
assert(d.rooms.some(r=>r.number==='1.05'&&r.rectsMm.some(s=>s.x0<=d.showerFootprint.x0&&s.x1>=d.showerFootprint.x1&&s.y0<=d.showerFootprint.y0&&s.y1>=d.showerFootprint.y1)));
assert(Number.isFinite(d.livingFlueRoofMm));
const rows=openingRows(d);
assert.equal(rows.length,d.openings.length);
assert.equal(new Set(rows.map(o=>o.code)).size,rows.length);
for(const o of rows){assert.equal(o.end-o.start,o.width,`${o.code}: opening width`);assert(Number.isFinite(o.plane));}
assert.equal(rows.find(o=>o.code==='O4').kind,'fixed');
assert.equal(rows.find(o=>o.code==='D8').width,901);
assert.equal(rows.find(o=>o.code==='D9').start,6701.5);
assert.equal(d.triangle.vertices[2][1],4469.649649649649);
assert.equal(Math.max(...sectionRoof(d,CUTS[2]).flatMap(s=>[s.a[1],s.b[1]])),4312.804878048781);
assert.deepEqual(sectionGarageGable(d,CUTS[2]),{at:6432,bottom:3125,top:4312.804878048781});
assert.equal(sectionGarageGable(d,CUTS[0]),null);
assert.deepEqual(sectionRoomSpans(d,CUTS[0],d.rooms.find(r=>r.number==='1.03')),[[11012,19035]]);
assert.deepEqual(sectionRoomSpans(d,CUTS[1],d.rooms.find(r=>r.number==='1.03')),[[21543,27541]]);
assert.deepEqual(terraceIntervals(d,'x',18620),[[18040,21040]]);
assert.equal(d.exteriorSteps.length,2);
for(const s of d.exteriorSteps){assert.equal(s.rect.x1-s.rect.x0,2400);assert.equal(s.rect.y1-s.rect.y0,380);assert.equal(s.z1-s.z0,70);}
assert.equal(d.h200Joints.J1.x1-d.h200Joints.J1.x0,5);
assert.equal(d.h200Joints.J2.y1-d.h200Joints.J2.y0,5);
assert.equal(sectionPorchEnvelope(d,CUTS[0]).filter(p=>p.kind==='LARCH_GABLE').at(-1).points[2][1],5500);
for(const c of CUTS){const points=sectionDimensionPoints(d,c);assert(points.every(Number.isFinite));assert(points.every((v,i)=>!i||v>points[i-1]));}
const report={sheetCount:register.length,checks:['codes and opening chains','three shared cuts','active B/B','no historical foundation input','O4 fixed','O11 profile','real cut roof height','full cast L and unreflected view','R7 own-weight intervals and unchanged partition role','SA30 mass from mesh height and declared product facts'],partitionSelfWeight:{status:d.partitionLoads.status,unplasteredKg:d.partitionLoads.totals.unplasteredKg,bricksOnlyKg:d.partitionLoads.totals.bricksOnlyKg,finalDesignApproved:false},color:{},mono:{}};
const browser=await chromium.launch({headless:true});
try{for(const variant of ['color','mono']){
  const page=await browser.newPage();await page.goto(new URL(`file://${resolve(out,`drawing-set-${variant}.html`)}`).href);await page.evaluate(()=>document.fonts.ready);
  const currentBrief=await page.locator('[data-sheet="D1.1.ZA-02"]').innerText();
  assert(currentBrief.includes('1 : 10')&&currentBrief.includes('200 mm = 20 mm'));
  const heavyWallsSheet=await page.locator('[data-sheet="D1.1.ZA-01"]').innerText();
  assert(heavyWallsSheet.includes('456,25')&&heavyWallsSheet.includes('AK-01')&&heavyWallsSheet.includes('AK-02'));
  assert((await page.locator('[data-sheet="D1.1.ZA-03"]').innerText()).includes('R7'));
  assert((await page.locator('[data-sheet="D1.1.TZ-01"]').innerText()).includes('1.07'));
  const results=await page.evaluate(()=>Array.from(document.querySelectorAll('.page')).map(el=>{
    const svg=el.querySelector('svg'),box=svg.getBoundingClientRect(),scale=box.width/841;
    const overflow=Array.from(svg.querySelectorAll('text')).filter(t=>!t.closest('defs')&&t.textContent.trim()).flatMap(t=>{const r=t.getBoundingClientRect();const b={x:(r.x-box.x)/scale,y:(r.y-box.y)/scale,w:r.width/scale,h:r.height/scale};return b.x<4||b.y<4||b.x+b.w>837||b.y+b.h>590?[{text:t.textContent,...b}]:[];});
    return {sheet:el.getAttribute('data-sheet'),overflow};
  }));
  report[variant]={pages:results};
  await page.close();
}}
finally{await browser.close();}
await writeFile(resolve(out,'verification.json'),JSON.stringify(report,null,2));
const overflowing=Object.entries(report).filter(([k])=>['color','mono'].includes(k)).flatMap(([k,v])=>v.pages.filter(p=>p.overflow.length).map(p=>({variant:k,...p})));
console.log(JSON.stringify({sheetCount:register.length,overflowing},null,2));
assert.equal(overflowing.length,0,'Sheet text overflows: see verification.json');
