import test from "node:test";
import assert from "node:assert/strict";
import { validateTVOakReceipt } from "./package-gate.mjs";

// Deliberately synthetic receipts exercise acceptance/rejection only. They are
// never saved as native evidence and make no Unreal graph execution claim.
function fixture() {
  const hash = "a".repeat(64), ids = ["DOM_01293", "DOM_01296", "DOM_01300"];
  const base = "/Game/Brezi/MaterialStudies/TVPhotoOak/V_0123456789abcdef";
  const material = `${base}/Materials/M_TVCabinetPhotoOak.M_TVCabinetPhotoOak`;
  const pipelineFiles = Object.fromEntries([
    ...["tv_oak.py", "oak_reference.py", "oak-basis.hlsl"].map((name) => `scripts/unreal/tv-oak/${name}`),
    ...["candidate.json", "material-study.json", "source-uv-metric.json", "oak_veneer_01_diff_4k.jpg", "oak_veneer_01_nor_gl_4k.jpg", "oak_veneer_01_rough_4k.jpg"].map((name) => `output/unreal/wood-study/${name}`),
  ].map((file) => [file, hash]));
  const assetHashes = Object.fromEntries(["Materials/M_TVCabinetPhotoOak", "Textures/T_albedo", "Textures/T_normalMap", "Textures/T_roughMap"]
    .map((file) => [`${base.replace("/Game/", "unreal/BreziTwin/Content/")}/${file}.uasset`, hash]));
  const canonicalAssetHashes = { "unreal/BreziTwin/Content/Brezi/Geometry/source.uasset": hash };
  const scene = { objSha256: hash, objects: ids.map((id) => ({ id, sourceId: `source-${id}`, materialSlots: ["MAT_0078"] })) };
  const proof = { asset: material, graphNodes: 19, worldSpaceNormal: true, sourceUVDependency: false, naniteUsage: true,
    textures: Object.fromEntries(["albedo", "normalMap", "roughMap"].map((role) => [role, { pixels: [4096, 4096],
      sourceDimensionReadback: true, wrapXY: true, srgb: role === "albedo", greenFlipped: role === "normalMap", sourceSha256: hash }])) };
  const oak = { status: "native-tv-oak-saved-reload-validated", nativeApplied: true, activationStarted: true,
    rollbackRequired: false, rollbackAttempted: false, sourceManifestSha256: hash, sourceObjSha256: hash,
    selectedIds: ids, woodObjects: 158, preservedWoodObjects: 155, excludedOvalCoffeeTable: "DOM_01326",
    verification: { nativeGraphGetters: true, newAssetsSavedBeforeActivation: true, twoMapReloads: true,
      other155WoodBindingsUnchanged: true, sourceMeshUvCollisionAndAssetBytesUnchanged: true, geometryChanged: false, sourceWebTexturesChanged: false },
    bindings: scene.objects.map((record) => ({ objectId: record.id, sourceId: record.sourceId, sourceSlot: "MAT_0078", material, savedReloadVerified: true, priorOverrides: [] })),
    stagedMaterialProof: structuredClone(proof), savedReloadMaterialProof: structuredClone(proof), pipelineFiles, assetHashes, canonicalAssetHashes };
  return { scene, imported: { tvOak: oak, sourceManifestSha256: hash, pipelineFiles: { ...pipelineFiles }, finalAssetHashes: { ...assetHashes, ...canonicalAssetHashes } } };
}

test("complete native receipt contract is accepted without rendering claims", () => {
  const { imported, scene } = fixture();
  assert.equal(validateTVOakReceipt(imported, scene).status, "native-tv-oak-package-inputs-validated");
});

for (const [name, mutate] of [
  ["missing stage", (f) => { delete f.imported.tvOak; }],
  ["pre-activation graph failure", (f) => { Object.assign(f.imported.tvOak, { status: "failed", nativeApplied: false, activationStarted: false, rollbackErrors: [] }); }],
  ["rollback after activation", (f) => { f.imported.tvOak.rollbackAttempted = true; }],
  ["scene identity drift", (f) => { f.imported.tvOak.sourceManifestSha256 = "b".repeat(64); }],
  ["OBJ identity drift", (f) => { f.scene.objSha256 = "b".repeat(64); }],
  ["oval selection", (f) => { f.imported.tvOak.selectedIds[2] = "DOM_01326"; }],
  ["duplicate binding", (f) => { f.imported.tvOak.bindings[2] = f.imported.tvOak.bindings[0]; }],
  ["extra binding", (f) => { f.imported.tvOak.bindings.push({ ...f.imported.tvOak.bindings[0], objectId: "DOM_01326" }); }],
  ["wrong source ID", (f) => { f.imported.tvOak.bindings[0].sourceId = "unrelated"; }],
  ["wrong source material", (f) => { f.scene.objects[0].materialSlots[0] = "MAT_0064"; }],
  ["unverified binding", (f) => { f.imported.tvOak.bindings[0].savedReloadVerified = false; }],
  ["unowned material", (f) => { f.imported.tvOak.savedReloadMaterialProof.asset = "/Game/Manual.Material"; }],
  ["missing preserved-wood proof", (f) => { delete f.imported.tvOak.verification.other155WoodBindingsUnchanged; }],
  ["reported geometry change", (f) => { f.imported.tvOak.verification.geometryChanged = true; }],
  ["missing first graph proof", (f) => { delete f.imported.tvOak.stagedMaterialProof; }],
  ["changed normal conversion", (f) => { f.imported.tvOak.savedReloadMaterialProof.textures.normalMap.greenFlipped = false; }],
  ["non-4K source", (f) => { f.imported.tvOak.savedReloadMaterialProof.textures.albedo.pixels = [2048, 2048]; }],
  ["changed photograph hash", (f) => { f.imported.tvOak.savedReloadMaterialProof.textures.albedo.sourceSha256 = "b".repeat(64); }],
  ["unmerged recipe", (f) => { delete f.imported.pipelineFiles["scripts/unreal/tv-oak/tv_oak.py"]; }],
  ["missing photographed source pin", (f) => { delete f.imported.tvOak.pipelineFiles["output/unreal/wood-study/candidate.json"]; }],
  ["unmerged new asset", (f) => { delete f.imported.finalAssetHashes[Object.keys(f.imported.tvOak.assetHashes)[0]]; }],
  ["missing new texture package", (f) => { delete f.imported.tvOak.assetHashes[Object.keys(f.imported.tvOak.assetHashes)[1]]; }],
  ["changed preserved asset", (f) => { f.imported.finalAssetHashes[Object.keys(f.imported.tvOak.canonicalAssetHashes)[0]] = "b".repeat(64); }],
]) test(`rejects ${name}`, () => {
  const f = fixture(); mutate(f);
  assert.throws(() => validateTVOakReceipt(f.imported, f.scene), /TV oak package gate:/);
});
