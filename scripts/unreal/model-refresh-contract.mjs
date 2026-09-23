import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

// Accepted C/B/B revision; the regression test checks these against the live source contracts.
export const EXPECTED_MODEL = Object.freeze({
  island: { x0: 23381, y0: 12880, x1: 26021, y1: 13800, z0: 880, z1: 900 },
  sink: { x0: 24091, y0: 12990, x1: 24691, y1: 13390, z0: 700, z1: 703 },
  hob: { x0: 24596, y0: 11174, x1: 25396, y1: 11684 },
  oven: { x0: 23393, x1: 23989, z0: 850, z1: 1445 },
  dishwasher: { x0: 25393, x1: 25989 },
  sidePassageMm: 900, workAisleMm: 1150,
  office: { startXmm: 24442, widthMm: 2000, heightMm: 1600, sillMm: 900, frameWidthMm: 35, kind: 'fixed' },
  portal: { startXmm: 11990, widthMm: 2200, heightMm: 2400, sillMm: 0 },
});
export const MODEL_SOURCE_NAMES = Object.freeze({
  island: 'KITCHEN-RUN · pracovná doska ostrovčeka · minerálny povrch',
  sink: 'KITCHEN-RUN · drez · zapustené dno 600',
  hob: 'KITCHEN-RUN · varná doska · indukcia 800',
  oven: 'KITCHEN-RUN · OVEN-ELEVATED · rúra so zasúvacím krídlom',
  dishwasher: 'KITCHEN-RUN · DISHWASHER · umývačka 4',
  back: 'KITCHEN-RUN · nika · minerálna pracovná doska',
  right: 'KITCHEN-RUN · L-RETURN-EAST · minerálna doska pri okne',
});
export const OAK_FRONT_NAMES = [
  'FRIDGE-600 · dubový blok 2026', 'OVEN-TOWER · horné dvierka 2026',
  'nika · zásuvky 1', 'horné skrinky · matná nika 2026',
  'ostrovček · zásuvková skrinka 1', 'DISHWASHER · umývačka 4',
  'ostrovček · plytké úložisko 1', 'L-RETURN-EAST · dvierka 1',
].map(name => `KITCHEN-RUN · ${name}`);
const identity = object => (object.sourceId ?? object.name).replace(/_merged$/, '');
const near = (actual, expected, label) => assert(Number.isFinite(actual)
  && Math.abs(actual - expected) <= 0.1, `${label}: expected ${expected} mm, got ${actual}`);
const one = (scene, name) => {
  const rows = scene.objects.filter(object => identity(object) === name && object.enabled);
  assert.equal(rows.length, 1, `Expected one active source: ${name}`);
  return rows[0];
};
function bounds(scene, objects) {
  assert(objects.length, 'Missing measured source geometry');
  const min = [0, 1, 2].map(i => Math.min(...objects.map(o => o.boundsMm.min[i])));
  const max = [0, 1, 2].map(i => Math.max(...objects.map(o => o.boundsMm.max[i])));
  return { x0: min[0] + scene.sceneCenterMm.x, y0: min[1] + scene.sceneCenterMm.y,
    x1: max[0] + scene.sceneCenterMm.x, y1: max[1] + scene.sceneCenterMm.y, z0: min[2], z1: max[2] };
}
const dimensions = b => [b.x1 - b.x0, b.y1 - b.y0, b.z1 - b.z0];
const compareBounds = (actual, expected, label) => {
  for (const [key, value] of Object.entries(expected)) near(actual[key], value, `${label}.${key}`);
};
function opening(scene, facade, id) {
  const found = scene.house.facades[facade].openings.filter(o => o.id === id);
  assert.equal(found.length, 1, `Missing or ambiguous opening ${id}`);
  return found[0];
}
function verifyOpening(scene, facade, id, expected, prefix) {
  const definition = opening(scene, facade, id);
  for (const [key, value] of Object.entries(expected)) assert.equal(definition[key], value, `${id}.${key}`);
  const frames = scene.objects.filter(o => o.enabled && identity(o).startsWith(prefix) && identity(o).includes(' · rám '));
  const measured = bounds(scene, frames);
  compareBounds(measured, { x0: definition.startXmm, x1: definition.startXmm + definition.widthMm,
    z0: definition.sillMm, z1: definition.sillMm + definition.heightMm }, id);
  if (definition.frameWidthMm) {
    for (const frame of frames) {
      const b = bounds(scene, [frame]);
      near(identity(frame).endsWith('stĺpik') ? b.x1 - b.x0 : b.z1 - b.z0, definition.frameWidthMm, `${id} slim frame`);
    }
  }
  return { definition, measured, sourceNames: frames.map(identity) };
}

