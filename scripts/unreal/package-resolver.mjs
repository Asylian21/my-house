import { readFile, lstat, realpath } from 'node:fs/promises';
import { resolve, isAbsolute, basename, dirname } from 'node:path';
import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify, isDeepStrictEqual } from 'node:util';
import { verifyPackagedPayload } from './package-verify.mjs';
import { resolveAppLaunch } from './app-launch.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const need = (ok, why) => { if (!ok) throw Error(why); };
const digest = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const absolute = value => typeof value === 'string' && isAbsolute(value) && resolve(value) === value;
const exec = promisify(execFile);
const resources = 'Contents/UE/BreziTwin/Plugins/BreziCausticsProbe/Resources/';
const paks = 'Contents/UE/BreziTwin/Content/Paks/';
export const deliveryRoles = Object.freeze(['acceptedEditor', 'acceptedGame', 'cookReceipt', 'archiveReceipt',
  'cookedBindingReceipt', 'sourceClosure', 'sealReceipt']);

export function selectPackageReport(root, env = process.env) {
  const path = env.BREZI_PACKAGE_REPORT, expected = env.BREZI_PACKAGE_REPORT_SHA256;
  need((path === undefined) === (expected === undefined), 'Set both BREZI_PACKAGE_REPORT and BREZI_PACKAGE_REPORT_SHA256');
  if (path !== undefined) need(typeof path === 'string' && path.trim() && digest(expected), 'Invalid explicit package path or SHA-256');
  return { path: resolve(root, path ?? 'output/unreal/package-report.json'), expectedSha256: expected ?? null,
    explicit: path !== undefined };
}

export function renderProfileForAction(action, env = process.env, nativeInterface = null) {
  const name = env.BREZI_RENDER_PROFILE ?? 'native';
  need(['native', 'tsr67', 'tsr50'].includes(name), 'BREZI_RENDER_PROFILE must be native, tsr67 or tsr50');
  need(name === 'native' || action === 'open', 'Scaled render profiles are supported only by unreal:open; existing QA requires native 100%');
  const percentage = name === 'tsr67' ? 67 : name === 'tsr50' ? 50 : 100;
  if (nativeInterface?.schemaVersion === 1 && action === 'open') {
    const explicit = env.BREZI_RENDER_PROFILE !== undefined;
    const nativeName = { native: 'native', tsr67: 'balanced', tsr50: 'performance' }[name];
    return { name: explicit ? name : 'saved-or-default', percentage: explicit ? percentage : null,
      historyPercentage: explicit ? (name === 'native' ? 200 : 100) : null,
      userCanChangeInApp: true,
      args: explicit ? [`-BreziRenderProfile=${nativeName}`] : [] };
  }
  return { name, percentage, historyPercentage: name === 'native' ? 200 : 100,
    // Native preserves the packaged defaults; experimental profiles use one closed command list.
    args: name === 'native' ? [] : [`-ExecCmds=r.AntiAliasingMethod 4,r.DynamicRes.OperationMode 0,r.ScreenPercentage ${percentage},r.TSR.History.ScreenPercentage 100`] };
}

function inspectBundle(bundle) {
  need(bundle?.status === 'bundle-validated' && bundle.payloadHashScope === 'all-bundle-files'
    && bundle.codeSignature === 'deep-strict-valid' && bundle.symbolicLinks === 0 && bundle.highDpi === true,
  'No complete signed standalone bundle receipt');
  need(bundle.payloadHashes && Object.keys(bundle.payloadHashes).length > 0
    && Object.values(bundle.payloadHashes).every(digest), 'Malformed bundle payload pins');
}

