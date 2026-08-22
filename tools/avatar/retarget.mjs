// Avatar pipeline step 2: retarget the Mixamo locomotion clips (source
// skeleton) onto Michelle's skeleton by matching world-space bone orientation
// deltas against both T-poses, then bake them into the shipped GLB:
//   node tools/avatar/retarget.mjs tools/avatar/work/locomotion-mixamo.glb tools/avatar/work/michelle.glb public/assets/avatar/avatar.glb
import { NodeIO, Accessor } from "@gltf-transform/core";
import { prune } from "@gltf-transform/functions";

const [, , srcPath, dstPath, outPath] = process.argv;
const io = new NodeIO();
const src = await io.read(srcPath);
const dst = await io.read(dstPath);

// ---- quaternion helpers (x, y, z, w)
const qMul = (a, b) => [
  a[3] * b[0] + a[0] * b[3] + a[1] * b[2] - a[2] * b[1],
  a[3] * b[1] - a[0] * b[2] + a[1] * b[3] + a[2] * b[0],
  a[3] * b[2] + a[0] * b[1] - a[1] * b[0] + a[2] * b[3],
  a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2],
];
const qInv = (q) => [-q[0], -q[1], -q[2], q[3]];
const qNorm = (q) => { const l = Math.hypot(...q) || 1; return q.map((v) => v / l); };
const qRot = (q, v) => { // rotate vector by quaternion
  const u = [q[0], q[1], q[2]]; const s = q[3];
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const uv = cross(u, v); const uuv = cross(u, uv);
  return v.map((_, i) => v[i] + 2 * (s * uv[i] + uuv[i]));
};
const slerp = (a, b, t) => {
  let d = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3];
  if (d < 0) { b = b.map((v) => -v); d = -d; }
  if (d > 0.9995) return qNorm(a.map((v, i) => v + (b[i] - v) * t));
  const th = Math.acos(d); const s = Math.sin(th);
  const wa = Math.sin((1 - t) * th) / s; const wb = Math.sin(t * th) / s;
  return a.map((v, i) => v * wa + b[i] * wb);
};

// ---- skeleton description
function describe(doc) {
  const nodes = doc.getRoot().listNodes();
  const byName = new Map(nodes.map((n) => [n.getName(), n]));
  const parent = new Map();
  for (const n of nodes) for (const c of n.listChildren()) parent.set(c, n);
  return { nodes, byName, parent };
}
const S = describe(src);
const T = describe(dst);

function restWorldRotation(sk, node, localOverride = null) {
  let q = [0, 0, 0, 1];
  let n = node;
  while (n) {
    const local = localOverride?.get(n.getName()) ?? n.getRotation();
    q = qMul(local, q);
    n = sk.parent.get(n);
  }
  return qNorm(q);
}

/** Local rotations (and hips translation) at frame 0 of a clip named `name`. */
function referencePose(doc, name) {
  const anim = doc.getRoot().listAnimations().find((a) => a.getName() === name);
  const rot = new Map();
  let hips = null;
  if (!anim) return { rot, hips };
  for (const ch of anim.listChannels()) {
    const node = ch.getTargetNode().getName();
    const out = ch.getSampler().getOutput().getArray();
    if (ch.getTargetPath() === "rotation") rot.set(node, qNorm(Array.from(out.subarray(0, 4))));
    if (ch.getTargetPath() === "translation" && node === "mixamorig:Hips") hips = Array.from(out.subarray(0, 3));
  }
  return { rot, hips };
}
const refS = referencePose(src, "TPose");
const refT = referencePose(dst, "TPose");

