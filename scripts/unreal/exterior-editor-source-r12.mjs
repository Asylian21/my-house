// Closed actual saved R24b R2 original-tree reader. Built Nanite data is not a rendered-pass proof.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR10,validateProjectClosure} from './exterior-editor-source-r10.mjs';
export {validateProjectClosure};
const OWNER='scripts/unreal/exterior-original-tree-native-r2.py';
const HELPER_SHA='c719f61f70bafd53e296cc2ac7167233a604e0f69692381bb6951e3a0a381f87';
const REPORT_SHA='869ed396ed7946cb0ea562d3f2da77f8dbd9f3d65777250b9686171697aa10f1';
const PREFLIGHT_SHA='745b78be48b25ecdcfdeef60deb43878d723b61f001a8f4a28f32c54f70418d3';
const R10_SHA='23652e2dd8969e57fa85c0e3cb935317cb452417964748fd66f4602720563756';
const CHECKER_SHA='79e7ada622b0fc2555d6bb0949de169a200b65ee6582a22453ccfa97ec7c6257';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const exec=promisify(execFile),read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const sha=async file=>{const h=createHash('sha256');for await(const b of createReadStream(file))h.update(b);return h.digest('hex');};

export function validateTreeHeader(r,{source,project}){
  assert.equal(r.schemaVersion,2);assert.equal(r.owner,OWNER);assert.equal(r.status,'verified-saved-single-original-tree-overlay');
  assert.equal(r.output,source);assert.equal(r.project,project);assert.equal(r.nativeProcessId,60411);
  assert.equal(r.savedMapUnloadedReloaded,true);assert.equal(r.originalSavedR22Unchanged,true);
  assert.deepEqual(r.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(r.setbacksMm,{street:3000,east:3000});
  assert.equal(r.sourceStudy.sha256,'c45ff265adc98c394a58b69167066f3445f53800d4c6d9aa7fdb7d0cc1eb1ba6');
  assert.equal(r.tangentSupplement.sha256,'0e24b32ffc0f65d5888bb33c1410b0f42769e831e53523559bb884f1aeec0025');
  assert.equal(r.sourcePreflight.sha256,PREFLIGHT_SHA);assert.equal(r.baseNativeReport.sha256,'999fc17ea7600136a2097aecefed3d846ff0d7e9baeb7f005480b113b60b1f40');
  for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified',
    'ecologicalFitVerified','nativeNormalTangentReadbackAvailable','naniteRenderPassVerified',
    'nativeGeometryPackagesIndependentlyReloaded','nativeMaterialsPackagesIndependentlyReloaded','sourceRootGroundElevationSurveyed'])assert.equal(r[k],false);
  assert.equal(r.originalActorCount,5346);assert.equal(r.savedActorCount,5347);assert.equal(r.newTreeActors,1);assert.equal(r.retiredTreeInstances,1);
  assert.equal(r.retainedOriginalTreeInstances,3);assert.equal(r.originalMaterialGraphsPreserved,56);assert.equal(r.originalTextureObjectsPreserved,84);
  assert.equal(r.materials.materialCount,3);assert.equal(r.materials.textureCount,10);
}