export function inspectDeliveryReceipts(report, roles) {
  const bundle = report.bundle, pins = report.inputs;
  inspectBundle(bundle);
  need(report.schemaVersion === 1 && report.status === 'caustics-delivery-package-validated', 'Unaccepted delivery package');
  need(absolute(report.app) && report.app.endsWith('.app') && absolute(report.engine) && absolute(report.project)
    && report.project.startsWith(report.engine + '/') && report.engine !== '/Users/Shared/Epic Games/UE_5.8', 'Invalid delivery app/engine/project identity');
  need(bundle.launch?.executable === resolve(report.app, 'Contents/MacOS/BreziTwin'), 'Delivery launch points to another app');
  need(pins && Object.keys(pins).length > 0 && Object.entries(pins).every(([p, h]) => absolute(p) && digest(h)), 'Malformed delivery provenance pins');
  for (const role of deliveryRoles) need(absolute(report[role]) && digest(pins[report[role]]) && roles[role], 'Missing pinned delivery role: ' + role);
  const { acceptedEditor: editor, acceptedGame: game, sourceClosure: source, cookReceipt: cook,
    archiveReceipt: archive, cookedBindingReceipt: cooked, sealReceipt: seal } = roles;
  for (const [value, status] of [[editor, 'caustics-delivery-editor-build-accepted'], [game, 'caustics-delivery-game-build-accepted'], [source, 'caustics-delivery-source-frozen']]) {
    need(value.status === status && Array.isArray(value.errors) && value.errors.length === 0
      && value.engineRoot === report.engine && value.projectRoot === report.project, 'Unaccepted or unrelated source/build receipt');
    need(value.fileHashes && Object.keys(value.fileHashes).length > 0
      && Object.entries(value.fileHashes).every(([p, h]) => absolute(p) && digest(h)), 'Missing historical source/build pins');
  }
  if (report.renderProfileInterface !== undefined) {
    const capability = report.renderProfileInterface;
    need(capability.schemaVersion === 1
      && isDeepStrictEqual(capability.profiles, ['native', 'balanced', 'performance'])
      && capability.sourcePins
      && isDeepStrictEqual(Object.keys(capability.sourcePins).sort(),
        ['BreziRenderQualityPolicy.h', 'BreziRenderQuality.cpp', 'BreziPlayerController.cpp', 'BreziPlayerController.h']
          .map(name => resolve(report.project, 'Source/BreziTwin', name)).sort())
      && Object.entries(capability.sourcePins).every(([path, hash]) => absolute(path) && digest(hash)
        && path.startsWith(resolve(report.project, 'Source/BreziTwin') + '/')
        && source.fileHashes[path] === hash), 'Native profile interface lacks compiled source provenance');
  }
  need(editor.sourceClosure === report.sourceClosure && game.sourceClosure === report.sourceClosure, 'Build source closure differs');
  for (const [value, mode] of [[cook, 'cook'], [archive, 'archive']]) {
    need(value.status === 'native-delivery-exited-zero-and-drained' && value.mode === mode && value.nativeExitCode === 0
      && ['errors', 'remainingOwned', 'changedPinnedInputs', 'errorLines'].every(k => Array.isArray(value[k]) && value[k].length === 0)
      && value.engineRoot === report.engine && value.projectRoot === report.project, 'Cook/archive did not close cleanly');
    for (const role of ['acceptedEditor', 'acceptedGame', 'sourceClosure']) need(value.inputs?.[role]?.path === report[role]
      && value.inputs[role].sha256 === pins[report[role]], 'Cook/archive provenance differs: ' + role);
  }
  need(archive.cookReceipt === report.cookReceipt && archive.appPath === report.app, 'Archive app/cook differs');
  need(cooked.schemaVersion === 1 && cooked.status === 'cooked-source-container-lineage-validated'
    && cooked.cookReceiptSha256 === pins[report.cookReceipt] && cooked.archiveReceiptSha256 === pins[report.archiveReceipt]
    && cooked.sourcePinsUnchangedAcrossCookAndArchive === true && cooked.freshCookOutput === true
    && cooked.allRequiredPackagesInContainer === true && cooked.receiverCount === 45 && cooked.waterCount === 1
    && cooked.waveCount === 12, 'Cooked source/container lineage differs');
  for (const [name, hash] of [['cooked-runtime-binding.json', pins[report.cookedBindingReceipt]],
    ['active-water-binding.json', cooked.activeWaterBindingSha256], ['transport-scene-binding.json', cooked.sourceBindingSha256]]) {
    need(digest(hash) && bundle.payloadHashes[resources + name] === hash, 'Sealed cooked binding differs: ' + name);
    if (name !== 'cooked-runtime-binding.json') need(source.fileHashes[resolve(report.project, 'Plugins/BreziCausticsProbe/Resources', name)] === hash,
      'Compiled source binding differs: ' + name);
  }
  const containers = cooked.containerFiles;
  need(Array.isArray(containers) && containers.length > 0 && new Set(containers.map(r => r.name)).size === containers.length, 'Invalid cooked container list');
  need(isDeepStrictEqual(Object.keys(bundle.payloadHashes).filter(k => k.startsWith(paks)).sort(), containers.map(r => paks + r.name).sort()), 'Cooked container inventory differs');
  for (const row of containers) need(typeof row.name === 'string' && basename(row.name) === row.name
    && Number.isSafeInteger(row.bytes) && row.bytes > 0 && digest(row.sha256) && bundle.payloadHashes[paks + row.name] === row.sha256, 'Cooked container pin differs');
  need(seal.status === 'self-exec-entry-sealed-and-signed' && seal.app === report.app && seal.codeSignature === 'deep-strict-valid'
    && isDeepStrictEqual(seal.launch, bundle.launch) && seal.proof?.status === 'signature-only-change-validated'
    && seal.proof.afterSha256 === bundle.launch.executableSha256, 'Signature/entry seal differs');
  need(seal.additionalResources?.some(r => r.source === report.cookedBindingReceipt && r.sha256 === pins[report.cookedBindingReceipt]
    && r.relativePath === resources + 'cooked-runtime-binding.json'), 'Cooked binding was not included in the seal');
  need(report.linkedGameProof?.status === 'raw-linked-code-preserved-through-packaging-signature'
    && report.linkedGameProof.actualPackagedSha256 === seal.proof.beforeSha256, 'Raw linked Game to signed app proof differs');
}

