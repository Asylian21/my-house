// Pure receipt gate; no process, renderer, filesystem or native API calls.
const ids = ["DOM_01293", "DOM_01296", "DOM_01300"];
const recipeFiles = [
  "scripts/unreal/tv-oak/tv_oak.py", "scripts/unreal/tv-oak/oak_reference.py", "scripts/unreal/tv-oak/oak-basis.hlsl",
  "output/unreal/wood-study/candidate.json", "output/unreal/wood-study/material-study.json", "output/unreal/wood-study/source-uv-metric.json",
  "output/unreal/wood-study/oak_veneer_01_diff_4k.jpg", "output/unreal/wood-study/oak_veneer_01_nor_gl_4k.jpg", "output/unreal/wood-study/oak_veneer_01_rough_4k.jpg",
];
const digest = (value) => typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
const require = (value, message) => { if (!value) throw new Error(`TV oak package gate: ${message}`); };
const exactIds = (actual) => Array.isArray(actual) && actual.length === ids.length && [...actual].sort().every((id, i) => id === ids[i]);

export function validateTVOakReceipt(imported, scene) {
  const oak = imported?.tvOak;
  require(oak?.status === "native-tv-oak-saved-reload-validated" && oak.nativeApplied === true
    && oak.activationStarted === true && oak.rollbackRequired === false && oak.rollbackAttempted === false,
  "missing successful native activation and saved reload");
  require(Array.isArray(scene?.objects) && oak.sourceManifestSha256 === imported.sourceManifestSha256 && digest(oak.sourceManifestSha256)
    && oak.sourceObjSha256 === scene?.objSha256 && digest(oak.sourceObjSha256), "source scene/OBJ provenance differs");
  require(exactIds(oak.selectedIds) && oak.woodObjects === 158 && oak.preservedWoodObjects === 155
    && oak.excludedOvalCoffeeTable === "DOM_01326", "three-body scope or preserved wood coverage differs");
  for (const flag of ["nativeGraphGetters", "newAssetsSavedBeforeActivation", "twoMapReloads", "other155WoodBindingsUnchanged", "sourceMeshUvCollisionAndAssetBytesUnchanged"])
    require(oak.verification?.[flag] === true, `missing native provenance flag ${flag}`);
  require(oak.verification?.geometryChanged === false && oak.verification?.sourceWebTexturesChanged === false, "source mutation reported");
  require(Array.isArray(oak.bindings) && exactIds(oak.bindings.map((binding) => binding?.objectId)), "expected three unique saved bindings");
  const material = oak.savedReloadMaterialProof?.asset;
  require(typeof material === "string" && /^\/Game\/Brezi\/MaterialStudies\/TVPhotoOak\/V_[a-f0-9]{16}\/Materials\/M_TVCabinetPhotoOak\.M_TVCabinetPhotoOak$/.test(material), "unowned material binding");
  for (const binding of oak.bindings) {
    const records = scene.objects.filter((record) => record.id === binding.objectId);
    require(records.length === 1 && binding.sourceId === records[0].sourceId && records[0].materialSlots?.length === 1
      && records[0].materialSlots[0] === "MAT_0078" && binding.sourceSlot === "MAT_0078"
      && binding.savedReloadVerified === true && binding.material === material && Array.isArray(binding.priorOverrides),
    `source identity or saved material binding differs: ${binding.objectId}`);
  }
  for (const stage of ["stagedMaterialProof", "savedReloadMaterialProof"]) {
    const proof = oak[stage];
    require(proof?.asset === material && proof.graphNodes === 19 && proof.worldSpaceNormal === true
      && proof.sourceUVDependency === false && proof.naniteUsage === true, `incomplete graph proof: ${stage}`);
    for (const [role, suffix] of [["albedo", "diff"], ["normalMap", "nor_gl"], ["roughMap", "rough"]]) {
      const texture = proof.textures?.[role];
      require(texture?.pixels?.length === 2 && texture.pixels.every((size) => size === 4096)
        && texture.sourceDimensionReadback === true && texture.wrapXY === true
        && texture.srgb === (role === "albedo") && texture.greenFlipped === (role === "normalMap")
        && digest(texture.sourceSha256) && texture.sourceSha256 === oak.pipelineFiles?.[`output/unreal/wood-study/oak_veneer_01_${suffix}_4k.jpg`],
      `incomplete photographed texture provenance: ${stage}.${role}`);
    }
  }
  require(recipeFiles.every((file) => digest(oak.pipelineFiles?.[file])), "missing source/photo/recipe hashes");
  for (const [file, hash] of Object.entries(oak.pipelineFiles))
    require(digest(hash) && imported.pipelineFiles?.[file] === hash, `recipe missing from final provenance: ${file}`);
  const prefix = material.split("/Materials/")[0].replace("/Game/", "unreal/BreziTwin/Content/") + "/";
  const expectedAssets = ["Materials/M_TVCabinetPhotoOak", "Textures/T_albedo", "Textures/T_normalMap", "Textures/T_roughMap"];
  require(expectedAssets.every((file) => digest(oak.assetHashes?.[`${prefix}${file}.uasset`])), "missing saved material/texture packages");
  for (const [file, hash] of Object.entries(oak.assetHashes))
    require(file.startsWith(prefix) && digest(hash) && imported.finalAssetHashes?.[file] === hash, `asset missing from final provenance: ${file}`);
  require(Object.keys(oak.canonicalAssetHashes ?? {}).length > 0, "missing preserved source asset hashes");
  for (const [file, hash] of Object.entries(oak.canonicalAssetHashes))
    require(digest(hash) && imported.finalAssetHashes?.[file] === hash, `preserved source asset missing from final provenance: ${file}`);
  return { status: "native-tv-oak-package-inputs-validated", selectedIds: [...ids] };
}