// World-frame alignment between the rigs: Mixamo exports may face +z or -z.
// Compare the direction of the left arm in both T-poses and conjugate every
// world delta by the yaw that aligns them.
function worldPositions(sk, doc, ref) {
  const world = new Map();
  const walk = (n, pq, pp) => {
    const lq = ref.rot.get(n.getName()) ?? n.getRotation();
    const lt = n.getName() === "mixamorig:Hips" && ref.hips ? ref.hips : n.getTranslation();
    const p = pp.map((v, i) => v + qRot(pq, lt)[i]);
    const q = qMul(pq, lq);
    world.set(n.getName(), p);
    for (const c of n.listChildren()) walk(c, q, p);
  };
  walk(doc.getRoot().listScenes()[0].listChildren()[0], [0, 0, 0, 1], [0, 0, 0]);
  return world;
}
function armYaw(world) {
  const hips = world.get("mixamorig:Hips");
  const hand = world.get("mixamorig:LeftHand");
  return Math.atan2(hand[2] - hips[2], hand[0] - hips[0]);
}
const yawS = armYaw(worldPositions(S, src, refS));
const yawT = armYaw(worldPositions(T, dst, refT));
const alignYaw = yawT - yawS;
const ALIGN = [0, Math.sin(alignYaw / 2), 0, Math.cos(alignYaw / 2)];
console.log("facing alignment yaw", (alignYaw * 180 / Math.PI).toFixed(1), "deg");
console.log("reference poses: source", refS.rot.size, "bones, target", refT.rot.size, "bones");

function sampleChannel(sampler, time) {
  const input = sampler.getInput().getArray();
  const output = sampler.getOutput().getArray();
  const size = sampler.getOutput().getElementSize();
  if (time <= input[0]) return Array.from(output.subarray(0, size));
  const last = input.length - 1;
  if (time >= input[last]) return Array.from(output.subarray(last * size, last * size + size));
  let i = 0;
  while (input[i + 1] < time) i += 1;
  const t = (time - input[i]) / (input[i + 1] - input[i]);
  const a = Array.from(output.subarray(i * size, i * size + size));
  const b = Array.from(output.subarray((i + 1) * size, (i + 1) * size + size));
  return size === 4 ? slerp(a, b, t) : a.map((v, k) => v + (b[k] - v) * t);
}

const sourceHipsHeight = Math.hypot(...S.byName.get("mixamorig:Hips").getTranslation());
const targetHipsHeight = Math.hypot(...T.byName.get("mixamorig:Hips").getTranslation());
const hipsScale = targetHipsHeight / sourceHipsHeight;
console.log("hips scale", hipsScale.toFixed(3));

// Target bones in parent-first order.
const targetOrder = [];
(function walk(n) { targetOrder.push(n); for (const c of n.listChildren()) walk(c); })(dst.getRoot().listScenes()[0].listChildren()[0]);

const buffer = dst.getRoot().listBuffers()[0];

