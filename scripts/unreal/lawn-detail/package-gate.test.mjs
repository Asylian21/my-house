import {test} from 'node:test';
import assert from 'node:assert/strict';
import {validateLawnDetailReceipt} from './package-gate.mjs';

// Synthetic receipt fixture exercises packaging rejection, never native proof.
function fixture() {
  const h = 'a'.repeat(64);
  const assetHashes = Object.fromEntries(Array.from({length: 10}, (_, i) =>
    [`unreal/BreziTwin/Content/Brezi/LawnDetail/R_${h.slice(0, 16)}/A${i}.uasset`, h]));
  const pipelineFiles = {'scripts/unreal/lawn-detail/native_layer.py': h};
  const groups = [...'abcd'].map(c => ({prototypeId: `grass_bermuda_01_small_${c}`,
    groupId: `LAWN_grass_bermuda_01_small_${c}`, instances: 10,
    serializedReloadVerified: true, nativeOrderedTransformsSha256: h, maxComponentBoundsErrorCm: .001,
    collision: 'NoCollision', navigation: false, tick: false, cullStartCm: 600, cullEndCm: 1200}));
  return {sourceManifestSha256: h, finalAssetHashes: {...assetHashes}, pipelineFiles: {...pipelineFiles},
    lawnDetail: {status: 'lawn-detail-authored-validated', nativeApplied: true, preservedBaseLawn: true,
      serializedSavedReloadVerified: true, stagedSavedReloadVerified: true, sourceObjectId: 'DOM_00001',
      sourceManifestSha256: h, sourceObjSha256: h, recipeSha256: h, groups, instanceCount: 40,
      material: {masked: true, twoSidedFoliage: true, alphaCutoff: .45, worldPositionOffset: false},
      assetHashes, pipelineFiles}};
}

test('packaging accepts a complete synthetic saved-layer receipt without claiming runtime QA', () => {
  const r = validateLawnDetailReceipt(fixture());
  assert.equal(r.instanceCount, 40); assert.equal(r.runtimeQualityVerified, false);
});
for (const [name, mutate] of [
  ['missing layer', r => delete r.lawnDetail],
  ['unsaved instances', r => r.lawnDetail.groups[0].serializedReloadVerified = false],
  ['duplicate prototype', r => r.lawnDetail.groups[1] = r.lawnDetail.groups[0]],
  ['nonfinite bounds', r => r.lawnDetail.groups[0].maxComponentBoundsErrorCm = NaN],
  ['changed instance count', r => r.lawnDetail.instanceCount++],
  ['walking collision enabled', r => r.lawnDetail.groups[0].collision = 'BlockAll'],
  ['missing final asset', r => delete r.finalAssetHashes[Object.keys(r.finalAssetHashes)[0]]],
  ['changed pipeline', r => r.pipelineFiles[Object.keys(r.pipelineFiles)[0]] = 'b'.repeat(64)],
  ['foreign asset namespace', r => r.lawnDetail.assetHashes['foreign.uasset'] = 'a'.repeat(64)],
]) test(`packaging rejects ${name}`, () => {
  const r = fixture(); mutate(r); assert.throws(() => validateLawnDetailReceipt(r), /Lawn detail:/);
});
