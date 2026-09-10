// Separate source-triangle collision supplement; never append to the visible OBJ.
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
export const collisionId = (sourceId) => `COLL_${sha(Buffer.from(sourceId, "utf8")).slice(0, 20)}`;
const transform = (p, m) => [0, 1, 2].map((axis) => p[0] * m[axis] + p[1] * m[axis + 4] + p[2] * m[axis + 8] + m[axis + 12]);

/** Export exact captured source triangle hulls; no box fitting or convex approximation. */
export function buildHiddenCollisionGlb(scene, capture, sourceManifestSha256) {
  assert.equal(capture.mainObjSha256, scene.objSha256, "Auxiliary capture does not belong to the canonical OBJ");
  assert(/^[a-f0-9]{64}$/.test(sourceManifestSha256), "Missing exact source manifest hash");
  const expected = scene.skipped.filter((r) => r.enabled && r.babylonCheckCollisions);
  assert(expected.every((r) => r.reason === "hidden-proxy-or-collider"), "An enabled source collider was skipped for another reason; review required");
  const expectedIds = new Set(expected.map((r) => r.sourceId));
  assert.equal(expectedIds.size, expected.length, "Ambiguous hidden source ID");
  assert.equal(capture.colliders.length, expected.length, "Hidden collider coverage differs");
  const capturedIds = new Set(capture.colliders.map((r) => r.sourceId));
  assert.equal(capturedIds.size, capture.colliders.length, "Duplicate hidden source capture");
  assert(expected.every((r) => capturedIds.has(r.sourceId)), "Missing or unregistered hidden source collider");
  const document = { asset: { version: "2.0", generator: "Brezi exact source collision supplement" },
    scene: 0, scenes: [{ nodes: [] }], nodes: [], meshes: [], accessors: [], bufferViews: [], buffers: [] };
  const blocks = [], records = [], used = new Set(); let byteLength = 0, maxQuantizationErrorMm = 0;
  function append(bytes, componentType, type, count, min, max, target) {
    const aligned = Buffer.alloc(Math.ceil(bytes.length / 4) * 4); bytes.copy(aligned);
    const view = document.bufferViews.length;
    document.bufferViews.push({ buffer: 0, byteOffset: byteLength, byteLength: bytes.length, target });
    blocks.push(aligned); byteLength += aligned.length;
    const index = document.accessors.length;
    document.accessors.push({ bufferView: view, componentType, type, count, ...(min ? { min, max } : {}) });
    return index;
  }
  for (const source of [...capture.colliders].sort((a, b) => a.sourceId < b.sourceId ? -1 : a.sourceId > b.sourceId ? 1 : 0)) {
    const id = collisionId(source.sourceId);
    assert(!used.has(id), "Stable collision ID hash collision"); used.add(id);
    assert(source.sourceEnabled === true && source.sourceHidden === true && source.sourceCheckCollisions === true
      && source.sourceArchived === false, "Only enabled hidden non-archive source colliders qualify");
    assert(source.metadata?.walkSurface !== true, "Hidden floor needs a separate reviewed floor contract");
    assert(Array.isArray(source.positions) && source.positions.length >= 9 && source.positions.length % 3 === 0
      && source.positions.every(Number.isFinite), "Invalid source vertices");
    assert(Array.isArray(source.indices) && source.indices.length && source.indices.length % 3 === 0
      && source.indices.every((v) => Number.isInteger(v) && v >= 0 && v < source.positions.length / 3), "Invalid source indices");
    assert(Array.isArray(source.transforms) && source.transforms.length > 0
      && source.transforms.every((m) => m.length === 16 && m.every(Number.isFinite)), "Invalid source instance transforms");
    assert(source.transforms.every((m) => m[3] === 0 && m[7] === 0 && m[11] === 0 && m[15] === 1),
      "Collision transforms must be affine");
    assert(Array.isArray(source.normals) && source.normals.length === source.positions.length && source.normals.every(Number.isFinite)
      && Array.isArray(source.normalTransforms) && source.normalTransforms.length === source.transforms.length
      && source.normalTransforms.every((m) => m.length === 16 && m.every(Number.isFinite)), "Invalid source normals or normal transforms");
    const points = [], indices = [], low = [Infinity, Infinity, Infinity], high = [-Infinity, -Infinity, -Infinity];
    const sourceLow = [...low], sourceHigh = [...high];
    for (const [instance, matrix] of source.transforms.entries()) {
      const offset = points.length / 3, exactPoints = [];
      for (let i = 0; i < source.positions.length; i += 3) {
        const exact = transform(source.positions.slice(i, i + 3), matrix); exactPoints.push(exact);
        exact.forEach((v, axis) => {
          const quantized = Math.fround(v); assert(Number.isFinite(quantized), "Float32 coordinate overflow");
          maxQuantizationErrorMm = Math.max(maxQuantizationErrorMm, Math.abs(v - quantized) * 1000);
          sourceLow[axis] = Math.min(sourceLow[axis], v); sourceHigh[axis] = Math.max(sourceHigh[axis], v);
          low[axis] = Math.min(low[axis], quantized); high[axis] = Math.max(high[axis], quantized); points.push(quantized);
        });
      }
      for (let i = 0; i < source.indices.length; i += 3) {
        const face = source.indices.slice(i, i + 3), [a, b, c] = face.map((index) => exactPoints[index]);
        const u = b.map((v, axis) => v - a[axis]), v = c.map((value, axis) => value - a[axis]);
        const cross = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]];
        assert(cross.some((value) => value !== 0), "Degenerate authored collision triangle requires review");
        const nm = source.normalTransforms?.[instance], normal = source.normals?.slice(face[0] * 3, face[0] * 3 + 3);
        assert(nm?.length === 16 && normal?.length === 3, "Collision winding requires captured source normals");
        const n = [0, 1, 2].map((axis) => normal[0]*nm[axis] + normal[1]*nm[axis+4] + normal[2]*nm[axis+8]);
        if (cross.reduce((sum, value, axis) => sum + value*n[axis], 0) < 0) [face[1], face[2]] = [face[2], face[1]];
        indices.push(...face.map((index) => index + offset));
      }
    }
    const positions = Buffer.alloc(points.length * 4), indexBytes = Buffer.alloc(indices.length * 4);
    points.forEach((v, i) => positions.writeFloatLE(v, i * 4)); indices.forEach((v, i) => indexBytes.writeUInt32LE(v, i * 4));
    const positionAccessor = append(positions, 5126, "VEC3", points.length / 3, low, high, 34962);
    const indexAccessor = append(indexBytes, 5125, "SCALAR", indices.length, null, null, 34963);
    const meshIndex = document.meshes.length;
    document.meshes.push({ name: id, primitives: [{ attributes: { POSITION: positionAccessor }, indices: indexAccessor, mode: 4 }] });
    document.scenes[0].nodes.push(document.nodes.length);
    document.nodes.push({ name: id, mesh: meshIndex, extras: { source_collision_id: id, source_id: source.sourceId,
      collision_only: true, render_authorized: false, source_check_collisions: true, source_enabled: true } });
    records.push({ id, sourceId: source.sourceId, sourceName: source.name, instances: source.transforms.length,
      vertices: points.length / 3, triangles: indices.length / 3,
      nativeBoundsCm: { min: [sourceLow[0]*100, sourceLow[2]*100, sourceLow[1]*100],
        max: [sourceHigh[0]*100, sourceHigh[2]*100, sourceHigh[1]*100] },
      capturedTransforms: source.transforms, sourceGeometrySha256: sha(JSON.stringify({ positions: source.positions,
        indices: source.indices, transforms: source.transforms })), sourceMetadata: source.metadata,
      runtimeTags: ["BreziHiddenCollision", `BreziSourceObjectId=${id}`, `BreziSourceId=${source.sourceId}`],
      nativeRole: "blocking-only-never-a-floor", sourceShapePolicy: "exact authored hull, including deliberately conservative navigation extents",
      dynamicSource: source.metadata?.vehicleCollider === true || source.metadata?.dynamicCameraOccluder === true || Boolean(source.metadata?.doorMotion),
      dynamicNativePolicy: "frozen captured transform; runtime vehicle/door motion is outside this supplement" });
  }
  assert(maxQuantizationErrorMm <= 0.5, "Supplement quantization exceeds canonical geometry tolerance");
  document.buffers.push({ byteLength });
  const rawJson = Buffer.from(JSON.stringify(document)), json = Buffer.alloc(Math.ceil(rawJson.length / 4) * 4, 0x20); rawJson.copy(json);
  const header = Buffer.alloc(20), binHeader = Buffer.alloc(8);
  header.write("glTF"); header.writeUInt32LE(2, 4); header.writeUInt32LE(28 + json.length + byteLength, 8);
  header.writeUInt32LE(json.length, 12); header.write("JSON", 16); binHeader.writeUInt32LE(byteLength); binHeader.write("BIN\0", 4);
  const glb = Buffer.concat([header, json, binHeader, ...blocks]);
  return { glb, contract: { schemaVersion: 1, status: "auxiliary-source-exported-native-pending", sourceManifestSha256,
    mainObjSha256: scene.objSha256, supplementSha256: sha(glb), namespace: "COLL_", coordinateSystem: "unreal-centimeters",
    gltfToUnreal: "[100*x,100*z,100*y]", maxQuantizationErrorMm, objects: records,
    verification: { canonicalGeometryModified: false, materialsExported: false, nativeImported: false, collisionQueriesVerified: false } } };
}
