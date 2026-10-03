// Changed camera-stage contract fixtures only; no project writes or native launch.
import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {validateByteInsertion,validateCameraStageHeader} from './exterior-editor-source-r29-r3-camera.mjs';

const sha=b=>createHash('sha256').update(b).digest('hex');
const root='/Users/davidzita/www/dom',source=root+'/output/unreal/exterior-20261002-r38b-two-camera-candidate-r29-r3';
const native=root+'/output/unreal/exterior-20261002-r38b';
const close={id:'exterior-context-yard-572063-close-r18',targetCm:[1,2,35]};
const ground={id:'exterior-neighborhood-ground-r38',label:'Dvor · pôvodné hranice',eyeCm:[5900,24700,165],targetCm:[7800,28500,185],horizontalFovDegrees:72};
function insertedFixture(){
  const original=Buffer.from(JSON.stringify({coordinateSystem:'cm',defaultView:'exterior-garden',views:[{id:'exterior-garden',label:'Záhrada · "[pôvodné]"'}],sun:{angle:35}},null,2)+'\n');
  const n=original.indexOf('\n  ],');
  const entries=[close,ground].map(v=>JSON.stringify(v,null,2).split('\n').map(line=>'    '+line).join('\n'));
  // The Python producer preserves a float spelling which JS would serialize as35.
  const insertion=Buffer.from(',\n'+entries.join(',\n').replace('      35\n','      35.0\n'));
  const payload=Buffer.concat([original.subarray(0,n),insertion,original.subarray(n)]);
  return{original,payload,proof:{insertionOffsetBytes:n,insertedBytes:insertion.length,
    allOriginalDataBytesPreservedOutsideInsertion:true,originalFileSha256:sha(original),
    originalPrefixSha256:sha(original.subarray(0,n)),originalSuffixSha256:sha(original.subarray(n)),insertedBytesSha256:sha(insertion)}};
}
function stage(){return{
  schema:'brezi-saved-r38r2-two-camera-data-only-qa-clone-r29-r3',schemaVersion:1,
  owner:'scripts/unreal/exterior-soft-ground-camera-stage-r29-r3.py',status:'verified-independent-saved-r38r2-two-camera-data-only-qa-clone-r29-r3',
  sourceNativeOutput:native,project:source+'/Project/BreziTwin',
  sourceNativeReport:{path:native+'/soft-ground-native-report-r2.json',sha256:'077e36066dc49f2c3fa379893c39fc5659e8261385030d86266316e1bde9f2b9'},
  sourceNativeProcess:{path:native+'/soft-ground-native-r2-process.json',sha256:'c5fb163aa2989503b842d17dd464ec5baae88f881a3f543207101a7f640fa3e5'},
  sourceCurrentByteAudit:{path:native+'/root-native-success-byte-audit-r38b-r2.json',sha256:'a30063dc99bd3fa3fcd7d202aa77209b74f36c06bde77a47fba1c071564c5edb'},
  projectClone:{sha256:'08a3e767db06eaa2d96a7466533faa883b4f61100670999358fa4ca4fbe3c536'},
  frozenCloseSupplement:{sha256:'768274f6eb2dab6d7bcd0bee2b930feec8e2665bba7dfafb6e929f35b38ebab1'},
  cameraProposal:{sha256:'ab77379c4f97dd351b15c4e48d0791825ec3f5eab685efddc659bad6cb9ec996'},
  appendedViewCount:2,originalContentFileCount:4103,protectedFileCount:132,changedContentFiles:['Data/viewpoints.json'],
  originalViewsPrefixPreserved:true,lightingUnchanged:true,nativeSourceUnchanged:true,allOriginalProjectFilesIndependentBeforeStage:true,
  sceneMapChanged:false,nativeExecuted:false,nativeCameraRuntimeVerified:false,nativeAppearanceAccepted:false,
  performanceAccepted:false,fullPhotorealismAccepted:false,shippingPackageProduced:false,currentVegetationVisibilityRecomputed:false,walkingOrCollisionAccepted:false,
  sourceCameraScope:'FROZEN_R18_CLOSE_PLUS_R37_SOURCE_FRAMING_ONLY_GROUND_VIEW'};}

test('exact UTF8 prefix/suffix and Python float spelling pass',()=>{
  const x=insertedFixture();assert(x.payload.includes('35.0'));
  validateByteInsertion(x.original,x.payload,x.proof,close,ground);
});
test('altered original prefix fails despite valid insertion',()=>{
  const x=insertedFixture(),changed=Buffer.from(x.payload);changed[2]^=1;
  assert.throws(()=>validateByteInsertion(x.original,changed,x.proof,close,ground));
});
test('wrong ground camera FOV fails',()=>{
  const x=insertedFixture();assert.throws(()=>validateByteInsertion(x.original,x.payload,x.proof,close,{...ground,horizontalFovDegrees:73}));
});
test('actual typed stage shape passes but copied native report rejects',()=>{
  validateCameraStageHeader(stage(),{source,root,names:[]});
  assert.throws(()=>validateCameraStageHeader(stage(),{source,root,names:['soft-ground-native-report-r2.json']}));
});
test('foreign clone source rejects',()=>{
  const s=stage();s.sourceNativeOutput=native+'-other';assert.throws(()=>validateCameraStageHeader(s,{source,root,names:[]}));
});
test('native visibility claim rejects',()=>{
  const s=stage();s.nativeCameraRuntimeVerified=true;assert.throws(()=>validateCameraStageHeader(s,{source,root,names:[]}));
});
