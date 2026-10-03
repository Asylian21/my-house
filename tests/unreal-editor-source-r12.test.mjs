import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateTreeHeader,validateTreeProofLimits,validateTreeContent} from '../scripts/unreal/exterior-editor-source-r12.mjs';
const root=fileURLToPath(new URL('../',import.meta.url)),source=path.join(root,'output/unreal/exterior-20261002-r24b');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const r=read(path.join(source,'original-tree-native-report-r2.json')),pf=read(r.sourcePreflight.path);

test('actual successful tree header stays closed to failed/old owners and acceptance upgrades',()=>{
  const options={source,project:path.join(source,'Project/BreziTwin')};validateTreeHeader(r,options);
  for(const[k,v]of [['status','original-tree-native-failed'],['status','original-tree-native-running'],['schemaVersion',1],
    ['owner','scripts/unreal/exterior-original-tree-native.py'],['nativeAppearanceAccepted',true],['naniteRenderPassVerified',true]]){
    const bad=structuredClone(r);bad[k]=v;assert.throws(()=>validateTreeHeader(bad,options));
  }
});

test('source full census, exact samples and actual fallback/Nanite input counts remain separate',()=>{
  validateTreeProofLimits(r,pf);
  for(const[k,v]of [['nativeFullPositionUV0UV1CornerReadbackPerformed',true],['nativeNormalTangentReadbackAvailable',true],
    ['renderFallbackTriangles',2062487],['unsampledNativeTriangles',0]]){
    const bad=structuredClone(r);bad.nativeSourceGeometry[k]=v;assert.throws(()=>validateTreeProofLimits(bad,pf));
  }
  const bad=structuredClone(r);bad.nativeSourceGeometry.sourceSections[0].sampledFloat32PositionUV0UV1OrderedCornerSha256='0'.repeat(64);
  assert.throws(()=>validateTreeProofLimits(bad,pf));
});

test('remaining three actual tree matrices preserve original order without reconstruction',()=>{
  const bad=structuredClone(r);bad.originalRootRetirement.storedMatricesRetained.reverse();assert.throws(()=>validateTreeProofLimits(bad,pf));
  const changed=structuredClone(r);changed.originalRootRetirement.storedMatricesRetained[0][3][0]+=.001;
  assert.throws(()=>validateTreeProofLimits(changed,pf));
});

test('actual seventeen-package/map-only delta rejects original assets or an unregistered namespace',()=>{
  const before=read(r.baseContentInventory.path),after=read(r.afterContentInventory.path);
  validateTreeContent(before,after,r.newContentPackages,r.assetDelta);
  const changed=structuredClone(after),key=Object.keys(before).find(k=>k!=='Brezi/Maps/Brezi.umap');changed[key].sha256='0'.repeat(64);
  assert.throws(()=>validateTreeContent(before,changed,r.newContentPackages,r.assetDelta));
  const packages=[...r.newContentPackages];packages[0]='Brezi/Foreign/mesh.uasset';
  assert.throws(()=>validateTreeContent(before,after,packages,r.assetDelta));
});
