import assert from 'node:assert/strict';
import test from 'node:test';
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url));
const geometry = process.env.BREZI_WORLD_NORMAL_GEOMETRY
  ? resolve(process.env.BREZI_WORLD_NORMAL_GEOMETRY)
  : resolve(root, 'output/unreal/archviz-game-20260922/geometry');
const gableNames = [
  '1.03 · južný štít podhľadu · ústie chodby',
  '1.03 · štít podhľadu · nad východnou stenou chodby',
  '1.03 · južný štít podhľadu · nad nosnou stenou kuchyne',
];
const dot = (a, b) => a.reduce((sum, value, i) => sum + value*b[i], 0);
const scale = (v, factor) => v.map(value => value*factor);
const unit = v => scale(v, 1 / Math.hypot(...v));
const minus = (a, b) => a.map((v, i) => v-b[i]);
const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
const cosine = (normal, lightDirection) => Math.max(0, dot(normal, lightDirection));
const near = (a, b) => assert(Math.abs(a-b) < 1e-8, `${a} != ${b}`);

function currentGables(t) {
  const scenePath = resolve(geometry, 'scene.json');
  const objPath = resolve(geometry, 'dom-mm.obj');
  if (!existsSync(scenePath) || !existsSync(objPath)) {
    t.skip('Current native source export is unavailable; no geometry verification claimed');
    return null;
  }
  const scene = JSON.parse(readFileSync(scenePath, 'utf8'));
  assert.deepEqual(scene.activeDesign, { variant: 'C', heatingLayout: 'B', livingLayout: 'B' });
  const objects = gableNames.map(sourceId => {
    const matches = scene.objects.filter(object => object.enabled && object.sourceId === sourceId);
    assert.equal(matches.length, 1, `Expected one current source gable: ${sourceId}`);
    return matches[0];
  });
  const byId = new Map(objects.map(object => [object.id, { object, triangles: [] }]));
  const vertices = [], normals = [];
  let selected;
  for (const line of readFileSync(objPath, 'utf8').split('\n')) {
    if (line.startsWith('v ')) vertices.push(line.trim().split(/\s+/).slice(1).map(Number));
    else if (line.startsWith('vn ')) normals.push(line.trim().split(/\s+/).slice(1).map(Number));
    else if (line.startsWith('o ')) selected = byId.get(line.trim().slice(2));
    else if (selected && line.startsWith('f ')) {
      const indices = line.trim().split(/\s+/).slice(1).map(item => item.split('/').map(Number));
      assert.equal(indices.length, 3);
      selected.triangles.push({
        points: indices.map(([index]) => vertices[index-1]),
        normals: indices.map(([, , index]) => normals[index-1]),
      });
    }
  }
  return { scene, gables: [...byId.values()] };
}

test('current dark gables are pale non-emissive plaster, beside self-lit source SDK', t => {
  const source = currentGables(t);
  if (!source) return;
  for (const { object } of source.gables) {
    const material = source.scene.materials[object.materialSlots[0]];
    assert.equal(material.name, 'real-interior-plaster');
    assert(material.color.every(value => value > .9));
    assert.deepEqual(material.emission, [0, 0, 0]);
  }
  const ceiling = Object.values(source.scene.materials).find(material => material.name === 'real-interior-ceiling');
  assert(ceiling.emission.every(value => value > .5), 'The existing SDK comparison includes source emission');
});

test('actual opposite gable faces need explicit facing correction for world-space normals', t => {
  const source = currentGables(t);
  if (!source) return;
  let verifiedPairs = 0;
  for (const { object, triangles } of source.gables) {
    assert.equal(triangles.length, object.triangles);
    const coincident = new Map();
    for (const triangle of triangles) {
      const geometric = unit(cross(minus(triangle.points[1], triangle.points[0]), minus(triangle.points[2], triangle.points[0])));
      assert(triangle.normals.every(normal => dot(geometric, normal) > 0), 'OBJ winding agrees with its source normals');
      // The visible gable caps have a constant plan Y. Extrusion rim vertices
      // can carry smoothed corner normals, which are a separate shading case.
      if (Math.max(...triangle.points.map(point => point[1])) - Math.min(...triangle.points.map(point => point[1])) > .001) continue;
      const key = triangle.points.map(point => point.join(',')).sort().join('|');
      if (!coincident.has(key)) coincident.set(key, []);
      coincident.get(key).push({ geometric, normal: unit(triangle.normals[0]) });
    }
    for (const pair of coincident.values()) {
      assert.equal(pair.length, 2, 'Current Babylon DOUBLESIDE source duplicates each triangle');
      near(dot(pair[0].normal, pair[1].normal), -1);
      for (const viewSide of [-1, 1]) {
        const towardViewer = scale(pair[0].geometric, viewSide);
        const fixed = pair.map(face => {
          // UE leaves custom world-space Normal unflipped. The material must
          // supply the same front/back correction UE applies to tangent normals.
          const twoSidedSign = dot(face.geometric, towardViewer) > 0 ? 1 : -1;
          return scale(face.normal, twoSidedSign);
        });
        near(dot(fixed[0], fixed[1]), 1);
        // Test oblique as well as perpendicular light, independently of which
        // coincident triangle wins native depth/rasterization.
        const tangent = unit(cross(towardViewer, Math.abs(towardViewer[2]) < .9 ? [0, 0, 1] : [1, 0, 0]));
        for (const oblique of [0, .4, .9]) {
          const light = unit(towardViewer.map((value, i) => value + tangent[i]*oblique));
          const old = pair.map(face => cosine(face.normal, light));
          assert(Math.abs(old[0]-old[1]) > .7, 'Uncorrected duplicate can shade black under the same light');
          near(cosine(fixed[0], light), cosine(fixed[1], light));
          assert(cosine(fixed[0], light) > .7);
        }
      }
      verifiedPairs++;
    }
  }
  assert(verifiedPairs >= 3, 'All three source closures contribute real coincident-face evidence');
});

test('a tangent-space material already receives the engine facing sign exactly once', () => {
  const front = unit([.12, -.08, 1]);
  const reverseWindingNormal = scale(front, -1);
  const engineBackFaceNormal = scale(reverseWindingNormal, -1);
  near(dot(front, engineBackFaceNormal), 1);
  // Applying the new world-space correction again on this path would invert it.
  near(dot(front, scale(engineBackFaceNormal, -1)), -1);
});
