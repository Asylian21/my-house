// Repackage the explicitly accepted final exterior in an isolated APFS clone.
// Never write to the accepted project or rewrite its historical receipts.
import { execFile, spawn } from 'node:child_process';
import { constants } from 'node:fs';
import { access, cp, mkdir, readFile, readdir, lstat, writeFile, rename } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { dirname, resolve, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
import { sealStartupEntry } from './startup-entry-package.mjs';
import { verifyPackage } from './package-verify.mjs';
import { inspectCookLog } from './cook-log.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const output = resolve(root, process.env.DOM_APP_OUTPUT ?? 'output/unreal/dom-app-20261003-r1');
const engine = resolve(process.env.UNREAL_ENGINE_ROOT ?? '/Users/Shared/Epic Games/UE_5.8');
const project = resolve(output, 'Project/BreziTwin');
const exec = promisify(execFile), sha = bytes => createHash('sha256').update(bytes).digest('hex');
const need = (ok, why) => { if (!ok) throw Error(why); };
const save = async (file, value) => writeFile(file, JSON.stringify(value, null, 2) + '\n');
const launchArgs = ['-windowed', '-ResX=1920', '-ResY=1080', '-BreziOutput=retina',
  '-BreziRenderProfile=full', '-BreziView=exterior-neighborhood-ground-r38'];
const renderSourceFiles = ['BreziRenderQualityPolicy.h', 'BreziRenderQuality.cpp',
  'BreziPlayerController.h', 'BreziPlayerController.cpp'];

async function inventory(directory) {
  const hashes = {};
  async function visit(path) {
    for (const name of await readdir(path)) {
      const file = resolve(path, name), stat = await lstat(file);
      need(!stat.isSymbolicLink(), 'Source clone must not contain symlinks: ' + file);
      if (stat.isDirectory()) await visit(file);
      else if (stat.isFile()) hashes[relative(directory, file)] = sha(await readFile(file));
      else throw Error('Nonregular source: ' + file);
    }
  }
  await visit(directory); return hashes;
}
async function run(command, args, logName) {
  const startedAt = new Date().toISOString();
  let log = '';
  const outcome = await new Promise((accept, reject) => {
    const child = spawn(command, args, { cwd: root, env: { ...process.env,
      DOTNET_SYSTEM_NET_SOCKETS_INLINE_COMPLETIONS: '1' }, stdio: ['ignore', 'pipe', 'pipe'] });
    for (const stream of [child.stdout, child.stderr]) stream.on('data', bytes => {
      log += bytes; process.stdout.write(bytes);
    });
    child.once('error', reject);
    child.once('close', (code, signal) => accept({ pid: child.pid, code, signal }));
  });
  await writeFile(resolve(output, logName), log);
  await save(resolve(output, logName + '.json'), { command, args, startedAt,
    endedAt: new Date().toISOString(), ...outcome });
  need(outcome.code === 0 && !/\*\* BUILD FAILED \*\*|The following build commands failed:/i.test(log),
    'Native package phase failed; inspect ' + resolve(output, logName));
  return log;
}

async function prepare() {
  for (const existing of ['Project', 'package', 'source-clone.json']) {
    try { await access(resolve(output, existing)); throw Error('Fresh output required; do not overlay a prior package'); }
    catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
  const selectionPath = resolve(root, 'output/unreal/exterior-final-current.json');
  const selectionBytes = await readFile(selectionPath), selection = JSON.parse(selectionBytes);
  need(selection.status === 'final-saved-editor-exterior-user-accepted'
    && selection.userAcceptedCurrentVisualResult === true && selection.activeDesign === 'C/B/B'
    && selection.streetAndRightSetbackMm === 3000, 'No explicitly accepted final exterior');
  const sourceProject = dirname(selection.launchProject);
  need(sha(await readFile(selection.launchMap.path)) === selection.launchMap.sha256
    && selection.launchMap.sha256 === selection.savedMap.sha256, 'Accepted saved/launch map differs');
  await mkdir(dirname(project), { recursive: true });
  const before = {};
  for (const name of ['Source', 'Config', 'Content', 'Binaries']) {
    before[name] = await inventory(resolve(sourceProject, name));
    await cp(resolve(sourceProject, name), resolve(project, name), {
      recursive: true, mode: constants.COPYFILE_FICLONE, preserveTimestamps: true });
    need(JSON.stringify(await inventory(resolve(project, name))) === JSON.stringify(before[name]),
      'Clone inventory differs: ' + name);
  }
  const descriptor = await readFile(selection.launchProject);
  await writeFile(resolve(project, 'BreziTwin.uproject'), descriptor);
  // The accepted scene intentionally retains only runtime-authoring dependencies.
  // Restore build metadata from canonical source in this isolated destination.
  await cp(resolve(root, 'unreal/BreziTwin/Build'), resolve(project, 'Build'), {
    recursive: true, mode: constants.COPYFILE_FICLONE, preserveTimestamps: true });
  const target = JSON.parse(await readFile(resolve(project, 'Binaries/Mac/BreziTwin-Mac-Shipping.target')));
  need(target.TargetName === 'BreziTwin' && target.Platform === 'Mac' && target.Configuration === 'Shipping',
    'Accepted native target is not a relocatable Shipping Game');
  await save(resolve(output, 'source-clone.json'), { schemaVersion: 1,
    status: 'accepted-final-project-cloned-and-verified', createdAt: new Date().toISOString(),
    sourceProject, project, selectionPath, selectionSha256: sha(selectionBytes), selection,
    descriptorSha256: sha(descriptor), sourceHashes: before,
    nativeBuild: { configuration: 'Shipping', method: 'verified-existing-native-game',
      executableSha256: sha(await readFile(resolve(project, 'Binaries/Mac/BreziTwin'))),
      targetReceiptSha256: sha(await readFile(resolve(project, 'Binaries/Mac/BreziTwin-Mac-Shipping.target'))) },
    launchArgs, cloneMethod: 'COPYFILE_FICLONE' });
}

async function packageApp() {
  const clone = JSON.parse(await readFile(resolve(output, 'source-clone.json')));
  need(clone.project === project, 'Wrong cloned project');
  await access(resolve(project, 'BreziTwin.uproject'));
  try {
    await access(resolve(output, 'package'));
    const retained = resolve(output, 'package-history', new Date().toISOString().replace(/[:.]/g, '-'));
    await mkdir(dirname(retained), { recursive: true });
    await rename(resolve(output, 'package'), retained);
  } catch (error) { if (error.code !== 'ENOENT') throw error; }
  const args = ['BuildCookRun', '-project=' + resolve(project, 'BreziTwin.uproject'),
    '-noP4', '-platform=Mac', '-clientconfig=Shipping', '-skipbuild', '-cook', '-stage', '-pak',
    '-package', '-archive', '-archivedirectory=' + resolve(output, 'package'), '-unattended', '-utf8output',
    '-xcodebuildoptions=-derivedDataPath "' + resolve(output, 'xcode-data') + '"'
      + ' UE_UBT_BINARY_SUBPATH=BreziTwin UE_MAC_EXECUTABLE_NAME=BreziTwin PRODUCT_NAME=BreziTwin EXECUTABLE_NAME=BreziTwin'];
  const log = await run(resolve(engine, 'Engine/Build/BatchFiles/RunUAT.sh'), args, 'package.log');
  const cook = inspectCookLog(log);
  need(cook.status === 'cook-log-validated', 'Cook validation failed: ' + JSON.stringify(cook));
  await save(resolve(output, 'cook.json'), cook);
}

async function buildDomEntry() {
  const source = resolve(project, 'Source/BreziTwin/BreziStartupEntry.cpp');
  const clone = JSON.parse(await readFile(resolve(output, 'source-clone.json')));
  const before = await readFile(source), domEntry = await readFile(resolve(root, 'scripts/unreal/dom-startup-entry.cpp'));
  need(sha(before) === clone.sourceHashes.Source['BreziTwin/BreziStartupEntry.cpp'],
    'Only replace the exact cloned original app entry');
  await writeFile(source, domEntry);
  // Keep the accepted map, materials and geometry byte-identical. Only the
  // maintained quality policy/UI and app entry are rebuilt in this fresh clone.
  const renderSourceHashes = {};
  for (const name of renderSourceFiles) {
    const canonical = resolve(root, 'unreal/BreziTwin/Source/BreziTwin', name);
    const bytes = await readFile(canonical);
    const destination = resolve(project, 'Source/BreziTwin', name);
    await writeFile(destination, bytes);
    renderSourceHashes['BreziTwin/' + name] = sha(bytes);
  }
  await save(resolve(output, 'dom-entry-source.json'), { schemaVersion: 1,
    status: 'isolated-dom-viewer-startup-defaults', source, originalSha256: sha(before), domEntrySha256: sha(domEntry),
    launchArgs, renderSourceHashes, policy: 'Viewer defaults only with no explicit arguments except LLM/hitch and macOS psn tokens; explicit CLI/QA is preserved.',
    scope: 'App-owned startup entry and maintained render policy/UI replaced in isolated clone; accepted project and cloned Config/Content unchanged.' });
  await save(resolve(output, 'profile.json'), { gameConfiguration: 'Shipping' });
  const descriptor = resolve(project, 'BreziTwin.uproject');
  await run(resolve(engine, 'Engine/Build/BatchFiles/Mac/GenerateProjectFiles.sh'), [
    '-project=' + descriptor, '-game', '-platforms=Mac', '-DeployOnly', '-NoIntellisense', '-NoDotNet',
    '-IgnoreJunk', '-IncludeTempTargets', '-projectfileformat=XCode', '-automated', '-singletarget=BreziTwin'], 'game-project-files.log');
  await run(resolve(engine, 'Engine/Build/BatchFiles/Mac/Build.sh'), ['BreziTwin', 'Mac', 'Shipping', descriptor,
    '-WaitMutex', '-NoUBA', '-createstripflagfile', '-WriteOutdatedActions=' + resolve(output, 'game-actions.json')], 'game-graph.log');
  await run('python3', ['-B', 'scripts/unreal/model-refresh-build.py', '--output', output, '--engine', engine], 'game-build.log');
  await run(process.execPath, ['tests/unreal-dom-startup-native.mjs'], 'startup-fixture.log');
}

async function finish() {
  const clone = JSON.parse(await readFile(resolve(output, 'source-clone.json')));
  const app = resolve(output, 'package/Mac/BreziTwin.app');
  const plist = resolve(app, 'Contents/Info.plist');
  const iconSource = resolve(root, 'unreal/BreziTwin/Build/Mac/Resources/Dom.icns');
  await exec('/usr/bin/codesign', ['--verify', '--deep', '--strict', app]);
  const originalEntitlements = (await exec('/usr/bin/codesign', ['--display', '--entitlements', '-', '--xml', app])).stdout;
  const entitlements = resolve(output, 'branding-entitlements.plist');
  await writeFile(entitlements, originalEntitlements);
  // UAT redundantly stages the build-product .app inside the already complete
  // standalone outer app. Runtime dependencies are the retained raw binary and
  // sibling libraries. Move just that redundant bundle out of distribution.
  let redundantNestedBundle = null;
  const nestedApp = resolve(app, 'Contents/UE/BreziTwin/Binaries/Mac/BreziTwin.app');
  try {
    await access(nestedApp);
    const preserved = resolve(output, 'package-history/redundant-nested-build-product/BreziTwin.app');
    await mkdir(dirname(preserved), { recursive: true });
    const preservedHashes = await inventory(nestedApp);
    await rename(nestedApp, preserved);
    need(JSON.stringify(await inventory(preserved)) === JSON.stringify(preservedHashes), 'Nested build-product preservation differs');
    redundantNestedBundle = { originalPath: nestedApp, preservedPath: preserved, preservedHashes,
      reason: 'Redundant nested build-product bundle; outer standalone main and every raw runtime library retained.' };
  } catch (error) { if (error.code !== 'ENOENT') throw error; }
  const icon = await readFile(iconSource);
  need(icon.subarray(0, 4).toString() === 'icns', 'Invalid Dom.icns');
  await writeFile(resolve(app, 'Contents/Resources/Dom.icns'), icon);
  // Build the project-owned catalog as well, so every native AppIcon fallback
  // contains the same Dom brand. This never modifies the installed UE catalog.
  const catalogSource = resolve(root, 'unreal/BreziTwin/Build/Mac/Resources/Assets.xcassets');
  const catalogOutput = resolve(output, 'branding/catalog-final');
  await mkdir(catalogOutput, { recursive: true });
  const catalogHashes = await inventory(catalogSource);
  await exec('xcrun', ['actool', '--compile', catalogOutput, '--platform', 'macosx', '--minimum-deployment-target', '14.0',
    '--app-icon', 'AppIcon', '--output-partial-info-plist', resolve(catalogOutput, 'AssetsInfo.plist'), catalogSource]);
  need(JSON.stringify(await inventory(catalogSource)) === JSON.stringify(catalogHashes), 'Dom catalog source changed while compiling');
  const catalogResources = {};
  for (const name of ['Assets.car', 'AppIcon.icns']) {
    const bytes = await readFile(resolve(catalogOutput, name));
    await writeFile(resolve(app, 'Contents/Resources', name), bytes);
    catalogResources[name] = sha(bytes);
  }
  for (const [key, value] of [['CFBundleName', 'Dom'], ['CFBundleDisplayName', 'Dom'], ['CFBundleIconFile', 'Dom.icns']])
    await exec('/usr/bin/plutil', ['-replace', key, '-string', value, plist]);
  const plistBeforeIconSelection = JSON.parse((await exec('/usr/bin/plutil', ['-convert', 'json', '-o', '-', plist])).stdout);
  if (plistBeforeIconSelection.CFBundleIconName !== undefined)
    await exec('/usr/bin/plutil', ['-remove', 'CFBundleIconName', plist]);
  await exec('/usr/bin/codesign', ['--force', '--sign', '-', '--preserve-metadata=identifier,requirements,flags,runtime',
    '--entitlements', entitlements, app]);
  await exec('/usr/bin/codesign', ['--verify', '--deep', '--strict', app]);
  const creditsPath = resolve(root, 'unreal/BreziTwin/Build/Mac/Resources/ExteriorDataCredits.json');
  const creditBytes = await readFile(creditsPath);
  const legacyReceipt = JSON.parse(await readFile(resolve(root, 'output/unreal/exterior-20260930-r5/model-package.json')));
  need(legacyReceipt.bundle.payloadHashes['Contents/Resources/ExteriorDataCredits.json'] === sha(creditBytes),
    'Historical exterior attribution resource changed');
  const additionalResources = [{ relativePath: 'Contents/Resources/ExteriorDataCredits.json', source: creditsPath, sha256: sha(creditBytes) }];
  const roofPacketPath = resolve(root, 'output/unreal/exterior-clay-roof-photo-20261002-r45-unbound-proposal/clay-roof-photo-proposal.json');
  const roofPacket = JSON.parse(await readFile(roofPacketPath));
  const finalDocPath = resolve(root, 'docs/unreal-final-exterior.md');
  const currentCreditsPath = resolve(output, 'FinalExteriorSources.json');
  await save(currentCreditsPath, { schemaVersion: 1, finalExteriorDocumentation: { path: finalDocPath,
    sha256: sha(await readFile(finalDocPath)) }, acceptedSavedScene: clone.selection.savedMap,
    clayRoofPhotoSource: roofPacket.source, localSourcePacket: { path: roofPacketPath, sha256: sha(await readFile(roofPacketPath)) },
    note: 'Current roof source metadata copied from the explicit local source packet. Original dataset attribution is retained byte-for-byte in ExteriorDataCredits.json.' });
  additionalResources.push({ relativePath: 'Contents/Resources/FinalExteriorSources.json', source: currentCreditsPath,
    sha256: sha(await readFile(currentCreditsPath)) });
  const startupEntry = await sealStartupEntry({ app, source: resolve(project, 'Source/BreziTwin/BreziStartupEntry.cpp'),
    output: resolve(output, 'startup-seal'), additionalResources });
  const bundle = await verifyPackage(app, engine);
  for (const name of ['Source', 'Config', 'Content', 'Binaries'])
    need(JSON.stringify(await inventory(resolve(clone.sourceProject, name))) === JSON.stringify(clone.sourceHashes[name]),
      'Accepted source project changed during packaging: ' + name);
  need(sha(await readFile(resolve(clone.sourceProject, 'BreziTwin.uproject'))) === clone.descriptorSha256,
    'Accepted descriptor changed during packaging');
  const cookedSource = await inventory(resolve(project, 'Content'));
  need(JSON.stringify(cookedSource) === JSON.stringify(clone.sourceHashes.Content), 'Cloned authored content changed during cooking');
  need(JSON.stringify(await inventory(resolve(project, 'Config'))) === JSON.stringify(clone.sourceHashes.Config),
    'Cloned scene configuration changed during build/cooking');
  const finalSources = await inventory(resolve(project, 'Source'));
  const sourceDifferences = [...new Set([...Object.keys(clone.sourceHashes.Source), ...Object.keys(finalSources)])]
    .filter(path => clone.sourceHashes.Source[path] !== finalSources[path]);
  const qualitySource = JSON.parse(await readFile(resolve(output, 'dom-entry-source.json')));
  const allowedSources = new Set(['BreziTwin/BreziStartupEntry.cpp', ...renderSourceFiles.map(name => 'BreziTwin/' + name)]);
  need(sourceDifferences.every(path => allowedSources.has(path)), 'Unrelated isolated source changed');
  need(finalSources['BreziTwin/BreziStartupEntry.cpp'] === sha(await readFile(resolve(root, 'scripts/unreal/dom-startup-entry.cpp'))),
    'Compiled Dom entry source differs from reproducible source');
  for (const [path, hash] of Object.entries(qualitySource.renderSourceHashes))
    need(finalSources[path] === hash && hash === sha(await readFile(resolve(root, 'unreal/BreziTwin/Source', path))),
      'Compiled render quality source differs: ' + path);
  await save(resolve(output, 'dom-package.json'), { schemaVersion: 1,
    status: 'dom-final-exterior-standalone-package-validated', createdAt: new Date().toISOString(),
    appPath: app, project, engine, sourceProject: clone.sourceProject, selection: clone.selection,
    sourceCloneReceiptSha256: sha(await readFile(resolve(output, 'source-clone.json'))),
    activeDesign: 'C/B/B', streetAndRightSetbackMm: 3000, gameConfiguration: 'Shipping',
    appName: 'Dom', iconSha256: sha(icon), launchArgs, bundle, startupEntry,
    launcherSourceChange: JSON.parse(await readFile(resolve(output, 'dom-entry-source.json'))),
    nativeGameBuildReceiptSha256: sha(await readFile(resolve(output, 'model-game-build.json'))),
    nativeStartupFixtureReceiptSha256: sha(await readFile(resolve(output, 'startup-default-fixture/receipt.json'))),
    nativeArchiveProcessReceiptSha256: sha(await readFile(resolve(output, 'package.log.json'))),
    sourceDifferences, renderSourceHashes: qualitySource.renderSourceHashes,
    clonedSceneConfigurationPreserved: true, redundantNestedBundle,
    nativeIconCatalog: { source: catalogSource, sourceHashes: catalogHashes, resources: catalogResources },
    approvedSourceProjectPreserved: true, authoredContentPreserved: true,
    runtimeVisualVerified: false, installed: false });
  console.log(JSON.stringify({ status: 'dom-package-ready-for-native-visual-check', app, output }, null, 2));
}

async function refinish() {
  // Preserve a previously completed package and its seals before a new branding
  // pass. Start again from the untouched successful UAT-native build product.
  const snapshot = resolve(output, 'package-history', 'before-final-catalog-' + new Date().toISOString().replace(/[:.]/g, '-'));
  await mkdir(snapshot, { recursive: true });
  await cp(resolve(output, 'dom-package.json'), resolve(snapshot, 'dom-package.json'));
  await cp(resolve(output, 'startup-seal'), resolve(snapshot, 'startup-seal'), { recursive: true, mode: constants.COPYFILE_FICLONE });
  const app = resolve(output, 'package/Mac/BreziTwin.app');
  await rename(app, resolve(snapshot, 'BreziTwin.app'));
  await cp(resolve(project, 'Binaries/Mac/BreziTwin.app'), app, { recursive: true, mode: constants.COPYFILE_FICLONE });
  // The preserved redundant nested bundle path must be unique for each pass.
  try { await access(resolve(output, 'package-history/redundant-nested-build-product'));
    await rename(resolve(output, 'package-history/redundant-nested-build-product'), resolve(snapshot, 'redundant-nested-build-product'));
  } catch (error) { if (error.code !== 'ENOENT') throw error; }
  await finish();
}

const action = process.argv[2] ?? 'all';
if (action === 'prepare' || action === 'all') await prepare();
if (action === 'build' || action === 'all') await buildDomEntry();
if (action === 'package' || action === 'all') await packageApp();
if (action === 'finish' || action === 'all') await finish();
if (action === 'refinish') await refinish();
need(['prepare', 'build', 'package', 'finish', 'refinish', 'all'].includes(action), 'Use prepare | build | package | finish | refinish | all');
