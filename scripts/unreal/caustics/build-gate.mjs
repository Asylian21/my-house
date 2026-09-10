import { readFile, realpath } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const overlay = resolve(dirname(fileURLToPath(import.meta.url)), '../engine-overlays/ue-5.8.2-floor-caustics');

export function configuredCausticsMode(ini) {
  let section = '', mode = '';
  for (const raw of ini.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith(';') || line.startsWith('#')) continue;
    const header = /^\[([^\]]+)\]$/.exec(line);
    if (header) { section = header[1].toLowerCase(); continue; }
    const pair = /^([^=]+)=(.*)$/.exec(line);
    if (section === 'brezifloorcaustics' && pair?.[1].trim().toLowerCase() === 'mode') {
      mode = pair[2].trim();
      if (mode.startsWith('"') && mode.endsWith('"')) mode = mode.slice(1, -1);
    }
  }
  if (mode && mode !== 'transport-continuous') throw Error(`Unsupported configured BreziFloorCaustics mode: ${mode}`);
  return mode;
}

export function requirePhasedContinuousBuild(action, mode, pluginEnabled, engineVerified) {
  if (!['editor-build', 'package'].includes(action) || !mode) return;
  if (!pluginEnabled) throw Error('Continuous caustics is configured but BreziCausticsProbe is not enabled in the project.');
  if (!engineVerified) throw Error('Continuous caustics requires the reviewed isolated UE 5.8.2 engine; stock or changed engine source is unsupported. See scripts/unreal/caustics/README.md.');
  throw Error(`Continuous ${action} requires the phased runner in scripts/unreal/caustics/phase_runner.py. The legacy command does not join reviewed build/cook/container receipts and cooked-runtime-binding before sealing. See scripts/unreal/caustics/README.md; no native command was started.`);
}

export async function verifyPromotedEngine(engine) {
  const E = resolve(engine);
  if (await realpath(E) !== E) throw Error('Engine root must be canonical.');
  if ((await readFile(resolve(E, '.brezi-isolated-engine'), 'utf8')).replace(/[\r\n]+$/, '') !== E) throw Error('Isolated engine marker differs.');
  const manifest = JSON.parse(await readFile(resolve(overlay, 'manifest.json'), 'utf8'));
  if (sha(await readFile(resolve(overlay, 'engine.patch'))) !== manifest.patchSha256) throw Error('Tracked engine patch changed.');
  const files = [{path:'Engine/Build/Build.version',resultSha256:manifest.engineBuildVersionSha256}, ...manifest.files];
  for (const file of files) {
    const path = resolve(E, file.path);
    if (!path.startsWith(E + '/') || await realpath(path) !== path || sha(await readFile(path)) !== file.resultSha256) {
      throw Error(`Reviewed engine source differs: ${file.path}`);
    }
  }
  return true; // Source preflight only; binary/shader acceptance stays in the phased workflow.
}

export async function guardLegacyContinuousBuild({ action, projectFile, engine }) {
  if (!['editor-build', 'package'].includes(action)) return;
  const ini = await readFile(resolve(dirname(projectFile), 'Config/DefaultGame.ini'), 'utf8');
  const mode = configuredCausticsMode(ini);
  if (!mode) return;
  const project = JSON.parse(await readFile(projectFile, 'utf8'));
  const enabled = project.Plugins?.some(p => p.Name === 'BreziCausticsProbe' && p.Enabled === true) ?? false;
  if (!enabled) requirePhasedContinuousBuild(action, mode, false, false);
  try { await verifyPromotedEngine(engine); }
  catch (error) { throw Error(`Continuous caustics engine preflight failed: ${error.message}. Use the isolated engine and phased commands in scripts/unreal/caustics/README.md; no native command was started.`); }
  requirePhasedContinuousBuild(action, mode, enabled, true);
}
