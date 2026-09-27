// A separate, reproducible exterior revision of an inherited C/B/B scene.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
const sha=b=>createHash('sha256').update(b).digest('hex');
const read=async p=>JSON.parse(await readFile(p));
const isHash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);

export function validateExteriorReceipt({report,source,project}) {
  assert.equal(report.schemaVersion,1);
  assert.equal(report.owner,'scripts/unreal/exterior-import.py');
  assert.equal(report.status,'exterior-import-validated');
  assert.equal(report.project,project);assert.equal(report.sourceOutput,source.donor);
  assert.deepEqual(report.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});
  assert.deepEqual(report.setbacksMm,{street:3000,east:3000});
  for(const key of ['savedReloaded','protectedContentUnchanged','sourceGeometryCollisionAndTransformsPreserved','originalMaterialAssetsPreserved'])
    assert.equal(report[key],true,'Missing exterior invariant: '+key);
  assert.deepEqual(report.beforeAssetHashes,source.content);
  const content=resolve(project,'Content'),map=resolve(content,'Brezi/Maps/Brezi.umap');
  const views=resolve(content,'Data/viewpoints.json'),after=report.afterAssetHashes;
  assert(Object.values(after).every(isHash));
  for(const [path,value] of Object.entries(source.content)) {
    assert(Object.hasOwn(after,path),'Exterior deleted original Content');
    if(path!==map&&path!==views)assert.equal(after[path],value,'Exterior changed original asset: '+path);
  }
  const added=Object.keys(after).filter(p=>!Object.hasOwn(source.content,p)).sort();
  assert(added.length>0);assert.deepEqual(report.newAssets,added);
  for(const path of added)assert(path===resolve(path)&&path.startsWith(resolve(content,'Brezi/Exterior20260926')+'/')&&/\.(uasset|uexp|ubulk)$/.test(path));
  const changed=Object.keys(source.content).filter(p=>source.content[p]!==after[p]).sort();
  assert(changed.includes(map));assert(changed.every(p=>p===map||p===views));
  assert.deepEqual(report.changedAssets.map(r=>r.path).sort(),changed);
  for(const row of report.changedAssets)assert.deepEqual(row,{path:row.path,beforeSha256:source.content[row.path],afterSha256:after[row.path]});
  assert.deepEqual(report.viewpoints.after.views.slice(0,report.viewpoints.before.views.length),report.viewpoints.before.views);
  const beforeOther={...report.viewpoints.before},afterOther={...report.viewpoints.after};delete beforeOther.views;delete afterOther.views;
  assert.deepEqual(afterOther,beforeOther,'Exterior changed original lighting or viewpoint settings');
  assert.equal(new Set(report.viewpoints.after.views.map(v=>v.id)).size,report.viewpoints.after.views.length);
  assert.equal(report.finalActorCount,report.originalActorCount+report.addedActors.length);
  assert.equal(new Set(report.addedActors).size,report.addedActors.length);
  for(const key of ['protectedActorWitnessSha256','authoredActorWitnessSha256'])assert(isHash(report[key]));
  assert.equal(report.savedProtectedActorWitnessSha256,report.protectedActorWitnessSha256);
  assert.equal(report.savedActorWitnessSha256,report.authoredActorWitnessSha256);
  assert(report.savedGeometryReadback.meshCount>0&&report.savedGeometryReadback.instanceCount>0);
  assert.equal(report.savedGeometryReadback.allNewVisualsNoCollision,true);
  assert(report.context.parcelCount>13);assert.equal(report.materialReadback.status,'verified-saved-exterior-materials');
  return after;
}

export async function verifyExteriorScene({root,output,project,source}) {
  const file=resolve(output,'exterior-import-report.json'),report=await read(file);
  const hostFile=resolve(output,'exterior-import-process.json'),host=await read(hostFile);
  const processFile=resolve(output,'exterior-import.log.json'),logFile=resolve(output,'exterior-import.log');
  assert.equal(host.processFile,processFile);assert.equal(host.logFile,logFile);
  const process=await read(processFile),profile=await read(resolve(output,'profile.json'));
  assert.equal(process.code,0);assert.equal(process.signal,null);assert.equal(process.pid,report.nativeProcessId);
  assert.equal(process.command,resolve(profile.engine,'Engine/Binaries/Mac/UnrealEditor-Cmd'));
  assert(process.args.includes(resolve(project,'BreziTwin.uproject'))&&process.args.includes('-run=pythonscript')&&process.args.includes('-script='+resolve(root,'scripts/unreal/exterior-import.py')));
  assert(Date.parse(report.startedAt)>=Date.parse(process.startedAt)&&Date.parse(report.generatedAt)<=Date.parse(process.endedAt));
  const inputs={[file]:host.reportSha256,[hostFile]:sha(await readFile(hostFile)),[processFile]:host.processFileSha256,[logFile]:host.logSha256,...report.pipelineFiles,...report.inputFiles};
  for(const [path,value] of Object.entries(inputs)){assert(isHash(value));assert.equal(sha(await readFile(path)),value,'Exterior input changed: '+path);}
  const content=validateExteriorReceipt({report,source,project});
  const manifests=Object.keys(report.inputFiles).filter(p=>p.endsWith('/geometry-manifest.json'));
  assert(manifests.length>0);
  // New composite libraries explicitly name the imported master. Their old
  // library and garden provenance remains pinned without being mistaken for it.
  let primary=report.plantGeometryManifest;
  if(primary)assert(manifests.includes(primary),'Imported plant master must be pinned');
  else {
    assert.equal(new Set(manifests.map(path=>report.inputFiles[path])).size,1,'Ambiguous exterior plant geometry manifests');
    primary=manifests[0];
  }
  const plants=await read(primary);
  assert.deepEqual(report.savedPlantReadback.map(r=>r.id).sort(),plants.meshes.map(r=>r.id).sort());
  for(const row of report.savedPlantReadback){
    const expected=plants.meshes.find(m=>m.id===row.id);
    assert(row.mesh.startsWith('/Game/Brezi/Exterior20260926/Geometry/'));
    assert.deepEqual(row.lodTriangles,expected.lods.map(l=>l.triangles));
    const screens=expected.role==='tree'?[1,.32,.10]:[1,.15,.04];
    assert.equal(row.lodScreens.length,3);assert(row.lodScreens.every((n,i)=>Math.abs(n-screens[i])<1e-5));
    assert.deepEqual([...row.materials].sort(),expected.materialKeys.map(k=>report.materials.materials[k].asset).sort());
  }
  const saved=await read(resolve(project,'Content/Data/viewpoints.json'));assert.deepEqual(saved,report.viewpoints.after);
  return {content,inputs,exterior:{status:report.status,report:file,reportSha256:host.reportSha256,parcelCount:report.context.parcelCount,instanceCount:report.savedGeometryReadback.instanceCount,nativeRenderedVerified:false,
    ...(report.regionalVegetation?{regionalVegetation:report.regionalVegetation}:{}),
    ...(report.seasonalFields?{seasonalFields:report.seasonalFields}:{}),
    ...(report.fieldMacro?{fieldMacro:report.fieldMacro}:{}),
    ...(report.orthophoto?{orthophoto:report.orthophoto}:{})}};
}