export function verifyModelRefresh(scene, previous = null) {
  assert.equal(scene.units, 'millimetres');
  assert.deepEqual(scene.activeDesign, { variant: 'C', heatingLayout: 'B', livingLayout: 'B' }, 'Export must be explicit C/B/B');
  const records = Object.fromEntries(Object.entries(MODEL_SOURCE_NAMES).map(([key, name]) => [key, one(scene, name)]));
  const measured = Object.fromEntries(Object.entries(records).map(([key, object]) => [key, bounds(scene, [object])]));
  for (const key of ['island', 'sink', 'hob', 'oven', 'dishwasher']) compareBounds(measured[key], EXPECTED_MODEL[key], key);
  const sidePassageMm = measured.right.x0 - measured.island.x1;
  const workAisleMm = measured.island.y0 - measured.back.y1;
  near(sidePassageMm, EXPECTED_MODEL.sidePassageMm, 'Right passage');
  near(workAisleMm, EXPECTED_MODEL.workAisleMm, 'Work aisle');
  near(measured.island.x1, measured.back.x1, 'Aligned island and back worktop');
  near(measured.island.y1, measured.right.y1, 'Full right return');
  assert(measured.dishwasher.x0 > measured.sink.x1 && measured.dishwasher.x1 < measured.island.x1, 'Dishwasher must remain east of the sink');
  assert(measured.hob.y1 < measured.island.y0 && measured.oven.y1 < measured.island.y0, 'Cooking must remain on the rear run');
  assert(!scene.objects.some(o => /OVEN-UNDER-HOB|ostrovný odsávač|komín odsávača/.test(identity(o))), 'Legacy island cooking geometry remains');
  const material = object => {
    assert.equal(object.materialSlots.length, 1, `Ambiguous material for ${identity(object)}`);
    const result = scene.materials[object.materialSlots[0]];
    assert(result, `Missing material for ${identity(object)}`);
    return result;
  };
  const stone = ['island', 'back', 'right'].map(key => material(records[key]));
  assert(stone.every(m => m.texture?.endsWith('/stone-dark-albedo.jpg') && m.color.length === 3
    && m.color.every(v => Number.isFinite(v) && v >= 0 && v < 0.25) && m.metallic === 0), 'All worktops must retain black stone');
  const oak = OAK_FRONT_NAMES.map(name => material(one(scene, name)));
  assert(oak.every(m => m.texture?.endsWith('/living-natural-oak-albedo.jpg') && m.metallic === 0), 'Cabinet elevations must retain natural oak');
  const office = verifyOpening(scene, 'front', 'FRONT-07', EXPECTED_MODEL.office, 'Výplň otvoru FRONT-07 ·');
  const portal = verifyOpening(scene, 'garden', 'GARDEN-02', EXPECTED_MODEL.portal, 'Terasové presklenie 2200 ·');
  return { status: 'source-model-refresh-verified', generatedAt: new Date().toISOString(),
    sourceGeneratedAt: scene.generatedAt, sourceCommit: scene.sourceCommit, activeDesign: scene.activeDesign,
    selectionMethod: 'Stable sourceId/name and opening IDs; ordinal DOM/material IDs are resolved from this manifest only.',
    kitchen: { measured, islandDimensionsMm: dimensions(measured.island), sidePassageMm, workAisleMm,
      stoneMaterial: stone[0], oakMaterial: oak[0], checkedOakElevations: oak.length },
    windows: { office, portal }, previous: previous ? summarizePreviousModel(previous) : null,
    verification: 'Source manifest geometry and scalar/material texture references only; native import, render and interaction require separate verification.' };
}

export function summarizePreviousModel(scene) {
  const optional = name => {
    const rows = scene.objects.filter(o => identity(o) === name);
    return rows.length === 1 ? bounds(scene, rows) : null;
  };
  return { generatedAt: scene.generatedAt, sourceCommit: scene.sourceCommit, activeDesign: scene.activeDesign ?? null,
    peninsula: optional('KITCHEN-RUN · pracovná doska polostrova'),
    rearSink: optional('KITCHEN-RUN · nerezový drez'),
    islandHob: optional('KITCHEN-RUN · indukčná varná doska'),
    hasUnderHobOven: scene.objects.some(o => identity(o).includes('OVEN-UNDER-HOB')),
    office: opening(scene, 'front', 'FRONT-07'), portal: opening(scene, 'garden', 'GARDEN-02') };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [scenePath, previousPath, reportPath] = process.argv.slice(2);
  assert(scenePath && reportPath, 'Usage: node model-refresh-contract.mjs <scene.json> <previous-scene.json|-> <report.json>');
  const bytes = await readFile(scenePath);
  const previousBytes = previousPath === '-' ? null : await readFile(previousPath);
  const report = verifyModelRefresh(JSON.parse(bytes), previousBytes ? JSON.parse(previousBytes) : null);
  const sha = buffer => createHash('sha256').update(buffer).digest('hex');
  Object.assign(report, { sourceManifestSha256: sha(bytes), previousManifestSha256: previousBytes ? sha(previousBytes) : null });
  await writeFile(reportPath, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ status: report.status, reportPath, islandMm: report.kitchen.islandDimensionsMm,
    sidePassageMm: report.kitchen.sidePassageMm, workAisleMm: report.kitchen.workAisleMm }));
}
