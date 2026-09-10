import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, writeFile, rm, symlink, rename } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { verifyPackage, hashPackagedPayload, verifyPackagedPayload, assertPackagedUfsDependencies,
  requiredUfsDependencies } from "../scripts/unreal/package-verify.mjs";

// These fixtures intentionally are not executable applications. Each case must
// fail the structural checks before codesign, PlistBuddy, or UnrealPak is called.
// A signature/tool error is not accepted as proof that the regression is caught.
const containers = ["BreziTwin-Mac.pak", "BreziTwin-Mac.utoc", "BreziTwin-Mac.ucas", "global.utoc", "global.ucas"];
const payloadDirectory = "Contents/UE/BreziTwin/Content/Paks";

async function fixture(t, withPayload = true) {
  const directory = await mkdtemp(resolve(tmpdir(), "brezi-package-integrity-"));
  t.after(() => rm(directory, { recursive: true, force: true }));
  const app = resolve(directory, "Archived App/BreziTwin.app");
  const engine = resolve(directory, "engine-does-not-exist");
  async function put(relativePath, bytes = "fixture payload\n") {
    const path = resolve(app, relativePath);
    await mkdir(dirname(path), { recursive: true });
    await writeFile(path, bytes);
    return path;
  }
  await put("Contents/MacOS/BreziTwin", Buffer.from([0xcf, 0xfa, 0xed, 0xfe]));
  await put("Contents/Resources/BreziStartupPolicy.json", "structural fixture, not a signed policy\n");
  await put("Contents/MacOS/libFixture.dylib");
  await put("Contents/Info.plist", '<?xml version="1.0"?><plist version="1.0"><dict><key>NSHighResolutionCapable</key><true/></dict></plist>');
  if (withPayload) {
    await put("Contents/UE/UECommandLine.txt", "../../../BreziTwin/BreziTwin.uproject\n");
    for (const name of containers) await put(`${payloadDirectory}/${name}`);
  }
  return { directory, app, engine, put, run: () => verifyPackage(app, engine) };
}

test("a full payload without the original application executable is rejected", async (t) => {
  const f = await fixture(t);
  await rm(resolve(f.app, "Contents/MacOS/BreziTwin"));
  await assert.rejects(f.run(), /Incomplete standalone package: missing Contents\/MacOS\/BreziTwin/);
});

test("the sealed startup policy is a required packaged resource", async (t) => {
  const f = await fixture(t);
  await rm(resolve(f.app, "Contents/Resources/BreziStartupPolicy.json"));
  await assert.rejects(f.run(), /Incomplete standalone package: missing Contents\/Resources\/BreziStartupPolicy\.json/);
});

test("a development-only .app is rejected even when staged payload exists beside it", async (t) => {
  const f = await fixture(t, false);
  const staged = resolve(f.directory, "StagedBuilds/Mac/BreziTwin/Content/Paks");
  await mkdir(staged, { recursive: true });
  for (const name of containers) await writeFile(resolve(staged, name), "staged but not bundled\n");
  await assert.rejects(f.run(), /Incomplete standalone package: missing Contents\/UE\/UECommandLine\.txt/);
});

test("an archive containing a pak and IoStore tables still needs the actual IoStore payload", async (t) => {
  const f = await fixture(t);
  await rm(resolve(f.app, payloadDirectory, "BreziTwin-Mac.ucas"));
  await assert.rejects(f.run(), /Incomplete standalone package: missing .*BreziTwin-Mac\.ucas/);
});

test("an empty IoStore payload cannot satisfy the packaged-content gate", async (t) => {
  const f = await fixture(t);
  await f.put(`${payloadDirectory}/global.ucas`, Buffer.alloc(0));
  await assert.rejects(f.run(), /Incomplete standalone package: missing .*global\.ucas/);
});

test("a required payload symlink is rejected instead of following files outside the bundle", async (t) => {
  const f = await fixture(t);
  const path = resolve(f.app, payloadDirectory, "BreziTwin-Mac.ucas");
  const outside = resolve(f.directory, "external-payload.ucas");
  await rename(path, outside);
  await symlink(outside, path);
  await assert.rejects(f.run(), /Package must contain its payload, not symlinks: .*BreziTwin-Mac\.ucas/);
});

