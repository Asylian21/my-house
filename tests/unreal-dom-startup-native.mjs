// Actual OS/NSProcessInfo argv validation for Dom's one-time self-exec defaults.
import { execFile } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
import assert from 'node:assert/strict';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const output = resolve(root, process.env.DOM_APP_OUTPUT ?? 'output/unreal/dom-app-20261003-r1', 'startup-default-fixture');
const executable = resolve(output, 'Contents/MacOS/BreziTwin');
const stub = resolve(output, 'Fixture.mm'), exec = promisify(execFile);
await mkdir(dirname(executable), { recursive: true });
await writeFile(stub, '#import <Foundation/Foundation.h>\n#include <stdio.h>\n#include <unistd.h>\nint main(int, char**) { @autoreleasepool { NSDictionary* result = @{ @"pid": @(getpid()), @"arguments": [[NSProcessInfo processInfo] arguments] }; NSData* data = [NSJSONSerialization dataWithJSONObject:result options:0 error:nil]; fwrite(data.bytes,1,data.length,stdout); puts(""); } return 0; }\n');
await exec('xcrun', ['clang++', '-arch', 'arm64', '-mmacosx-version-min=14.0', '-O2', '-Wall', '-Wextra', '-Werror',
  '-DBREZI_STARTUP_ENTRY_FIXTURE=1', '-Wl,-e,_BreziMain', resolve(root, 'scripts/unreal/dom-startup-entry.cpp'),
  stub, '-framework', 'Foundation', '-o', executable]);
const flags = ['-LLM', '-DetectHitchesWithLLM'];
const defaults = ['-windowed', '-ResX=1920', '-ResY=1080', '-BreziOutput=retina',
  '-BreziRenderProfile=full', '-BreziView=exterior-neighborhood-ground-r38'];
const cases = [];
for (const { args, viewer, canonical } of [
  { args: [], viewer: true }, { args: flags, viewer: true, canonical: true },
  { args: ['-LLM'], viewer: true }, { args: ['-psn_0_12345'], viewer: true },
  { args: ['-BreziCapture4K'], viewer: false },
  { args: ['-BreziView=interior', '-BreziRenderProfile=performance', '-BreziOutput=4k', '-ResX=3840'], viewer: false },
  { args: [...flags, '-BreziProfileGPU'], viewer: false, canonical: true },
  { args: ['-fullscreen', '-BreziWalkTraversal=basic', 'space Žlté $(literal)'], viewer: false },
]) {
  const result = await exec(executable, args, { timeout: 10000 });
  const actual = JSON.parse(result.stdout);
  assert.deepEqual(actual.arguments, [executable, ...(canonical ? [] : flags), ...(viewer ? defaults : []), ...args]);
  const entries = [...result.stderr.matchAll(/^BreziStartupEntry: pid=(\d+) phase=enter-engine /gm)];
  const reexecs = [...result.stderr.matchAll(/^BreziStartupEntry: pid=(\d+) phase=self-exec /gm)];
  assert.equal(entries.length, 1);
  assert.equal(reexecs.length, canonical && !viewer ? 0 : 1);
  assert(entries.concat(reexecs).every(match => Number(match[1]) === actual.pid));
  assert.equal(result.stderr.includes('DomStartupDefaults:'), viewer);
  cases.push({ args, viewer, canonical: !!canonical, actual, stderr: result.stderr, status: 'passed' });
}
for (const args of [['-NOLLM'], ['-LLM=0'], ['-DetectHitchesWithLLM=false']]) {
  let failure;
  try { await exec(executable, args, { timeout: 10000 }); } catch (error) { failure = error; }
  assert.equal(failure?.code, 64);
  assert.equal(failure.stdout, '');
  cases.push({ args, expectedCode: 64, status: 'passed' });
}
const report = { status: 'dom-native-startup-default-fixture-passed', cases,
  actualOSProcessArgumentsVerified: true, samePidOneSelfExecVerified: true,
  explicitCLIAndQAArgumentsPreserved: true, unrealOrRenderingExecuted: false };
await writeFile(resolve(output, 'receipt.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ status: report.status, cases: cases.length,
  receipt: resolve(output, 'receipt.json') }, null, 2));
