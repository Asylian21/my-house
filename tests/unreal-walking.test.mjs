import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { buildWalkingContract, exportWalking, readWalkingConstants, walkingBoundsToUnreal } from "../scripts/unreal/walking.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const viewport = await readFile(resolve(root, "lib/twin-viewport-contract.ts"), "utf8");
const constants = readWalkingConstants(viewport);
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const provenance = { sceneSha256: "a".repeat(64), viewportSha256: sha(viewport), writerSha256: "b".repeat(64) };

function object(index, metadata, extra = {}) {
  return { id: `DOM_${String(index).padStart(5, "0")}`, sourceId: "repeated Babylon mesh ID", name: `Fixture ${index}`,
    enabled: true, triangles: 2, instances: 1, boundsMm: { min: [100, 200, -9], max: [900, 1200, -9] },
    metadata: { babylonCheckCollisions: false, ...metadata }, ...extra };
}
const surface = (id, offset = 0) => ({ walkSurface: true, walkSurfaceId: id, walkSurfaceKind: "exterior", walkSurfaceElevationOffsetM: offset });
function fixture() {
  return {
    units: "millimetres", coordinateSystem: "right-handed Z-up", sceneCenterMm: { x: 15200, y: 10800 }, layoutId: "fixture",
    objects: [
      object(0, surface("deck-authored", 0.029)),
      object(1, { cameraOccluder: true }),
      object(2, { cameraOccluder: true, dynamicCameraOccluder: true, doorId: "DOOR-A", doorMotion: "HINGED" }),
      object(3, { ...surface("closed-hatch"), cameraOccluder: true, dynamicCameraOccluder: true, doorId: "HATCH-A" }),
      object(4, { dynamicCameraOccluder: true, doorId: "HANDLE-ONLY", doorMotion: "HINGED" }),
      object(5, surface("disabled-surface"), { enabled: false }),
      object(6, surface("overlay-surface"), { name: "Bazén · odraz oblohy" }),
    ],
  };
}

test("extracts actual source units and deliberately records capsule adaptation and native gaps", () => {
  const value = buildWalkingContract(fixture(), constants, provenance);
  assert.equal(value.eyeHeightCm, 165);
  assert.deepEqual(value.speedsCmPerSecond, { precision: 50, normal: 115, boost: 240 });
  assert.equal(value.maxStepHeightCm, 22);
  assert.equal(value.maxDropCm, 78);
  assert.equal(value.capsuleRadiusCm, 22);
  assert.equal(value.capsuleHalfHeightCm, 85);
  assert.deepEqual(value.sourceCollider, { kind: "ellipsoid", ellipsoidRadiiCm: [22, 22, 80], centerOffsetCm: [0, 0, 82],
    topAboveFloorCm: 162, bottomAboveFloorCm: 2 });
  assert.equal(value.nativeAdaptation.eyeOffsetFromCenterCm, 80);
  assert.equal(value.nativeAdaptation.floorClearancePolicy, "engine-floor-gap-compensated-in-camera");
  assert.equal(value.nativeAdaptation.geometricallyIdentical, false);
  assert.deepEqual(value.nativeValidation, { characterMovementImplemented: false, collisionQueriesVerified: false, runtimeWalkingVerified: false });
});

test("reads a changed source speed instead of a copied default and rejects executable initializers", () => {
  const edited = readWalkingConstants(viewport.replace("normal: 1.15", "normal: 1.27"));
  assert.equal(buildWalkingContract(fixture(), edited, provenance).speedsCmPerSecond.normal, 127);
  assert.throws(() => readWalkingConstants(viewport.replace("WALK_EYE_HEIGHT_M = 1.65", "WALK_EYE_HEIGHT_M = (() => 1.65)()")), /Unsupported walking constant/);
  assert.throws(() => readWalkingConstants(viewport.replace("WALK_EYE_HEIGHT_M", "NO_EYE_HEIGHT")), /Missing walking source constants/);
});

