import test from "node:test";
import assert from "node:assert/strict";
import validator from "gltf-validator";
import { mkdtemp, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { buildHiddenCollisionGlb, collisionId } from "../scripts/unreal/hidden-collision-export.mjs";
const identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
function fixture() {
  const source = { sourceId: "authored hidden hull", name: "Fixture only", sourceEnabled: true, sourceHidden: true,
    sourceCheckCollisions: true, sourceArchived: false, metadata: { walkCollisionOnly: true },
    positions: [0, 0, 0, 1, 0, 0, 0, 1, 0], normals: [0, 0, 1, 0, 0, 1, 0, 0, 1], indices: [0, 1, 2],
    transforms: [[...identity.slice(0, 12), 2, 3, -4, 1]], normalTransforms: [identity] };
  const scene = { objSha256: "a".repeat(64), objects: [{ id: "DOM_00000", fixture: "unchanged visible geometry" }],
    skipped: [{ sourceId: source.sourceId, enabled: true, babylonCheckCollisions: true, reason: "hidden-proxy-or-collider" }] };
  return { source, scene, capture: { mainObjSha256: scene.objSha256, colliders: [source] } };
}
const build = ({ scene, capture }) => buildHiddenCollisionGlb(scene, capture, "b".repeat(64));

test("the collision-only container preserves actual transforms and leaves the main DOM namespace unchanged", async () => {
  const f = fixture(), before = structuredClone(f.scene), { glb, contract } = build(f);
  assert.deepEqual(f.scene, before);
  assert.equal(contract.objects[0].id, collisionId(f.source.sourceId));
  assert.deepEqual(contract.objects[0].nativeBoundsCm, { min: [200, -400, 300], max: [300, -400, 400] });
  const result = await validator.validateBytes(new Uint8Array(glb), { maxIssues: 0 });
  assert.equal(result.issues.numErrors, 0); assert.equal(result.issues.numWarnings, 0); assert.equal(result.issues.truncated, false);
  assert.equal(contract.verification.nativeImported, false);
});

test("adding or reordering hidden hulls never renumbers existing identities", () => {
  const f = fixture(), first = build(f).contract.objects[0].id;
  const source2 = { ...f.source, sourceId: "second hidden hull" };
  f.scene.skipped.unshift({ ...f.scene.skipped[0], sourceId: source2.sourceId });
  f.capture.colliders.unshift(source2);
  const result = build(f);
  assert.equal(result.contract.objects.find((r) => r.sourceId === f.source.sourceId).id, first);
  f.capture.colliders.reverse();
  assert.equal(build(f).contract.supplementSha256, result.contract.supplementSha256);
});

test("unregistered, duplicate, disabled, visible and archive colliders are refused", () => {
  for (const mutate of [
    (f) => f.source.sourceId = "unregistered", (f) => f.capture.colliders.push(f.source),
    (f) => f.source.sourceEnabled = false, (f) => f.source.sourceHidden = false,
    (f) => f.source.sourceArchived = true, (f) => f.source.sourceCheckCollisions = false,
    (f) => f.source.metadata.walkSurface = true,
  ]) { const f = fixture(); mutate(f); assert.throws(() => build(f)); }
});

test("stale source captures and unsupported skip reasons cannot become collision evidence", () => {
  const f = fixture(); f.capture.mainObjSha256 = "c".repeat(64); assert.throws(() => build(f), /canonical OBJ/);
  const g = fixture(); g.scene.skipped[0].reason = "environment-or-label"; assert.throws(() => build(g), /another reason/);
});

test("nonfinite, degenerate, out-of-range and nonaffine collision input is rejected", () => {
  for (const mutate of [
    (f) => f.source.positions[0] = Infinity,
    (f) => f.source.indices[0] = 100,
    (f) => f.source.indices = [0, 0, 0],
    (f) => f.source.transforms[0][3] = .2,
    (f) => f.source.normalTransforms = [],
  ]) { const f = fixture(); mutate(f); assert.throws(() => build(f)); }
});

test("native authoring reader checks all source triangles and detects same-bounds substitutions", async () => {
  const directory = await mkdtemp(join(tmpdir(), "brezi-hidden-collision-test-"));
  try {
    const { glb, contract } = build(fixture());
    await writeFile(join(directory, "fixture.glb"), glb);
    await writeFile(join(directory, "fixture.json"), JSON.stringify(contract));
    const result = spawnSync("python3", ["-c", String.raw`
import importlib.util,json,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('hidden_collision',Path.cwd()/'scripts/unreal/hidden_collision.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
directory=Path(sys.argv[1]);contract=json.loads((directory/'fixture.json').read_text())
records={r['id']:r for r in contract['objects']}
parsed=module.read_glb_triangles((directory/'fixture.glb').read_bytes(),records)
assert len(parsed)==1 and len(next(iter(parsed.values())))==1
expected=[((0,0,0),(1,0,0),(0,1,0)),((1,0,0),(1,1,0),(0,1,0))]
reordered=[tuple(reversed(t)) for t in reversed(expected)]
assert module.triangle_error(expected,reordered)==0
substituted=[((0,0,0),(1,0,0),(1,1,0)),((0,0,0),(1,1,0),(0,1,0))]
for actual in [expected[:1],substituted,[tuple((x,y,z+.1) for x,y,z in t) for t in expected]]:
 try: module.triangle_error(expected,actual)
 except RuntimeError: pass
 else: raise AssertionError('Accepted changed native topology')
raw=bytearray((directory/'fixture.glb').read_bytes());raw[8]=0
try: module.read_glb_triangles(bytes(raw),records)
except RuntimeError: pass
else: raise AssertionError('Accepted invalid GLB size')
`, directory], { encoding: "utf8" });
    assert.equal(result.status, 0, result.stderr || result.error?.message);
  } finally { await rm(directory, { recursive: true, force: true }); }
});