async function pinnedBytes(path, expected = null) {
  const stat = await lstat(path);
  need(stat.isFile() && !stat.isSymbolicLink() && await realpath(path) === path, 'Receipt must be a regular canonical file: ' + path);
  const bytes = await readFile(path), hash = sha(bytes);
  need(expected === null || hash === expected, 'Package receipt/provenance changed: ' + path);
  return { bytes, hash, value: JSON.parse(bytes) };
}

export async function loadSelectedPackage({ root, env = process.env }) {
  const selection = selectPackageReport(root, env), loaded = await pinnedBytes(selection.path, selection.expectedSha256);
  const report = loaded.value;
  inspectBundle(report.bundle);
  let app, kind, artifactPins = {}, sourceClosureSha256 = null, cookedBindingSha256 = null;
  if (report.status === 'packaged') {
    need(report.renderProfileInterface === undefined, 'Legacy package cannot advertise an unproven native profile interface');
    kind = 'legacy';
    app = report.appPath;
    need(absolute(app) && app.endsWith('.app') && dirname(app) === resolve(root, 'output/unreal/package/Mac')
      && report.bundle.launch?.executable === resolve(app, 'Contents/MacOS/BreziTwin'), 'Legacy app identity differs');
  } else {
    need(selection.explicit, 'Delivery packages require an explicit report path and SHA-256');
    need(report.status === 'caustics-delivery-package-validated', 'Unknown package receipt schema');
    const roles = {};
    for (const role of deliveryRoles) {
      const path = report[role], expected = report.inputs?.[path];
      need(absolute(path) && digest(expected), 'Missing pinned delivery role: ' + role);
      roles[role] = (await pinnedBytes(path, expected)).value;
      artifactPins[path] = expected;
    }
    inspectDeliveryReceipts(report, roles);
    app = report.app; kind = 'caustics-delivery';
    sourceClosureSha256 = report.inputs[report.sourceClosure]; cookedBindingSha256 = report.inputs[report.cookedBindingReceipt];
  }
  return { app, report, reportBytes: loaded.bytes, provenance: { kind, reportPath: selection.path,
    reportSha256: loaded.hash, artifactPins, sourceClosureSha256, cookedBindingSha256,
    sourceFreshness: 'Build/source/helper pins are historical receipt provenance; current workspace and old generated build products are not revalidated by app launch.' } };
}

export async function verifySelectedPackage(selected) {
  await pinnedBytes(selected.provenance.reportPath, selected.provenance.reportSha256);
  for (const [path, hash] of Object.entries(selected.provenance.artifactPins)) await pinnedBytes(path, hash);
  const payload = await verifyPackagedPayload(selected.app, selected.report.bundle);
  const launch = await resolveAppLaunch(selected.app, selected.report.bundle);
  // Read-only verification of the current signature. Never signs or invokes UnrealPak/UE.
  await exec('/usr/bin/codesign', ['--verify', '--deep', '--strict', selected.app], { timeout: 60000 });
  return { payload, launch, signature: 'deep-strict-valid' };
}
