// Explicit, isolated Editor/Metal transport capture; never a packaged-app or FPS receipt.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawn, execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url));
const plugin = path.join(root, 'unreal/BreziTwin/Plugins/BreziCausticsProbe');
const engine = '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor';
const phase = Number(process.argv[2]);
if (process.argv.length !== 3 || ![0, 0.125].includes(phase)) throw new Error('Usage: node scripts/unreal/caustics-qa.mjs <0|0.125>');
const inventory = execFileSync('ps', ['-axo', 'pid=,comm='], { encoding: 'utf8' });
if (inventory.split('\n').some(line => /\/(BreziTwin|UnrealEditor(?:-Cmd)?|ShaderCompileWorker)$/.test(line.trim()))) throw new Error('Another native renderer/compiler is active');
execFileSync('python3', [path.join(plugin, 'Tools/water_binding.py'), '--source-root', root, '--check'], { encoding: 'utf8' });
const run = path.join(root, 'output/unreal/caustics-wave-runtime', `time-${phase}-${crypto.randomUUID()}`);
await fs.mkdir(run, { recursive: true });
const sha = async file => crypto.createHash('sha256').update(await fs.readFile(file)).digest('hex');
async function filesBelow(directory) {
  const rows = [];
  for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
    const file = path.join(directory, entry.name);
    if (entry.isDirectory() && !['Intermediate', '__pycache__', 'Saved'].includes(entry.name)) rows.push(...await filesBelow(file));
    else if (entry.isFile()) rows.push(file);
  }
  return rows;
}
const pluginFiles = (await Promise.all(['Resources', 'Source', 'Shaders', 'Binaries'].map(dir => filesBelow(path.join(plugin, dir))))).flat();
const files = [...pluginFiles, path.join(plugin, 'BreziCausticsProbe.uplugin'), path.join(plugin, 'Tools/water_binding.py'),
  ...await filesBelow(path.join(root, 'unreal/BreziTwin/Source')),
  ...await filesBelow(path.join(root, 'unreal/BreziTwin/Config')), ...await filesBelow(path.join(root, 'unreal/BreziTwin/Content/Data')),
  path.join(root, 'scripts/unreal/optics.py'), fileURLToPath(import.meta.url),
  path.join(root, 'unreal/BreziTwin/Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),
  path.join(root, 'unreal/BreziTwin/Content/Brezi/OpticsGenerated/M_PoolWater.uasset'),
  path.join(root, 'output/unreal/package-report.json'), engine];
files.push(...(await filesBelow(path.join(root, 'unreal/BreziTwin/Content'))).filter(file => file.endsWith('.umap')));
const pins = async () => Object.fromEntries(await Promise.all([...new Set(files)].sort().map(async file => [path.relative(root, file), await sha(file)])));
const before = await pins();
const args = [path.join(root, 'unreal/BreziTwin/BreziTwin.uproject'), '-game', '-EnablePlugins=BreziCausticsProbe',
  '-BreziCausticsProbe', '-BreziCausticsCapture', '-BreziView=pool', '-windowed', '-ResX=3840', '-ResY=2160',
  '-BreziBenchmarkFrames=120', '-BreziWarmupFrames=240', '-BreziExitAfterCapture', '-unattended', '-nosplash',
  `-ExecCmds=r.Test.OverrideTimeMaterialExpressions ${phase},r.ScreenPercentage 100,r.DynamicRes.OperationMode 0`,
  `-UserDir=${run}/`, `-abslog=${run}/engine.log`];
const receipt = { status: 'starting', scope: 'Editor-game isolated diagnostic transport', argv: [engine, ...args],
  requestedShaderTimeSeconds: phase, productionLightingBound: false, standaloneAppTest: false, fpsClaim: false,
  inputSha256: before, startedAt: new Date().toISOString() };
const save = () => fs.writeFile(path.join(run, 'process.json'), JSON.stringify(receipt, null, 2) + '\n');
await save();
console.log(JSON.stringify({ run, requestedShaderTimeSeconds: phase }));
const log = await fs.open(path.join(run, 'stdout.log'), 'w');
const child = spawn(engine, args, { cwd: root, stdio: ['ignore', log.fd, log.fd] });
receipt.pid = child.pid; receipt.status = 'running'; await save();
console.log(JSON.stringify({ pid: child.pid }));
const deadline = setTimeout(() => { receipt.deadlineExceeded = true; child.kill('SIGTERM'); }, 600_000);
const exit = await new Promise((resolve, reject) => { child.once('error', reject); child.once('close', (code, signal) => resolve({ code, signal })); });
clearTimeout(deadline); await log.close();
receipt.exit = exit; receipt.endedAt = new Date().toISOString();
receipt.inputSha256After = await pins();
const errors = [];
if (exit.code !== 0) errors.push(`Native exit ${exit.code}/${exit.signal}`);
if (JSON.stringify(before) !== JSON.stringify(receipt.inputSha256After)) errors.push('Recorded input changed during run');
const nativeLog = await fs.readFile(path.join(run, 'engine.log'), 'utf8');
const badLines = nativeLog.split('\n').filter(line => /Fatal error:|Assertion failed:|Ensure condition failed:|Shader compilation failures|Failed to compile.*shader/i.test(line));
if (badLines.length) errors.push(...badLines);
const saved = path.join(run, 'Saved/CausticsProbe');
const captures = (await fs.readdir(saved).catch(() => [])).map(name => path.join(saved, name));
if (captures.length !== 1) errors.push(`Expected one capture, received ${captures.length}`);
if (captures.length === 1) {
  receipt.captureDirectory = captures[0];
  const meta = JSON.parse(await fs.readFile(path.join(captures[0], 'capture.json'), 'utf8'));
  receipt.capture = meta;
  if (meta.shaderTimeSeconds !== phase || meta.waveCount !== 12 || !meta.waterBindingSha256) errors.push('Native wave/time binding differs');
  if (!(meta.viewFamilyFrameNumber >= 60) || JSON.stringify(meta.unscaledViewPixels) !== '[3840,2160]') errors.push('Capture predates settled view or unscaled view is not 4K');
  receipt.captureFileSha256 = Object.fromEntries(await Promise.all((await filesBelow(captures[0])).map(async file => [path.basename(file), await sha(file)])));
}
receipt.errors = errors; receipt.status = errors.length ? 'native-capture-rejected' : 'clean-native-capture-awaiting-independent-transport-validation';
receipt.nativeLogSha256 = await sha(path.join(run, 'engine.log'));
await save();
console.log(JSON.stringify({ run, status: receipt.status, exit, errors, captureDirectory: receipt.captureDirectory }));
process.exitCode = errors.length ? 1 : 0;