export function validateTreeProofLimits(r,pf){
  const geo=r.nativeSourceGeometry,n=r.naniteResourceReadback;
  assert.equal(geo.sourceTriangles,2062487);assert.equal(geo.sourceDescriptionVertices,1777278);assert.equal(geo.sourceLODCount,1);
  assert.equal(geo.sampledNativeTriangles,4096);assert.equal(geo.unsampledNativeTriangles,2058391);
  assert.equal(geo.nativeFullPositionUV0UV1CornerReadbackPerformed,false);assert.equal(geo.nativeNormalTangentReadbackAvailable,false);
  assert.equal(geo.nativeTangentHandednessVerified,false);assert.equal(geo.nativeSampledPositionUV0UV1SectionOrderVerified,true);
  assert.equal(geo.nativeSourceSectionPolygonCountsVerified,true);assert.equal(geo.renderFallbackTriangles,2247);assert.equal(geo.renderFallbackSections,3);
  assert.equal(n.nativeResourceInputTriangles,2062487);assert.equal(n.nativeResourceInputVertices,1777276);
  assert.equal(n.enabled,true);assert.equal(n.actualNonemptyResourceGetterVerified,true);assert.equal(n.nativeRenderPassVerified,false);
  assert.equal(n.performanceAccepted,false);assert.equal(n.shippingVerified,false);assert.equal(geo.sourceSections.length,3);
  for(const [i,row]of geo.sourceSections.entries()){
    const wanted=pf.nativeExpectedSections[i];assert.equal(row.section,i);assert.equal(row.material,wanted.material);
    assert.equal(row.sourceSectionPolygonCount,wanted.triangles);assert.deepEqual(row.sampleTriangleIndices,wanted.sampleTriangleIndices);
    assert.equal(row.sampleTriangles,wanted.sampleTriangles);assert.equal(row.sampledFloat32PositionUV0UV1OrderedCornerSha256,wanted.sampledFloat32PositionUV0UV1OrderedCornerSha256);
    assert.equal(row.fullSourceCornerHashCpuOnly,wanted.orderedFloat32PositionUV0UV1CornersSha256);
  }
  const retired=r.originalRootRetirement;
  assert.equal(retired.retiredOriginalIndex,0);assert.deepEqual(retired.retainedOriginalIndices,[1,2,3]);assert.equal(retired.storedMatricesBefore.length,4);
  assert.deepEqual(retired.storedMatricesRetained,retired.storedMatricesBefore.slice(1));assert.deepEqual(retired.nativeRemovalInitialOrder,[3,1,2]);
  assert.equal(retired.allRetainedNativeMatrixAndRecoveredTransformBytesExact,true);assert.equal(retired.retainedSourceOrderRestoredWithoutTransformRecomposition,true);
}