test("a symlinked payload directory cannot make an archive appear self-contained", async (t) => {
  const f = await fixture(t);
  const path = resolve(f.app, payloadDirectory);
  const outside = resolve(f.directory, "external-paks");
  await rename(path, outside);
  await symlink(outside, path, "dir");
  await assert.rejects(f.run(), /Package must contain its payload, not symlinks: .*Paks/);
});

test("a dangling symlink is rejected even when every required payload file is present", async (t) => {
  const f = await fixture(t);
  const resources = resolve(f.app, "Contents/Resources");
  await mkdir(resources, { recursive: true });
  await symlink(resolve(f.directory, "missing-runtime-library"), resolve(resources, "runtime-link"));
  await assert.rejects(f.run(), /Package must contain its payload, not symlinks: .*runtime-link/);
});

test("the .app root itself cannot be a symlink to another bundle", async (t) => {
  const f = await fixture(t);
  const alias = resolve(f.directory, "BreziTwin.app");
  await symlink(f.app, alias, "dir");
  await assert.rejects(verifyPackage(alias, f.engine), /Package root must be a real app directory/);
});

test("a regular file with an .app extension is not a package directory", async (t) => {
  const f = await fixture(t);
  const file = resolve(f.directory, "ExecutableOnly.app");
  await writeFile(file, "development executable\n");
  await assert.rejects(verifyPackage(file, f.engine), /Package root must be a real app directory/);
});

test("the packaged walking contract is mandatory even when camera and ICU dependencies exist", () => {
  const listing = requiredUfsDependencies.filter((p) => !p.endsWith("walking.json")).map((p) => `"${p}"`).join("\n");
  assert.throws(() => assertPackagedUfsDependencies(listing), /Missing packaged UFS dependency: .*walking\.json/);
  assert.deepEqual(assertPackagedUfsDependencies(`${listing}\n"BreziTwin/Content/Data/walking.json"`), requiredUfsDependencies);
});

async function receipt(f) {
  return { status: "bundle-validated", payloadHashScope: "all-bundle-files", payloadHashes: await hashPackagedPayload(f.app) };
}

test("fresh QA payload comparison covers every bundle file", async (t) => {
  const f = await fixture(t), bundle = await receipt(f);
  const proof = await verifyPackagedPayload(f.app, bundle);
  assert.equal(proof.status, "packaged-payload-unchanged");
  assert.equal(proof.fileCount, Object.keys(bundle.payloadHashes).length);
  await f.put("Contents/MacOS/libFixture.dylib", "changed library outside the old seven-file receipt");
  await assert.rejects(verifyPackagedPayload(f.app, bundle), /Packaged payload changed.*libFixture/);
});

test("QA rejects added, removed, and symlinked files after bundle validation", async (t) => {
  const f = await fixture(t), bundle = await receipt(f);
  await f.put("Contents/injected.txt");
  await assert.rejects(verifyPackagedPayload(f.app, bundle), /Packaged payload changed.*injected/);
  await rm(resolve(f.app, "Contents/injected.txt"));
  await rm(resolve(f.app, "Contents/MacOS/libFixture.dylib"));
  await assert.rejects(verifyPackagedPayload(f.app, bundle), /Packaged payload changed.*libFixture/);
  await symlink(resolve(f.app, "Contents/MacOS/BreziTwin"), resolve(f.app, "Contents/MacOS/libFixture.dylib"));
  await assert.rejects(verifyPackagedPayload(f.app, bundle), /not symlinks/);
});

test("an old partial receipt cannot establish current complete-bundle provenance", async (t) => {
  const f = await fixture(t), bundle = await receipt(f);
  delete bundle.payloadHashScope;
  await assert.rejects(verifyPackagedPayload(f.app, bundle), /No complete bundle payload receipt/);
});

// Package selection fixtures validate receipt joins only. They never invoke an app,
// codesign, PlistBuddy, or UnrealPak; complete payload mutation cases are above.
import { realpath } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { selectPackageReport, loadSelectedPackage, inspectDeliveryReceipts, renderProfileForAction }
  from '../scripts/unreal/package-resolver.mjs';
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const A = 'a'.repeat(64), B = 'b'.repeat(64), C = 'c'.repeat(64);
const resourcePrefix = 'Contents/UE/BreziTwin/Plugins/BreziCausticsProbe/Resources/';