for (const anim of src.getRoot().listAnimations()) {
  if (anim.getName() === "TPose") continue;
  const channels = anim.listChannels();
  const rotBySource = new Map();
  let hipsTranslation = null;
  for (const ch of channels) {
    const name = ch.getTargetNode().getName();
    if (ch.getTargetPath() === "rotation") rotBySource.set(name, ch.getSampler());
    if (ch.getTargetPath() === "translation" && name === "mixamorig:Hips") hipsTranslation = ch.getSampler();
  }
  const master = Array.from(rotBySource.get("mixamorig:Hips").getInput().getArray());
  const frames = master.length;
  const outRot = new Map(targetOrder.filter((n) => rotBySource.has(n.getName()) || T.byName.has(n.getName())).map((n) => [n, new Float32Array(frames * 4)]));
  const outHips = new Float32Array(frames * 3);
  const restWorldS = new Map([...S.byName.values()].map((n) => [n.getName(), restWorldRotation(S, n, refS.rot)]));
  const restWorldT = new Map(targetOrder.map((n) => [n, restWorldRotation(T, n, refT.rot)]));
  const restLocalT = (n) => refT.rot.get(n.getName()) ?? n.getRotation();

  for (let f = 0; f < frames; f += 1) {
    const time = master[f];
    // Source animated world rotations.
    const worldS = new Map();
    const srcOrder = [];
    (function walk(n) { srcOrder.push(n); for (const c of n.listChildren()) walk(c); })(src.getRoot().listScenes()[0].listChildren()[0]);
    for (const n of srcOrder) {
      const local = rotBySource.has(n.getName()) ? sampleChannel(rotBySource.get(n.getName()), time) : n.getRotation();
      const p = S.parent.get(n);
      worldS.set(n.getName(), qNorm(p ? qMul(worldS.get(p.getName()), local) : local));
    }
    // Target: apply world delta to target rest, derive locals parent-first.
    const worldT = new Map();
    for (const n of targetOrder) {
      const name = n.getName();
      const p = T.parent.get(n);
      let world;
      if (worldS.has(name) && rotBySource.has(name)) {
        const deltaS = qMul(worldS.get(name), qInv(restWorldS.get(name)));
        const delta = qMul(qMul(ALIGN, deltaS), qInv(ALIGN));
        world = qNorm(qMul(delta, restWorldT.get(n)));
      } else {
        // Unanimated (or missing) bone keeps its reference orientation relative to its parent.
        world = qNorm(p ? qMul(worldT.get(p), restLocalT(n)) : restLocalT(n));
      }
      worldT.set(n, world);
      const local = qNorm(p ? qMul(qInv(worldT.get(p)), world) : world);
      const arr = outRot.get(n);
      if (arr) arr.set(local, f * 4);
    }
    // Hips translation: source world position (without root scale) mapped into
    // the target hips parent space, scaled to the target leg length.
    if (hipsTranslation) {
      // Hips offset relative to the reference pose, scaled to the target
      // leg length and added to the target's reference hips position.
      const tS = sampleChannel(hipsTranslation, time);
      const refHipsS = refS.hips ?? S.byName.get("mixamorig:Hips").getTranslation();
      const refHipsT = refT.hips ?? T.byName.get("mixamorig:Hips").getTranslation();
      const charS = src.getRoot().listScenes()[0].listChildren()[0];
      const charT = T.parent.get(T.byName.get("mixamorig:Hips"));
      const worldDelta = qRot(ALIGN, qRot(charS.getRotation(), tS.map((v, i) => v - refHipsS[i])));
      const localDelta = qRot(qInv(charT.getRotation()), worldDelta).map((v) => v * hipsScale);
      outHips.set(refHipsT.map((v, i) => v + localDelta[i]), f * 3);
    }
  }

  // Write into target document.
  const animT = dst.createAnimation(anim.getName());
  const input = dst.createAccessor(`${anim.getName()}_time`).setType(Accessor.Type.SCALAR).setArray(new Float32Array(master)).setBuffer(buffer);
  for (const [node, arr] of outRot) {
    if (!rotBySource.has(node.getName())) continue;
    const output = dst.createAccessor(`${anim.getName()}_${node.getName()}_rot`).setType(Accessor.Type.VEC4).setArray(arr).setBuffer(buffer);
    const sampler = dst.createAnimationSampler().setInput(input).setOutput(output).setInterpolation("LINEAR");
    const channel = dst.createAnimationChannel().setTargetNode(node).setTargetPath("rotation").setSampler(sampler);
    animT.addSampler(sampler).addChannel(channel);
  }
  if (hipsTranslation) {
    const output = dst.createAccessor(`${anim.getName()}_hips_pos`).setType(Accessor.Type.VEC3).setArray(outHips).setBuffer(buffer);
    const sampler = dst.createAnimationSampler().setInput(input).setOutput(output).setInterpolation("LINEAR");
    const channel = dst.createAnimationChannel().setTargetNode(T.byName.get("mixamorig:Hips")).setTargetPath("translation").setSampler(sampler);
    animT.addSampler(sampler).addChannel(channel);
  }
  console.log("retargeted", anim.getName(), frames, "frames", outRot.size, "bones");
}

for (const anim of dst.getRoot().listAnimations()) if (anim.getName() === "TPose") anim.dispose();
await dst.transform(prune());
await io.write(outPath, dst);
console.log("wrote", outPath);
