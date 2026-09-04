import test from "node:test";
import assert from "node:assert/strict";
import { exportPoint, serializeObj } from "../scripts/archviz/geometry.mjs";

const identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
test("export converts Babylon RHS metres to centred Z-up millimetres", () => {
  assert.deepEqual(
    exportPoint([-3.46, -0.012, -2.6], identity),
    [-3460, 2600, -12],
  );
  const translated = [...identity];
  translated[12] = 2;
  translated[13] = 3;
  translated[14] = -4;
  assert.deepEqual(exportPoint([1, 2, 3], translated), [3000, 1000, 5000]);
});
test("expands every instance and repairs triangle handedness from normals", () => {
  const second = [...identity];
  second[12] = 10;
  const mesh = {
    name: "test wall",
    sourceId: "wall",
    enabled: true,
    positions: [0, 0, 0, 1, 0, 0, 0, 0, 1],
    normals: [0, 1, 0, 0, 1, 0, 0, 1, 0],
    uvs: [0, 0, 1, 0, 0, 1],
    indices: [0, 1, 2],
    transforms: [identity, second],
    normalTransforms: [identity, identity],
    materials: [{ name: "real-wall", color: [1, 1, 1] }],
    subMeshes: [],
  };
  const manifest = { materials: {}, objects: [] };
  const obj = [...serializeObj([mesh], manifest)].join("");
  assert.match(obj, /f 1\/1\/1 3\/3\/3 2\/2\/2/);
  assert.match(obj, /f 4\/4\/4 6\/6\/6 5\/5\/5/);
  assert.equal(manifest.objects[0].instances, 2);
  assert.deepEqual(JSON.parse(JSON.stringify(manifest.objects[0].boundsMm)), {
    min: [0, -1000, 0],
    max: [11000, 0, 0],
  });
});
test("keeps material slots and writes valid OBJ when attributes are absent", () => {
  const mesh = {
    name: "multi",
    sourceId: "multi",
    enabled: true,
    positions: [0, 0, 0, 1, 0, 0, 0, 1, 0],
    normals: [],
    uvs: [],
    indices: [0, 1, 2],
    transforms: [identity],
    normalTransforms: [identity],
    materials: [{ name: "unused" }, { name: "assigned" }],
    subMeshes: [{ start: 0, count: 3, material: 1 }],
  };
  const manifest = { materials: {}, objects: [] };
  const obj = [...serializeObj([mesh], manifest)].join("");
  assert.match(obj, /usemtl MAT_0001\ns 1\nf 1 2 3\n/);
  assert.equal(manifest.objects[0].materialSlots.length, 2);
});