async function selectedFixture(t) {
  const temporary = await mkdtemp(resolve(tmpdir(), 'brezi-selected-package-'));
  t.after(() => rm(temporary, { recursive: true, force: true }));
  const root = await realpath(temporary), engine = resolve(root, 'engine'), project = resolve(engine, 'project');
  const app = resolve(root, 'archive/BreziTwin.app'), roles = {}, inputs = {}, paths = {};
  const launch = { executable: resolve(app, 'Contents/MacOS/BreziTwin'), executableSha256: C };
  const bundle = { status: 'bundle-validated', payloadHashScope: 'all-bundle-files', codeSignature: 'deep-strict-valid',
    symbolicLinks: 0, highDpi: true, launch, payloadHashes: {
      [resourcePrefix + 'active-water-binding.json']: A, [resourcePrefix + 'transport-scene-binding.json']: B,
      [payloadDirectory + '/BreziTwin-Mac.ucas']: C, 'Contents/MacOS/BreziTwin': C } };
  async function put(role, value) {
    const path = resolve(root, role + '.json'), bytes = JSON.stringify(value, null, 2) + '\n';
    await writeFile(path, bytes); paths[role] = path; roles[role] = value; inputs[path] = sha256(bytes); return path;
  }
  const fileHashes = { [resolve(project, 'Plugins/BreziCausticsProbe/Resources/active-water-binding.json')]: A,
    [resolve(project, 'Plugins/BreziCausticsProbe/Resources/transport-scene-binding.json')]: B };
  await put('sourceClosure', { status: 'caustics-delivery-source-frozen', errors: [], engineRoot: engine, projectRoot: project, fileHashes });
  for (const [role, kind] of [['acceptedEditor', 'editor'], ['acceptedGame', 'game']]) await put(role, {
    status: `caustics-delivery-${kind}-build-accepted`, errors: [], engineRoot: engine, projectRoot: project,
    sourceClosure: paths.sourceClosure, fileHashes });
  for (const [role, mode] of [['cookReceipt', 'cook'], ['archiveReceipt', 'archive']]) await put(role, {
    status: 'native-delivery-exited-zero-and-drained', mode, nativeExitCode: 0, errors: [], remainingOwned: [],
    changedPinnedInputs: [], errorLines: [], engineRoot: engine, projectRoot: project,
    inputs: Object.fromEntries(['acceptedEditor', 'acceptedGame', 'sourceClosure'].map(k => [k, { path: paths[k], sha256: inputs[paths[k]] }])),
    ...(mode === 'archive' ? { cookReceipt: paths.cookReceipt, appPath: app } : {}) });
  await put('cookedBindingReceipt', { schemaVersion: 1, status: 'cooked-source-container-lineage-validated',
    cookReceiptSha256: inputs[paths.cookReceipt], archiveReceiptSha256: inputs[paths.archiveReceipt],
    sourcePinsUnchangedAcrossCookAndArchive: true, freshCookOutput: true, allRequiredPackagesInContainer: true,
    receiverCount: 45, waterCount: 1, waveCount: 12, activeWaterBindingSha256: A, sourceBindingSha256: B,
    containerFiles: [{ name: 'BreziTwin-Mac.ucas', bytes: 42, sha256: C }] });
  bundle.payloadHashes[resourcePrefix + 'cooked-runtime-binding.json'] = inputs[paths.cookedBindingReceipt];
  await put('sealReceipt', { status: 'self-exec-entry-sealed-and-signed', app, codeSignature: 'deep-strict-valid', launch,
    proof: { status: 'signature-only-change-validated', beforeSha256: B, afterSha256: C },
    additionalResources: [{ source: paths.cookedBindingReceipt, sha256: inputs[paths.cookedBindingReceipt],
      relativePath: resourcePrefix + 'cooked-runtime-binding.json' }] });
  const report = { schemaVersion: 1, status: 'caustics-delivery-package-validated', app, engine, project, bundle, inputs, ...paths,
    linkedGameProof: { status: 'raw-linked-code-preserved-through-packaging-signature', actualPackagedSha256: B } };
  const bytes = JSON.stringify(report, null, 2) + '\n', path = resolve(root, 'selected.json'); await writeFile(path, bytes);
  return { root, app, report, roles, path, bytes, env: { BREZI_PACKAGE_REPORT: path, BREZI_PACKAGE_REPORT_SHA256: sha256(bytes) } };
}

