// Icon-only continuation of an immutable, already sealed Dom package.
// The installed app and prior receipt are read-only; all writes use a fresh output.
import { execFile } from 'node:child_process';
import { lstat, mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { dirname, isAbsolute, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
import { compareSignatureOnly } from './macho-signature.mjs';
import { inspectStartupEntry } from './startup-entry.mjs';
import { resolveAppLaunch } from './app-launch.mjs';
import { verifyPackage, verifyPackagedPayload } from './package-verify.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const installedApp = '/Applications/Dom.app';
const exec = promisify(execFile);
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const need = (ok, message) => { if (!ok) throw Error(message); };
const saveNew = (path, value) => writeFile(path, JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
const icons = ['Contents/Resources/Dom.icns', 'Contents/Resources/AppIcon.icns', 'Contents/Resources/Assets.car'];
const provenance = 'Contents/Resources/Dom-icon-source.json';
const main = 'Contents/MacOS/BreziTwin';
const policy = 'Contents/Resources/BreziStartupPolicy.json';
const signingResources = 'Contents/_CodeSignature/CodeResources';
const sameHashes = (a, b) => {
  const paths = [...new Set([...Object.keys(a), ...Object.keys(b)])].sort();
  return paths.every(path => a[path] === b[path]);
};

/** Protect the complete runtime/scene payload, including Info.plist and policy.
 * The main binary is checked separately with the stricter Mach-O signing gate.
 */
export function assertRebrandPayloadScope(before, after) {
  for (const path of [main, policy, signingResources, ...icons])
    need(typeof before[path] === 'string', 'Required original rebranding payload missing: ' + path);
  need(!(provenance in before), 'This continuation requires an original package without icon provenance');
  const allowedChanges = new Set([main, signingResources, ...icons]);
  const changedFiles = [];
  for (const [path, digest] of Object.entries(before)) {
    need(path in after, 'Rebranding removed original payload: ' + path);
    if (after[path] !== digest) {
      need(allowedChanges.has(path), 'Unrelated payload changed during rebranding: ' + path);
      changedFiles.push(path);
    }
  }
  const addedFiles = Object.keys(after).filter(path => !(path in before));
  need(addedFiles.length === 1 && addedFiles[0] === provenance,
    'Rebranding may add only the canonical Dom-icon-source.json');
  return { changedFiles: changedFiles.sort(), addedFiles,
    unchangedFileCount: Object.keys(before).length - changedFiles.length,
    startupPolicyPreservedByteForByte: after[policy] === before[policy] };
}

/** Signing must retain the exact extracted original entitlement representation. */
export function assertOriginalEntitlements(before, after) {
  need(Buffer.from(before).equals(Buffer.from(after)), 'Original GUI entitlements changed during icon signing');
}

function isWithin(parent, child) {
  const path = relative(parent, child);
  return path === '' || (!isAbsolute(path) && path !== '..' && !path.startsWith('../'));
}

async function inventory(directory) {
  const rootStat = await lstat(directory);
  need(!rootStat.isSymbolicLink() && rootStat.isDirectory(), 'Expected a real source directory: ' + directory);
  const hashes = {};
  async function visit(path) {
    for (const name of (await readdir(path)).sort()) {
      const file = resolve(path, name), stat = await lstat(file);
      need(!stat.isSymbolicLink(), 'Source must not contain symlinks: ' + file);
      if (stat.isDirectory()) await visit(file);
      else {
        need(stat.isFile(), 'Nonregular source: ' + file);
        hashes[relative(directory, file)] = sha(await readFile(file));
      }
    }
  }
  await visit(directory);
  return hashes;
}

async function readRegular(path) {
  const stat = await lstat(path);
  need(stat.isFile() && !stat.isSymbolicLink(), 'Expected a regular resource: ' + path);
  return readFile(path);
}

async function assertSourceConserved(clone) {
  for (const name of ['Source', 'Config', 'Content', 'Binaries']) {
    need(clone.sourceHashes?.[name], 'Original source conservation hashes missing: ' + name);
    need(sameHashes(await inventory(resolve(clone.sourceProject, name)), clone.sourceHashes[name]),
      'Accepted source project differs from its original clone receipt: ' + name);
  }
  need(sha(await readFile(resolve(clone.sourceProject, 'BreziTwin.uproject'))) === clone.descriptorSha256,
    'Accepted source project descriptor changed');
}

export async function rebrandDomApp(environment = process.env) {
  const sourceOutput = resolve(root, environment.DOM_APP_SOURCE_OUTPUT ?? 'output/unreal/dom-app-20261003-r1');
  const output = resolve(root, environment.DOM_APP_OUTPUT ?? 'output/unreal/dom-app-20261003-r2');
  const app = resolve(output, 'package/Mac/BreziTwin.app');
  const previousReceiptPath = resolve(sourceOutput, 'dom-package.json');
  const previousReceiptBytes = await readRegular(previousReceiptPath);
  const previous = JSON.parse(previousReceiptBytes);
  need(previous.status === 'dom-final-exterior-standalone-package-validated'
    && previous.activeDesign === 'C/B/B' && previous.streetAndRightSetbackMm === 3000
    && previous.appName === 'Dom' && previous.gameConfiguration === 'Shipping'
    && previous.bundle?.fileCount === 35
    && previous.approvedSourceProjectPreserved === true && previous.authoredContentPreserved === true,
    'An original validated 35-file final Dom package receipt is required');
  const engine = resolve(environment.UNREAL_ENGINE_ROOT ?? previous.engine);
  const cloneReceiptPath = previous.sourceCloneReceiptPath ?? resolve(sourceOutput, 'source-clone.json');
  const cloneBytes = await readRegular(cloneReceiptPath), clone = JSON.parse(cloneBytes);
  need(sha(cloneBytes) === previous.sourceCloneReceiptSha256
    && clone.sourceProject === previous.sourceProject, 'Original source clone receipt changed');
  need(isWithin(resolve(root, 'output/unreal'), output) && output !== resolve(root, 'output/unreal'),
    'Use a fresh output directory under output/unreal');
  for (const protectedPath of [sourceOutput, installedApp, clone.sourceProject, previous.project,
    resolve(root, 'unreal/BreziTwin')])
    need(!isWithin(protectedPath, output) && !isWithin(output, protectedPath), 'Output overlaps protected source: ' + protectedPath);
  try { await lstat(output); throw Error('Fresh output required; do not overlay a prior package or receipt'); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  const currentSelection = JSON.parse(await readFile(resolve(root, 'output/unreal/exterior-final-current.json')));
  need(currentSelection.status === 'final-saved-editor-exterior-user-accepted'
    && currentSelection.userAcceptedCurrentVisualResult === true
    && currentSelection.launchMap?.sha256 === previous.selection?.launchMap?.sha256,
    'The accepted final scene changed; icon-only rebranding cannot update the scene');
  need(sha(await readFile(previous.selection.launchMap.path)) === previous.selection.launchMap.sha256,
    'Accepted final scene map changed');

  const beforePayload = await verifyPackagedPayload(installedApp, previous.bundle);
  await exec('/usr/bin/codesign', ['--verify', '--deep', '--strict', installedApp]);
  const signingBefore = (await exec('/usr/bin/codesign', ['--display', '--verbose=4', installedApp])).stderr;
  need(/^Signature=adhoc$/m.test(signingBefore) && /^Identifier=local\.brezi\.twin$/m.test(signingBefore),
    'Only the reviewed original local ad-hoc GUI app is supported');
  const plist = JSON.parse((await exec('/usr/bin/plutil', ['-convert', 'json', '-o', '-',
    resolve(installedApp, 'Contents/Info.plist')])).stdout);
  need(plist.CFBundleName === 'Dom' && plist.CFBundleDisplayName === 'Dom'
    && plist.CFBundleIconFile === 'Dom.icns' && plist.CFBundleIconName === undefined,
    'Original Dom plist/icon selection must already be correct');
  const beforeMain = await readRegular(resolve(installedApp, main));
  const beforeEntry = inspectStartupEntry(beforeMain);
  const beforeLaunch = await resolveAppLaunch(installedApp);
  need(beforeLaunch.startupPolicySha256 === previous.bundle.launch.startupPolicySha256
    && JSON.stringify(beforeEntry) === JSON.stringify(previous.bundle.launch.linkedEntry),
    'Original linked startup entry differs from the previous receipt');
  const originalEntitlementsText = (await exec('/usr/bin/codesign',
    ['--display', '--entitlements', '-', '--xml', installedApp])).stdout;

  const resources = resolve(root, 'unreal/BreziTwin/Build/Mac/Resources');
  const iconSource = resolve(resources, 'Dom.icns'), icon = await readRegular(iconSource);
  need(icon.length >= 8 && icon.subarray(0, 4).toString() === 'icns'
    && icon.readUInt32BE(4) === icon.length, 'Invalid canonical Dom.icns');
  const provenanceSource = resolve(resources, 'Dom-icon-source.json');
  const provenanceBytes = await readRegular(provenanceSource);
  const iconProvenance = JSON.parse(provenanceBytes);
  need(iconProvenance && typeof iconProvenance === 'object' && !Array.isArray(iconProvenance),
    'Canonical icon provenance must be a JSON object');
  const catalogSource = resolve(resources, 'Assets.xcassets');
  const catalogHashes = await inventory(catalogSource);
  need(Object.keys(catalogHashes).some(path => path.startsWith('AppIcon.appiconset/') && path.endsWith('.png')),
    'Canonical AppIcon catalog has no raster icons');
  await assertSourceConserved(clone);

  // Exclusive creation is the final preflight gate. A failed attempt is retained
  // for review and cannot be silently reused or overwrite its partial evidence.
  await mkdir(dirname(output), { recursive: true });
  await mkdir(output);
  const commands = [];
  const run = async (command, args) => {
    const result = await exec(command, args, { maxBuffer: 8 * 1024 * 1024 });
    commands.push({ command, args, stdout: result.stdout, stderr: result.stderr });
    return result;
  };
  try {
    await mkdir(dirname(app), { recursive: true });
    await run('/bin/cp', ['-cR', installedApp, app]);
    await verifyPackagedPayload(app, previous.bundle);
    const catalogSnapshot = resolve(output, 'branding/catalog-source');
    await mkdir(dirname(catalogSnapshot), { recursive: true });
    await run('/bin/cp', ['-cR', catalogSource, catalogSnapshot]);
    need(sameHashes(await inventory(catalogSnapshot), catalogHashes), 'Catalog snapshot differs from canonical source');
    const catalogOutput = resolve(output, 'branding/catalog-final');
    await mkdir(catalogOutput);
    await run('xcrun', ['actool', '--compile', catalogOutput, '--platform', 'macosx',
      '--minimum-deployment-target', '14.0', '--app-icon', 'AppIcon', '--output-partial-info-plist',
      resolve(catalogOutput, 'AssetsInfo.plist'), catalogSnapshot]);
    await writeFile(resolve(app, icons[0]), icon);
    const catalogResources = {};
    for (const name of ['Assets.car', 'AppIcon.icns']) {
      const bytes = await readRegular(resolve(catalogOutput, name));
      need(bytes.length > 0, 'Empty native icon catalog resource: ' + name);
      await writeFile(resolve(app, 'Contents/Resources', name), bytes);
      catalogResources[name] = sha(bytes);
    }
    await writeFile(resolve(app, provenance), provenanceBytes, { flag: 'wx' });
    const entitlementsPath = resolve(output, 'original-entitlements.plist');
    await writeFile(entitlementsPath, originalEntitlementsText, { flag: 'wx' });
    const originalEntitlements = JSON.parse((await run('/usr/bin/plutil',
      ['-convert', 'json', '-o', '-', entitlementsPath])).stdout);
    need(originalEntitlements['com.apple.security.app-sandbox'] === true
      && originalEntitlements['com.apple.security.inherit'] === undefined,
      'Expected original full GUI sandbox without helper inheritance');
    // Do not call sealStartupEntry: this app already carries its immutable policy.
    await run('/usr/bin/codesign', ['--force', '--sign', '-',
      '--preserve-metadata=identifier,requirements,flags,runtime', '--entitlements', entitlementsPath, app]);
    await run('/usr/bin/codesign', ['--verify', '--deep', '--strict', app]);
    const finalEntitlementsText = (await run('/usr/bin/codesign',
      ['--display', '--entitlements', '-', '--xml', app])).stdout;
    assertOriginalEntitlements(originalEntitlementsText, finalEntitlementsText);
    await writeFile(resolve(output, 'final-entitlements.plist'), finalEntitlementsText, { flag: 'wx' });
    const afterMain = await readRegular(resolve(app, main));
    const proof = compareSignatureOnly(beforeMain, afterMain);
    const finalEntry = inspectStartupEntry(afterMain);
    need(JSON.stringify(finalEntry) === JSON.stringify(beforeEntry), 'Icon signing changed the linked startup entry');
    const bundle = await verifyPackage(app, engine);
    const payloadScope = assertRebrandPayloadScope(beforePayload.payloadHashes, bundle.payloadHashes);
    need(bundle.payloadHashes[icons[0]] === sha(icon)
      && bundle.payloadHashes[provenance] === sha(provenanceBytes), 'Canonical branding resources changed while signing');
    for (const [name, digest] of Object.entries(catalogResources))
      need(bundle.payloadHashes['Contents/Resources/' + name] === digest, 'Compiled native icon changed while signing: ' + name);
    need(bundle.launch.startupPolicySha256 === beforeLaunch.startupPolicySha256
      && bundle.launch.entrySourceSha256 === beforeLaunch.entrySourceSha256,
      'Existing startup policy must remain byte-for-byte');
    await verifyPackagedPayload(installedApp, previous.bundle);
    await run('/usr/bin/codesign', ['--verify', '--deep', '--strict', installedApp]);
    assertOriginalEntitlements(originalEntitlementsText, (await run('/usr/bin/codesign',
      ['--display', '--entitlements', '-', '--xml', installedApp])).stdout);
    need(sha(await readRegular(previousReceiptPath)) === sha(previousReceiptBytes), 'Prior immutable package receipt changed');
    need(sha(await readRegular(cloneReceiptPath)) === sha(cloneBytes), 'Original clone receipt changed');
    await assertSourceConserved(clone);
    need(sha(await readRegular(iconSource)) === sha(icon)
      && sha(await readRegular(provenanceSource)) === sha(provenanceBytes)
      && sameHashes(await inventory(catalogSource), catalogHashes)
      && sameHashes(await inventory(catalogSnapshot), catalogHashes), 'Canonical icon inputs changed while rebranding');
    const previousPackage = { receiptPath: previousReceiptPath, receiptSha256: sha(previousReceiptBytes),
      installedSourceApp: installedApp, startupEntry: previous.startupEntry };
    const startupEntry = { status: 'self-exec-entry-preserved-and-signed', app, linkedEntry: finalEntry,
      proof, launch: bundle.launch, entrySourceSha256: beforeLaunch.entrySourceSha256,
      startupPolicySha256: beforeLaunch.startupPolicySha256, startupPolicyPreservedByteForByte: true,
      originalEntitlements, finalEntitlements: originalEntitlements, entitlementSemanticDiff: [],
      entitlementXmlPreservedByteForByte: true, codeSignature: 'deep-strict-valid',
      inheritedSeal: { receiptPath: previousReceiptPath, receiptSha256: sha(previousReceiptBytes),
        field: 'startupEntry' }, actualGameLaunchPending: true };
    const rebranding = { status: 'icon-only-rebranding-validated', previousPackage, payloadScope,
      cloneMethod: 'native macOS /bin/cp -cR APFS copy-on-write clone',
      originalInstalledAppPreserved: true, sceneRuntimeUnchanged: true,
      signingEntitlementsSha256: sha(originalEntitlementsText), commands,
      scope: 'Only the three native icon resources, added canonical icon provenance and outer signing bytes changed. Main code, data, UUID, linked entry, startup policy, Info.plist, scene and every runtime dependency are preserved.' };
    await saveNew(resolve(output, 'rebranding.json'), rebranding);
    const receipt = { ...previous, createdAt: new Date().toISOString(), appPath: app,
      sourceCloneReceiptPath: cloneReceiptPath, iconSha256: sha(icon), bundle, startupEntry,
      nativeIconCatalog: { source: catalogSource, sourceHashes: catalogHashes, resources: catalogResources },
      iconSource: { path: provenanceSource, sha256: sha(provenanceBytes), bundledPath: provenance },
      rebrandingReceiptPath: resolve(output, 'rebranding.json'),
      rebrandingReceiptSha256: sha(await readFile(resolve(output, 'rebranding.json'))),
      previousPackageReceiptPath: previousReceiptPath, previousPackageReceiptSha256: sha(previousReceiptBytes),
      iconOnlyRebranding: true, sceneRuntimeUnchanged: true, runtimeVisualVerified: false, installed: false };
    await saveNew(resolve(output, 'dom-package.json'), receipt);
    console.log(JSON.stringify({ status: 'dom-icon-only-package-validated', app, output,
      receiptPath: resolve(output, 'dom-package.json'), changedFiles: payloadScope.changedFiles,
      addedFiles: payloadScope.addedFiles, sceneRuntimeUnchanged: true }, null, 2));
    return receipt;
  } catch (error) {
    await saveNew(resolve(output, 'rebranding-failure.json'), { status: 'failed', failedAt: new Date().toISOString(),
      message: error.message, app, previousReceiptPath, commands }).catch(() => {});
    throw error;
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  need(process.argv.length === 2, 'Configure DOM_APP_SOURCE_OUTPUT and DOM_APP_OUTPUT; no positional arguments');
  await rebrandDomApp();
}
