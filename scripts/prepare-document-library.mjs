import { existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { verifyDocumentSnapshot } from './document-library-snapshot.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
if (existsSync(new URL('../output/pdf/construction-cbb/DOM-CBB-A1-color.pdf', import.meta.url))) {
  const result = spawnSync(process.execPath, ['scripts/document-library/generate.mjs', ...process.argv.slice(2)], {
    cwd: root, stdio: 'inherit',
  });
  if (result.error) throw result.error;
  process.exitCode = result.status ?? 1;
} else {
  if (process.argv.includes('--force')) throw new Error('Regenerating documents requires the local construction source PDFs.');
  await verifyDocumentSnapshot();
}
