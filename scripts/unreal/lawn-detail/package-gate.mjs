const ids = [...'abcd'].map(c => `grass_bermuda_01_small_${c}`);
const hash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const need = (condition, message) => { if (!condition) throw new Error(`Lawn detail: ${message}`); };

// The package verifies the receipt and its inclusion in the final input/asset
// closure. Native geometry and transforms are checked by the saved-map stage.
export function validateLawnDetailReceipt(imported) {
  const r = imported.lawnDetail;
  need(r?.status === 'lawn-detail-authored-validated' && r.nativeApplied === true
    && r.preservedBaseLawn === true && r.serializedSavedReloadVerified === true
    && r.stagedSavedReloadVerified === true, 'missing saved native layer');
  need(r.sourceObjectId === 'DOM_00001' && r.sourceManifestSha256 === imported.sourceManifestSha256
    && hash(r.sourceObjSha256) && hash(r.recipeSha256), 'source or recipe differs');
  need(r.groups?.length === 4 && new Set(r.groups.map(g => g.prototypeId)).size === 4
    && r.groups.every(g => ids.includes(g.prototypeId) && g.groupId === `LAWN_${g.prototypeId}`), 'four short grass groups required');
  need(Number.isSafeInteger(r.instanceCount) && r.instanceCount > 0 && r.instanceCount <= 100000
    && r.groups.reduce((n, g) => n + g.instances, 0) === r.instanceCount, 'instance count differs');
  for (const g of r.groups) {
    need(Number.isSafeInteger(g.instances) && g.instances > 0 && g.serializedReloadVerified === true
      && hash(g.nativeOrderedTransformsSha256) && Number.isFinite(g.maxComponentBoundsErrorCm)
      && g.maxComponentBoundsErrorCm >= 0 && g.maxComponentBoundsErrorCm <= .05,
    'serialized instances or bounds unverified');
    need(g.collision === 'NoCollision' && g.navigation === false && g.tick === false
      && g.cullStartCm === 600 && g.cullEndCm === 1200, 'runtime grass policy differs');
  }
  need(r.material?.masked === true && r.material.twoSidedFoliage === true
    && r.material.alphaCutoff === .45 && r.material.worldPositionOffset === false,
  'grass material policy differs');
  const prefix = `unreal/BreziTwin/Content/Brezi/LawnDetail/R_${r.recipeSha256.slice(0, 16)}/`;
  need(Object.keys(r.assetHashes ?? {}).length >= 10 && Object.keys(r.pipelineFiles ?? {}).length > 0,
    'asset or pipeline closure missing');
  for (const [file, digest] of Object.entries(r.assetHashes))
    need(file.startsWith(prefix) && hash(digest) && imported.finalAssetHashes?.[file] === digest,
      'owned asset missing from final import');
  for (const [file, digest] of Object.entries(r.pipelineFiles))
    need(hash(digest) && imported.pipelineFiles?.[file] === digest, 'source omitted from final import');
  return {status: 'lawn-package-inputs-validated', instanceCount: r.instanceCount, runtimeQualityVerified: false};
}
