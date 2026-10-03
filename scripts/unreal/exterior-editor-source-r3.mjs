// Source receipt guards for an uncooked Editor pilot. CPU checks do not create
// native, visual, package, or performance acceptance evidence.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';

export const TRANSMISSION_SCHEMA='brezi-canopy-transmission-component-overlay-r1';
export const TRANSMISSION_STATUS='verified-saved-canopy-transmission-component-overlay';
export const TRANSMISSION_PLAN_SHA='2f9032afd061b5681844911959fb9247af8a1197a2c8cded78f1ee5cdbcd0ccb';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const hashLike=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const falseFlags=v=>{for(const key of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingPackageProduced'])assert.equal(v[key],false,'Overlay acceptance flag differs: '+key);};
const exec=promisify(execFile);
async function sha(file) {const h=createHash('sha256');for await(const bytes of createReadStream(file))h.update(bytes);return h.digest('hex');}
const read=async file=>JSON.parse(await fs.readFile(file,'utf8'));
const relativeOwned=(relative)=>typeof relative==='string'&&relative.length>0&&!path.isAbsolute(relative)&&
  path.normalize(relative)===relative&&!relative.startsWith('../');

export function validateProjectClosure({project,contentInventory,projectProof,closure}) {
  const content=path.join(project,'Content');
  const contentFiles=Object.keys(closure).filter(file=>file.startsWith(content+path.sep));
  assert.equal(contentFiles.length,Object.keys(contentInventory).length,'Own Content differs from its exact saved inventory');
  for(const [relative,row] of Object.entries(contentInventory)) {
    assert(relativeOwned(relative),'Content inventory escapes the own project');assert(hashLike(row.sha256));
    const actual=closure[path.join(content,relative)];assert(actual,'Saved Content file missing');assert.equal(actual.sha256,row.sha256);
    if(Object.hasOwn(row,'bytes'))assert.equal(actual.bytes,row.bytes);
  }
  if(projectProof) {
    const protectedFiles=Object.keys(closure).filter(file=>file===path.join(project,'BreziTwin.uproject')||
      ['Config','Source','Binaries'].some(folder=>file.startsWith(path.join(project,folder)+path.sep)));
    assert.deepEqual(protectedFiles.sort(),Object.keys(projectProof).map(relative=>path.join(project,relative)).sort(),
      'Own protected source/config/binary file set differs from its exact base proof');
    for(const [relative,row] of Object.entries(projectProof)) {
      assert(relativeOwned(relative)&&(relative==='BreziTwin.uproject'||/^(Config|Source|Binaries)\//.test(relative)),
        'Overlay project proof escapes protected source/binary scope');
      assert.deepEqual(closure[path.join(project,relative)],row,'Own protected source/config/binary bytes differ: '+relative);
    }
  }
}

export function validateOverlayAssetDelta(before,after,delta,variants) {
  const original=Object.keys(before),actual=Object.keys(after);
  assert(original.every(key=>Object.hasOwn(after,key)),'Overlay removed protected Content');
  const changed=original.filter(key=>!Object.is(before[key].sha256,after[key].sha256)||before[key].bytes!==after[key].bytes).sort();
  assert.deepEqual(changed,['Brezi/Maps/Brezi.umap'],'Overlay changed Content beyond its own map');
  const added=actual.filter(key=>!Object.hasOwn(before,key)).sort();
  const packages=Object.values(variants).map(v=>v.newAsset.split('.')[0].slice('/Game/'.length));
  assert.equal(packages.length,2);assert.equal(new Set(packages).size,2);
  for(const key of added) {
    assert(['.uasset','.uexp','.ubulk'].includes(path.extname(key))&&packages.includes(key.slice(0,-path.extname(key).length)),
      'Overlay added a foreign material/texture/mesh package');
  }
  assert.deepEqual(added.filter(key=>key.endsWith('.uasset')),packages.map(p=>p+'.uasset').sort(),'Overlay must add exactly two full Material packages');
  assert.deepEqual(delta,{changedFiles:changed,newFiles:added,protectedFilesByteIdentical:original.length-1});
}

export function validateOverlayActorDelta(before,after,targets,bindings) {
  assert.equal(targets.length,23);assert.equal(targets.reduce((n,t)=>n+t.baseGroup.instances,0),78);
  const expected=structuredClone(before),expectedBindings=[],components=new Set();
  for(const target of targets) {
    assert.equal(target.slot,1);assert.equal(target.unchangedBarkSlot,0);
    const actor=expected[target.baseGroup.actor];assert(actor,'Overlay target actor missing');
    const candidates=actor.components.filter(c=>c.mesh===target.baseGroup.mesh&&c.instanceCount===target.baseGroup.instances);
    assert.equal(candidates.length,1,'Overlay target component missing or ambiguous');const component=candidates[0];
    assert.deepEqual(component.materials,[target.unchangedBarkAsset,target.originalLeafAsset]);
    assert.equal(component.orderedInstanceTransformsSha256,target.baseGroup.transformsSha256);
    assert(Array.isArray(component.overrideMaterials)&&component.overrideMaterials.length<=2);
    assert(component.overrideMaterials.every((v,i)=>v===null||v===component.materials[i]));
    while(component.overrideMaterials.length<2)component.overrideMaterials.push(null);
    component.overrideMaterials[1]=target.newLeafAsset;component.materials[1]=target.newLeafAsset;
    assert(!components.has(component.path),'Overlay target component duplicated');components.add(component.path);
    expectedBindings.push({groupId:target.groupId,actor:target.baseGroup.actor,component:component.path,slot:1,
      before:target.originalLeafAsset,after:target.newLeafAsset,barkSlot0:component.materials[0]});
  }
  assert.deepEqual(bindings,expectedBindings,'Overlay binding receipt differs from its exact23 component changes');
  assert.deepEqual(after,expected,'Overlay changed actor/mesh/transform/light/cull/collision/render policy beyond leaf slot1');
}

export function validateTransmissionEvidence({overlay,plan,base,beforeContent,afterContent,beforeActors,afterActors,originalMaterials,
  process,canonicalHashes}) {
  assert.equal(overlay.schema,TRANSMISSION_SCHEMA);assert.equal(overlay.owner,'scripts/unreal/exterior-canopy-transmission-native.py');
  assert.equal(overlay.status,TRANSMISSION_STATUS);falseFlags(overlay);falseFlags(plan);
  assert.equal(plan.schema,TRANSMISSION_SCHEMA);assert.equal(plan.owner,'scripts/unreal/exterior-canopy-transmission-study.py');
  assert.equal(plan.status,'source-only-canopy-transmission-native-trial-pending');
  assert.equal(base.status,'exterior-import-validated');assert.equal(base.savedReloaded,true);
  assert.deepEqual(base.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(base.setbacksMm,{street:3000,east:3000});
  assert.equal(process.code,0);assert.equal(process.signal,null);
  assert(Number.isFinite(Date.parse(process.startedAt))&&Date.parse(process.endedAt)>=Date.parse(process.startedAt));
  assert.equal(process.pid,overlay.nativeProcessId);assert(Number.isInteger(process.pid)&&process.pid>0);assert(process.args.includes('-nullrhi'));
  assert.equal(process.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');
  assert.equal(process.args[0],path.join(overlay.project,'BreziTwin.uproject'));
  assert(process.args.includes('-run=pythonscript'));
  assert(process.args.includes('-script='+plan.newSourceFiles.nativeHelper.live.path));
  assert(process.args.includes('-abslog='+path.join(overlay.output,'canopy-transmission-native.log')));
  assert.deepEqual(overlay.selectedPlan.sha256,TRANSMISSION_PLAN_SHA);assert.deepEqual(overlay.baseNativeReport,plan.baseNativeReport);
  for(const key of ['baseContentInventory','baseProjectProof','consumedSourceSnapshot','newSourceFiles','frozenPipeline','engineEvidence'])
    assert.deepEqual(overlay[key],plan[key],'Overlay receipt/source plan closure differs: '+key);
  assert.equal(overlay.nativeEngineBuildId,plan.nativeEngineBuildId);
  assert.equal(overlay.savedMapUnloadedReloaded,true);assert.equal(overlay.materialPackagesIndependentlyReloaded,false);
  assert.equal(overlay.originalR16Unchanged,true);assert.equal(overlay.originalContentExceptMapByteIdentical,true);
  assert.equal(overlay.effectiveLeafOverrideGroups,23);assert.equal(overlay.effectiveLeafOverrideInstances,78);
  assert.deepEqual(overlay.actualAudit,plan.audit);
  for(const [key,value] of Object.entries({originalMaterialGraphs:42,proposedMaterialGraphs:44,textureObjects:74,plantStaticMeshes:135,
    plantLods:405,targetGroups:23,targetInstances:78,allExteriorGroups:1980,allExteriorInstances:632026,geometryChanges:0,staticMeshSlotChanges:0,newTextureObjects:0}))
    assert.equal(overlay.actualAudit[key],value,'Overlay actual inventory differs: '+key);
  assert.equal(Object.keys(base.materials.materials).length,42);assert.equal(Object.keys(base.materials.textures).length,74);
  assert.equal(base.savedPlantReadback.length,135);assert.equal(base.savedPlantReadback.reduce((n,p)=>n+p.lodTriangles.length,0),405);
  assert.deepEqual(overlay.baseGeometryReadback,base.savedGeometryReadback);assert.deepEqual(overlay.savedGeometryReadback,base.savedGeometryReadback);
  assert.equal(Object.keys(beforeActors).length,base.finalActorCount);assert.equal(overlay.actualAudit.allLevelActors,base.finalActorCount);
  assert.deepEqual(plan.targets.map(t=>t.groupId).sort(),[...base.canopyReplacement.groupIds].sort());
  for(const target of plan.targets)assert.deepEqual(target.baseGroup,base.geometry.groups[target.groupId]);
  for(const [relative,row] of Object.entries(beforeContent))assert.equal(base.afterAssetHashes[path.join(base.project,'Content',relative)],row.sha256);
  assert.equal(Object.keys(beforeContent).length,Object.keys(base.afterAssetHashes).length);
  validateOverlayAssetDelta(beforeContent,afterContent,overlay.assetDelta,plan.variants);
  validateOverlayActorDelta(beforeActors,afterActors,plan.targets,overlay.componentBindings);
  assert.equal(overlay.beforeActorWitnessSha256,canonicalHashes.beforeActors);
  assert.equal(overlay.expectedActorWitnessSha256,canonicalHashes.afterActors);assert.equal(overlay.savedActorWitnessSha256,canonicalHashes.afterActors);
  assert.equal(overlay.originalMaterialsWitnessSha256,canonicalHashes.originalMaterials);
  assert.equal(Object.keys(originalMaterials.graphs).length,42);assert.equal(Object.keys(originalMaterials.textures).length,74);
  for(const [key,row] of Object.entries(base.materials.materials)) {
    assert.equal(originalMaterials.graphs[key].asset,row.asset);assert.equal(originalMaterials.graphs[key].graphSha256,row.graphSha256);
    assert.deepEqual(originalMaterials.graphs[key].usage,{instancedStaticMeshes:true,nanite:true});
  }
  for(const [key,row] of Object.entries(base.materials.textures)) {
    const actual=originalMaterials.textures[key];assert.equal(actual.asset,row.asset);assert.deepEqual(actual.values.size,[row.width,row.height]);
    assert.equal(actual.metadata.source_sha256,row.sourceSha256);assert.equal(actual.metadata.BreziSourceLicense,row.sourceLicense);
    assert.equal(actual.metadata.BreziSourcePage,row.sourcePage);
  }
  assert.deepEqual(Object.keys(overlay.variants).sort(),Object.keys(plan.variants).sort());
  for(const [key,row] of Object.entries(plan.variants)) {
    const actual=overlay.variants[key];assert.equal(actual.asset,row.newAsset);assert.deepEqual(actual.graph,row.expectedGraph);
    assert.equal(actual.graphSha256,row.expectedGraphSha256);assert.deepEqual(actual.usage,{instancedStaticMeshes:true,nanite:true});
  }
  const witness=overlay.nativeModuleWitness;
  assert.equal(witness.source,plan.nativeModule.path);assert.equal(witness.sha256,MODULE_SHA);assert.equal(witness.bytes,2818384);
  assert.equal(witness.independentInodes,true);assert.equal(witness.sha256,plan.nativeModule.sha256);assert.equal(witness.bytes,plan.nativeModule.bytes);
  return {mode:'canopy-transmission-overlay',targetGroups:23,targetInstances:78,originalMaterialGraphs:42,newMaterialGraphs:2,
    originalTextureObjects:74,plantStaticMeshes:135,plantLods:405,nativeAppearanceAccepted:false,fullPhotorealismAccepted:false,
    performanceAccepted:false,shippingPackageProduced:false};
}

export async function loadEditorSourceEvidence(source,{root}={}) {
  source=path.resolve(source);const project=path.join(source,'Project/BreziTwin'),closure=new Set();
  const importPath=path.join(source,'exterior-import-report.json'),overlayPath=path.join(source,'canopy-transmission-native-report.json');
  const exists=async p=>{try{await fs.access(p);return true;}catch(error){if(error.code==='ENOENT')return false;throw error;}};
  async function pinned(pin) {
    assert(pin&&path.isAbsolute(pin.path)&&path.resolve(pin.path)===pin.path&&hashLike(pin.sha256)&&Number.isInteger(pin.bytes)&&pin.bytes>=0,'Malformed overlay file pin');
    const stat=await fs.lstat(pin.path);assert(stat.isFile()&&!stat.isSymbolicLink(),'Overlay source pin is not a regular owned file');
    assert.equal(stat.size,pin.bytes);assert.equal(await sha(pin.path),pin.sha256,'Overlay pinned source changed: '+pin.path);closure.add(pin.path);return pin.path;
  }
  async function pinnedJson(pin) {return read(await pinned(pin));}
  if(!(await exists(overlayPath))) {
    assert(await exists(importPath),'Actual saved exterior or completed transmission overlay receipt is required');
    const report=await read(importPath);assert.equal(report.status,'exterior-import-validated');assert.equal(report.savedReloaded,true);
    assert.equal(path.resolve(report.project),project);closure.add(importPath);
    return {mode:'exterior-import',project,nativeReceiptPath:importPath,base:report,
      contentInventory:Object.fromEntries(Object.entries(report.afterAssetHashes).map(([file,h])=>{
        const relative=path.relative(path.join(project,'Content'),file);assert(relative&&!relative.startsWith('../')&&!path.isAbsolute(relative));return [relative,{sha256:h}];
      })),additionalClosureFiles:[...closure]};
  }
  assert(!(await exists(importPath)),'Overlay candidate must not carry a copied base exterior report');
  assert(root&&path.dirname(source)===path.join(path.resolve(root),'output/unreal')&&/^exterior-20261001-r17[a-z]*$/.test(path.basename(source)),
    'Overlay pilot needs the selected isolated R17 project');
  const overlay=await read(overlayPath);closure.add(overlayPath);
  assert.equal(path.resolve(overlay.project),project);assert.equal(path.resolve(overlay.output),source);
  assert.equal(overlay.selectedPlan.sha256,TRANSMISSION_PLAN_SHA,'Overlay selected source plan differs');
  const plan=await pinnedJson(overlay.selectedPlan),base=await pinnedJson(overlay.baseNativeReport);
  assert.equal(path.basename(path.dirname(overlay.baseNativeReport.path)),'exterior-20261001-r16a');
  assert.equal(path.resolve(base.project),path.join(path.dirname(overlay.baseNativeReport.path),'Project/BreziTwin'));
  const beforeContent=await pinnedJson(overlay.baseContentInventory),afterContent=await pinnedJson(overlay.afterContentInventory);
  const projectProof=await pinnedJson(overlay.baseProjectProof);
  for(const relative of Object.keys(projectProof))assert(relativeOwned(relative)&&(relative==='BreziTwin.uproject'||/^(Config|Source|Binaries)\//.test(relative)),
    'Overlay protected project proof escapes its source/binary scope');
  const beforeActors=await pinnedJson(overlay.witnessBefore),afterActors=await pinnedJson(overlay.witnessAfter);
  const originalMaterials=await pinnedJson(overlay.originalMaterialsBefore);
  const snapshot=await pinnedJson(overlay.consumedSourceSnapshot);
  assert.equal(snapshot.nativeExitCode,0);assert.equal(snapshot.hostControllerExitCode,1);assert.equal(snapshot.allHashesVerified,true);
  for(const row of Object.values(plan.frozenPipeline))await pinned(row);
  for(const entry of Object.values(plan.newSourceFiles)) {await pinned(entry.live);await pinned(entry.snapshot);assert.equal(entry.live.sha256,entry.snapshot.sha256);}
  for(const row of Object.values(plan.engineEvidence))await pinned(row);
  await pinned(plan.nativeModule);await pinned(plan.baseProjectModuleMap);
  await pinned(plan.sourceGuardTests);
  const processPath=path.join(source,'canopy-transmission-native.log.json'),processReceiptPath=path.join(source,'canopy-transmission-native-process.json');
  const process=await read(processPath),processReceipt=await read(processReceiptPath);
  assert.equal(processReceipt.processFile,processPath);assert.equal(processReceipt.processFileSha256,await sha(processPath));
  assert.equal(processReceipt.logFile,path.join(source,'canopy-transmission-native.log'));
  assert.equal(processReceipt.logSha256,await sha(processReceipt.logFile));assert.equal(processReceipt.reportSha256,await sha(overlayPath));
  for(const file of [processPath,processReceiptPath,processReceipt.logFile])closure.add(file);
  // Python's canonical witness JSON preserves float-vs-int spelling and
  // exponent formatting. Re-encoding parsed native floats with JSON.stringify
  // would not produce the native digest; hash the actual verified JSON files.
  const python="import hashlib,json,sys;print(json.dumps([hashlib.sha256(json.dumps(json.load(open(p)),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest() for p in sys.argv[1:]]))";
  const {stdout}=await exec('python3',['-c',python,overlay.witnessBefore.path,overlay.witnessAfter.path,overlay.originalMaterialsBefore.path],
    {timeout:60000,maxBuffer:1024*1024,env:{...processEnv(),PYTHONDONTWRITEBYTECODE:'1'}});
  const hashes=JSON.parse(stdout);assert.equal(hashes.length,3);assert(hashes.every(hashLike));
  const summary=validateTransmissionEvidence({overlay,plan,base,beforeContent,afterContent,beforeActors,afterActors,originalMaterials,process,
    canonicalHashes:{beforeActors:hashes[0],afterActors:hashes[1],originalMaterials:hashes[2]}});
  for(const key of ['afterContentInventory','witnessBefore','witnessAfter','originalMaterialsBefore'])
    assert(overlay[key].path.startsWith(source+path.sep),'Overlay native evidence is outside its own candidate');
  assert.equal(overlay.nativeModuleWitness.destination,path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));
  const donor=await fs.stat(overlay.nativeModuleWitness.source),own=await fs.stat(overlay.nativeModuleWitness.destination);
  assert(donor.dev!==own.dev||donor.ino!==own.ino,'Overlay Editor module aliases the donor inode');
  assert.equal(own.size,overlay.nativeModuleWitness.bytes);assert.equal(await sha(overlay.nativeModuleWitness.destination),MODULE_SHA);
  closure.add(overlay.nativeModuleWitness.source);closure.add(overlay.nativeModuleWitness.destination);
  return {mode:'canopy-transmission-overlay',project,nativeReceiptPath:overlayPath,base,overlay,plan,summary,
    contentInventory:afterContent,projectProof,additionalClosureFiles:[...closure],nativeModuleWitness:overlay.nativeModuleWitness};
}

// Kept separate from the local variable named process in the loader.
const processEnv=()=>globalThis.process.env;
