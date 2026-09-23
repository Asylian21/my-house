import test from 'node:test';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve } from 'node:path';

test('stacked native appliance doors follow vertical eye aim', { skip: process.platform !== 'darwin' }, () => {
  const directory = mkdtempSync(resolve(tmpdir(), 'brezi-door-selection-'));
  const root = resolve(import.meta.dirname, '..');
  try {
    const binary = resolve(directory, 'door-selection');
    execFileSync('xcrun', ['clang++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-O2',
      '-I', resolve(root, 'unreal/BreziTwin/Source/BreziTwin'),
      resolve(root, 'tests/unreal-door-selection-policy.cpp'), '-o', binary], { timeout: 30000 });
    execFileSync(binary, [], { timeout: 5000 });
  } finally { rmSync(directory, { recursive: true, force: true }); }
});
