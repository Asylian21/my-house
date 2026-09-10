import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdir, readFile, rename, rm, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const VIEWPORT = "lib/twin-viewport-contract.ts";
const CONSTANTS = ["WALK_EYE_HEIGHT_M", "WALK_SPEED_MPS", "WALK_CAMERA", "WALK_SURFACE",
  "WALK_COLLISION_ELLIPSOID_M", "WALK_COLLISION_OFFSET_M"];
const sha = (bytes) => createHash("sha256").update(bytes).digest("hex");
const cm = (metres) => Number((metres * 100).toPrecision(15));
const mm = (metres) => Number((metres * 1000).toPrecision(15));
const finite = (value, label) => assert(Number.isFinite(value), `${label} must be finite`);

/** Read only literal declarations; never execute the renderer or evaluate source code. */
export function readWalkingConstants(source) {
  const file = ts.createSourceFile(VIEWPORT, source, ts.ScriptTarget.Latest, true);
  assert.equal(file.parseDiagnostics.length, 0, "Invalid viewport TypeScript");
  function literal(node) {
    if (ts.isNumericLiteral(node)) return Number(node.text);
    if (ts.isPrefixUnaryExpression(node) && node.operator === ts.SyntaxKind.MinusToken) return -literal(node.operand);
    if (ts.isObjectLiteralExpression(node)) {
      return Object.fromEntries(node.properties.map((property) => {
        assert(ts.isPropertyAssignment(property) && ts.isIdentifier(property.name), "Expected named numeric property");
        return [property.name.text, literal(property.initializer)];
      }));
    }
    if (ts.isCallExpression(node) && node.expression.getText(file) === "Object.freeze" && node.arguments.length === 1) {
      return literal(node.arguments[0]);
    }
    throw new Error(`Unsupported walking constant initializer: ${node.getText(file)}`);
  }
  const result = {};
  for (const statement of file.statements) {
    if (!ts.isVariableStatement(statement)) continue;
    for (const declaration of statement.declarationList.declarations) {
      const name = declaration.name.getText(file);
      if (!CONSTANTS.includes(name)) continue;
      assert(!(name in result), `Duplicate walking constant: ${name}`);
      assert(declaration.initializer, `Missing initializer: ${name}`);
      result[name] = literal(declaration.initializer);
    }
  }
  assert.deepEqual(Object.keys(result).sort(), [...CONSTANTS].sort(), "Missing walking source constants");
  return result;
}

/** OBJ is right handed Z-up mm; the native bridge flips plan Y and scales to cm. */
export function walkingBoundsToUnreal(bounds) {
  for (const key of ["min", "max"]) {
    assert(Array.isArray(bounds?.[key]) && bounds[key].length === 3, `Invalid bounds.${key}`);
    bounds[key].forEach((n) => finite(n, `bounds.${key}`));
  }
  bounds.min.forEach((n, i) => assert(n <= bounds.max[i], "Inverted source bounds"));
  return {
    min: [bounds.min[0] / 10, -bounds.max[1] / 10, bounds.min[2] / 10],
    max: [bounds.max[0] / 10, -bounds.min[1] / 10, bounds.max[2] / 10],
  };
}

// This is the exact render/archive rule in convert.py and validate.mjs.
function runtimeObject(object) {
  return object.enabled && !["odlesk vod", "kaustick", "odraz oblohy"].some((part) => object.name.toLowerCase().includes(part));
}

function reference(object) {
  assert(typeof object.sourceId === "string" && object.sourceId.length, `${object.id}: missing sourceId`);
  assert(Number.isSafeInteger(object.triangles) && object.triangles > 0, `${object.id}: invalid source triangles`);
  assert(Number.isSafeInteger(object.instances) && object.instances > 0, `${object.id}: invalid source instances`);
  return {
    objectId: object.id,
    sourceId: object.sourceId,
    entityId: object.metadata?.entityId ?? null,
    name: object.name,
    sourceBoundsMm: structuredClone(object.boundsMm),
    nativeBoundsCm: walkingBoundsToUnreal(object.boundsMm),
    sourceGeometry: { objectId: object.id, triangles: object.triangles, instances: object.instances },
  };
}