test('legacy selection remains the default; explicit selection requires both path and SHA', () => {
  assert.deepEqual(selectPackageReport('/tmp/root', {}), { path: '/tmp/root/output/unreal/package-report.json', expectedSha256: null, explicit: false });
  for (const env of [{ BREZI_PACKAGE_REPORT: 'a.json' }, { BREZI_PACKAGE_REPORT_SHA256: A },
    { BREZI_PACKAGE_REPORT: '', BREZI_PACKAGE_REPORT_SHA256: A }, { BREZI_PACKAGE_REPORT: 'a.json', BREZI_PACKAGE_REPORT_SHA256: 'wrong' }])
    assert.throws(() => selectPackageReport('/tmp/root', env), /both|Invalid/);
});

test('delivery selection preserves exact report bytes and historical source provenance', async t => {
  const f = await selectedFixture(t), loaded = await loadSelectedPackage(f);
  assert.equal(loaded.app, f.app); assert.equal(loaded.provenance.kind, 'caustics-delivery');
  assert.equal(loaded.reportBytes.toString(), f.bytes); assert.equal(loaded.provenance.reportSha256, f.env.BREZI_PACKAGE_REPORT_SHA256);
  assert.equal(Object.keys(loaded.provenance.artifactPins).length, 7);
  // This fixture has no current project/build files: launching a signed archive must not rewrite historical source evidence.
  assert.match(loaded.provenance.sourceFreshness, /historical/);
});

test('legacy packaged report loads through the same explicit selector', async t => {
  const f = await selectedFixture(t), app = resolve(f.root, 'output/unreal/package/Mac/BreziTwin.app');
  const report = { status: 'packaged', appPath: app, bundle: { ...f.report.bundle,
    launch: { ...f.report.bundle.launch, executable: resolve(app, 'Contents/MacOS/BreziTwin') } } };
  const bytes = JSON.stringify(report); await writeFile(f.path, bytes);
  f.env.BREZI_PACKAGE_REPORT_SHA256 = sha256(bytes);
  assert.equal((await loadSelectedPackage(f)).provenance.kind, 'legacy');
  report.renderProfileInterface = { schemaVersion: 1 };
  const unsupported = JSON.stringify(report); await writeFile(f.path, unsupported);
  f.env.BREZI_PACKAGE_REPORT_SHA256 = sha256(unsupported);
  await assert.rejects(loadSelectedPackage(f), /Legacy package cannot advertise/);
});

test('explicit wrong SHA and mutated role bytes fail before any application inspection', async t => {
  const f = await selectedFixture(t);
  await assert.rejects(loadSelectedPackage({ ...f, env: { ...f.env, BREZI_PACKAGE_REPORT_SHA256: A } }), /provenance changed/);
  await writeFile(f.report.cookReceipt, '{}\n');
  await assert.rejects(loadSelectedPackage(f), /provenance changed/);
});

test('a delivery report cannot silently replace the default legacy report', async t => {
  const f = await selectedFixture(t), path = resolve(f.root, 'output/unreal/package-report.json');
  await mkdir(dirname(path), { recursive: true }); await writeFile(path, f.bytes);
  await assert.rejects(loadSelectedPackage({ root: f.root, env: {} }), /explicit report path/);
});

