import { createServer } from 'vite';
import { readFile, writeFile } from 'node:fs/promises';

const server = await createServer({ configFile: false, cacheDir:'node_modules/.vite-plan-documentation', server: { middlewareMode: true }, appType: 'custom' });
try {
  const { extractPlanGeometry } = await server.ssrLoadModule('/scripts/plan-documentation/extract.ts');
  const result = extractPlanGeometry(await readFile(new URL('../../public/assets/archviz/dom-terrace.glb',import.meta.url)));
  await writeFile(new URL('../../lib/plan-geometry.generated.json', import.meta.url), JSON.stringify(result));
  console.log(`Plan documentation: ${result.meshes.length} measured components.`);
} finally {
  await server.close();
}
