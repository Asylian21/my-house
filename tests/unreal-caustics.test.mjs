import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { configuredCausticsMode, requirePhasedContinuousBuild } from '../scripts/unreal/caustics/build-gate.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const plugin = path.join(root, 'unreal/BreziTwin/Plugins/BreziCausticsProbe');
const python = process.env.BREZI_PYTHON || 'python3';
function run(args) {
  const result = spawnSync(python, args, { cwd: root, encoding: 'utf8', timeout: 30_000, env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' } });
  assert.equal(result.error, undefined, result.error?.message);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  return JSON.parse(result.stdout);
}

test('frozen receiver pins and full BVH ownership are valid without the engine', () => {
  const result = run([path.join(plugin, 'Tools/verify_contract.py')]);
  assert.equal(result.receiverObjectCount, 45);
  assert.equal(result.receiverTriangleCount, 1076);
  assert.equal(result.gpuExecuted, false);
});

test('CPU readback validator rejects stale, corrupt and synthetic native evidence', () => {
  const result = run([path.join(plugin, 'Tools/test_validator.py')]);
  assert.equal(result.nativeBuildOrGPUExecuted, false);
  assert.deepEqual(result.negativeRejected, [
    'truncated-photon', 'nan-photon', 'foreign-triangle', 'doubled-atlas-energy',
    'fresnel-disagreement', 'beer-lambert-disagreement', 'floor-reclassification',
    'atlas-spatial-rearrangement-with-same-energy',
    'synthetic-native-evidence', 'unreviewed-receiver-contract',
  ]);
});

test('validation gates also execute with Python optimization enabled', () => {
  const result = run(['-O', path.join(plugin, 'Tools/test_validator.py')]);
  assert.equal(result.negativeRejected.length, 10);
});

for (const optimization of [[], ['-O']]) {
  test(`listed float32 identity policy rejects foreign geometry and external expansion${optimization.length ? ' under Python optimization' : ''}`, () => {
    const result = run([...optimization, path.join(plugin, 'Tools/test_identity_policy.py')]);
    assert.equal(result.status, 'CPU-identity-policy-tests-passed');
    assert.equal(result.testsRun, 24);
    assert.equal(result.nativeBuildOrGPUExecuted, false);
  });
}

test('project explicitly enables continuous delivery while plugin discovery remains dormant', () => {
  const descriptor = JSON.parse(readFileSync(path.join(plugin, 'BreziCausticsProbe.uplugin'), 'utf8'));
  assert.equal(descriptor.EnabledByDefault, false);
  assert.equal(descriptor.CanContainContent, false);
  assert.equal(descriptor.Modules[0].LoadingPhase, 'PostConfigInit');
  const project = JSON.parse(readFileSync(path.join(root, 'unreal/BreziTwin/BreziTwin.uproject'), 'utf8'));
  assert.equal(project.Plugins?.find(p => p.Name === 'BreziCausticsProbe')?.Enabled, true);
  assert.equal(configuredCausticsMode(readFileSync(path.join(root, 'unreal/BreziTwin/Config/DefaultGame.ini'), 'utf8')), 'transport-continuous');
  const source = readFileSync(path.join(plugin, 'Source/BreziCausticsProbe/Private/BreziCausticsProbe.cpp'), 'utf8');
  assert.ok(source.indexOf('AddShaderSourceDirectoryMapping') < source.indexOf('if(IsRunningCommandlet())return;'));
  assert.ok(source.indexOf('if(IsRunningCommandlet())return;') < source.indexOf('if(FloorSwitches==0 && GConfig)'));
  assert.match(source, /if\(FloorSwitches==0 && GConfig\)/); // Explicit diagnostic mode keeps precedence over config.
});

for (const script of ['test_water_binding.py', 'test_water_normal_alignment.py']) {
  for (const optimization of [[], ['-O']]) {
    test(`current saved water binding and physical conventions: ${script}${optimization.length ? ' with -O' : ''}`, () => {
      const result = spawnSync(python, [...optimization, path.join(plugin, 'Tools', script)], {
        cwd: root, encoding: 'utf8', timeout: 30_000,
        env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
      });
      assert.equal(result.error, undefined, result.error?.message);
      assert.equal(result.status, 0, result.stderr || result.stdout);
    });
  }
}

test('continuous build guard preserves config semantics and refuses the legacy package path', () => {
  assert.equal(configuredCausticsMode('[Other]\nMode=wrong\n'), '');
  assert.equal(configuredCausticsMode('[BreziFloorCaustics]\nMode="transport-continuous"\n'), 'transport-continuous');
  assert.equal(configuredCausticsMode('[BreziFloorCaustics]\nMode=transport-continuous\nMode=\n'), '');
  assert.throws(() => configuredCausticsMode('[BreziFloorCaustics]\nMode=continous\n'), /Unsupported configured/);
  assert.doesNotThrow(() => requirePhasedContinuousBuild('package', '', false, false));
  assert.throws(() => requirePhasedContinuousBuild('package', 'transport-continuous', false, true), /not enabled/);
  assert.throws(() => requirePhasedContinuousBuild('editor-build', 'transport-continuous', true, false), /stock or changed/);
  assert.throws(() => requirePhasedContinuousBuild('package', 'transport-continuous', true, true), /phased runner/);
});

test('ordinary package command fails before launching native work with the stock engine', () => {
  const result = spawnSync(process.execPath, ['scripts/unreal/run.mjs', 'package'], {
    cwd: root, encoding: 'utf8', timeout: 30_000,
    env: {...process.env, UNREAL_ENGINE_ROOT: '/Users/Shared/Epic Games/UE_5.8'},
  });
  assert.equal(result.error, undefined, result.error?.message);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /Continuous caustics engine preflight failed/);
  assert.match(result.stderr, /no native command was started/);
});
