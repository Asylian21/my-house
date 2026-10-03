import { execFile } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { promisify } from 'node:util';
import { verifyPackagedPayload } from './package-verify.mjs';

const exec = promisify(execFile);
const sha = bytes => createHash('sha256').update(bytes).digest('hex');

export async function openInstalledDom(root, argv = [], environment = process.env) {
  if (environment.BREZI_MODEL_OUTPUT || environment.BREZI_PACKAGE_REPORT || environment.BREZI_PACKAGE_REPORT_SHA256)
    return false;
  let installed;
  try { installed = JSON.parse(await readFile(resolve(root, 'output/unreal/dom-app-current.json'), 'utf8')); }
  catch (error) { if (error.code === 'ENOENT') return false; throw error; }
  if (installed.status !== 'dom-installed-native-visually-verified') throw Error('Dom installation has not passed native visual verification');
  const packageBytes = await readFile(installed.packageReceiptPath);
  if (sha(packageBytes) !== installed.packageReceiptSha256) throw Error('Dom package receipt changed after installation');
  const packaged = JSON.parse(packageBytes);
  const accepted = JSON.parse(await readFile(resolve(root, 'output/unreal/exterior-final-current.json'), 'utf8'));
  if (packaged.status !== 'dom-final-exterior-standalone-package-validated'
    || accepted.status !== 'final-saved-editor-exterior-user-accepted'
    || accepted.launchMap.sha256 !== packaged.selection.launchMap.sha256)
    throw Error('The accepted final scene changed; package and verify the current Dom application');
  await verifyPackagedPayload(installed.appPath, packaged.bundle);
  await exec('/usr/bin/codesign', ['--verify', '--deep', '--strict', installed.appPath]);
  const renderArgs = environment.BREZI_RENDER_PROFILE ? ['-BreziRenderProfile=' + environment.BREZI_RENDER_PROFILE] : [];
  const launchArgs = argv.map((argument, index) => index === 0 && !argument.startsWith('-')
    ? '-BreziView=' + argument : argument);
  const viewerArgs = renderArgs.length && !launchArgs.length
    ? packaged.launchArgs.filter(argument => !argument.startsWith('-BreziRenderProfile=')) : [];
  await exec('/usr/bin/open', ['-a', installed.appPath,
    ...((renderArgs.length || launchArgs.length) ? ['--args', ...viewerArgs, ...renderArgs, ...launchArgs] : [])]);
  console.log('Opened or focused installed Dom: ' + installed.appPath);
  return true;
}
