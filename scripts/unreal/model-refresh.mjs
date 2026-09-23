// Separate current architectural model builds from immutable historical look-dev packages.
import { spawn, execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir, cp, access, readdir, rename } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { sealStartupEntry } from './startup-entry-package.mjs';
import { verifyPackage, verifyPackagedPayload } from './package-verify.mjs';
import { requireIdleApp } from './app-launch.mjs';
import { inspectCookLog } from './cook-log.mjs';
import { buildModelRefreshViewpoints } from './model-refresh-viewpoints.mjs';
import { verifyModelRefresh } from './model-refresh-contract.mjs';
import { buildArchvizRoomViewpoints } from './archviz-room-viewpoints.mjs';
import { buildWalkthroughContract } from './walkthrough-contract.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const output = resolve(root, process.env.BREZI_MODEL_OUTPUT ?? 'output/unreal/model-refresh-20260922');
const engine = resolve(process.env.UNREAL_ENGINE_ROOT ?? '/Users/Shared/Epic Games/UE_5.8');
const project = resolve(output, 'Project/BreziTwin');
const descriptor = resolve(project, 'BreziTwin.uproject');
const geometry = resolve(output, 'geometry');
const canonical = resolve(root, 'unreal/BreziTwin');
const [action, requestedView] = process.argv.slice(2);
const view = requestedView ?? 'interior';
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const execFileAsync = promisify(execFile);
const read = async path => JSON.parse(await readFile(path, 'utf8'));
const save = async (path, value) => writeFile(path, JSON.stringify(value, null, 2) + '\n');
async function hashes(directory) {
  const result = {};
  async function visit(path) {
    for (const entry of await readdir(path, { withFileTypes: true })) {
      const file = resolve(path, entry.name);
      if (entry.isSymbolicLink()) throw Error('Source input may not be a symlink: ' + file);
      if (entry.isDirectory()) await visit(file);
      else if (entry.isFile() && !file.includes('/FileOpenOrder/') && !file.endsWith('.PackageVersionCounter'))
        result[file] = sha(await readFile(file));
    }
  }
  await visit(directory);
  return result;
}
async function pinnedFiles(files) {
  for (const [file, hash] of Object.entries(files))
    if (sha(await readFile(file)) !== hash) throw Error('Model input changed: ' + file);
}
async function run(command, args, logName, env = {}) {
  const startedAt = new Date().toISOString();
  let log = '';
  const result = await new Promise((accept, reject) => {
    const child = spawn(command, args, { cwd: root, env: { ...process.env, ...env }, stdio: ['ignore', 'pipe', 'pipe'] });
    for (const stream of [child.stdout, child.stderr]) stream.on('data', chunk => { log += chunk; process.stdout.write(chunk); });
    child.once('error', reject);
    child.once('close', (code, signal) => accept({ code, signal }));
  });
  await writeFile(resolve(output, logName), log);
  await save(resolve(output, logName + '.json'), { command, args, startedAt, endedAt: new Date().toISOString(), ...result });
  if (result.code !== 0 || /\*\* BUILD FAILED \*\*|The following build commands failed:/i.test(log))
    throw Error('Native phase failed: ' + logName);
  return log;
}
async function authoringHashes() {
  return Object.assign({ [descriptor]: sha(await readFile(descriptor)) },
    ...await Promise.all(['Source', 'Config', 'Build', 'Content'].map(name => hashes(resolve(project, name)))));
}
async function checkProfile() {
  const data = await read(descriptor);
  const ini = await readFile(resolve(project, 'Config/DefaultGame.ini'), 'utf8');
  if (data.Plugins.some(plugin => plugin.Name === 'BreziCausticsProbe' && plugin.Enabled)
    || /Mode=transport-continuous/.test(ini)) throw Error('Current model review must use its separate source-material profile');
}
async function verifyGameBuild() {
  const game = await read(resolve(output, 'model-game-build.json'));
  const reused = game.status === 'model-game-build-reused-validated';
  if ((!reused && (game.status !== 'model-game-build-validated' || !game.allActionsExecuted))
    || (reused && (game.allActionsExecuted !== false || game.compilationActionsExecuted !== 0
      || game.reuse?.method !== 'byte-identical-verified-copy' || game.reuse?.sourceAuthoringIdentical !== true))
    || game.project !== project || game.engine !== engine
    || !game.buildProductHashes || game.appExecutable !== resolve(project, 'Binaries/Mac/BreziTwin.app/Contents/MacOS/BreziTwin')
    || game.buildProductHashes[game.appExecutable] !== game.appExecutableSha256)
    throw Error('Current project has no completed native Game build with finalized executable');
  await pinnedFiles(game.sourcePins);
  const inputs = { [game.rawExecutable]: game.rawExecutableSha256, [game.targetReceipt]: game.targetReceiptSha256,
    ...game.buildProductHashes };
  await pinnedFiles(inputs);
  return { game, inputs };
}
async function binaryUUID(path) {
  const { stdout } = await execFileAsync('/usr/bin/xcrun', ['dwarfdump', '--uuid', path]);
  const matches = [...stdout.matchAll(/UUID: ([A-F0-9-]+) \(([^)]+)\)/g)];
  if (matches.length !== 1 || matches[0][2] !== 'arm64') throw Error('Expected one native arm64 linked executable: ' + path);
  return matches[0][1];
}
async function verifyImport({ baselineOnly = false, excludeRural = false } = {}) {
  const imported = await read(resolve(output, 'model-refresh-import-report.json'));
  const host = await read(resolve(output, 'model-import-process.json'));
  await pinnedFiles({ [resolve(output, 'model-refresh-import-report.json')]: host.reportSha256,
    [host.processFile]: host.processFileSha256 });
  const process = await read(host.processFile);
  if (imported.status !== 'model-refresh-import-validated' || process.code !== 0
    || Date.parse(imported.generatedAt) < Date.parse(process.startedAt)
    || Date.parse(imported.generatedAt) > Date.parse(process.endedAt)) throw Error('Current model has no successful native import process');
  let final = imported;
  let photoreal = null;
  let rural = null;
  const profile = await read(resolve(output, 'profile.json'));
  const enhancementInputs = {};
  if (profile.archvizGame && !baselineOnly) {
    const file = resolve(output, 'archviz-import-report.json');
    const enhanced = await read(file);
    const host = await read(resolve(output, 'archviz-import-process.json'));
    const process = await read(host.processFile);
    if (enhanced.status !== 'archviz-import-validated' || process.code !== 0
      || Date.parse(enhanced.generatedAt) < Date.parse(process.startedAt)
      || Date.parse(enhanced.generatedAt) > Date.parse(process.endedAt)
      || enhanced.baselineReportSha256 !== sha(await readFile(resolve(output, 'model-refresh-import-report.json'))))
      throw Error('Current archviz profile has no successful native enhancement process');
    Object.assign(enhancementInputs, { [file]: host.reportSha256, [host.processFile]: host.processFileSha256 },
      ...Object.values({ inputs: enhanced.inputFiles, pipeline: enhanced.pipelineFiles, receipts: enhanced.receiptPins })
        .map(pins => Object.fromEntries(Object.entries(pins ?? {}).map(([path, hash]) => [resolve(root, path), hash]))));
    final = enhanced;
  }
  const archviz = final === imported ? null : final;
  if (!baselineOnly && await access(resolve(output, 'photoreal-import-report.json')).then(() => true, () => false)) {
    const file = resolve(output, 'photoreal-import-report.json');
    photoreal = await read(file);
    const host = await read(resolve(output, 'photoreal-import-process.json'));
    const native = await read(host.processFile);
    if (photoreal.status !== 'photoreal-import-validated' || native.code !== 0
      || photoreal.baselineReportSha256 !== sha(await readFile(resolve(output, 'archviz-import-report.json')))
      || Date.parse(photoreal.generatedAt) < Date.parse(native.startedAt)
      || Date.parse(photoreal.generatedAt) > Date.parse(native.endedAt))
      throw Error('Photoreal enhancement has no successful matching native process');
    Object.assign(enhancementInputs, { [file]: host.reportSha256, [host.processFile]: host.processFileSha256 },
      ...[photoreal.inputFiles, photoreal.pipelineFiles].map(pins => Object.fromEntries(
        Object.entries(pins).map(([path, hash]) => [resolve(root, path), hash]))));
    final = photoreal;
  }
  if (!baselineOnly && !excludeRural && await access(resolve(output, 'rural-import-report.json')).then(() => true, () => false)) {
    const file = resolve(output, 'rural-import-report.json');
    rural = await read(file);
    const host = await read(resolve(output, 'rural-import-process.json'));
    const native = await read(host.processFile);
    if (!photoreal || rural.status !== 'rural-import-validated' || native.code !== 0
      || !Number.isFinite(Date.parse(rural.generatedAt))
      || rural.baselineReportSha256 !== sha(await readFile(resolve(output, 'photoreal-import-report.json')))
      || Date.parse(rural.generatedAt) < Date.parse(native.startedAt)
      || Date.parse(rural.generatedAt) > Date.parse(native.endedAt))
      throw Error('Rural context has no successful matching native process');
    Object.assign(enhancementInputs, { [file]: host.reportSha256, [host.processFile]: host.processFileSha256 },
      ...[rural.inputFiles, rural.pipelineFiles].map(pins => Object.fromEntries(
        Object.entries(pins).map(([path, hash]) => [resolve(root, path), hash]))));
    final = rural;
  }
  const inputs = {
    ...enhancementInputs,
    [resolve(geometry, 'scene.json')]: imported.sourceManifestSha256,
    [resolve(geometry, 'brezi-twin.glb')]: imported.sourceGlbSha256,
    [resolve(geometry, 'viewpoints.json')]: imported.viewpointsSha256,
    [resolve(geometry, 'walking.json')]: imported.walkingSha256,
    [resolve(project, 'Content/Brezi/Maps/Brezi.umap')]: final.mapFileSha256,
    [resolve(project, 'Content/Data/walking.json')]: imported.walkingSha256,
    [resolve(project, 'Content/Data/hidden-collision.json')]: imported.hiddenCollision.sourceContractSha256,
    [resolve(geometry, 'hidden-collision.json')]: imported.hiddenCollision.sourceContractSha256,
    [resolve(geometry, 'brezi-collision-only.glb')]: imported.hiddenCollision.sourceGlbSha256,
    ...Object.fromEntries(Object.entries({ ...final.finalAssetHashes, ...imported.pipelineFiles }).map(([path, hash]) => [resolve(root, path), hash])),
  };
  if (imported.doors) {
    if (imported.doors.status !== 'source-doors-saved-reloaded-validated' || imported.doors.architecturalDoorCount !== 16)
      throw Error('Interactive source doors have not passed native saved/reload verification');
    inputs[resolve(geometry, 'doors.json')] = imported.doors.contractSha256;
    inputs[resolve(project, 'Content/Data/doors.json')] = imported.doors.contractSha256;
  }
  await pinnedFiles(inputs);
  const scene = await read(resolve(geometry, 'scene.json'));
  Object.assign(inputs, Object.fromEntries(Object.entries(scene.sourceFiles).map(([path, hash]) => [resolve(root, path), hash])),
    Object.fromEntries(imported.materials.textures.map(texture => [resolve(root, texture.source), texture.sha256])));
  await pinnedFiles(inputs);
  verifyModelRefresh(scene);
  const expectedViews = await modelViewpoints(scene);
  if (rural) {
    const rotation = rural.sun?.rotation;
    if (!Array.isArray(rotation) || rotation.length !== 3 || !rotation.every(Number.isFinite)
      || Math.abs(rotation[0] + 48) > .001 || Math.abs(rural.sun.sourceAngleDegrees - .75) > .00001)
      throw Error('Rural summer-lighting contract differs');
    expectedViews.sun.dayRotationDegrees = rotation;
    if (rural.stagedViewpointsSha256 !== sha(await readFile(resolve(project, 'Content/Data/viewpoints.json'))))
      throw Error('Rural runtime sun data changed');
  }
  if (JSON.stringify(await read(resolve(project, 'Content/Data/viewpoints.json'))) !== JSON.stringify(expectedViews))
    throw Error('Staged viewpoints differ from the current source-derived safe arrival');
  return { imported: { ...imported, ...(archviz ? { archviz } : {}), ...(photoreal ? { photoreal } : {}), ...(rural ? { rural } : {}) }, inputs };
}
async function bindImportProcess(logName) {
  const reportFile = resolve(output, 'model-refresh-import-report.json');
  if ((await read(reportFile)).status !== 'model-refresh-import-validated') throw Error('Native model import did not validate');
  const processFile = resolve(output, logName + '.json');
  await save(resolve(output, 'model-import-process.json'), {
    processFile, processFileSha256: sha(await readFile(processFile)), reportSha256: sha(await readFile(reportFile)),
  });
}
async function modelViewpoints(scene) {
  const views = buildModelRefreshViewpoints(scene, await read(resolve(geometry, 'viewpoints.json')));
  if ((await read(resolve(output, 'profile.json'))).archvizGame) {
    const bytes = await Promise.all(['scene', 'walking', 'hidden-collision'].map(name => readFile(resolve(geometry, name + '.json'))));
    const fixture = buildWalkthroughContract(scene, JSON.parse(bytes[1]), JSON.parse(bytes[2]), {
      sceneSha256: sha(bytes[0]), walkingSha256: sha(bytes[1]), hiddenCollisionSha256: sha(bytes[2]),
      helperSha256: sha(await readFile(resolve(root, 'scripts/unreal/walkthrough-contract.mjs'))),
    });
    views.views.push(...buildArchvizRoomViewpoints(scene, fixture));
  }
  return views;
}
async function prepareViewpoints() {
  const source = await read(resolve(geometry, 'scene.json'));
  verifyModelRefresh(source);
  const views = await modelViewpoints(source);
  await save(resolve(project, 'Content/Data/viewpoints.json'), views);
}