/** Pure manifest builder. It exports references to captured triangles, never new geometry. */
export function buildWalkingContract(scene, constants, provenance, { nativeCapsuleHalfHeightCm = 85 } = {}) {
  assert.equal(scene.units, "millimetres", "Walking requires the millimetre scene manifest");
  assert.equal(scene.coordinateSystem, "right-handed Z-up", "Unexpected source coordinate system");
  assert(Array.isArray(scene.objects), "Missing source objects");
  finite(scene.sceneCenterMm?.x, "sceneCenterMm.x");
  finite(scene.sceneCenterMm?.y, "sceneCenterMm.y");
  for (const key of ["sceneSha256", "viewportSha256", "writerSha256"]) {
    assert(/^[a-f0-9]{64}$/.test(provenance?.[key] ?? ""), `Missing ${key}`);
  }
  const source = structuredClone(constants);
  for (const name of CONSTANTS) {
    assert(name in source, `Missing ${name}`);
    for (const value of typeof source[name] === "object" ? Object.values(source[name]) : [source[name]]) finite(value, name);
  }
  const ellipsoid = source.WALK_COLLISION_ELLIPSOID_M;
  const offset = source.WALK_COLLISION_OFFSET_M;
  assert(ellipsoid.x > 0 && ellipsoid.y > 0 && ellipsoid.z > 0, "Invalid source ellipsoid");
  assert.equal(ellipsoid.x, ellipsoid.z, "Asymmetric ellipsoid needs a reviewed native capsule adaptation");
  assert.equal(offset.x, 0, "Nonvertical collider offset needs native review");
  assert.equal(offset.z, 0, "Nonvertical collider offset needs native review");
  const eyeHeightCm = cm(source.WALK_EYE_HEIGHT_M);
  const capsuleRadiusCm = cm(ellipsoid.x);
  finite(nativeCapsuleHalfHeightCm, "nativeCapsuleHalfHeightCm");
  assert(nativeCapsuleHalfHeightCm >= capsuleRadiusCm && nativeCapsuleHalfHeightCm * 2 > eyeHeightCm,
    "Native capsule must enclose the eye with positive head clearance");
  assert(eyeHeightCm > 0 && source.WALK_SURFACE.maxStepUpM > 0 && source.WALK_SURFACE.maxDropM > 0,
    "Invalid source movement distances");
  assert(Object.values(source.WALK_SPEED_MPS).every((n) => n > 0), "Invalid source walking speed");
  assert.deepEqual(Object.keys(source.WALK_SPEED_MPS).sort(), ["boost", "normal", "precision"]);

  const ids = new Set();
  const walkSurfaceIds = new Set();
  const walkSurfaces = [], staticBlockers = [], capturedClosedBlockers = [];
  let excludedDynamicMembers = 0, archivedObjects = 0;
  for (const object of scene.objects) {
    assert(typeof object.id === "string" && /^DOM_\d+$/.test(object.id), "Invalid canonical object ID");
    assert(!ids.has(object.id), `Duplicate source object ID: ${object.id}`);
    ids.add(object.id);
    assert.equal(typeof object.enabled, "boolean", `${object.id}: missing enabled state`);
    assert.equal(typeof object.name, "string", `${object.id}: missing source name`);
    if (!runtimeObject(object)) { archivedObjects += 1; continue; }
    const metadata = object.metadata ?? {};
    assert.equal(typeof metadata.babylonCheckCollisions, "boolean",
      `${object.id}: missing captured babylonCheckCollisions; re-export the source scene`);
    for (const key of ["walkSurface", "cameraOccluder", "dynamicCameraOccluder"]) {
      assert(metadata[key] === undefined || typeof metadata[key] === "boolean", `${object.id}: invalid ${key}`);
    }
    const dynamic = metadata.dynamicCameraOccluder === true || Boolean(metadata.doorMotion);
    const collision = metadata.babylonCheckCollisions || metadata.walkSurface === true || metadata.cameraOccluder === true;
    if (dynamic && !collision) { excludedDynamicMembers += 1; continue; }
    if (!collision) continue;
    const ref = { ...reference(object), collisionReasons: [
      ...(metadata.babylonCheckCollisions ? ["babylon-check-collisions"] : []),
      ...(metadata.walkSurface === true ? ["explicit-walk-surface"] : []),
      ...(metadata.cameraOccluder === true ? ["explicit-camera-occluder"] : []),
    ] };
    if (dynamic) {
      assert(typeof metadata.doorId === "string" && metadata.doorId.length, `${object.id}: dynamic blocker lacks doorId`);
      assert(metadata.doorMotion === undefined || ["HINGED", "SLIDING", "OVERHEAD"].includes(metadata.doorMotion),
        `${object.id}: unreviewed door motion`);
      capturedClosedBlockers.push({ ...ref, doorId: metadata.doorId, motion: metadata.doorMotion ?? null,
        subject: metadata.doorSubject ?? null, cameraOccluder: metadata.cameraOccluder === true,
        walkSurface: metadata.walkSurface === true, requiredState: "captured-closed", collisionRequired: true,
        runtimeTags: ["BreziClosedBlocker", `BreziSourceObjectId=${object.id}`, `BreziSourceId=${object.sourceId}`, `BreziDoorId=${metadata.doorId}`] });
    } else {
      staticBlockers.push({ ...ref, cameraOccluder: metadata.cameraOccluder === true,
        walkSurface: metadata.walkSurface === true, babylonCheckCollisions: metadata.babylonCheckCollisions, collisionRequired: true });
    }
    if (metadata.walkSurface === true) {
      assert(typeof metadata.walkSurfaceId === "string" && metadata.walkSurfaceId.length, `${object.id}: missing walkSurfaceId`);
      assert(!walkSurfaceIds.has(metadata.walkSurfaceId), `Duplicate walkSurfaceId: ${metadata.walkSurfaceId}`);
      walkSurfaceIds.add(metadata.walkSurfaceId);
      assert(["interior", "exterior", "terrain"].includes(metadata.walkSurfaceKind), `${object.id}: missing walkSurfaceKind`);
      finite(metadata.walkSurfaceElevationOffsetM, `${object.id}: walkSurfaceElevationOffsetM`);
      const supportOffsetCm = cm(metadata.walkSurfaceElevationOffsetM);
      walkSurfaces.push({ ...ref, walkSurfaceId: metadata.walkSurfaceId, kind: metadata.walkSurfaceKind,
        supportOffsetCm, sourceElevationOffsetM: metadata.walkSurfaceElevationOffsetM,
        sourceElevationOffsetMm: mm(metadata.walkSurfaceElevationOffsetM),
        supportTranslationCm: [0, 0, supportOffsetCm],
        dynamic, doorId: metadata.doorId ?? null,
        query: "source-triangle-hit-plus-authored-vertical-offset",
        runtimeTags: ["BreziWalkSurface", `BreziSourceObjectId=${object.id}`, `BreziSourceId=${object.sourceId}`,
          `BreziWalkSurfaceId=${metadata.walkSurfaceId}`],
        supportRuntimeTags: supportOffsetCm === 0 ? [] : ["BreziWalkSupportProxy", `BreziSupportOffsetCm=${supportOffsetCm}`] });
    }
  }
  assert(walkSurfaces.length > 0, "No source walk surfaces");
  return {
    schemaVersion: 1,
    status: "source-walking-contract-exported",
    coordinateSystem: "unreal-centimeters",
    sourceCoordinateSystem: "right-handed Z-up millimetres",
    coordinateTransform: "source OBJ [x,y,z] mm -> Unreal [x/10,-y/10,z/10] cm",
    sceneCenterMm: structuredClone(scene.sceneCenterMm),
    layoutId: scene.layoutId,
    provenance: { ...provenance, viewportSource: VIEWPORT, sourceObjSha256: scene.objSha256 ?? null },
    eyeHeightCm, capsuleRadiusCm, capsuleHalfHeightCm: nativeCapsuleHalfHeightCm,
    speedsCmPerSecond: Object.fromEntries(Object.entries(source.WALK_SPEED_MPS).map(([key, value]) => [key, cm(value)])),
    maxStepHeightCm: cm(source.WALK_SURFACE.maxStepUpM), maxDropCm: cm(source.WALK_SURFACE.maxDropM),
    probeHeadroomCm: cm(source.WALK_SURFACE.probeHeadroomM),
    sourceCollider: {
      kind: "ellipsoid", ellipsoidRadiiCm: [cm(ellipsoid.x), cm(ellipsoid.z), cm(ellipsoid.y)],
      centerOffsetCm: [cm(offset.x), cm(offset.z), cm(offset.y)],
      topAboveFloorCm: cm(offset.y) + cm(ellipsoid.y), bottomAboveFloorCm: cm(offset.y) - cm(ellipsoid.y),
    },
    nativeAdaptation: {
      id: "NATIVE-CHARACTER-CAPSULE-20260908", kind: "capsule-approximation-of-source-ellipsoid",
      reason: `ACharacter sweeps a capsule. Its floor-based height includes the ${eyeHeightCm} cm source eye; the source ellipsoid ends at ${cm(offset.y + ellipsoid.y)} cm.`,
      sourceHalfHeightCm: cm(ellipsoid.y), sourceCenterHeightCm: cm(offset.y),
      nominalCenterHeightCm: nativeCapsuleHalfHeightCm, eyeOffsetFromCenterCm: eyeHeightCm - nativeCapsuleHalfHeightCm,
      floorClearancePolicy: "engine-floor-gap-compensated-in-camera",
      nativeHeadClearanceCm: 2 * nativeCapsuleHalfHeightCm - eyeHeightCm, geometricallyIdentical: false,
    },
    sourceConstants: source,
    walkSurfaces, staticBlockers, capturedClosedBlockers,
    summary: { sourceObjects: scene.objects.length, archivedObjects, walkSurfaces: walkSurfaces.length,
      offsetSurfaces: walkSurfaces.filter((s) => s.supportOffsetCm !== 0).length, staticBlockers: staticBlockers.length,
      capturedClosedBlockers: capturedClosedBlockers.length,
      capturedCheckCollisionObjects: scene.objects.filter((o) => runtimeObject(o) && o.metadata?.babylonCheckCollisions).length,
      closedDoorOrHatchGroups: new Set(capturedClosedBlockers.map((b) => b.doorId)).size, excludedDynamicMembers },
    collisionContract: {
      geometry: "existing-runtime-GLB-source-triangles", boundsAreBroadPhaseOnly: true,
      blockerEligibility: "captured-babylon-checkCollisions-or-explicit-walkSurface-or-cameraOccluder",
      skippedSourceColliders: structuredClone((scene.skipped ?? []).filter((r) => r.enabled && r.babylonCheckCollisions)),
      visualMeshesMustRemainUnchanged: true,
      offsetsApplyTo: "support-query-hit-height-or-exact-translated-source-triangles",
      floorEligibility: "only-explicit-walkSurfaces", closedBlockerPolicy: "preserve-captured-transforms-and-enable-collision",
      doorAnimationExported: false, doorProgressSerializedByScene: false,
      closedStateEvidence: "fresh-scene capture; AnimatedDoorController defaults initiallyOpen to false; hatchProgress starts at zero",
    },
    nativeValidation: { characterMovementImplemented: false, collisionQueriesVerified: false, runtimeWalkingVerified: false },
    pending: [
      "Bind source object IDs to existing native mesh/component assets and retain serialized runtime tags.",
      "Configure ACharacter capsule, eye offset, speeds, step and source surface/drop policy; verify swept collision and low ceilings.",
      "Apply every authored support offset to queries or exact source-mesh support components; do not use AABBs as floors.",
      "Enable every captured closed door/hatch blocker; animated door progress/transforms require a separate source export and native implementation.",
      "Review skipped hidden source colliders separately; this contract does not claim they were exported as render meshes.",
      "Verify floor eligibility, thresholds, deck gaps, pool/shaft voids and transitions in the native runtime before claiming walk support.",
    ],
  };
}