test("offsets are exact vertical support translations and bounds flip plan Y without becoming floor meshes", () => {
  const scene = fixture(), before = structuredClone(scene);
  const value = buildWalkingContract(scene, constants, provenance);
  const deck = value.walkSurfaces[0];
  assert.deepEqual(deck.nativeBoundsCm, { min: [10, -120, -0.9], max: [90, -20, -0.9] });
  assert.equal(deck.supportOffsetCm, 2.9);
  assert.equal(deck.sourceElevationOffsetMm, 29);
  assert.deepEqual(deck.supportTranslationCm, [0, 0, 2.9]);
  assert.equal(deck.query, "source-triangle-hit-plus-authored-vertical-offset");
  assert.deepEqual(deck.sourceGeometry, { objectId: "DOM_00000", triangles: 2, instances: 1 });
  assert(deck.runtimeTags.includes("BreziWalkSurfaceId=deck-authored"));
  assert(deck.supportRuntimeTags.includes("BreziSupportOffsetCm=2.9"));
  assert.equal(value.collisionContract.boundsAreBroadPhaseOnly, true);
  assert.deepEqual(scene, before, "Exporter must not shift the visual scene");
});

test("includes source door and hatch blockers, excludes decorative members and archive overlays", () => {
  const value = buildWalkingContract(fixture(), constants, provenance);
  assert.deepEqual(value.staticBlockers.map((o) => o.objectId), ["DOM_00000", "DOM_00001"]);
  assert.deepEqual(value.walkSurfaces.map((o) => o.objectId), ["DOM_00000", "DOM_00003"]);
  assert.deepEqual(value.capturedClosedBlockers.map((o) => [o.objectId, o.doorId, o.motion]),
    [["DOM_00002", "DOOR-A", "HINGED"], ["DOM_00003", "HATCH-A", null]]);
  assert(value.capturedClosedBlockers.every((o) => o.collisionRequired && o.requiredState === "captured-closed"));
  assert.equal(value.summary.excludedDynamicMembers, 1);
  assert.equal(value.summary.archivedObjects, 2);
  assert.equal(value.collisionContract.doorAnimationExported, false);
  assert.equal(value.collisionContract.doorProgressSerializedByScene, false);
});

test("preserves actual Babylon-only wall collision regardless of display name or material semantics", () => {
  const scene = fixture();
  scene.objects.push(object(7, { entityId: "HOUSE-DESIGN", babylonCheckCollisions: true }, { name: "arbitrary label" }));
  scene.objects.push(object(8, { entityId: "HOUSE-DESIGN" }, { name: "Vnútorná stena · decorative non-collider" }));
  const before = structuredClone(scene), value = buildWalkingContract(scene, constants, provenance);
  const wall = value.staticBlockers.find((r) => r.objectId === "DOM_00007");
  assert(wall && wall.babylonCheckCollisions && wall.collisionRequired);
  assert.deepEqual(wall.collisionReasons, ["babylon-check-collisions"]);
  assert.equal(wall.cameraOccluder, false);
  assert(!value.staticBlockers.some((r) => r.objectId === "DOM_00008"));
  assert.deepEqual(scene, before, "Collision export must not mutate source geometry or IDs");
});

test("a dynamic Babylon collider remains captured-closed rather than becoming a static or walkable wall", () => {
  const scene = fixture(); scene.objects.push(object(7, { babylonCheckCollisions: true, doorId: "SOURCE-DOOR", doorMotion: "HINGED" }));
  const value = buildWalkingContract(scene, constants, provenance);
  assert(value.capturedClosedBlockers.some((r) => r.objectId === "DOM_00007"));
  assert(!value.staticBlockers.some((r) => r.objectId === "DOM_00007"));
  assert(!value.walkSurfaces.some((r) => r.objectId === "DOM_00007"));
});

