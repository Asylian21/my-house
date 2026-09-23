import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const pointInRect = (p, r) => p[0] >= r[0] && p[0] <= r[2] && p[1] >= r[1] && p[1] <= r[3];
const distance = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
const same = (a, b) => distance(a, b) < 0.001;
const midpoint = bounds => bounds.min.map((n, i) => (n + bounds.max[i]) / 2);
const bounds = values => ({ min: [0, 1, 2].map(i => Math.min(...values.map(v => v.min[i]))),
  max: [0, 1, 2].map(i => Math.max(...values.map(v => v.max[i]))) });
const cmBounds = b => ({ min: [b.min[0] / 10, -b.max[1] / 10, b.min[2] / 10], max: [b.max[0] / 10, -b.min[1] / 10, b.max[2] / 10] });
export function transformBounds(b, m) {
  assert.equal(m.length, 16);
  const corners = [];
  for (const x of [b.min[0], b.max[0]]) for (const y of [b.min[1], b.max[1]]) for (const z of [b.min[2], b.max[2]]) {
    const p = [0, 1, 2].map(i => m[i] * x + m[4 + i] * y + m[8 + i] * z + m[12 + i]);
    corners.push({ min: p, max: p });
  }
  return bounds(corners);
}
const blocksPoint = (p, b, radius) => p[0] > b.min[0] - radius && p[0] < b.max[0] + radius
  && p[1] > b.min[1] - radius && p[1] < b.max[1] + radius;

export function insidePolygon(point, polygon) {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const a = polygon[i], b = polygon[j];
    if ((a[1] > point[1]) !== (b[1] > point[1]) && point[0] < (b[0] - a[0]) * (point[1] - a[1]) / (b[1] - a[1]) + a[0]) inside = !inside;
  }
  return inside;
}

/** A conservative planning aid only. Actual native capsule samples establish reachability. */
export function planWalkPath(start, goal, { contains, obstacles, radiusCm, gridCm = 5 }) {
  const blocked = p => obstacles.some(b => p[0] > b.min[0] - radiusCm && p[0] < b.max[0] + radiusCm
    && p[1] > b.min[1] - radiusCm && p[1] < b.max[1] + radiusCm);
  const clear = p => contains(p) && !blocked(p);
  const segment = (a, b) => {
    const steps = Math.max(1, Math.ceil(distance(a, b) / (gridCm / 2)));
    for (let i = 0; i <= steps; ++i) if (!clear([a[0] + (b[0] - a[0]) * i / steps, a[1] + (b[1] - a[1]) * i / steps])) return false;
    return true;
  };
  assert(clear(start), `Blocked path start ${JSON.stringify(start)}`);
  assert(clear(goal), `Blocked path goal ${JSON.stringify(goal)}`);
  if (segment(start, goal)) return [start, goal];
  // The grid is local to the exact start; add the exact goal only after a clear segment.
  const key = (x, y) => `${x},${y}`, point = (x, y) => [start[0] + x * gridCm, start[1] + y * gridCm];
  const open = [{ x: 0, y: 0, cost: 0, estimate: distance(start, goal), prior: null }], best = new Map([[key(0, 0), 0]]);
  let found;
  for (let visited = 0; open.length && visited < 80000; ++visited) {
    let at = 0;
    for (let i = 1; i < open.length; ++i) if (open[i].estimate < open[at].estimate) at = i;
    const current = open.splice(at, 1)[0], here = point(current.x, current.y);
    if (distance(here, goal) <= gridCm * 2 && segment(here, goal)) { found = current; break; }
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]]) {
      const x = current.x + dx, y = current.y + dy, next = point(x, y), cost = current.cost + Math.hypot(dx, dy) * gridCm;
      if (cost >= (best.get(key(x, y)) ?? Infinity) || !segment(here, next)) continue;
      best.set(key(x, y), cost); open.push({ x, y, cost, estimate: cost + distance(next, goal), prior: current });
    }
  }
  assert(found, `No conservative source path from ${JSON.stringify(start)} to ${JSON.stringify(goal)}`);
  const route = [goal];
  for (let entry = found; entry; entry = entry.prior) route.unshift(point(entry.x, entry.y));
  const simplified = [route[0]];
  for (let i = 0; i < route.length - 1;) {
    let end = route.length - 1;
    while (end > i + 1 && !segment(route[i], route[end])) --end;
    simplified.push(route[end]); i = end;
  }
  return simplified;
}