export function validateTreeContent(before,after,packages,delta){
  assert.equal(Object.keys(before).length,4049);assert.equal(Object.keys(after).length,4066);assert.equal(packages.length,17);
  assert.equal(new Set(packages).size,17);assert(packages.every(p=>p.startsWith('Brezi/OriginalTree20261002R24/')&&p.endsWith('.uasset')));
  assert.deepEqual(Object.keys(after).filter(p=>!Object.hasOwn(before,p)).sort(),[...packages].sort());
  assert.deepEqual(Object.keys(before).filter(p=>!Object.hasOwn(after,p)),[]);
  assert.deepEqual(Object.keys(before).filter(p=>before[p].sha256!==after[p].sha256||before[p].bytes!==after[p].bytes).sort(),['Brezi/Maps/Brezi.umap']);
  assert.deepEqual(delta,{changedOriginalFiles:['Brezi/Maps/Brezi.umap'],newPackageFiles:[...packages].sort(),originalContentFiles:4049,
    savedContentFiles:4066,unchangedOriginalContentFiles:4048,newPackages:17});
}

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);const name='original-tree-native-report-r2.json',names=await fs.readdir(source);
  const previous=fileURLToPath(new URL('exterior-editor-source-r10.mjs',import.meta.url));assert.equal(await sha(previous),R10_SHA);
  if(!names.includes(name)){
    assert(!/^exterior-20261002-r24/.test(path.basename(source))&&!names.some(n=>/^original-tree-native-report/.test(n)),
      'Failed/running/unknown tree candidate cannot inherit an old native receipt');
    const evidence=await loadR10(source,{root});evidence.additionalClosureFiles.push(previous);return evidence;
  }
  assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r24b'));
  assert(!names.some(n=>n==='exterior-import-report.json'||(n!==name&&/^original-tree-native-report/.test(n))||/^realism-integration-native-report/.test(n)),
    'Original-tree candidate may not carry a copied/failed historical report');
  const project=path.join(source,'Project/BreziTwin'),receiptPath=path.join(source,name),r=await read(receiptPath),closure=new Set([receiptPath,previous]);
  assert.equal(await sha(receiptPath),REPORT_SHA);validateTreeHeader(r,{source,project});
  async function pinned(p){
    assert(p&&path.isAbsolute(p.path)&&path.resolve(p.path)===p.path&&/^[a-f0-9]{64}$/.test(p.sha256)&&Number.isInteger(p.bytes)&&p.bytes>=0);
    const stat=await fs.lstat(p.path);assert(stat.isFile()&&!stat.isSymbolicLink());assert.equal(stat.size,p.bytes);assert.equal(await sha(p.path),p.sha256);
    closure.add(p.path);return p.path;
  }
  const pj=async p=>read(await pinned(p));
  const baseEvidence=await loadR10(path.join(root,'output/unreal/exterior-20261002-r22c'),{root});
  baseEvidence.additionalClosureFiles.forEach(p=>closure.add(p));
  const pf=await pj(r.sourcePreflight);assert.equal(pf.owner,OWNER);assert.equal(pf.schemaVersion,2);assert.equal(pf.nativeApplied,false);
  assert.deepEqual(r.inputFiles,pf.inputFiles);assert.deepEqual(r.pipelineFiles,pf.pipelineFiles);assert.deepEqual(r.importOrderRepair,pf.importOrderRepair);
  assert.deepEqual(r.projectClone,pf.candidateProjectClone);validateTreeProofLimits(r,pf);
  for(const[file,h]of Object.entries({...r.inputFiles,...r.pipelineFiles})){const s=await fs.stat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  assert.equal(r.pipelineFiles[path.join(root,OWNER)],HELPER_SHA);
  for(const key of ['sourceStudy','tangentSupplement','projectClone','baseNativeReport','baseNativeHelper','beforeActorWitness','expectedActorWitness',
    'savedActorWitness','originalMaterialTextureBefore','originalMaterialTextureSaved','baseContentInventory','afterContentInventory','protectedProjectProof'])await pinned(r[key]);
  const contentInventory=await pj(r.afterContentInventory),before=await pj(r.baseContentInventory),projectProof=await pj(r.protectedProjectProof);
  assert.deepEqual(before,baseEvidence.contentInventory);assert.deepEqual(projectProof,baseEvidence.projectProof);assert.equal(Object.keys(projectProof).length,132);
  validateTreeContent(before,contentInventory,r.newContentPackages,r.assetDelta);
  const checker=path.join(root,'scripts/unreal/exterior-original-tree-editor-check-r12.py');closure.add(checker);assert.equal(await sha(checker),CHECKER_SHA);
  const summary=JSON.parse((await exec('python3',['-B',checker,receiptPath],{timeout:120000,maxBuffer:1024*1024})).stdout);
  const processPath=path.join(source,'original-tree-native-r2.log.json'),processReceiptPath=path.join(source,'original-tree-native-r2-process.json');
  const raw=await read(processPath),terminal=await read(processReceiptPath);
  assert.equal(raw.code,0);assert.equal(raw.signal,null);assert.equal(raw.pid,r.nativeProcessId);assert.equal(terminal.reportSha256,REPORT_SHA);
  assert.equal(terminal.processFile,processPath);assert.equal(terminal.processFileSha256,await sha(processPath));
  assert.equal(terminal.logFile,path.join(source,'original-tree-native-r2.log'));assert.equal(terminal.logSha256,await sha(terminal.logFile));
  assert.equal(terminal.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(terminal.sourcePinsBeforeNative).length,566);
  for(const[file,h]of Object.entries(terminal.sourcePinsBeforeNative)){const s=await fs.stat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const file of [processPath,processReceiptPath,terminal.logFile,terminal.controller])closure.add(file);
  const w=r.nativeModuleWitness;assert.equal(w.sha256,MODULE_SHA);assert.equal(w.bytes,2818384);assert.equal(w.independentInodes,true);
  assert.equal(w.source,path.join(root,'output/unreal/exterior-20261002-r22c/Project/BreziTwin/Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));
  assert.equal(w.destination,path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));
  const[a,b]=await Promise.all([fs.stat(w.source),fs.stat(w.destination)]);assert(a.dev!==b.dev||a.ino!==b.ino);assert.equal(b.size,w.bytes);
  assert.equal(await sha(w.source),MODULE_SHA);assert.equal(await sha(w.destination),MODULE_SHA);closure.add(w.source);closure.add(w.destination);
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base:baseEvidence.base,summary,contentInventory,projectProof,
    additionalClosureFiles:[...closure],nativeModuleWitness:w,moduleWitnessSource:r.sourcePreflight,
    receiptSummary:{baseNativeReport:r.baseNativeReport,sourceStudy:r.sourceStudy,tangentSupplement:r.tangentSupplement,
      importOrderRepair:r.importOrderRepair.diagnosticReport,savedMapUnloadedReloaded:true,summary}};
}
