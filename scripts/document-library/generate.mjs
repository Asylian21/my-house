import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, resolve, delimiter } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const runtime = resolve(homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies');
const bundledPython = resolve(runtime, 'python/bin/python3');
const python = process.env.DOCUMENT_LIBRARY_PYTHON || (existsSync(bundledPython) ? bundledPython : 'python3');
const packages = process.env.DOCUMENT_LIBRARY_PYTHON_PACKAGES || resolve(homedir(), '.cache/dom-document-library/python');
const env = { ...process.env,
  PYTHONPATH: [packages, process.env.PYTHONPATH].filter(Boolean).join(delimiter),
  PATH: [resolve(runtime, 'native/poppler/poppler/bin'), process.env.PATH].filter(Boolean).join(delimiter),
};
const result = spawnSync(python, [resolve(root, 'scripts/document-library/build.py'), ...process.argv.slice(2)], {
  cwd: root, env, stdio: 'inherit',
});
if (result.error) console.error(`Document library: ${result.error.message}. Set DOCUMENT_LIBRARY_PYTHON to the prepared Python runtime.`);
process.exit(result.status ?? 1);
