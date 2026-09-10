import test from "node:test";
import assert from "node:assert/strict";
import { inspectWalkingEvidence, walkingQaPlan } from "../scripts/unreal/walking-qa.mjs";

function fixture() {
  // These are parser fixtures, never screenshots or native runtime evidence.
  const png = Buffer.alloc(24); Buffer.from("89504e470d0a1a0a", "hex").copy(png);
  png.writeUInt32BE(3840, 16); png.writeUInt32BE(2160, 20);
  const floor = { objectId: "DOM_00001", name: "Fixture floor", walkSurfaceId: "fixture-floor", supportOffsetCm: 0 };
  const contract = { provenance: { sceneSha256: "a".repeat(64) }, walkSurfaces: [floor], capturedClosedBlockers: [], staticBlockers: [],
    capsuleRadiusCm: 22, capsuleHalfHeightCm: 85, eyeHeightCm: 165, maxStepHeightCm: 22, maxDropCm: 78 };
  const runtime = { status: "capture-complete", activeView: "interior", frameInterval: { sampleCount: 300 },
    gameViewportWasAtLeast4KThroughoutBenchmark: true, viewportChangedDuringBenchmark: false,
    renderSettings: { "r.ScreenPercentage": 100, "r.SecondaryScreenPercentage.GameViewport": 100, "r.DynamicRes.OperationMode": 0 },
    screenshotSaved: true, screenshotPixels: [3840, 2160], walking: {
      contractLoaded: true, worldContractValidated: true, worldContractErrors: [], sceneSha256: contract.provenance.sceneSha256,
      expectedFloorObjects: 1, expectedOffsetObjects: 0, expectedClosedBlockers: 0, expectedAuxiliaryBlockers: 1,
      capsuleRadiusCm: 22, capsuleHalfHeightCm: 85, expectedEyeHeightCm: 165, entryAttempts: 1,
      entryQueryStatus: "entry-floor-and-capsule-queries-passed", entryLineHitObjectId: floor.objectId,
      entrySupportObjectId: floor.objectId, lastEntryCapsuleCenterCm: [0, 0, 87], lastEntryFloorHitCm: [0, 0, 0], supportQueries: 2,
      successfulEntries: 1, cameraMode: "walking", characterMovementMode: "Walking", currentSupportObjectId: floor.objectId,
      groundedEyeSamples: 540, unmeasuredOrAirborneEyeSamples: 0, lastMeasuredEyeHeightCm: 165, minMeasuredEyeHeightCm: 165,
      maxMeasuredEyeHeightCm: 165, maxEyeHeightErrorCm: 0, currentCapsuleCenterCm: [0, 0, 87], controlledVerticalDrops: 0 } };
  return { runtime, contract, png, auxiliary: { sourceManifestSha256: contract.provenance.sceneSha256, objects: [{ id: "COLL_fixture" }] },
    process: { code: 0, signal: null }, view: "interior", mode: "standing" };
}

test("a standing receipt makes no traversal, door, keyboard, or accessibility claim", () => {
  const result = inspectWalkingEvidence(fixture());
  assert.equal(result.status, "standing-native-validated");
  assert.equal(result.verification.standing, true);
  for (const key of ["traversal", "wallSliding", "closedDoorTraversal", "steps", "drops", "keyboard", "accessibility"])
    assert.equal(result.verification[key], false);
});

test("capture-complete and PNG do not turn a shutdown crash into a passing run", () => {
  const f = fixture(); f.process = { code: null, signal: "SIGTRAP" };
  const result = inspectWalkingEvidence(f);
  assert.equal(result.status, "failed"); assert(result.errors.includes("Application did not exit cleanly"));
});

test("orbit entry audit cannot masquerade as native standing", () => {
  const f = fixture(); f.runtime.walking.cameraMode = "orbit"; f.runtime.walking.successfulEntries = 0;
  assert.equal(inspectWalkingEvidence(f).status, "failed");
  f.mode = "audit";
  const result = inspectWalkingEvidence(f); assert.equal(result.status, "entry-audit-native-validated");
  assert.equal(result.verification.standing, false);
});

test("an explicit blocked entry is only an audit observation, never walking success", () => {
  const f = fixture(); Object.assign(f.runtime.walking, { cameraMode: "orbit", successfulEntries: 0,
    entryQueryStatus: "capsule-blocked-or-no-radius-valid-support", entrySupportObjectId: "", groundedEyeSamples: 0 });
  f.mode = "audit"; assert.equal(inspectWalkingEvidence(f).status, "entry-audit-native-validated");
  f.mode = "standing"; assert.equal(inspectWalkingEvidence(f).status, "failed");
});

test("stale scene, wrong body, unknown support, and duplicated entry are rejected", () => {
  for (const edit of [
    (w) => w.sceneSha256 = "b".repeat(64), (w) => w.capsuleRadiusCm = 10,
    (w) => w.entrySupportObjectId = "DOM_99999", (w) => w.entryAttempts = 2,
    (w) => w.expectedFloorObjects = 2,
  ]) { const f = fixture(); edit(f.runtime.walking); assert.equal(inspectWalkingEvidence(f).status, "failed"); }
});

test("native floor gap cannot inflate the declared 165cm eye height", () => {
  const f = fixture(); Object.assign(f.runtime.walking, { lastMeasuredEyeHeightCm: 167.15, maxMeasuredEyeHeightCm: 167.15, maxEyeHeightErrorCm: 2.15 });
  assert.equal(inspectWalkingEvidence(f).status, "failed");
});

test("airborne samples, horizontal drift, and unmeasured eye fields invalidate standing", () => {
  for (const edit of [
    (w) => w.unmeasuredOrAirborneEyeSamples = 1, (w) => w.currentCapsuleCenterCm[0] = 5,
    (w) => delete w.maxEyeHeightErrorCm, (w) => w.groundedEyeSamples = 299,
  ]) { const f = fixture(); edit(f.runtime.walking); assert.equal(inspectWalkingEvidence(f).status, "failed"); }
});

test("4K metadata cannot hide lower-resolution PNG bytes or resolution scaling", () => {
  const f = fixture(); f.png.writeUInt32BE(1920, 16); assert.equal(inspectWalkingEvidence(f).status, "failed");
  const scaled = fixture(); scaled.runtime.renderSettings["r.ScreenPercentage"] = 50;
  assert.equal(inspectWalkingEvidence(scaled).status, "failed");
});

test("a default-material fallback invalidates otherwise successful runtime evidence", () => {
  const f = fixture(); f.runtimeLog = "LogMaterial: Warning: Failed to compile Material for platform SF_METAL_SM6, Default Material will be used in game.";
  assert.equal(inspectWalkingEvidence(f).status, "failed");
});

test("a handled viewport ensure invalidates a clean process exit", () => {
  const f = fixture(); f.runtimeLog = "LogOutputDevice: Error: Ensure condition failed: SlateViewport.IsValid()";
  assert.equal(inspectWalkingEvidence(f).status, "failed");
});

test("the generated plan marks all interaction cases as pending", () => {
  const plan = walkingQaPlan(fixture().contract);
  assert.equal(plan.status, "prepared-not-executed"); assert.equal(plan.automated.length, 8);
  assert.equal(plan.pendingNativeInteraction.length, 5);
  assert(plan.pendingNativeInteraction.every((item) => item.status.startsWith("pending-")));
});
