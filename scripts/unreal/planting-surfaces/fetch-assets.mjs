// Download only the fixed CC0 input set. Never overwrite a different local file.
import { createHash, randomUUID } from 'node:crypto';
import { readFile, mkdir, writeFile, link, unlink, stat } from 'node:fs/promises';
import { dirname, resolve, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../../..');
const manifest = JSON.parse(await readFile(resolve(here, 'inputs.json'), 'utf8'));
const hash = (bytes, algorithm) => createHash(algorithm).update(bytes).digest('hex');
const check = (bytes, entry) => {
  if (bytes.length !== entry.bytes || hash(bytes, 'sha256') !== entry.sha256 || hash(bytes, 'md5') !== entry.md5)
    throw new Error(`Downloaded/local bytes differ from the pinned source: ${entry.path}`);
};

for (const [role, entry] of Object.entries(manifest.maps)) {
  const target = resolve(root, entry.path);
  const url = new URL(entry.url);
  if (!relative(root, target).startsWith('public/assets/archviz/wood_chips/')
      || url.protocol !== 'https:' || url.hostname !== 'dl.polyhaven.org'
      || !url.pathname.startsWith('/file/ph-assets/Textures/jpg/4k/wood_chips/')
      || !Number.isSafeInteger(entry.bytes) || entry.bytes <= 0 || entry.bytes > 32 * 1024 * 1024)
    throw new Error(`Unexpected input destination, source URL or size: ${role}`);
  let present = true;
  try { await stat(target); } catch (error) { if (error.code === 'ENOENT') present = false; else throw error; }
  if (present) {
    check(await readFile(target), entry);
    console.log(`${role}: verified ${entry.path}`);
    continue;
  }
  const response = await fetch(url, {
    headers: { 'User-Agent': 'BreziTwinAssetPipeline/1.0 (local architectural visualization)' },
    signal: AbortSignal.timeout(120_000), redirect: 'error',
  });
  if (!response.ok) throw new Error(`Download failed for ${role}: HTTP ${response.status}`);
  const chunks = []; let length = 0;
  for await (const chunk of response.body) {
    length += chunk.length;
    if (length > entry.bytes) throw new Error(`Oversized response for ${role}`);
    chunks.push(chunk);
  }
  const bytes = Buffer.concat(chunks); check(bytes, entry);
  await mkdir(dirname(target), { recursive: true });
  const temporary = `${target}.${randomUUID()}.tmp`;
  await writeFile(temporary, bytes, { flag: 'wx' });
  try { await link(temporary, target); } finally { await unlink(temporary); }
  check(await readFile(target), entry);
  console.log(`${role}: downloaded and verified ${entry.path}`);
}