await mkdir(output, { recursive: true });
if (action === 'prepare') {
  try { await access(descriptor); throw Error('Use a fresh BREZI_MODEL_OUTPUT; prior projects are preserved'); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  await mkdir(project, { recursive: true });
  for (const name of ['Source', 'Config', 'Build']) await cp(resolve(canonical, name), resolve(project, name), {
    recursive: true, filter: path => !path.includes('/FileOpenOrder') && !path.endsWith('.PackageVersionCounter'),
  });
  const data = await read(resolve(canonical, 'BreziTwin.uproject'));
  data.Description = 'Current C/B/B architectural model review; source materials; historical pool caustics excluded.';
  data.Plugins = data.Plugins.filter(plugin => plugin.Name !== 'BreziCausticsProbe');
  await save(descriptor, data);
  for (const name of ['DefaultGame.ini', 'DefaultEngine.ini']) {
    const file = resolve(project, 'Config', name);
    const ini = (await readFile(file, 'utf8')).replace('[BreziFloorCaustics]\nMode=transport-continuous', '').replace('r.Brezi.FloorCaustics=1\n', '');
    await writeFile(file, ini);
  }
  const doubleGlass = process.env.BREZI_DOUBLE_GLASS === '1';
  if (doubleGlass) {
    const file = resolve(project, 'Config/DefaultEngine.ini');
    const ini = await readFile(file, 'utf8');
    if (!ini.includes('[/Script/Engine.RendererSettings]') || /^r\.AllowGlobalClipPlane=/m.test(ini))
      throw Error('Inspect global clip-plane configuration before preparing double glass');
    await writeFile(file, ini.replace('[/Script/Engine.RendererSettings]',
      '[/Script/Engine.RendererSettings]\nr.AllowGlobalClipPlane=True'));
  }
  // The interactive profile starts within the measured 1080p GPU budget.
  // Existing deliberate user settings still take precedence when opening the app directly.
  const settings = resolve(project, 'Config/DefaultGameUserSettings.ini');
  await writeFile(settings, (await readFile(settings, 'utf8'))
    .replace(/^(ResolutionSizeX|LastUserConfirmedResolutionSizeX)=\d+$/gm, '$1=1920')
    .replace(/^(ResolutionSizeY|LastUserConfirmedResolutionSizeY)=\d+$/gm, '$1=1080')
    + '\n[Brezi.RenderQuality]\nProfileV1=performance\n');
  await mkdir(resolve(project, 'Content/Data'), { recursive: true });
  await save(resolve(output, 'profile.json'), {
    status: 'current-model-project-prepared', project, engine, geometry,
    scope: 'Current C/B/B geometry, source materials and navigation. Historical caustics and look-dev packages remain separate.',
    archvizGame: process.env.BREZI_ARCHVIZ_GAME === '1',
    doubleGlass,
    nativeBuildVerified: false,
  });
  if (process.env.BREZI_ARCHVIZ_GAME === '1') {
    const file = resolve(project, 'Config/DefaultGame.ini');
    await writeFile(file, (await readFile(file, 'utf8')).replace('+MapsToCook=', '+DirectoriesToAlwaysCook=(Path="/Game/Brezi/Avatar")\n+MapsToCook='));
  }
} else if (action === 'export') {
  await run(process.execPath, ['scripts/unreal/export.mjs'], 'export.log', { UNREAL_OUTPUT: geometry });
} else if (action === 'editor-build') {
  await checkProfile();
  await run(resolve(engine, 'Engine/Build/BatchFiles/Mac/Build.sh'), ['BreziTwinEditor', 'Mac', 'Development', descriptor, '-WaitMutex'], 'editor-build.log');
} else if (action === 'reuse-build') {
  // A model/material revision needs a new map and cook, but unchanged native
  // sources may reuse verified relocatable build products. Preserve the donor.
  const origin = resolve(root, requestedView ?? '');
  const originProject = resolve(origin, 'Project/BreziTwin');
  if (!requestedView || origin === output || !origin.startsWith(resolve(root, 'output/unreal') + '/'))
    throw Error('Specify a different existing output/unreal profile as the build donor');
  await checkProfile();
  const gamePath = resolve(origin, 'model-game-build.json'), packagePath = resolve(origin, 'model-package.json');
  const original = await read(gamePath), packaged = await read(packagePath);
  if (original.status !== 'model-game-build-validated' || !original.allActionsExecuted
    || original.phases.some(phase => phase.exitCode !== 0) || original.project !== originProject
    || packaged.status !== 'current-model-packaged' || packaged.project !== originProject
    || original.engine !== engine || packaged.engine !== engine
    || packaged.inputs[gamePath] !== sha(await readFile(gamePath)))
    throw Error('Build donor must have its original complete native build and a matching successful package');
  await verifyPackagedPayload(packaged.appPath, packaged.bundle);
  // UAT regenerates Intermediate response/Xcode files during its successful
  // packaging phase. Their original hashes remain sealed by the accepted
  // build report; current reuse checks the immutable authored inputs instead.
  const donorPins = Object.fromEntries(Object.entries(original.sourcePins)
    .filter(([path]) => !path.startsWith(resolve(originProject, 'Intermediate') + '/')));
  await pinnedFiles(donorPins);
  const authoring = async dir => Object.assign({ [resolve(dir, 'BreziTwin.uproject')]: sha(await readFile(resolve(dir, 'BreziTwin.uproject'))) },
    ...await Promise.all(['Source', 'Config', 'Build'].map(name => hashes(resolve(dir, name)))));
  const sourceAuthoring = await authoring(originProject), destinationAuthoring = await authoring(project);
  const moved = path => path.replace(originProject + '/', project + '/');
  if (JSON.stringify(Object.fromEntries(Object.entries(sourceAuthoring).map(([path, hash]) => [moved(path), hash])))
    !== JSON.stringify(destinationAuthoring)) throw Error('Native source/config/build inputs differ; compile this project normally');
  const sourceProducts = { ...original.buildProductHashes, ...packaged.finalizedBuildProducts,
    [original.targetReceipt]: original.targetReceiptSha256 };
  await pinnedFiles(sourceProducts);
  if (await binaryUUID(original.rawExecutable) !== packaged.linkedUUID
    || await binaryUUID(original.appExecutable) !== packaged.linkedUUID)
    throw Error('Donor finalized executable differs from its verified native link');
  for (const target of ['BreziTwin.target', 'BreziTwinEditor.target']) {
    const file = resolve(originProject, 'Binaries/Mac', target), bytes = await readFile(file, 'utf8');
    if (bytes.includes(originProject)) throw Error('Native receipt contains a non-relocatable donor project path');
  }
  const destinationBinaries = resolve(project, 'Binaries');
  try { await access(destinationBinaries); throw Error('Build reuse requires empty destination Binaries'); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  const nativeFiles = await hashes(resolve(originProject, 'Binaries'));
  await cp(resolve(originProject, 'Binaries'), destinationBinaries, { recursive: true });
  await pinnedFiles(Object.fromEntries(Object.entries(nativeFiles).map(([path, hash]) => [moved(path), hash])));
  const products = Object.fromEntries(Object.entries(sourceProducts).filter(([path]) => path !== original.targetReceipt)
    .map(([path, hash]) => [moved(path), hash]));
  const nativeSourcePins = { ...donorPins, ...sourceProducts, ...destinationAuthoring,
    [gamePath]: sha(await readFile(gamePath)), [packagePath]: sha(await readFile(packagePath)) };
  const appExecutable = moved(original.appExecutable);
  await save(resolve(output, 'model-game-build.json'), {
    schemaVersion: 1, status: 'model-game-build-reused-validated', generatedAt: new Date().toISOString(), project, engine,
    sourcePins: nativeSourcePins, rawExecutable: moved(original.rawExecutable), rawExecutableSha256: original.rawExecutableSha256,
    targetReceipt: moved(original.targetReceipt), targetReceiptSha256: original.targetReceiptSha256,
    buildProductHashes: products, appExecutable, appExecutableSha256: products[appExecutable],
    allActionsExecuted: false, compilationActionsExecuted: 0, nativeRuntimeVerified: false,
    reuse: { method: 'byte-identical-verified-copy', sourceAuthoringIdentical: true, origin,
      originalGameReportSha256: sha(await readFile(gamePath)), originalPackageReportSha256: sha(await readFile(packagePath)),
      originalExecutedActions: original.phases.length, copiedNativeFiles: Object.keys(nativeFiles).length,
      originalGeneratedIntermediateInputsSealedInBuildReport: Object.keys(original.sourcePins).length - Object.keys(donorPins).length,
      linkedUUID: packaged.linkedUUID, editorAndGameCopied: true },
    scope: 'Verified identical native source/config/build inputs and copied Editor/Game binaries. No new compile/link actions. New model import, cook and visual validation remain required.',
  });
  await verifyGameBuild();
  console.log('Verified native Editor/Game build reuse; no compilation actions executed.');
} else if (action === 'game-build') {
  await checkProfile();
  let reusable = false;
  try { await verifyGameBuild(); reusable = true; } catch { /* Changed or absent inputs require a real build. */ }
  if (reusable) {
    console.log('Current native Game build and finalized build products are unchanged.');
    process.exit(0);
  }
  // Match Apple's run-only project generation before executing the exported
  // graph. A fresh isolated project has no Xcode workspace until this step.
  await run(resolve(engine, 'Engine/Build/BatchFiles/Mac/GenerateProjectFiles.sh'), [
    '-project=' + descriptor, '-game', '-platforms=Mac', '-DeployOnly', '-NoIntellisense', '-NoDotNet',
    '-IgnoreJunk', '-development', '-IncludeTempTargets', '-projectfileformat=XCode', '-automated', '-singletarget=BreziTwin',
  ], 'game-project-files.log');
  await run(resolve(engine, 'Engine/Build/BatchFiles/Mac/Build.sh'), ['BreziTwin', 'Mac', 'Development', descriptor,
    '-WaitMutex', '-NoUBA', '-WriteOutdatedActions=' + resolve(output, 'game-actions.json')], 'game-graph.log');
  await run('python3', ['-B', 'scripts/unreal/model-refresh-build.py', '--output', output, '--engine', engine], 'game-build.log');
} else if (action === 'import') {
  await requireIdleApp();
  await checkProfile();
  await run(process.execPath, ['scripts/unreal/validate.mjs'], 'geometry-check.log', { UNREAL_OUTPUT: geometry });
  for (const name of ['viewpoints', 'walking', 'hidden-collision', 'exterior-lighting', 'interior-lighting', 'doors'])
    await cp(resolve(geometry, name + '.json'), resolve(project, 'Content/Data', name + '.json'));
  await prepareViewpoints();
  await run(resolve(engine, 'Engine/Binaries/Mac/UnrealEditor-Cmd'), [descriptor, '-run=pythonscript',
    '-script=' + resolve(root, 'scripts/unreal/model-refresh-import.py'), '-unattended', '-nosplash', '-nullrhi'],
  'import.log', { BREZI_GEOMETRY: geometry });
  await bindImportProcess('import.log');
} else if (action === 'archviz' || action === 'normal-refresh') {
  await requireIdleApp();
  await checkProfile();
  if (!(await read(resolve(output, 'profile.json'))).archvizGame) throw Error('Archviz enhancement requires an explicitly prepared archvizGame profile');
  const refreshNormals = action === 'normal-refresh';
  const nativeScript = refreshNormals ? 'archviz-normal-refresh.py' : 'archviz-import.py';
  const nativeLog = refreshNormals ? 'normal-refresh.log' : 'archviz-import.log';
  await run(resolve(engine, 'Engine/Binaries/Mac/UnrealEditor-Cmd'), [descriptor, '-run=pythonscript',
    '-script=' + resolve(root, 'scripts/unreal/' + nativeScript), '-unattended', '-nosplash', '-nullrhi'],
  nativeLog, { BREZI_GEOMETRY: geometry, BREZI_ARCHVIZ_OUTPUT: output });
  const reportFile = resolve(output, 'archviz-import-report.json');
  if ((await read(reportFile)).status !== 'archviz-import-validated') throw Error('Native archviz enhancement did not validate');
  const processFile = resolve(output, nativeLog + '.json');
  await save(resolve(output, 'archviz-import-process.json'), {
    processFile, processFileSha256: sha(await readFile(processFile)), reportSha256: sha(await readFile(reportFile)),
  });
} else if (action === 'photoreal') {
  await requireIdleApp();
  await checkProfile();
  const profile = await read(resolve(output, 'profile.json'));
  await run(resolve(engine, 'Engine/Binaries/Mac/UnrealEditor-Cmd'), [descriptor, '-run=pythonscript',
    '-script=' + resolve(root, 'scripts/unreal/photoreal-import.py'), '-unattended', '-nosplash', '-nullrhi'],
  'photoreal-import.log', { BREZI_GEOMETRY: geometry, BREZI_PHOTOREAL_OUTPUT: output,
    BREZI_PHOTOREAL_DOUBLE_GLASS: profile.doubleGlass ? '1' : '0' });
  const reportFile = resolve(output, 'photoreal-import-report.json');
  const processFile = resolve(output, 'photoreal-import.log.json');
  const report = await read(reportFile), native = await read(processFile);
  const generated = Date.parse(report.generatedAt), started = Date.parse(report.startedAt);
  if (report.status !== 'photoreal-import-validated' || !Number.isFinite(generated) || !Number.isFinite(started)
    || started < Date.parse(native.startedAt) || generated < started || generated > Date.parse(native.endedAt)
    || report.baselineReportSha256 !== sha(await readFile(resolve(output, 'archviz-import-report.json'))))
    throw Error('Photoreal native enhancement failed or returned a stale report');
  await save(resolve(output, 'photoreal-import-process.json'), {
    processFile, processFileSha256: sha(await readFile(processFile)), reportSha256: sha(await readFile(reportFile)),
  });
} else if (action === 'rural') {
  await requireIdleApp();
  await checkProfile();
  await verifyImport({ excludeRural: true });
  await run(resolve(engine, 'Engine/Binaries/Mac/UnrealEditor-Cmd'), [descriptor, '-run=pythonscript',
    '-script=' + resolve(root, 'scripts/unreal/rural-import.py'), '-unattended', '-nosplash', '-nullrhi'],
  'rural-import.log', { BREZI_GEOMETRY: geometry, BREZI_RURAL_OUTPUT: output });
  const reportFile = resolve(output, 'rural-import-report.json');
  const processFile = resolve(output, 'rural-import.log.json');
  const report = await read(reportFile), native = await read(processFile);
  if (report.status !== 'rural-import-validated'
    || !Number.isFinite(Date.parse(report.startedAt)) || !Number.isFinite(Date.parse(report.generatedAt))
    || report.baselineReportSha256 !== sha(await readFile(resolve(output, 'photoreal-import-report.json')))
    || Date.parse(report.startedAt) < Date.parse(native.startedAt)
    || Date.parse(report.generatedAt) < Date.parse(report.startedAt)
    || Date.parse(report.generatedAt) > Date.parse(native.endedAt))
    throw Error('Rural native enhancement failed or returned a stale report');
  await save(resolve(output, 'rural-import-process.json'), {
    processFile, processFileSha256: sha(await readFile(processFile)), reportSha256: sha(await readFile(reportFile)),
  });
} else if (action === 'materials') {
  await requireIdleApp();
  await checkProfile();
  await run(resolve(engine, 'Engine/Binaries/Mac/UnrealEditor-Cmd'), [descriptor, '-run=pythonscript',
    '-script=' + resolve(root, 'scripts/unreal/model-refresh-import.py'), '-unattended', '-nosplash', '-nullrhi'],
  'materials.log', { BREZI_GEOMETRY: geometry, BREZI_MODEL_MATERIALS_ONLY: '1' });
  await bindImportProcess('materials.log');
} else if (action === 'viewpoints') {
  await requireIdleApp();
  await prepareViewpoints();
} else if (action === 'package') {
  await requireIdleApp();
  await checkProfile();
  const { imported, inputs: importInputs } = await verifyImport();
  const { game, inputs: gameInputs } = await verifyGameBuild();
  // UAT overlays an existing archive and can retain its previously sealed
  // policy resource. Preserve prior artifacts and always seal a fresh archive.
  let retainedArchive = null;
  try {
    await access(resolve(output, 'package'));
    retainedArchive = resolve(output, 'package-history', new Date().toISOString().replace(/[:.]/g, '-'));
    await mkdir(dirname(retainedArchive), { recursive: true });
    await rename(resolve(output, 'package'), retainedArchive);
  } catch (error) { if (error.code !== 'ENOENT') throw error; }
  const linkedUUID = await binaryUUID(game.appExecutable);
  if (linkedUUID !== await binaryUUID(game.rawExecutable)) throw Error('Finalized application differs from the native link');
  // UAT's Xcode Package phase re-finalizes and signs these build outputs in place.
  // Everything else, including the raw linked binary, remains an immutable input.
  const signingOutputs = [game.appExecutable,
    resolve(project, 'Binaries/Mac/BreziTwin.app/Contents/Info.plist'),
    resolve(project, 'Binaries/Mac/BreziTwin.app/Contents/_CodeSignature/CodeResources')];
  const buildProductsBeforePackaging = { ...game.buildProductHashes };
  for (const path of signingOutputs) delete gameInputs[path];
  const authoring = await authoringHashes();
  const helpers = ['scripts/unreal/model-refresh.mjs', 'scripts/unreal/model-refresh-viewpoints.mjs', 'scripts/unreal/model-refresh-contract.mjs',
    'scripts/unreal/package-verify.mjs', 'scripts/unreal/startup-entry-package.mjs',
    'scripts/unreal/archviz-room-viewpoints.mjs', 'scripts/unreal/walkthrough-contract.mjs'];
  const receiptFiles = ['model-refresh-import-report.json', 'model-import-process.json', 'model-game-build.json', 'profile.json',
    ...(imported.archviz ? ['archviz-import-report.json', 'archviz-import-process.json'] : []),
    ...(imported.photoreal ? ['photoreal-import-report.json', 'photoreal-import-process.json'] : []),
    ...(imported.rural ? ['rural-import-report.json', 'rural-import-process.json'] : [])];
  const inputs = { ...authoring, ...importInputs, ...gameInputs,
    ...Object.fromEntries(await Promise.all([...helpers.map(path => resolve(root, path)), ...receiptFiles.map(path => resolve(output, path))]
      .map(async path => [path, sha(await readFile(path))]))),
  };
  await save(resolve(output, 'package-inputs.json'), inputs);
  // UE's Zen oplog reader blocks parallel workers on HTTP responses. Let socket
  // continuations complete on their event threads so staging cannot starve them.
  const stagingEnvironment = { DOTNET_SYSTEM_NET_SOCKETS_INLINE_COMPLETIONS: '1' };
  const log = await run(resolve(engine, 'Engine/Build/BatchFiles/RunUAT.sh'), ['BuildCookRun', '-project=' + descriptor,
    '-noP4', '-platform=Mac', '-clientconfig=Development', '-skipbuild', '-cook', '-stage', '-pak', '-package', '-archive',
    '-archivedirectory=' + resolve(output, 'package'), '-unattended', '-utf8output',
    '-xcodebuildoptions=-derivedDataPath "' + resolve(output, 'xcode-data') + '"'], 'package.log', stagingEnvironment);
  const cook = inspectCookLog(log);
  if (cook.status !== 'cook-log-validated') throw Error('Cook validation failed: ' + JSON.stringify(cook));
  await pinnedFiles(inputs);
  if (JSON.stringify(Object.entries(await authoringHashes()).sort()) !== JSON.stringify(Object.entries(authoring).sort()))
    throw Error('Project authoring inventory changed during build/cook');
  const app = resolve(output, 'package/Mac/BreziTwin.app');
  if (await binaryUUID(resolve(app, 'Contents/MacOS/BreziTwin')) !== linkedUUID
    || await binaryUUID(game.appExecutable) !== linkedUUID) throw Error('Packaged executable differs from the native linked build');
  const finalizedBuildProducts = Object.fromEntries(await Promise.all(signingOutputs.map(async path => [path, sha(await readFile(path))])));
  const startupEntry = await sealStartupEntry({ app, source: resolve(project, 'Source/BreziTwin/BreziStartupEntry.cpp'), output: resolve(output, 'startup-seal') });
  const bundle = await verifyPackage(app, engine);
  await save(resolve(output, 'model-package.json'), {
    status: 'current-model-packaged', generatedAt: new Date().toISOString(), appPath: app, engine, project,
    activeDesign: (await read(resolve(geometry, 'scene.json'))).activeDesign,
    viewpoints: (await read(resolve(project, 'Content/Data/viewpoints.json'))).views.map(item => item.id),
    sourceManifestSha256: imported.sourceManifestSha256, sourceGlbSha256: imported.sourceGlbSha256,
    importReportSha256: sha(await readFile(resolve(output, 'model-refresh-import-report.json'))),
    gameplay: imported.doors ? { mode: imported.archviz ? 'third-person-walk-first' : 'walk-first', doors: imported.doors } : null,
    archviz: imported.archviz ? { importReportSha256: sha(await readFile(resolve(output, 'archviz-import-report.json'))),
      lightingStatus: imported.archviz.archvizLighting.status, materialStatus: imported.archviz.archvizMaterials.status,
      avatar: imported.archviz.avatar.assets, avatarReadback: imported.archviz.avatarReadback } : null,
    photoreal: imported.photoreal ? { importReportSha256: sha(await readFile(resolve(output, 'photoreal-import-report.json'))),
      status: imported.photoreal.status, nativeRenderedVerified: false } : null,
    rural: imported.rural ? { importReportSha256: sha(await readFile(resolve(output, 'rural-import-report.json'))),
      status: imported.rural.status, nativeRenderedVerified: false } : null,
    inputs, buildProductsBeforePackaging, finalizedBuildProducts, linkedUUID,
    bundle, startupEntry, cook, retainedArchive, stagingEnvironment, runtimeVisualVerified: false,
    scope: 'Updated architectural model and source materials. Historical custom pool caustics are not part of this package.',
  });
} else if (action === 'open') {
  await requireIdleApp();
  const report = await read(resolve(output, 'model-package.json'));
  if (report.status !== 'current-model-packaged') throw Error('No validated current model package');
  await verifyPackagedPayload(report.appPath, report.bundle);
  if (!report.viewpoints.includes(view)) throw Error('Unknown model viewpoint: ' + view);
  await run('/usr/bin/open', ['-n', report.appPath, '--args', '-windowed', '-ResX=1920', '-ResY=1080', '-BreziOutput=retina',
    ...(requestedView || !report.gameplay ? ['-BreziView=' + view] : ['-BreziGameplay']), '-BreziRenderProfile=performance'], 'open.log');
} else throw Error('Use prepare | export | editor-build | reuse-build <donor-output> | game-build | import | archviz | photoreal | rural | normal-refresh | materials | viewpoints | package | open [view]');
