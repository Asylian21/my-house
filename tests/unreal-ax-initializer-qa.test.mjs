import test from "node:test";
import assert from "node:assert/strict";
import { inspectAXInitializer } from "../scripts/unreal/ax-initializer-qa.mjs";

const finished = () => ({ installedAtObjectiveCLoad: true, installationError: "none",
  engineGuard: "5.8.2-56702186-non-licensee", engineDeallocUnchanged: true,
  phase: "queues-drained-before-slate-shutdown", shutdownStarted: true, outstanding: 0,
  applied: 20, stressRequested: false });

test("AX initialization requires actual applied values and drained shutdown", () => {
  assert.equal(inspectAXInitializer(finished()).errors.length, 0);
  for (const change of [{ applied: 0 }, { outstanding: 1 }, { shutdownStarted: false },
    { phase: "verified-after-engine-startup" }, { engineDeallocUnchanged: false }]) {
    assert.equal(inspectAXInitializer({ ...finished(), ...change }).status, "failed");
  }
});

test("AX repair rejects unknown engine or missing early installation", () => {
  for (const change of [{ engineGuard: "5.9" }, { installedAtObjectiveCLoad: false },
    { installationError: "unexpected-class-layout-or-method-signature" }]) {
    assert.equal(inspectAXInitializer({ ...finished(), ...change }).status, "failed");
  }
  assert.equal(inspectAXInitializer(null).status, "failed");
});

test("AX stress requires all distinct absent-ID and generation observations", () => {
  const r = { ...finished(), stressRequested: true, stressFinished: true, stressPassed: true,
    stressAbsentIdCount: 16, stressMissingWidgetDrops: 32, stressStaleGenerationDrops: 16 };
  assert.equal(inspectAXInitializer(r, true).errors.length, 0);
  for (const change of [{ stressFinished: false }, { stressPassed: false },
    { stressMissingWidgetDrops: 31 }, { stressStaleGenerationDrops: 15 }, { stressAbsentIdCount: 0 }]) {
    assert.equal(inspectAXInitializer({ ...r, ...change }, true).status, "failed");
  }
  assert.equal(inspectAXInitializer(r, false).status, "failed");
  assert.equal(inspectAXInitializer(finished(), true).status, "failed");
});
