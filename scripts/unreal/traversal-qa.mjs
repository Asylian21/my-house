import { spawn, execFile } from "node:child_process";
import { createHash, randomUUID } from "node:crypto";
import { mkdir, readFile, writeFile, readdir } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { homedir } from "node:os";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { verifyPackagedPayload } from "./package-verify.mjs";
import { resolveAppLaunch, inspectLauncherExecution, requireIdleApp } from "./app-launch.mjs";
import { inspectTraversal } from "./inspect-traversal.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");

export function inspectTraversalRun({ runtime, contract, auxiliary, fixtures, outcome, runtimeLog, payloadBefore, payloadAfter }) {
  const result = inspectTraversal({ runtime, contract, fixtures });
  const check = (condition, message) => { if (!condition) result.errors.push(message); };
  check(auxiliary?.sourceManifestSha256 === contract.provenance.sceneSha256 && auxiliary?.objects?.length > 0
    && runtime?.results?.every((entry) => entry.entryObservation?.expectedAuxiliaryBlockers === auxiliary.objects.length),
  "Hidden source collider contract or native count differs");
  check(outcome?.code === 0 && outcome?.signal == null && !outcome?.timedOut && !outcome?.logTruncated && !outcome?.error,
    "Application did not exit cleanly");
  check(!/invalid ShaderMap|uncooked shader map|Failed to compile Material|Default Material will be used|Fatal error:|Assertion failed:|Ensure condition failed:|Handled ensure/i.test(runtimeLog ?? ""),
    "Runtime log contains a shader fallback, handled ensure or fatal failure");
  check(payloadBefore?.status === "packaged-payload-unchanged" && payloadAfter?.status === "packaged-payload-unchanged",
    "The complete packaged payload was not verified before and after execution");
  result.status = result.errors.length ? "failed" : "bounded-packaged-traversal-validated";
  if (result.errors.length) result.verifiedScope = [];
  result.performanceAcceptance = "20/60 simulation Hz do not certify rendering FPS, motion quality or photorealism.";
  return result;
}

