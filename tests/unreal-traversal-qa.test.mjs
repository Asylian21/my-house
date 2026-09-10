import test from "node:test";
import assert from "node:assert/strict";
import { inspectTraversalRun } from "../scripts/unreal/traversal-qa.mjs";

// Evidence fixtures exercise independent acceptance logic; they do not simulate
// Unreal physics or establish any native movement outcome.
function evidence() {
  const contract = { provenance: { sceneSha256: "source" }, capsuleRadiusCm: 22, eyeHeightCm: 165,
    walkSurfaces: [{ objectId: "DOM_00001", supportOffsetCm: 0 }], capturedClosedBlockers: [] };
  const fixtures = { schemaVersion: 1, sceneSha256: "source", simulationHz: [20, 60],
    cases: Array.from({ length: 6 }, (_, i) => ({ id: `case-${i}`, blockerObjectId: "DOM_00002",
      supportObjectId: "DOM_00001", allowedSupportObjectIds: ["DOM_00001"], eyeCm: [0, 0, 165],
      forward: [1, 0, 0], floorHeightCm: 0, holdSeconds: 2,
      sourceBoundsCm: { min: [60, -100, 0], max: [70, 100, 300] } })) };
  const results = fixtures.cases.flatMap((fixture) => [20, 60].map((hz) => {
    const holdFrames = 2 * hz, brakeFrames = hz / 2;
    return { id: fixture.id, simulationHz: hz, status: "passed", ...Object.fromEntries(
      ["blockerObjectId", "allowedSupportObjectIds"].map((key) => [key, fixture[key]])),
    expectedSupportObjectId: fixture.supportObjectId, baselineSweepBlockingHit: true,
    baselineSweepStartPenetrating: false, baselineSweepObjectId: fixture.blockerObjectId,
    entryObservation: { worldContractValidated: true, worldContractErrors: [], sceneSha256: "source",
      entrySupportObjectId: "DOM_00001", entryLineHitObjectId: "DOM_00001", cameraMode: "walking",
      entryQueryStatus: "entry-floor-and-capsule-queries-passed", expectedFloorObjects: 1,
      expectedOffsetObjects: 0, expectedClosedBlockers: 0, expectedAuxiliaryBlockers: 1, lastEntryCapsuleCenterCm: [0, 0, 87] },
    actualHoldFrames: holdFrames, holdWInputDownSamples: holdFrames, actualHoldSimulationSeconds: 2,
    releasedWInputDown: false, releasedSpeedCmPerSecond: 0, focusWasObservedBeforeNavigation: true,
    focusRestoredAfterEscape: true, cursorVisibleAfterEscape: true, actualColliderPointCm: [60, 0, 87],
    actualColliderNormal: [-1, 0, 0], startCapsuleCenterCm: [0, 0, 87],
    rendering: { sampleCount: holdFrames + brakeFrames, native4KThroughout: true, RHI: "Metal",
      "r.ScreenPercentage": 100, "r.SecondaryScreenPercentage.GameViewport": 100, "r.DynamicRes.OperationMode": 0,
      minimumSceneViewportPixels: [3840, 2160], minimumSceneRenderTargetPixels: [3840, 2160], minimumRHITexturePixels: [3840, 2160] },
    path: Array.from({ length: holdFrames + brakeFrames }, (_, i) => {
      const hold = i < holdFrames, x = Math.min(38, (i + 1) * 115 / hz);
      return { phase: hold ? "hold" : "brake", phaseFrame: hold ? i + 1 : i - holdFrames + 1,
        grounded: true, supportObjectId: "DOM_00001", wInputDown: hold, unexpectedOverlap: false, native4KSceneTargetAt100Percent: true,
        simulationDeltaSeconds: 1 / hz, wallIntervalSeconds: 0.045, measuredEyeHeightCm: 165,
        measuredFloorHeightCm: 0, eyeReferenceFloorObjectId: "DOM_00001", capsuleCenterCm: [x, 0, 87],
        cameraEyeCm: [x, 0, 165], velocityCmPerSecond: [x < 38 ? 115 : 0, 0, 0], colliderPlaneClearanceCm: 60 - x };
    }) };
  }));
  return { contract, fixtures, auxiliary: { sourceManifestSha256: "source", objects: [{ id: "COLL_fixture" }] },
    runtime: { schemaVersion: 1, status: "passed-bounded-cases", sceneSha256: "source",
    expectedCasesIncludingRates: 12, completedCases: 12, failedCases: 0, results },
  outcome: { code: 0, signal: null, timedOut: false, logTruncated: false }, runtimeLog: "clean native log",
  payloadBefore: { status: "packaged-payload-unchanged" }, payloadAfter: { status: "packaged-payload-unchanged" } };
}

test("complete synthetic traversal evidence passes without implying physical FPS", () => {
  const result = inspectTraversalRun(evidence());
  assert.equal(result.status, "bounded-packaged-traversal-validated");
  assert.match(result.performanceAcceptance, /do not certify/);
  assert.ok(result.pending.includes("native-macOS-keyboard"));
});

for (const [name, mutate, error] of [
  ["a frame crossing the source plane", (e) => { e.runtime.results[0].path[12].capsuleCenterCm[0] = 61; }, /crossed source collider plane/],
  ["an unsupported movement frame", (e) => { e.runtime.results[0].path[12].supportObjectId = "COLL_untrusted"; }, /unsupported/],
  ["a held key after release", (e) => { e.runtime.results[0].releasedWInputDown = true; }, /key release/],
  ["a missing simulation rate", (e) => { e.runtime.results.pop(); }, /Missing or failed cases/],
  ["a crash after saved success", (e) => { e.outcome.code = null; e.outcome.signal = "SIGTRAP"; }, /exit cleanly/],
  ["changed package bytes", (e) => { e.payloadAfter = null; }, /packaged payload/],
  ["missing native hidden colliders", (e) => { e.runtime.results[0].entryObservation.expectedAuxiliaryBlockers = 0; }, /Hidden source collider/],
  ["a low resolution GPU target", (e) => { e.runtime.results[0].rendering.minimumRHITexturePixels = [1920, 1080]; }, /native 4K rendering/],
  ["an actual shader fallback", (e) => { e.runtimeLog = "Default Material will be used in game"; }, /shader fallback/],
  ["a handled viewport ensure despite exit zero", (e) => { e.runtimeLog = "LogOutputDevice: Error: Ensure condition failed: SlateViewport.IsValid()"; }, /handled ensure/],
]) test(`rejects ${name}`, () => {
  const input = evidence(); mutate(input);
  const result = inspectTraversalRun(input);
  assert.equal(result.status, "failed");
  assert.ok(result.errors.some((entry) => error.test(entry)), result.errors.join("\n"));
  assert.deepEqual(result.verifiedScope, []);
});

test("a missing native report remains a recorded failure", () => {
  const input = evidence(); input.runtime = null;
  assert.equal(inspectTraversalRun(input).status, "failed");
});
