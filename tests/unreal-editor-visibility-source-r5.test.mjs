// CPU receipt fixtures. These checks launch no Unreal/GPU and do not establish
// a new native capture, appearance, performance, or Shipping acceptance.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {canonicalVisibilityTargets,validateVisibilityWitness} from '../scripts/unreal/exterior-editor-source-r5.mjs';
const read=async p=>JSON.parse(await fs.readFile(new URL('../'+p,import.meta.url),'utf8'));
const base=await read('output/unreal/exterior-20261001-r16a/exterior-import-report.json');
const report=await read('output/unreal/exterior-20261001-r19a/meadow-visibility-native-report.json');
const plan=JSON.parse(await fs.readFile(report.selectedPlan.path,'utf8'));
const before=JSON.parse(await fs.readFile(report.witnessBefore.path,'utf8'));
const saved=JSON.parse(await fs.readFile(report.witnessAfter.path,'utf8'));
test('CPU target fixture preserves exact471+130 original groups and excludes same-count foreign ecology',()=>{
  assert.deepEqual(canonicalVisibilityTargets(base),plan.targets);
  const foreign=structuredClone(base),id=foreign.canopyEcology.groupIds[0];
  foreign.geometry.groups[id].mesh=foreign.savedPlantReadback.find(p=>!p.id.startsWith('canopy_ecology_')).mesh;
  assert.throws(()=>canonicalVisibilityTargets(foreign));
  const badLod=structuredClone(base);badLod.nativeMeadow.prototypes.LawnTuft0.lodProofs[0].triangles+=1;
  assert.throws(()=>canonicalVisibilityTargets(badLod));
});
test('CPU complete-witness fixture rejects non-target changes, hidden shadow edits and broader cull values',()=>{
  const args={before,saved,targets:plan.targets,deltas:report.componentCullOverrides};validateVisibilityWitness(args);
  const changed=structuredClone(saved),nonTarget=Object.keys(changed).find(k=>!plan.targets.some(t=>t.baseGroup.actor===k));
  changed[nonTarget].transform[0][0]+=1;assert.throws(()=>validateVisibilityWitness({...args,saved:changed}));
  const shadow=structuredClone(saved),actor=plan.targets[0].baseGroup.actor;
  shadow[actor].components[0].renderFlags.cast_shadow=!shadow[actor].components[0].renderFlags.cast_shadow;
  assert.throws(()=>validateVisibilityWitness({...args,saved:shadow}));
  const broader=structuredClone(plan.targets);broader[0].proposedCullCm=[18000,25000];
  assert.throws(()=>validateVisibilityWitness({...args,targets:broader}));
});