export function buildWalkthroughContract(scene, walking, hidden, provenance) {
  assert.deepEqual(scene.activeDesign, { variant: 'C', heatingLayout: 'B', livingLayout: 'B' });
  assert.equal(scene.units, 'millimetres'); assert.equal(scene.coordinateSystem, 'right-handed Z-up');
  assert.equal(walking.provenance.sceneSha256, provenance.sceneSha256);
  assert.equal(hidden.sourceManifestSha256, provenance.sceneSha256);
  assert.equal(hidden.mainObjSha256, scene.objSha256);
  assert(scene.doorMotion?.closedCapture, 'Source door poses are required');
  const center = scene.sceneCenterMm;
  const point = p => [(p.x - center.x) / 10, (center.y - p.y) / 10];
  const rect = r => [(r.x0 - center.x) / 10, (center.y - r.y1) / 10, (r.x1 - center.x) / 10, (center.y - r.y0) / 10];
  const nodes = scene.interior.rooms.map(room => ({ id: room.id, label: room.name, kind: 'room', rectsCm: room.rectsMm.map(rect),
    standingPointCm: point(room.standingPointMm), source: `scene.interior.rooms[id=${room.id}]` }));
  for (const terrace of scene.terraces) nodes.push({ id: terrace.id, label: terrace.label, kind: 'terrace', rectsCm: terrace.rectsMm.map(rect), source: `scene.terraces[id=${terrace.id}]` });
  for (const name of ['entry', 'driveway', 'sideEntryApproach']) {
    const surface = scene.surfaces[name];
    nodes.push({ id: surface.id, label: name, kind: 'exterior-approach', polygonCm: surface.polygonMm.map(point), source: `scene.surfaces.${name}` });
  }
  assert.equal(new Set(nodes.map(n => n.id)).size, nodes.length, 'Duplicate coverage region');
  const node = id => { const n = nodes.find(n => n.id === id); assert(n, `Missing region ${id}`); return n; };
  const contains = (n, p) => n.rectsCm?.some(r => pointInRect(p, r)) || (n.polygonCm && insidePolygon(p, n.polygonCm));
  const radiusCm = walking.capsuleRadiusCm + 3;
  const obstacles = [
    ...scene.objects.filter(o => o.enabled && !o.metadata?.doorId && !o.metadata?.walkSurface
      && (o.metadata?.babylonCheckCollisions || o.metadata?.cameraOccluder)).map(o => ({ ...cmBounds(o.boundsMm), id: o.id, sourceId: o.sourceId })),
    ...hidden.objects.map(o => ({ ...o.nativeBoundsCm, id: o.id, sourceId: o.sourceId })),
  ].filter(b => b.min[2] < walking.capsuleHalfHeightCm * 2 && b.max[2] > walking.maxStepHeightCm);
  const blocked = p => obstacles.filter(b => blocksPoint(p, b, radiusCm));
  const movingDoors = scene.doorMotion.doors.filter(d => d.architectural).map(d => ({ ...d,
    closed: d.members.filter(m => m.collision).map(m => m.closedBoundsCm),
    open: d.members.filter(m => m.collision).map(m => transformBounds(m.closedBoundsCm, m.poses.at(-1))),
    sweep: d.members.filter(m => m.collision).flatMap(m => m.poses.map(pose => transformBounds(m.closedBoundsCm, pose))) }));
  const edges = [];
  function door(id, from, to, axis) {
    node(from); node(to);
    const leaves = scene.objects.filter(o => o.enabled && o.metadata?.doorId === id && o.metadata.babylonCheckCollisions);
    assert(leaves.length, `Door ${id} has no source physical leaf`);
    const motion = movingDoors.find(d => d.id === id); assert(motion, `Door ${id} has no source motion`);
    const b = bounds(leaves.map(o => cmBounds(o.boundsMm))), middle = midpoint(b), normalAxis = axis === 'X' ? 1 : 0;
    const candidates = [];
    for (let offset = 85; offset >= 35; offset -= 5) for (const sign of [-1, 1]) {
      const p = middle.slice(0, 2); p[normalAxis] += sign * offset; candidates.push(p);
    }
    const openClear = p => motion.open.every(b => b.min[2] >= walking.capsuleHalfHeightCm * 2 || b.max[2] <= walking.maxStepHeightCm || !blocksPoint(p, b, radiusCm));
    const fromPoint = candidates.find(p => contains(node(from), p) && !blocked(p).length && openClear(p));
    const toPoint = candidates.find(p => contains(node(to), p) && !blocked(p).length && openClear(p));
    assert(fromPoint && toPoint && !same(fromPoint, toPoint), `Door ${id} approach is not on opposite source regions`);
    edges.push({ id, kind: 'door', from, to, fromPointCm: fromPoint, toPointCm: toPoint, closedBoundsCm: b,
      closedObjectIds: scene.objects.filter(o => o.enabled && o.metadata?.doorId === id && (o.metadata.babylonCheckCollisions || o.metadata.cameraOccluder)).map(o => o.id),
      sourceIds: leaves.map(o => o.sourceId), motion: leaves[0].metadata.doorMotion });
  }
  for (const d of scene.interior.doors) door(d.id, d.fromRoomId, d.toRoomId, d.axis);
  for (const args of [
    ['FRONT-ENTRY', 'ROOM-1-01', scene.surfaces.entry.id, 'X'],
    ['EAST-03', 'ROOM-1-07', scene.surfaces.sideEntryApproach.id, 'Y'],
    ['LOGGIA-DOOR', 'ROOM-1-12', 'TERR-D1-GARDEN', 'X'],
    ['GARDEN-02', 'ROOM-1-10', 'TERR-D1-GARDEN', 'X'],
    ['WING-WEST-01', 'ROOM-1-03', 'TERR-D1-WING', 'Y'],
    ['GARAGE-DOOR', 'ROOM-1-12', scene.surfaces.driveway.id, 'X'],
  ]) door(...args);
  assert.deepEqual(edges.map(e => e.id).sort(), movingDoors.map(d => d.id).sort(), 'Architectural motion inventory differs from portal coverage');
  // Exact common rectangle boundaries establish open connections, never guessed wall openings.
  function openEdge(from, to) {
    let aperture;
    for (const a of node(from).rectsCm) for (const b of node(to).rectsCm) {
      for (const axis of [0, 1]) {
        const other = 1 - axis, low = Math.max(a[other], b[other]), high = Math.min(a[other + 2], b[other + 2]);
        if (high - low < walking.capsuleRadiusCm * 2 + 10) continue;
        for (const [sideA, sideB] of [[axis, axis + 2], [axis + 2, axis]]) {
          if (Math.abs(a[sideA] - b[sideB]) > 0.001) continue;
          const mid = [], pa = [], pb = []; mid[axis] = a[sideA]; mid[other] = (low + high) / 2;
          pa[other] = pb[other] = mid[other]; pa[axis] = mid[axis] + (sideA === axis ? 60 : -60); pb[axis] = mid[axis] - (pa[axis] - mid[axis]);
          if (contains(node(from), pa) && contains(node(to), pb)) aperture = { pa, pb };
        }
      }
    }
    assert(aperture, `No source open boundary ${from} -> ${to}`);
    edges.push({ id: `OPEN:${from}:${to}`, kind: 'open-passage', from, to, fromPointCm: aperture.pa, toPointCm: aperture.pb });
  }
  openEdge('ROOM-1-02', 'ROOM-1-03');
  openEdge('TERR-D1-GARDEN', 'TERR-D1-WING');
  openEdge('TERR-D1-WING', 'TERR-D1-PORCH');
  const startNode = node('ROOM-1-03');
  const sofa = scene.objects.filter(o => o.sourceId === 'LIVING-103-SOFA-L · TAILORED · hlavný modul · čalúnený rám');
  assert.equal(sofa.length, 1, 'Unique current B sofa required');
  const start = [sofa[0].boundsMm.min[0] / 10 - 75, -(sofa[0].boundsMm.min[1] / 10 - 40)];
  assert(contains(startNode, start) && blocked(start).length === 0, 'Current living arrival is obstructed');
  const steps = [], visitedEdges = new Set(), visitedNodes = new Set();
  const openDoors = new Set();
  const stageObstacles = () => [...obstacles, ...movingDoors.flatMap(d => openDoors.has(d.id) ? d.open : d.closed)
    .filter(b => b.min[2] < walking.capsuleHalfHeightCm * 2 && b.max[2] > walking.maxStepHeightCm)];
  let current = start;
  function travel(n, target, suffix) {
    let path;
    try { path = planWalkPath(current, target, { contains: p => contains(n, p), obstacles: stageObstacles(), radiusCm }); }
    catch (error) { throw new Error(`${n.id} ${suffix}: ${error.message}; start obstacles=${blocked(current).map(b => b.sourceId)}; goal obstacles=${blocked(target).map(b => b.sourceId)}`, { cause: error }); }
    for (const p of path.slice(1)) if (!same(current, p)) {
      steps.push({ id: `step-${steps.length}`, kind: 'move', regionId: n.id, targetCm: [...p, 0], toleranceCm: 5 }); current = p;
    }
  }
  function visit(id) {
    const n = node(id);
    if (!visitedNodes.has(id) && n.kind === 'room' && id !== startNode.id) {
      const candidates = [n.standingPointCm];
      for (let offset = 5; offset <= 150; offset += 5) for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]]) {
        candidates.push([n.standingPointCm[0] + offset * dx, n.standingPointCm[1] + offset * dy]);
      }
      const selected = candidates.find(p => contains(n, p) && !blocked(p).length);
      assert(selected, `No unblocked authored-room standing point for ${id}`);
      n.visitPointCm = selected; n.visitPointDerivation = 'nearest clear 5 cm source-bounds candidate to authored standing point';
      travel(n, selected, 'room-depth-coverage');
    }
    visitedNodes.add(id);
    steps.push({ id: `step-${steps.length}`, kind: 'visit', regionId: id, targetCm: [...current, 0] });
    for (const edge of edges.filter(e => e.from === id || e.to === id)) {
      if (visitedEdges.has(edge.id)) continue;
      visitedEdges.add(edge.id);
      const forward = edge.from === id, next = forward ? edge.to : edge.from;
      const a = forward ? edge.fromPointCm : edge.toPointCm, b = forward ? edge.toPointCm : edge.fromPointCm;
      travel(n, a, edge.id);
      if (edge.kind === 'door') {
        const motion = movingDoors.find(d => d.id === edge.id), interaction = motion.interactionPointCm;
        const candidates = [a];
        for (let offset = 5; offset <= 160; offset += 5) for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]]) candidates.push([a[0] + offset * dx, a[1] + offset * dy]);
        const safe = candidates.filter(p => contains(n, p) && distance(p, interaction) < scene.doorMotion.interaction.maxDistanceM * 100 - 10
          && !stageObstacles().some(b => blocksPoint(p, b, radiusCm))
          && !motion.sweep.some(b => b.min[2] < walking.capsuleHalfHeightCm * 2 && b.max[2] > walking.maxStepHeightCm && blocksPoint(p, b, radiusCm + 5)));
        let retreat, returning;
        for (const candidate of safe.slice(0, 80)) {
          try {
            retreat = planWalkPath(a, candidate, { contains: p => contains(n, p), obstacles: stageObstacles(), radiusCm });
            openDoors.add(edge.id);
            returning = planWalkPath(candidate, a, { contains: p => contains(n, p), obstacles: stageObstacles(), radiusCm });
            break;
          } catch { openDoors.delete(edge.id); retreat = returning = null; }
        }
        assert(retreat && returning, `No safe E interaction retreat for ${edge.id} from ${id}`);
        steps.push({ id: `step-${steps.length}`, kind: 'door', doorId: edge.id, regionId: id,
          targetCm: [...b, 0], approachCm: [...a, 0], closedObjectIds: edge.closedObjectIds, closedBoundsCm: edge.closedBoundsCm,
          interactionPointCm: interaction, retreatPathCm: retreat.map(p => [...p, 0]), returnPathCm: returning.slice(1).map(p => [...p, 0]) });
      }
      steps.push({ id: `step-${steps.length}`, kind: 'move', portalId: edge.id, regionId: next, targetCm: [...b, 0], toleranceCm: 5 }); current = b;
      visit(next);
      travel(node(next), b, `return ${edge.id}`);
      steps.push({ id: `step-${steps.length}`, kind: 'move', portalId: edge.id, regionId: id, targetCm: [...a, 0], toleranceCm: 5 }); current = a;
    }
  }
  visit(startNode.id);
  assert.equal(visitedNodes.size, nodes.length, 'Source graph has disconnected regions');
  assert(steps.length <= 800, 'Walkthrough exceeded bounded step count');
  return { schemaVersion: 1, status: 'source-walkthrough-planned-native-pending', coordinateSystem: 'unreal-centimeters',
    sceneSha256: provenance.sceneSha256, provenance, activeDesign: scene.activeDesign, startEyeCm: [...start, walking.eyeHeightCm],
    startForward: [0, 1, 0], requiredRegions: nodes, portals: edges, steps,
    interactiveDoorInventory: scene.doorMotion.doors.map(d => ({ id: d.id, kind: d.kind, subject: d.subject, architectural: d.architectural })),
    counts: { rooms: nodes.filter(n => n.kind === 'room').length, terraces: nodes.filter(n => n.kind === 'terrace').length,
      exteriorApproaches: nodes.filter(n => n.kind === 'exterior-approach').length, doors: edges.filter(e => e.kind === 'door').length,
      openPassages: edges.filter(e => e.kind === 'open-passage').length, steps: steps.length, planningObstacles: obstacles.length },
    capsuleRadiusCm: walking.capsuleRadiusCm, planningClearanceCm: radiusCm, allowedSupportObjectIds: walking.walkSurfaces.map(s => s.objectId),
    scope: 'One initial source living arrival followed by continuous native capsule movement. Every source room, terrace, approach and architectural door is required. Conservative bounds are planning inputs only; no reachability claim before native observations.' };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [directory, destination] = process.argv.slice(2);
  assert(directory && destination, 'Usage: walkthrough-contract.mjs <geometry-directory> <destination.json>');
  const [scene, walking, hidden] = await Promise.all(['scene.json', 'walking.json', 'hidden-collision.json'].map(name => readFile(resolve(directory, name))));
  const contract = buildWalkthroughContract(JSON.parse(scene), JSON.parse(walking), JSON.parse(hidden), {
    sceneSha256: hash(scene), walkingSha256: hash(walking), hiddenCollisionSha256: hash(hidden), helperSha256: hash(await readFile(fileURLToPath(import.meta.url))) });
  await writeFile(destination, JSON.stringify(contract, null, 2) + '\n'); console.log(JSON.stringify({ path: resolve(destination), counts: contract.counts }));
}