test("legacy manifests without collision properties are rejected instead of silently dropping walls", () => {
  for (const flag of [undefined, "true", 1, null]) {
    const scene = fixture(); scene.objects[0].metadata.babylonCheckCollisions = flag;
    assert.throws(() => buildWalkingContract(scene, constants, provenance), /missing captured babylonCheckCollisions; re-export/);
  }
});

test("rejects identity ambiguity, unknown surface offsets and malformed collision metadata", () => {
  const duplicate = fixture(); duplicate.objects[1].id = duplicate.objects[0].id;
  assert.throws(() => buildWalkingContract(duplicate, constants, provenance), /Duplicate source object ID/);
  const surfaceDuplicate = fixture(); surfaceDuplicate.objects[3].metadata.walkSurfaceId = "deck-authored";
  assert.throws(() => buildWalkingContract(surfaceDuplicate, constants, provenance), /Duplicate walkSurfaceId/);
  for (const value of [undefined, NaN, "0.029"]) {
    const missing = fixture(); missing.objects[0].metadata.walkSurfaceElevationOffsetM = value;
    assert.throws(() => buildWalkingContract(missing, constants, provenance), /walkSurfaceElevationOffsetM must be finite/);
  }
  const door = fixture(); delete door.objects[2].metadata.doorId;
  assert.throws(() => buildWalkingContract(door, constants, provenance), /dynamic blocker lacks doorId/);
  const flag = fixture(); flag.objects[0].metadata.walkSurface = "true";
  assert.throws(() => buildWalkingContract(flag, constants, provenance), /invalid walkSurface/);
});

test("rejects wrong axes, nonfinite/inverted geometry and a capsule shorter than the source eye", () => {
  const scene = fixture(); scene.units = "metres";
  assert.throws(() => buildWalkingContract(scene, constants, provenance), /millimetre scene/);
  assert.throws(() => walkingBoundsToUnreal({ min: [2, 0, 0], max: [1, 3, 3] }), /Inverted source bounds/);
  assert.throws(() => walkingBoundsToUnreal({ min: [0, 0, 0], max: [Infinity, 3, 3] }), /must be finite/);
  assert.throws(() => buildWalkingContract(fixture(), constants, provenance, { nativeCapsuleHalfHeightCm: 80 }), /enclose the eye/);
  const asymmetric = structuredClone(constants); asymmetric.WALK_COLLISION_ELLIPSOID_M.z = 0.25;
  assert.throws(() => buildWalkingContract(fixture(), asymmetric, provenance), /Asymmetric ellipsoid/);
});

test("file exporter pins actual scene bytes and rejects stale viewport or source OBJ", async (t) => {
  const directory = await mkdtemp(resolve(tmpdir(), "brezi-walking-"));
  t.after(() => rm(directory, { recursive: true, force: true }));
  await mkdir(resolve(directory, "lib"));
  const viewportPath = resolve(directory, "lib/twin-viewport-contract.ts"), objPath = resolve(directory, "dom-mm.obj");
  const scenePath = resolve(directory, "scene.json"), outputPath = resolve(directory, "walking.json");
  await writeFile(viewportPath, viewport); await writeFile(objPath, "exact fixture OBJ bytes");
  const scene = { ...fixture(), sourceFiles: { "lib/twin-viewport-contract.ts": sha(viewport) }, objSha256: sha("exact fixture OBJ bytes") };
  const sceneBytes = JSON.stringify(scene, null, 4);
  await writeFile(scenePath, sceneBytes);
  const result = await exportWalking({ rootDir: directory, scenePath, outputPath });
  assert.equal(result.contract.provenance.sceneSha256, sha(sceneBytes));
  assert.equal(result.sha256, sha(await readFile(outputPath)));
  await writeFile(viewportPath, `${viewport}\n// stale source\n`);
  await assert.rejects(exportWalking({ rootDir: directory, scenePath, outputPath }), /Source changed since scene capture/);
  await writeFile(viewportPath, viewport); await writeFile(objPath, "other geometry");
  await assert.rejects(exportWalking({ rootDir: directory, scenePath, outputPath }), /Source OBJ checksum mismatch/);
});
