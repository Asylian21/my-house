import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,symlink,rm,realpath} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';
import {inheritScene,inventory,pins,verifyInheritedScene} from '../scripts/unreal/performance-source.mjs';
async function fixture(t){
  const root=await realpath(await mkdtemp(resolve(tmpdir(),'brezi-performance-source-')));
  t.after(()=>rm(root,{recursive:true,force:true}));
  const donor=resolve(root,'output/unreal/donor'),output=resolve(root,'output/unreal/candidate'),project=resolve(output,'Project/BreziTwin');
  await mkdir(donor,{recursive:true});await mkdir(resolve(project,'Content/Data'),{recursive:true});
  return {root,donor,output,project};
}
test('scene inheritance rejects nested or existing historical destinations before any copy',async t=>{
  const f=await fixture(t);
  await assert.rejects(inheritScene({...f,donor:f.output+'/nested'}),/Independent/);
  await writeFile(resolve(f.output,'model-package.json'),'historical');
  await assert.rejects(inheritScene(f),/historical output/);
});
test('scene inheritance refuses nonempty source content destination',async t=>{
  const f=await fixture(t);await writeFile(resolve(f.project,'Content/Data/authored.json'),'existing');
  await assert.rejects(inheritScene(f),/empty destination/);
});
test('unaccepted asset experiment cannot become a historical scene donor',async t=>{
  const f=await fixture(t);
  await writeFile(resolve(f.donor,'model-package.json'),JSON.stringify({experimentalStudy:{accepted:false}}));
  await assert.rejects(inheritScene(f),/unaccepted experimental study/);
});
test('failed experimental outputs must be preserved even before a package exists',async t=>{
  const f=await fixture(t);
  await writeFile(resolve(f.output,'nanite-study-state.json'),'protected source witness');
  await assert.rejects(inheritScene(f),/historical output/);
});
test('inventories reject symlinks and content pins detect byte changes',async t=>{
  const f=await fixture(t),p=resolve(f.donor,'input');await writeFile(p,'before');
  const recorded=await inventory(f.donor);await writeFile(p,'after');await assert.rejects(pins(recorded),/Input changed/);
  await symlink(p,resolve(f.donor,'alias'));await assert.rejects(inventory(f.donor),/symlink/);
});
test('migration verification independently rejects non-map asset changes',async t=>{
  const f=await fixture(t),asset=resolve(f.project,'Content/Data/protected.json');await writeFile(asset,'geometry');
  const content=await inventory(resolve(f.project,'Content'));
  await writeFile(resolve(f.output,'performance-source.json'),JSON.stringify({status:'verified-scene-inherited',project:f.project,donor:f.donor,
    receiptPins:{},sourcePins:{},geometry:{},content}));
  await writeFile(resolve(f.output,'performance-scene-report.json'),JSON.stringify({status:'performance-scene-validated',
    beforeAssetHashes:content,afterAssetHashes:{...content,[asset]:'0'.repeat(64)},savedReloaded:true,protectedContentUnchanged:true,
    sourceTransformsMaterialsCollisionAndInstancesPreserved:true}));
  await assert.rejects(verifyInheritedScene(f),/protected asset/);
});
