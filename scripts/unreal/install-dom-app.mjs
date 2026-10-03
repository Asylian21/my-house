import { execFile } from 'node:child_process';
import { createHash } from 'node:crypto';
import { access, readFile, rename, writeFile, mkdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';
import { verifyPackagedPayload } from './package-verify.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const output = resolve(root, process.env.DOM_APP_OUTPUT ?? 'output/unreal/dom-app-20261003-r1');
const receiptPath = resolve(output, 'dom-package.json');
const receiptBytes = await readFile(receiptPath);
const packaged = JSON.parse(receiptBytes);
const appPath = '/Applications/Dom.app';
const exec = promisify(execFile);
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const replace = process.argv.includes('--replace');
const rollbackPath = resolve(output, 'installation-rollback/Dom.app');
let previous = null;
if (packaged.status !== 'dom-final-exterior-standalone-package-validated'
  || packaged.activeDesign !== 'C/B/B' || packaged.appName !== 'Dom'
  || packaged.appPath !== resolve(output, 'package/Mac/BreziTwin.app'))
  throw Error('No validated final Dom package in this output');
let existing = false;
try { await access(appPath); existing = true; }
catch (error) { if (error.code !== 'ENOENT') throw error; }
if (existing) {
  if (!replace) throw Error('Dom is already installed; use --replace only after native candidate verification');
  if (!process.env.DOM_NATIVE_REVIEW) throw Error('Replacement requires DOM_NATIVE_REVIEW');
  const reviewBytes = await readFile(resolve(root, process.env.DOM_NATIVE_REVIEW));
  const review = JSON.parse(reviewBytes);
  if (review.status !== 'dom-performance-candidate-accepted' || review.packageReceiptSha256 !== sha(receiptBytes)
    || review.sourceMapSha256 !== packaged.selection.launchMap.sha256 || review.nativeVisualReviewPassed !== true
    || review.nativePerformanceReviewPassed !== true)
    throw Error('Native review does not approve this exact candidate');
  const currentBytes = await readFile(resolve(root, 'output/unreal/dom-app-current.json'));
  const current = JSON.parse(currentBytes);
  const currentPackageBytes = await readFile(current.packageReceiptPath);
  if (current.appPath !== appPath || sha(currentPackageBytes) !== current.packageReceiptSha256)
    throw Error('Installed application binding changed');
  await verifyPackagedPayload(appPath, JSON.parse(currentPackageBytes).bundle);
  await exec('/usr/bin/codesign', ['--verify', '--deep', '--strict', appPath]);
  try { await access(rollbackPath); throw Error('Existing rollback must not be overwritten'); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  previous = { current, currentBytes, reviewPath: resolve(root, process.env.DOM_NATIVE_REVIEW), reviewSha256: sha(reviewBytes) };
}
await verifyPackagedPayload(packaged.appPath, packaged.bundle);
await exec('/usr/bin/codesign', ['--verify', '--deep', '--strict', packaged.appPath]);
try { if ((await exec('/usr/bin/pgrep', ['-x', 'BreziTwin'])).stdout.trim()) throw Error('Close Dom before installing'); }
catch (error) { if (error.code !== 1) throw error; }
if (previous) {
  await mkdir(dirname(rollbackPath), { recursive: true });
  await writeFile(resolve(output, 'installation-rollback/current-selection.json'), previous.currentBytes);
  await rename(appPath, rollbackPath);
}
try {
  await rename(packaged.appPath, appPath);
  await verifyPackagedPayload(appPath, packaged.bundle);
  await exec('/usr/bin/codesign', ['--verify', '--deep', '--strict', appPath]);
} catch (error) {
  try { await access(appPath); await rename(appPath, packaged.appPath); }
  catch (restoreError) { if (restoreError.code !== 'ENOENT') throw restoreError; }
  if (previous) await rename(rollbackPath, appPath);
  throw error;
}
const installation = {
  schemaVersion: 1, status: 'dom-installed-awaiting-native-verification',
  installedAt: new Date().toISOString(), appPath, packageReceiptPath: receiptPath,
  packageReceiptSha256: createHash('sha256').update(receiptBytes).digest('hex'),
  sourceMapSha256: packaged.selection.launchMap.sha256,
  activeDesign: packaged.activeDesign, streetAndRightSetbackMm: packaged.streetAndRightSetbackMm,
  appName: 'Dom', codeSignature: 'deep-strict-valid', duplicatePackageCopyRetained: false,
  replacement: previous ? { rollbackPath, previousPackageReceiptSha256: previous.current.packageReceiptSha256,
    nativeReviewPath: previous.reviewPath, nativeReviewSha256: previous.reviewSha256 } : null,
};
await writeFile(resolve(output, 'installation.json'), JSON.stringify(installation, null, 2) + '\n');
console.log(JSON.stringify(installation, null, 2));
