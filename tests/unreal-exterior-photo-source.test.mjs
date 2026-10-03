import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import test from 'node:test';
import {validatePhotographicLawnCoverage} from '../scripts/unreal/exterior-lawn-photo-source.mjs';
import {plantLodScreenSizes} from '../scripts/unreal/exterior-source.mjs';

const directory=resolve(import.meta.dirname,'../output/unreal/exterior-lawn-photo-integration-20261001-r1');
const plan=JSON.parse(await readFile(resolve(directory,'lawn-natural-plan.json')));
const meshes=JSON.parse(await readFile(resolve(directory,'photo-geometry-manifest.json'))).meshes;

test('actual photographic source measurements retain original interior and boundary coverage gates',()=>{
  validatePhotographicLawnCoverage(plan.audit);
  assert.equal(meshes.length,20);
  for(const mesh of meshes)assert.deepEqual(plantLodScreenSizes(mesh),[1,.025,.007]);
});

test('photographic transparency cannot borrow passing flags when measured coverage falls below the gate',()=>{
  for(const mutate of [
    audit=>{audit.physicalCoverage.windows[0].lods[0].projectedCoverage=.749999;},
    audit=>{audit.physicalCoverage.windows[0].lods[0].tenCmBinCoverageP10=.549999;},
    audit=>{audit.boundaryCoverage.windows[0].lods[0].boundaryBands[0].physicalCoverFraction=.119999;},
    audit=>{audit.physicalCoverage.windows[0].lods[2].projectedCoverage-=.000001;},
  ]) {
    const audit=structuredClone(plan.audit);mutate(audit);
    assert.throws(()=>validatePhotographicLawnCoverage(audit));
  }
});

test('source coverage never establishes native appearance or permits different density and geometry',()=>{
  for(const [key,value] of [['nativeAppearanceAccepted',true],['fullPhotorealismAccepted',true],
    ['instances',102012],['allSourceGeometryExceptUv0TangentsPreserved',false],['performanceAccepted',true]]) {
    const audit=structuredClone(plan.audit);audit[key]=value;
    assert.throws(()=>validatePhotographicLawnCoverage(audit));
  }
});

test('photographic LOD policy is restricted to the twenty approved IDs and their matching material',()=>{
  for(const mutate of [
    row=>{row.id='lawn_photo_2_0';},
    row=>{row.id='lawn_photo_edge_0_2';},
    row=>{row.materialKeys=['lawn_natural_blade'];},
    row=>{row.lodScreenSizes=[1,.15,.04];},
    row=>{row.role='tree';},
  ]) {
    const row=structuredClone(meshes[0]);mutate(row);
    assert.throws(()=>plantLodScreenSizes(row));
  }
});
