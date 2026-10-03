import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {validateQualityBuildHeader} from '../scripts/unreal/exterior-editor-source-r20.mjs';
const project='/Users/davidzita/www/dom/output/unreal/exterior-20261002-r31a-quality/Project/BreziTwin';
const proof=JSON.parse(await fs.readFile('/Users/davidzita/www/dom/output/unreal/exterior-20261002-r31a-quality/quality-editor-build-proof-r3.json','utf8'));
test('actual completed header-only Editor build has the reviewed identity',()=>validateQualityBuildHeader(proof,{project}));
test('an old copied module cannot establish the new Cinematic recipe',()=>{
  const b=structuredClone(proof);b.newModule.sha256='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
  assert.throws(()=>validateQualityBuildHeader(b,{project}));
});
test('failed, pending or misbound builds cannot inherit the successful proof',()=>{
  for(const change of [{actualNativeBuildExitCode:1},{nativeBuildExecuted:false},{project:'/tmp/other'}])
    assert.throws(()=>validateQualityBuildHeader({...proof,...change},{project}));
});
test('compilation alone cannot silently promote appearance or Shipping acceptance',()=>{
  for(const key of ['appearanceAccepted','performanceAccepted','shippingVerified','fullPhotorealismAccepted'])
    assert.throws(()=>validateQualityBuildHeader({...proof,[key]:true},{project}));
});