for (const [name, corrupt, pattern] of [
  ['missing role pin', f => delete f.report.inputs[f.report.acceptedGame], /Missing pinned/],
  ['foreign app', f => { f.report.app = resolve(f.root, 'Other.app'); }, /another app/],
  ['partial payload receipt', f => { f.report.bundle.payloadHashScope = 'some-files'; }, /complete signed/],
  ['unsigned bundle', f => { f.report.bundle.codeSignature = 'unchecked'; }, /complete signed/],
  ['wrong build source', f => { f.roles.acceptedEditor.sourceClosure = f.report.acceptedGame; }, /source closure/],
  ['wrong archive source pin', f => { f.roles.archiveReceipt.inputs.sourceClosure.sha256 = A; }, /provenance differs/],
  ['nested archive failure', f => { f.roles.archiveReceipt.errorLines = ['BUILD FAILED']; }, /did not close/],
  ['missing native drain', f => { f.roles.cookReceipt.remainingOwned = [123]; }, /did not close/],
  ['foreign cooked receipt', f => { f.roles.cookedBindingReceipt.cookReceiptSha256 = A; }, /lineage differs/],
  ['wrong cooked wave count', f => { f.roles.cookedBindingReceipt.waveCount = 4; }, /lineage differs/],
  ['unsealed cooked binding', f => { f.report.bundle.payloadHashes[resourcePrefix + 'cooked-runtime-binding.json'] = A; }, /Sealed cooked binding/],
  ['wrong source binding', f => { f.roles.sourceClosure.fileHashes[resolve(f.report.project, 'Plugins/BreziCausticsProbe/Resources/active-water-binding.json')] = C; }, /Compiled source binding/],
  ['extra container', f => { f.report.bundle.payloadHashes[payloadDirectory + '/extra.ucas'] = C; }, /inventory differs/],
  ['wrong container hash', f => { f.roles.cookedBindingReceipt.containerFiles[0].sha256 = B; }, /container pin/],
  ['wrong signed executable', f => { f.roles.sealReceipt.proof.afterSha256 = B; }, /seal differs/],
  ['missing seal resource', f => { f.roles.sealReceipt.additionalResources = []; }, /included in the seal/],
  ['wrong original linked Game', f => { f.report.linkedGameProof.actualPackagedSha256 = A; }, /Raw linked Game/],
]) test(`delivery join rejects ${name}`, async t => {
  const f = await selectedFixture(t); corrupt(f);
  assert.throws(() => inspectDeliveryReceipts(f.report, f.roles), pattern);
});

test('open profiles are closed, use one ExecCmds, and never masquerade as native QA', () => {
  assert.deepEqual(renderProfileForAction('open', {}).args, []);
  for (const [name, percentage] of [['tsr67', 67], ['tsr50', 50]]) {
    const profile = renderProfileForAction('open', { BREZI_RENDER_PROFILE: name });
    assert.deepEqual(profile.args, [`-ExecCmds=r.AntiAliasingMethod 4,r.DynamicRes.OperationMode 0,r.ScreenPercentage ${percentage},r.TSR.History.ScreenPercentage 100`]);
    assert.equal(profile.historyPercentage, 100);
    for (const action of ['qa', 'qa-ui', 'package', 'editor-build'])
      assert.throws(() => renderProfileForAction(action, { BREZI_RENDER_PROFILE: name }), /only by unreal:open/);
  }
  for (const name of ['', 'quality', 'tsr66', 'TSR50', 'native,r.RayTracing 0'])
    assert.throws(() => renderProfileForAction('open', { BREZI_RENDER_PROFILE: name }), /must be native/);
});

test('native profile interface preserves saved choice and permits an explicit changeable launch profile', () => {
  const capability = { schemaVersion: 1 };
  const saved = renderProfileForAction('open', {}, capability);
  assert.deepEqual(saved.args, []);
  assert.equal(saved.percentage, null);
  assert.equal(saved.name, 'saved-or-default');
  for (const [name, native] of [['native', 'native'], ['tsr67', 'balanced'], ['tsr50', 'performance']]) {
    const profile = renderProfileForAction('open', { BREZI_RENDER_PROFILE: name }, capability);
    assert.deepEqual(profile.args, [`-BreziRenderProfile=${native}`]);
    assert.equal(profile.userCanChangeInApp, true);
  }
  assert.throws(() => renderProfileForAction('qa', { BREZI_RENDER_PROFILE: 'tsr50' }, capability), /only by unreal:open/);
});

test('native profile capability must be tied to all compiled implementation sources', async t => {
  const f = await selectedFixture(t);
  const names = ['BreziRenderQualityPolicy.h', 'BreziRenderQuality.cpp', 'BreziPlayerController.cpp', 'BreziPlayerController.h'];
  const sourcePins = Object.fromEntries(names.map(name => [resolve(f.report.project, 'Source/BreziTwin', name), A]));
  f.report.renderProfileInterface = { schemaVersion: 1, profiles: ['native', 'balanced', 'performance'], sourcePins };
  assert.throws(() => inspectDeliveryReceipts(f.report, f.roles), /compiled source provenance/);
  Object.assign(f.roles.sourceClosure.fileHashes, sourcePins);
  assert.doesNotThrow(() => inspectDeliveryReceipts(f.report, f.roles));
  delete f.report.renderProfileInterface.sourcePins[resolve(f.report.project, 'Source/BreziTwin/BreziRenderQuality.cpp')];
  assert.throws(() => inspectDeliveryReceipts(f.report, f.roles), /compiled source provenance/);
});
