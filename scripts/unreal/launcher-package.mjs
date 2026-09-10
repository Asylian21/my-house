/** App-scoped post-UAT/pre-receipt adoption. No engine source/binary code patch.
 * This draft deliberately supports the project's current local ad-hoc identity.
 */
import { execFile } from "node:child_process";
import { readFile, writeFile, copyFile, mkdir, readdir, lstat } from "node:fs/promises";
import { createHash } from "node:crypto";
import { resolve, relative, dirname } from "node:path";
import { promisify } from "node:util";
import { compareSignatureOnly } from "./macho-signature.mjs";
import { startupFlags } from "./app-launch.mjs";
const exec = promisify(execFile), sha = bytes => createHash("sha256").update(bytes).digest("hex");
async function inventory(app) {
  const result = {};
  async function walk(directory) {
    for (const name of await readdir(directory)) {
      const path = resolve(directory, name), stat = await lstat(path);
      if (stat.isSymbolicLink()) throw new Error("App payload contains a symlink");
      if (stat.isDirectory()) await walk(path); else if (stat.isFile()) result[relative(app, path)] = sha(await readFile(path));
      else throw new Error("Non-regular app payload");
    }
  }
  await walk(app); return result;
}
export async function installStartupLauncher({ app, source, output }) {
  await mkdir(output, { recursive: true });
  const commands = [];
  const run = async (command, args) => {
    const result = await exec(command, args, { maxBuffer: 8 * 1024 * 1024 });
    commands.push({ command, args, stdout: result.stdout, stderr: result.stderr }); return result;
  };
  await run("codesign", ["--verify", "--deep", "--strict", app]);
  const signingBefore = (await run("codesign", ["--display", "--verbose=4", app])).stderr;
  if (!/^Signature=adhoc$/m.test(signingBefore) || !/^Identifier=local\.brezi\.twin$/m.test(signingBefore))
    throw new Error("This reviewed local recipe supports only the existing local.brezi.twin ad-hoc identity; do not infer a distribution certificate");
  const plist = resolve(app, "Contents/Info.plist"), game = resolve(app, "Contents/MacOS/BreziTwin");
  const originalEntry = (await run("/usr/libexec/PlistBuddy", ["-c", "Print :CFBundleExecutable", plist])).stdout.trim();
  if (originalEntry !== "BreziTwin") throw new Error("Apply adoption exactly once to a freshly packaged original game");
  const beforeFiles = await inventory(app), before = await readFile(game), sourceBytes = await readFile(source);
  const entitlements = resolve(output, "original-entitlements.plist");
  const extracted = await run("codesign", ["--display", "--entitlements", "-", "--xml", app]);
  await writeFile(entitlements, extracted.stdout);
  const originalEntitlements = JSON.parse((await run("plutil", ["-convert", "json", "-o", "-", entitlements])).stdout);
  if (originalEntitlements["com.apple.security.app-sandbox"] !== true) throw new Error("Original sandbox entitlement is missing");
  const originalPlist = JSON.parse((await run("plutil", ["-convert", "json", "-o", "-", plist])).stdout);
  const built = resolve(output, "BreziStartupLauncher");
  await run("xcrun", ["clang", "-arch", "arm64", "-mmacosx-version-min=14.0", "-O2", "-Wall", "-Wextra", "-Werror", source, "-o", built]);
  if (sha(await readFile(source)) !== sha(sourceBytes)) throw new Error("Launcher source changed during compilation");
  await copyFile(built, resolve(app, "Contents/MacOS/BreziStartupLauncher"));
  await run("plutil", ["-replace", "CFBundleExecutable", "-string", "BreziStartupLauncher", plist]);
  const newPlist = JSON.parse((await run("plutil", ["-convert", "json", "-o", "-", plist])).stdout);
  newPlist.CFBundleExecutable = originalEntry;
  const sortedValue = value => Array.isArray(value) ? value.map(sortedValue) : value && typeof value === "object"
    ? Object.fromEntries(Object.entries(value).sort(([a], [b]) => a.localeCompare(b)).map(([key, item]) => [key, sortedValue(item)])) : value;
  const canonical = value => JSON.stringify(sortedValue(value));
  if (canonical(newPlist) !== canonical(originalPlist)) throw new Error("A plist property other than CFBundleExecutable changed");
  // The entry point initializes the original application sandbox. The exec'd
  // helper must inherit it: an independently sandboxed bare Mach-O has no signed
  // Info.plist and traps in libsecinit. This is Apple's documented helper policy,
  // not removal of the sandbox. All original grants stay on the launcher.
  const inheritedEntitlements = { "com.apple.security.app-sandbox": true, "com.apple.security.inherit": true };
  const inheritedEntitlementsFile = resolve(output, "inherited-entitlements.plist");
  await writeFile(inheritedEntitlementsFile, '<?xml version="1.0"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>com.apple.security.app-sandbox</key><true/><key>com.apple.security.inherit</key><true/></dict></plist>');
  await run("codesign", ["--force", "--sign", "-", "--preserve-metadata=identifier,requirements,flags,runtime", "--entitlements", inheritedEntitlementsFile, game]);
  const signedGame = await readFile(game), proof = compareSignatureOnly(before, signedGame);
  const entitlementSemanticDiff = Object.keys({ ...originalEntitlements, ...inheritedEntitlements }).sort().flatMap(key =>
    canonical(originalEntitlements[key]) === canonical(inheritedEntitlements[key]) ? [] : [{ key,
      operation: !(key in inheritedEntitlements) ? "removed-from-nested-helper" : !(key in originalEntitlements) ? "added-to-nested-helper" : "changed-on-nested-helper",
      before: originalEntitlements[key] ?? null, after: inheritedEntitlements[key] ?? null }]);
  const gameEntitlementsText = (await run("codesign", ["--display", "--entitlements", "-", "--xml", game])).stdout;
  const gameEntitlementsFile = resolve(output, "game-entitlements.plist");
  await writeFile(gameEntitlementsFile, gameEntitlementsText);
  const gameEntitlements = JSON.parse((await run("plutil", ["-convert", "json", "-o", "-", gameEntitlementsFile])).stdout);
  if (canonical(gameEntitlements) !== canonical(inheritedEntitlements)) throw new Error("Nested game entitlement semantics changed");
  // Reconstructible witness: old header + old signature, with all remaining
  // bytes recoverable from the verified unchanged payload in the final game.
  await writeFile(resolve(output, "engine-before-header.bin"), before.subarray(0, proof.beforeStructure.commandsEnd));
  await writeFile(resolve(output, "engine-before-signature.bin"), before.subarray(proof.beforeStructure.signature.offset));
  const policy = { schemaVersion: 1, status: "signature-only-engine-resign-validated", forcedFlags: [...startupFlags],
    launcherSourceSha256: sha(sourceBytes), engineSha256: sha(signedGame), engineSignatureProof: proof,
    originalEntitlements, inheritedEntitlements, entitlementSemanticDiff, sandboxPolicy: "outer-original-grants-helper-inherits-existing-sandbox", originalEntitlementsSha256: sha(Buffer.from(extracted.stdout)),
    scope: "Only the game signing blob (including documented inherited-sandbox entitlements) and explicitly classified signing-size metadata changed; no engine code, geometry, materials or renderer settings changed." };
  const policyFile = resolve(app, "Contents/Resources/BreziStartupPolicy.json");
  await mkdir(dirname(policyFile), { recursive: true }); await writeFile(policyFile, JSON.stringify(policy, null, 2) + "\n");
  // Outer bundle/new main executable signed once, after all nested code and
  // resources are final. Do not use --deep when signing; it would mutate siblings.
  await run("codesign", ["--force", "--sign", "-", "--identifier", "local.brezi.twin", "--entitlements", entitlements, app]);
  await run("codesign", ["--verify", "--deep", "--strict", app]);
  if (sha(await readFile(game)) !== sha(signedGame)) throw new Error("Outer signing changed the already validated UE Mach-O");
  const finalEntitlements = (await run("codesign", ["--display", "--entitlements", "-", "--xml", app])).stdout;
  const finalEntitlementsFile = resolve(output, "final-entitlements.plist"); await writeFile(finalEntitlementsFile, finalEntitlements);
  const finalValues = JSON.parse((await run("plutil", ["-convert", "json", "-o", "-", finalEntitlementsFile])).stdout);
  if (canonical(finalValues) !== canonical(originalEntitlements)) throw new Error("Launcher entitlement semantics changed");
  const afterFiles = await inventory(app), permittedChanged = new Set(["Contents/Info.plist", "Contents/MacOS/BreziTwin", "Contents/_CodeSignature/CodeResources"]);
  const permittedAdded = new Set(["Contents/MacOS/BreziStartupLauncher", "Contents/Resources/BreziStartupPolicy.json"]);
  for (const [file, digest] of Object.entries(beforeFiles)) if (!(file in afterFiles) || (!permittedChanged.has(file) && afterFiles[file] !== digest))
    throw new Error(`An unrelated sealed payload file changed: ${file}`);
  for (const file of Object.keys(afterFiles)) if (!(file in beforeFiles) && !permittedAdded.has(file)) throw new Error(`Unexpected new bundle resource: ${file}`);
  const report = { status: "launcher-packaged-and-signed", generatedAt: new Date().toISOString(), app, commands, proof,
    launcherSourceSha256: sha(sourceBytes), launcherSha256: afterFiles["Contents/MacOS/BreziStartupLauncher"],
    beforeFiles, afterFiles, originalEntitlements, gameEntitlements, entitlementSemanticDiff,
    debuggingLimitation: "The nested inherited helper has no get-task-allow entitlement; direct debugger attachment is not preserved or claimed. The outer launcher retains the original app entitlements.", finalEntitlements: finalValues, codeSignature: "deep-strict-valid",
    fullEngineFileChangedOnlyForSigning: proof.beforeSha256 !== proof.afterSha256, outsideClassifiedSigningBytesUnchanged: true,
    actualLaunchPending: true, signingBefore, signingAfter: (await run("codesign", ["--display", "--verbose=4", app])).stderr };
  await writeFile(resolve(output, "launcher-package.json"), JSON.stringify(report, null, 2) + "\n");
  return report;
}