/** File API for the export pipeline; all captured source hashes must still match. */
export async function exportWalking({ rootDir = ROOT, scenePath = resolve(rootDir, "output/unreal/geometry/scene.json"),
  outputPath = resolve(dirname(scenePath), "walking.json"), nativeCapsuleHalfHeightCm = 85 } = {}) {
  const bytes = await readFile(scenePath), scene = JSON.parse(bytes);
  assert(scene.sourceFiles && typeof scene.sourceFiles === "object", "Missing source hashes");
  assert(scene.sourceFiles[VIEWPORT], "Scene lacks the viewport source checksum");
  for (const [name, digest] of Object.entries(scene.sourceFiles)) {
    const path = resolve(rootDir, name), rel = relative(rootDir, path);
    assert(!isAbsolute(rel) && rel !== ".." && !rel.startsWith("../"), `Source path escapes project: ${name}`);
    assert.equal(sha(await readFile(path)), digest, `Source changed since scene capture: ${name}`);
  }
  assert.equal(sha(await readFile(resolve(dirname(scenePath), "dom-mm.obj"))), scene.objSha256, "Source OBJ checksum mismatch");
  const viewport = await readFile(resolve(rootDir, VIEWPORT));
  const writer = await readFile(fileURLToPath(import.meta.url));
  const contract = buildWalkingContract(scene, readWalkingConstants(viewport.toString("utf8")), {
    sceneSha256: sha(bytes), viewportSha256: sha(viewport), writerSha256: sha(writer),
  }, { nativeCapsuleHalfHeightCm });
  // Guard the validation-to-write window; never bless an export from changed bytes.
  assert.equal(sha(await readFile(scenePath)), contract.provenance.sceneSha256, "Scene changed during walking export");
  const output = `${JSON.stringify(contract, null, 2)}\n`, temporary = `${outputPath}.${process.pid}.tmp`;
  await mkdir(dirname(outputPath), { recursive: true });
  try { await writeFile(temporary, output); await rename(temporary, outputPath); }
  finally { await rm(temporary, { force: true }); }
  return { outputPath, sha256: sha(output), contract };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const directory = resolve(ROOT, process.env.UNREAL_OUTPUT ?? "output/unreal/geometry");
  const result = await exportWalking({ scenePath: resolve(directory, "scene.json"),
    outputPath: resolve(process.env.UNREAL_WALKING_OUTPUT ?? resolve(directory, "walking.json")) });
  console.log(JSON.stringify({ status: result.contract.status, outputPath: result.outputPath, sha256: result.sha256,
    summary: result.contract.summary, nativeValidation: result.contract.nativeValidation }, null, 2));
}
