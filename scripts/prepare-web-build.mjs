import assert from 'node:assert/strict';
import { readFile, readdir, rm, stat } from 'node:fs/promises';
import { resolve, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const dist = resolve(root, 'dist');
const client = resolve(dist, 'client');
// These original 4K textures are consumed only by scripts/unreal.
// Keep source assets and the frozen v1/v2 trees unchanged.
const unrealOnly = ['assets/archviz/wood_chips', 'assets/archviz/pool-coping'];
async function* files(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = resolve(directory, entry.name);
    if (entry.isDirectory()) yield* files(path);
    else if (entry.isFile()) yield path;
  }
}
for await (const path of files(client)) {
  if (!/\.(?:js|css|html|json)$/.test(path)) continue;
  const contents = await readFile(path, 'utf8');
  for (const asset of unrealOnly) {
    assert(!contents.includes(asset), `Web output references Unreal texture: ${relative(dist, path)} -> ${asset}`);
  }
}
// vinext's server bundle also contains an inventory of every public file.
// Check application source separately so that inventory is not mistaken for use.
for (const directory of ['app', 'lib']) for await (const path of files(resolve(root, directory))) {
  if (!/\.(?:ts|tsx|mjs)$/.test(path)) continue;
  const contents = await readFile(path, 'utf8');
  for (const asset of unrealOnly) assert(!contents.includes(asset), `Application references ${asset}: ${path}`);
}
const library = JSON.parse(await readFile(resolve(root, 'lib/document-library.generated.json'), 'utf8'));
const documentPaths = new Set();
function collect(value) {
  if (typeof value === 'string' && value.startsWith('/documents/')) {
    assert(!value.includes('..') && !value.includes('\\'), `Unsafe document URL: ${value}`);
    documentPaths.add(resolve(client, value.slice(1)));
  } else if (Array.isArray(value)) value.forEach(collect);
  else if (value && typeof value === 'object') Object.values(value).forEach(collect);
}
collect(library);
assert(documentPaths.size > 0, 'Document library has no downloadable assets');
for (const path of documentPaths) assert((await stat(path)).size > 0, `Missing document asset: ${path}`);
let removedBytes = 0;
for (const asset of unrealOnly) {
  const directory = resolve(client, asset);
  for await (const path of files(directory)) removedBytes += (await stat(path)).size;
  await rm(directory, { recursive: true });
}
// Publish all manifest-linked files; local renderer QA and superseded generated
// copies stay on disk in public/documents, outside the deployment output.
for await (const path of files(resolve(client, 'documents'))) {
  if (documentPaths.has(path)) continue;
  removedBytes += (await stat(path)).size;
  await rm(path);
}
console.log(`Web build: ${documentPaths.size} document assets retained; ${(removedBytes / 1024 ** 2).toFixed(1)} MiB of Unreal-only textures and document cache excluded.`);
