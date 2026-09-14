import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile, readdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const snapshotPath = resolve(root, 'lib/document-library.snapshot.json');
const hash = async path => createHash('sha256').update(await readFile(resolve(root, path))).digest('hex');
const manifestPath = 'lib/document-library.generated.json';
export async function verifyDocumentSnapshot(snapshot) {
  snapshot ??= JSON.parse(await readFile(snapshotPath, 'utf8'));
  assert.equal(snapshot.version, 1);
  assert.equal(await hash(manifestPath), snapshot.manifestSha256, 'Document manifest differs from its published snapshot');
  for (const [path, expected] of Object.entries(snapshot.sources)) {
    assert(!path.includes('..') && !path.startsWith('/'));
    assert.equal(await hash(path), expected, `Document source changed: ${path}. Regenerate and export the library locally.`);
  }
  const manifest = JSON.parse(await readFile(resolve(root, manifestPath), 'utf8'));
  const urls = new Set();
  function collect(value) {
    if (typeof value === 'string' && value.startsWith('/documents/')) urls.add(value);
    else if (Array.isArray(value)) value.forEach(collect);
    else if (value && typeof value === 'object') Object.values(value).forEach(collect);
  }
  collect(manifest);
  assert.equal(urls.size, Object.keys(snapshot.assets).length);
  for (const url of urls) {
    assert(!url.includes('..') && !url.includes('\\'));
    assert.equal(await hash(`public${url}`), snapshot.assets[url]?.sha256, `Missing or altered published document: ${url}`);
  }
  console.log(`Published document snapshot verified: ${manifest.documents.length} records, ${urls.size} assets.`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (process.argv.includes('--export')) {
    const state = JSON.parse(await readFile(resolve(root, 'public/documents/.build-state.json'), 'utf8'));
    const sources = Object.fromEntries(Object.entries(state.inputs)
      .filter(([path]) => !path.startsWith('output/'))
      .map(([path, value]) => [path, value.sha256]));
    // Catch geometry or renderer changes in a source-only remote checkout too.
    for (const directory of ['lib', 'scripts/construction-documentation']) {
      for (const file of await readdir(resolve(root, directory))) {
        if (!/\.(?:ts|tsx|mjs)$/.test(file)) continue;
        const path = `${directory}/${file}`;
        sources[path] = await hash(path);
      }
    }
    const snapshot = { version: 1, manifestSha256: state.manifestSha256, sources, assets: state.assets };
    await verifyDocumentSnapshot(snapshot);
    await writeFile(snapshotPath, JSON.stringify(snapshot, null, 2) + '\n');
  } else await verifyDocumentSnapshot();
}
