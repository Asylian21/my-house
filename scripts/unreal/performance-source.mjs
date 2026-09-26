// Inherit a verified authored scene without reimporting or rewriting its history.
import {readFile,writeFile,mkdir,readdir,cp,access,realpath,rm} from 'node:fs/promises';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {verifyPackagedPayload} from './package-verify.mjs';
import {verifyNaniteStudy} from './nanite-study.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex');
const read=async p=>JSON.parse(await readFile(p));
const save=(p,v)=>writeFile(p,JSON.stringify(v,null,2)+'\n');
export async function inventory(dir){
  const result={};
  async function visit(p){for(const e of await readdir(p,{withFileTypes:true})){
    const f=resolve(p,e.name);assert(!e.isSymbolicLink(),'No symlink inputs');
    if(e.isDirectory())await visit(f);else if(e.isFile())result[f]=sha(await readFile(f));
  }}await visit(dir);return result;
}
export async function pins(files){for(const [p,h] of Object.entries(files))assert.equal(sha(await readFile(p)),h,'Input changed: '+p);}
export async function inheritScene({root,output,project,donor}){
  donor=resolve(root,donor);const parent=resolve(root,'output/unreal')+'/';
  assert(donor!==output&&donor.startsWith(parent)&&output.startsWith(parent));
  assert(!donor.startsWith(output+'/')&&!output.startsWith(donor+'/'),'Independent source/destination required');
  assert.equal(await realpath(output),output);assert.equal(await realpath(donor),donor);
  for(const name of ['model-package.json','model-refresh-import-report.json','model-import-process.json','performance-scene-report.json',
    'nanite-study-report.json','nanite-study-state.json'])
    await access(resolve(output,name)).then(()=>{throw Error('Refuse to overwrite historical output: '+name);},e=>{if(e.code!=='ENOENT')throw e;});
  for(const directory of [resolve(project,'Content'),resolve(output,'geometry')]){
    const files=await inventory(directory).catch(e=>{if(e.code==='ENOENT')return {};throw e;});
    assert.equal(Object.keys(files).length,0,'Scene inheritance requires empty destination: '+directory);
  }
  await access(resolve(output,'performance-source.json')).then(()=>{throw Error('Scene already inherited');},e=>{if(e.code!=='ENOENT')throw e;});
  const receiptFile=resolve(donor,'model-package.json'),receipt=await read(receiptFile);
  assert(!receipt.experimentalStudy,'An unaccepted experimental study cannot become an inheritance donor');
  assert.equal(receipt.status,'current-model-packaged');await verifyPackagedPayload(receipt.appPath,receipt.bundle);
  const donorProject=resolve(donor,'Project/BreziTwin');assert.equal(receipt.project,donorProject);
  const donorProfile=await read(resolve(donor,'profile.json')),profile=await read(resolve(output,'profile.json'));
  assert(!donorProfile.doubleGlass||profile.doubleGlass,'Inherited glass needs BREZI_DOUBLE_GLASS=1 for native clipping');
  assert.equal(profile.archvizGame,donorProfile.archvizGame,'Inherited scene must retain its gameplay cook configuration');
  const sourcePins=Object.fromEntries(Object.entries(receipt.inputs).filter(([p])=>p.startsWith(donorProject+'/Content/')||p.startsWith(donor+'/geometry/')));
  assert(Object.keys(sourcePins).length>100,'Missing authored content provenance');await pins(sourcePins);
  const content=await inventory(resolve(donorProject,'Content')),geometry=await inventory(resolve(donor,'geometry'));
  // Every current native asset must occur in the original package authoring inventory.
  for(const [p,h] of Object.entries(content))assert.equal(sourcePins[p],h,'Unsealed donor asset: '+p);
  await cp(resolve(donorProject,'Content'),resolve(project,'Content'),{recursive:true});
  await cp(resolve(donor,'geometry'),resolve(output,'geometry'),{recursive:true});
  const sourceReceipts=['model-refresh-import-report.json','model-import-process.json','archviz-import-report.json','archviz-import-process.json',
    'photoreal-import-report.json','photoreal-import-process.json','rural-import-report.json','rural-import-process.json'];
  const receiptPins={[receiptFile]:sha(await readFile(receiptFile))};
  for(const name of sourceReceipts){const p=resolve(donor,name);const bytes=await readFile(p);receiptPins[p]=sha(bytes);
    assert.equal(receipt.inputs[p],receiptPins[p],'Historical receipt differs from package: '+p);
    await writeFile(resolve(output,name),bytes);}
  const movedContent=Object.fromEntries(Object.entries(content).map(([p,h])=>[p.replace(donorProject+'/',project+'/'),h]));
  const movedGeometry=Object.fromEntries(Object.entries(geometry).map(([p,h])=>[p.replace(donor+'/',output+'/'),h]));
  await pins({...movedContent,...movedGeometry});
  const provenance={status:'verified-scene-inherited',generatedAt:new Date().toISOString(),donor,project,receiptPins,sourcePins,
    content:movedContent,geometry:movedGeometry,scope:'Byte-identical authored Content and geometry copied from a verified package. Import reports are unchanged historical provenance, not claims of a new import.'};
  await save(resolve(output,'performance-source.json'),provenance);return provenance;
}
export async function baselineInstrumentation({root,output,project,donor}){
  // Rebuild the old renderer with only the diagnostic camera/measurement extension.
  // This supplies real-time walking evidence that the immutable original binary
  // cannot produce; it is always labeled as an instrumented baseline.
  donor=resolve(root,donor);
  await inheritScene({root,output,project,donor});
  const oldProject=resolve(donor,'Project/BreziTwin'),game=await read(resolve(donor,'model-game-build.json'));
  const oldPins=Object.fromEntries(Object.entries(game.sourcePins).filter(([p])=>
    ['Source','Config','Build'].some(name=>p.startsWith(resolve(oldProject,name)+'/'))));
  await pins(oldPins);
  const names=['BreziRuntimeDiagnostics.cpp','BreziRuntimeDiagnostics.h','BreziPawn.cpp','BreziPawn.h'];
  const canonical=resolve(root,'unreal/BreziTwin/Source/BreziTwin');
  const overlay=Object.fromEntries(await Promise.all(names.map(async n=>[n,await readFile(resolve(canonical,n))])));
  // inheritScene has just proved this is an empty, unbuilt destination. Remove
  // only its freshly generated source directory so no unused optimizer header
  // leaks into the diagnostic-only baseline provenance.
  await access(resolve(project,'Binaries')).then(()=>{throw Error('Do not replace built baseline sources');},e=>{if(e.code!=='ENOENT')throw e;});
  await rm(resolve(project,'Source'),{recursive:true});
  for(const name of ['Source','Config','Build'])await cp(resolve(oldProject,name),resolve(project,name),{recursive:true});
  for(const [name,bytes] of Object.entries(overlay))await writeFile(resolve(project,'Source/BreziTwin',name),bytes);
  const final=await inventory(resolve(project,'Source'));
  for(const [p,h] of Object.entries(oldPins))if(p.includes('/Source/')&&!names.includes(p.split('/').at(-1)))
    assert.equal(final[p.replace(oldProject+'/',project+'/')],h,'Baseline renderer changed');
  await save(resolve(output,'baseline-instrumentation.json'),{status:'old-renderer-with-diagnostic-walking',donor,oldPins,
    overlayPins:Object.fromEntries(names.map(n=>[resolve(canonical,n),sha(overlay[n])])),source:final,
    scope:'Original donor render quality, glass, lighting and scene assets; current four diagnostic/Pawn files add opt-in wall-time walking. No optimized render source is compiled.'});
}
export async function verifyInheritedScene({root,output,project}){
  const file=resolve(output,'performance-source.json'),source=await read(file);
  assert.equal(source.status,'verified-scene-inherited');assert.equal(source.project,project);
  await pins(source.receiptPins);await pins(source.sourcePins);await pins(source.geometry);
  const copiedReceipts=Object.fromEntries(Object.entries(source.receiptPins)
    .filter(([p])=>p!==resolve(source.donor,'model-package.json')).map(([p,h])=>[p.replace(source.donor+'/',output+'/'),h]));
  await pins(copiedReceipts);
  const instrumentationFile=resolve(output,'baseline-instrumentation.json');let instrumentationPins={};
  try{
    const instrumented=await read(instrumentationFile);
    assert.equal(instrumented.status,'old-renderer-with-diagnostic-walking');assert.equal(instrumented.donor,source.donor);
    await pins(instrumented.oldPins);await pins(instrumented.overlayPins);
    assert.deepEqual(await inventory(resolve(project,'Source')),instrumented.source);
    instrumentationPins={...instrumented.oldPins,...instrumented.overlayPins,[instrumentationFile]:sha(await readFile(instrumentationFile))};
  }catch(e){if(e.code!=='ENOENT')throw e;}
  let content=source.content,migration=null,migrationPins={};
  try{migration=await read(resolve(output,'performance-scene-report.json'));}catch(e){if(e.code!=='ENOENT')throw e;}
  if(migration){
    assert.equal(migration.status,'performance-scene-validated');
    assert.deepEqual(migration.beforeAssetHashes,source.content);
    for(const field of ['savedReloaded','protectedContentUnchanged','sourceTransformsMaterialsCollisionAndInstancesPreserved'])assert.equal(migration[field],true);
    assert.deepEqual(Object.keys(migration.afterAssetHashes).sort(),Object.keys(source.content).sort());
    for(const [p,h] of Object.entries(source.content))if(p!==resolve(project,'Content/Brezi/Maps/Brezi.umap'))
      assert.equal(migration.afterAssetHashes[p],h,'Migration altered protected asset: '+p);
    const hostFile=resolve(output,'performance-scene-process.json'),host=await read(hostFile);
    assert.equal(host.processFile,resolve(output,'performance-scene.log.json'));
    assert.equal(host.logFile,resolve(output,'performance-scene.log'));
    migrationPins={[hostFile]:sha(await readFile(hostFile)),[host.processFile]:host.processFileSha256,[host.logFile]:host.logSha256,
      [resolve(output,'performance-scene-report.json')]:host.reportSha256};await pins(migrationPins);
    const process=await read(host.processFile);assert.equal(process.code,0);assert.equal(process.signal,null);
    assert.equal(process.pid,migration.nativeProcessId);
    assert(Date.parse(migration.generatedAt)>=Date.parse(process.startedAt)&&Date.parse(migration.generatedAt)<=Date.parse(process.endedAt),
      'Migration report outside native process lifetime');
    content=migration.afterAssetHashes;await pins(migration.pipelineFiles);
  }
  let studyInputs={},experimentalStudy=null;
  if(await access(resolve(output,'nanite-study-report.json')).then(()=>true,e=>{if(e.code==='ENOENT')return false;throw e;})){
    assert(!migration,'Experimental Nanite study must remain separate from production map-only migration');
    const study=await verifyNaniteStudy({root,output,project,source});
    content=study.content;studyInputs=study.inputs;experimentalStudy=study.experimentalStudy;
  }
  assert.deepEqual(await inventory(resolve(project,'Content')),content,'Inherited content inventory changed');
  const base=await read(resolve(output,'model-refresh-import-report.json'));
  const archviz=await read(resolve(output,'archviz-import-report.json'));
  const photoreal=await read(resolve(output,'photoreal-import-report.json'));
  const rural=await read(resolve(output,'rural-import-report.json'));
  const scene=await read(resolve(output,'geometry/scene.json'));
  const canonicalPins={...Object.fromEntries(Object.entries(scene.sourceFiles).map(([p,h])=>[resolve(root,p),h])),
    ...Object.fromEntries(base.materials.textures.map(t=>[resolve(root,t.source),t.sha256]))};
  await pins(canonicalPins);
  assert.equal(sha(await readFile(resolve(output,'geometry/scene.json'))),base.sourceManifestSha256);
  return {imported:{...base,archviz,photoreal,rural,...(experimentalStudy?{experimentalStudy}:{})},inputs:{...content,...source.geometry,...source.receiptPins,...copiedReceipts,...canonicalPins,
    [file]:sha(await readFile(file)),...instrumentationPins,...migrationPins,...(migration?migration.pipelineFiles:{}),...studyInputs}};
}