async function execute(fixturesFile, renderer) {
  if (!["hwrt", "software"].includes(renderer)) throw new Error("Choose --hwrt or --software");
  try {
    const active = await promisify(execFile)("pgrep", ["-x", "BreziTwin"]);
    if (active.stdout.trim()) throw new Error("BreziTwin is already running; close it before traversal QA");
  } catch (error) { if (error.code !== 1) throw error; }
  const geometry = resolve(root, process.env.UNREAL_OUTPUT ?? "output/unreal/geometry");
  const contractBytes = await readFile(resolve(geometry, "walking.json"));
  const auxiliaryBytes = await readFile(resolve(geometry, "hidden-collision.json"));
  const fixturesBytes = await readFile(resolve(fixturesFile));
  const contract = JSON.parse(contractBytes), auxiliary = JSON.parse(auxiliaryBytes), fixtures = JSON.parse(fixturesBytes);
  if (fixtures.contractSha256 !== sha(contractBytes) || fixtures.sceneSha256 !== contract.provenance.sceneSha256
    || fixtures.sourceObjSha256 !== contract.provenance.sourceObjSha256)
    throw new Error("Traversal fixtures are stale; derive them again from the current source triangles");
  const packageBytes = await readFile(resolve(root, "output/unreal/package-report.json"));
  const receipt = JSON.parse(packageBytes);
  const imported = JSON.parse(await readFile(resolve(geometry, "../import-report.json"), "utf8"));
  if (receipt.status !== "packaged" || receipt.mapFileSha256 !== imported.mapFileSha256
    || receipt.nativeAuthoredStateSha256 !== imported.nativeAuthoredStateSha256 || imported.walkingSha256 !== sha(contractBytes)
    || imported.hiddenCollision?.sourceContractSha256 !== sha(auxiliaryBytes))
    throw new Error("Walking source and packaged map provenance differ; import and package again");
  // A prior successful package may predate the traversal driver entirely.
  const driver = "unreal/BreziTwin/Source/BreziTwin/BreziWalkingTraversal.cpp";
  if (receipt.nativeSourceFiles?.[driver] !== sha(await readFile(resolve(root, driver))))
    throw new Error("The packaged native traversal driver is stale; rebuild the application");
  const helperFiles = ["scripts/unreal/traversal-qa.mjs", "scripts/unreal/inspect-traversal.mjs", "scripts/unreal/package-verify.mjs", "scripts/unreal/app-launch.mjs", "scripts/unreal/startup-entry.mjs"];
  const helperHashes = Object.fromEntries(await Promise.all(helperFiles.map(async (file) => [file, sha(await readFile(resolve(root, file)))])));
  const app = receipt.appPath;
  const payloadBefore = await verifyPackagedPayload(app, receipt.bundle);
  const launch = await resolveAppLaunch(app, receipt.bundle);
  await requireIdleApp();
  const invocation = `walking-traversal-${renderer}-${randomUUID()}`;
  const sandbox = resolve(homedir(), "Library/Containers/local.brezi.twin/Data/Library/Application Support/BreziTwin/QA", invocation);
  const evidence = resolve(root, "output/unreal/runtime", invocation);
  await mkdir(sandbox, { recursive: true });
  await mkdir(evidence, { recursive: true });
  const sandboxFixtures = resolve(sandbox, "traversal-cases.json");
  await writeFile(sandboxFixtures, fixturesBytes);
  const args = ["-windowed", "-ResX=1600", "-ResY=900", `-UserDir=${sandbox}/`,
    `-ExecCmds=r.Lumen.HardwareRayTracing ${renderer === "hwrt" ? 1 : 0}`,
    `-BreziWalkTraversal=${sandboxFixtures}`, "-BreziTraversalExit"];
  const chunks = [];
  let bytes = 0, timedOut = false, logTruncated = false;
  const outcome = await new Promise((accept) => {
    const child = spawn(launch.executable, args, { cwd: root, stdio: ["ignore", "pipe", "pipe"] });
    let forcedExit;
    const stop = () => { child.kill("SIGTERM"); forcedExit ??= setTimeout(() => child.kill("SIGKILL"), 10000); };
    const timeout = setTimeout(() => { timedOut = true; stop(); }, 240000);
    for (const stream of [child.stdout, child.stderr]) stream.on("data", (chunk) => {
      bytes += chunk.length;
      if (bytes <= 64 * 1024 * 1024) chunks.push(chunk);
      else { logTruncated = true; stop(); }
    });
    child.once("error", (error) => { clearTimeout(timeout); clearTimeout(forcedExit); accept({ code: null, signal: null, error: error.message }); });
    child.once("close", (code, signal) => { clearTimeout(timeout); clearTimeout(forcedExit); accept({ code, signal, pid: child.pid, launch }); });
  });
  outcome.launchValidation = inspectLauncherExecution(launch, outcome, Buffer.concat(chunks).toString("utf8"));
  if (outcome.launchValidation.errors.length) outcome.error = outcome.launchValidation.errors.join("; ");
  outcome.timedOut = timedOut;
  outcome.logTruncated = logTruncated;
  const log = Buffer.concat(chunks);
  await writeFile(resolve(evidence, "process.log"), log);
  await writeFile(resolve(evidence, "package.json"), packageBytes);
  await writeFile(resolve(evidence, "walking-contract.json"), contractBytes);
  await writeFile(resolve(evidence, "hidden-collision-contract.json"), auxiliaryBytes);
  await writeFile(resolve(evidence, "cases.json"), fixturesBytes);
  let runtime = null, runtimeBytes = null, payloadAfter = null;
  const artifactErrors = [];
  try {
    const diagnostics = resolve(sandbox, "Saved/Diagnostics");
    const reports = (await readdir(diagnostics)).filter((file) => /^walking-traversal-.*\.json$/.test(file));
    if (reports.length !== 1) throw new Error("Expected one native traversal report from this invocation");
    runtimeBytes = await readFile(resolve(diagnostics, reports[0]));
    await writeFile(resolve(evidence, "runtime.json"), runtimeBytes);
    runtime = JSON.parse(runtimeBytes);
  } catch (error) { artifactErrors.push(error.message); }
  try { payloadAfter = await verifyPackagedPayload(app, receipt.bundle); }
  catch (error) { artifactErrors.push(error.message); }
  for (const [file, digest] of Object.entries(helperHashes)) {
    if (sha(await readFile(resolve(root, file))) !== digest) artifactErrors.push(`QA helper changed during execution: ${file}`);
  }
  const validation = inspectTraversalRun({ runtime, contract, auxiliary, fixtures, outcome, runtimeLog: log.toString("utf8"), payloadBefore, payloadAfter });
  validation.errors.push(...artifactErrors);
  if (validation.errors.length) { validation.status = "failed"; validation.verifiedScope = []; }
  const report = { ...validation, generatedAt: new Date().toISOString(), process: outcome, args,
    sandboxDirectory: sandbox, packageReceiptSha256: sha(packageBytes), fixturesSha256: sha(fixturesBytes),
    contractSha256: sha(contractBytes), auxiliaryContractSha256: sha(auxiliaryBytes), helperHashes, runtimeSha256: runtimeBytes ? sha(runtimeBytes) : null,
    packagePayloadVerifiedBefore: payloadBefore.status, packagePayloadVerifiedAfter: payloadAfter?.status ?? "failed",
    evidenceScope: "Listed source wall/closed-door approaches through engine InputKey and actual CharacterMovement; macOS keyboard delivery and unlisted paths remain pending." };
  await writeFile(resolve(evidence, "traversal-qa.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify({ reportPath: resolve(evidence, "traversal-qa.json"), status: report.status, errors: report.errors }, null, 2));
  if (report.status === "failed") process.exitCode = 1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [fixturesFile, ...flags] = process.argv.slice(2);
  if (!fixturesFile || flags.some((flag) => !["--hwrt", "--software"].includes(flag))
    || (flags.includes("--hwrt") && flags.includes("--software")))
    throw new Error("Usage: node scripts/unreal/traversal-qa.mjs <source-derived-cases.json> [--hwrt|--software]");
  await execute(fixturesFile, flags.includes("--software") ? "software" : "hwrt");
}
