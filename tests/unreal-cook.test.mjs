import test from "node:test";
import assert from "node:assert/strict";
import { inspectCookLog } from "../scripts/unreal/cook-log.mjs";

test("UAT success cannot bless a material fallback", () => {
  const report = inspectCookLog("LogMaterial: Warning: M_PoolWater: Failed to compile Material for platform SF_METAL_SM6, Default Material will be used in game.\nNo inputs to Single Layer Water Material.\nCOOK COMMAND COMPLETED\nBUILD SUCCESSFUL");
  assert.equal(report.status, "material-compilation-failed");
  assert.equal(report.failures.length, 1);
  assert.equal(report.failures[0].line, 1);
});

test("ordinary shader cache misses do not reject a successful cook", () => {
  assert.equal(inspectCookLog("LogMaterial: Missing cached shadermap, compiling.\nCOOK COMMAND COMPLETED").status, "cook-log-validated");
});

test("empty or partial output cannot prove successful shader cooking", () => {
  assert.equal(inspectCookLog("BUILD SUCCESSFUL").status, "cook-completion-unconfirmed");
  assert.equal(inspectCookLog("LogShaderCompilers: Error: compile failed\nCOOK COMMAND COMPLETED").status, "material-compilation-failed");
});
