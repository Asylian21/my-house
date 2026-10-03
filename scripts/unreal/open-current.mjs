// Prefer the explicitly promoted current-model package; preserve explicit historical selections.
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { openInstalledDom } from './open-dom-app.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
if (await openInstalledDom(root, process.argv.slice(2))) process.exit(0);
if (process.env.BREZI_MODEL_OUTPUT && !process.env.BREZI_PACKAGE_REPORT && !process.env.BREZI_PACKAGE_REPORT_SHA256) {
  const explicit = spawn(process.execPath, ['scripts/unreal/model-refresh.mjs', 'open', ...process.argv.slice(2)],
    { cwd: root, stdio: 'inherit', env: process.env });
  const code = await new Promise(resolveExit => {
    explicit.once('error', error => { console.error(error.message); resolveExit(1); });
    explicit.once('exit', code => { resolveExit(code ?? 1); });
  });
  process.exit(code);
}
let selected = null;
if (!process.env.BREZI_PACKAGE_REPORT && !process.env.BREZI_PACKAGE_REPORT_SHA256) {
  try { selected = JSON.parse(await readFile(resolve(root, 'output/unreal/model-refresh-current.json'), 'utf8')); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
}
if (selected) {
  if (selected.status === 'superseded-by-installed-dom')
    throw Error('The final scene uses the verified Dom installation. Restore or package that installation; the retired historical model is not a fallback.');
  const bytes = await readFile(resolve(selected.output, 'model-package.json'));
  const report = JSON.parse(bytes);
  if (createHash('sha256').update(bytes).digest('hex') !== selected.packageReportSha256
    || report.status !== 'current-model-packaged' || selected.status !== 'current-model-visually-reviewed')
    throw Error('Current model selection changed; inspect the reviewed package before opening');
}
const child = spawn(process.execPath,
  selected ? ['scripts/unreal/model-refresh.mjs', 'open', ...process.argv.slice(2)]
    : ['scripts/unreal/run.mjs', 'open', ...process.argv.slice(2)],
  { cwd: root, stdio: 'inherit', env: { ...process.env, ...(selected ? { BREZI_MODEL_OUTPUT: selected.output } : {}) } });
child.once('error', error => { console.error(error.message); process.exitCode = 1; });
child.once('exit', code => { process.exitCode = code ?? 1; });
