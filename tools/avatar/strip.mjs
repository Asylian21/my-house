// Avatar pipeline step 1 (needs `npm i @gltf-transform/core @gltf-transform/functions` in a scratch dir):
//   node tools/avatar/strip.mjs      → tools/avatar/work/{locomotion-mixamo,michelle}.glb
// Sources: three.js examples Soldier.glb (Mixamo "Vanguard" locomotion clips) and
// Michelle.glb (Mixamo character), see README for licensing.
import { mkdirSync } from "node:fs";
mkdirSync(new URL("./work/", import.meta.url), { recursive: true });
import { NodeIO } from "@gltf-transform/core";
import { prune } from "@gltf-transform/functions";
const io = new NodeIO();
const doc = await io.read(new URL("./sources/Soldier.glb", import.meta.url).pathname);
const root = doc.getRoot();
// Drop every mesh/material/texture; keep nodes (skeleton) + animations.
for (const node of root.listNodes()) { if (node.getMesh()) node.setMesh(null); if (node.getSkin()) node.setSkin(null); }
for (const s of root.listSkins()) s.dispose();
for (const m of root.listMeshes()) m.dispose();
for (const m of root.listMaterials()) m.dispose();
for (const t of root.listTextures()) t.dispose();
// Remove TPose animation and per-bone translation/scale tracks except hips translation.
for (const anim of root.listAnimations()) {
  // keep TPose: it is the retargeting reference pose
  for (const ch of anim.listChannels()) {
    const path = ch.getTargetPath(); const name = ch.getTargetNode()?.getName() ?? "";
    if (path === "scale" || (path === "translation" && name !== "mixamorig:Hips")) ch.dispose();
  }
}
await doc.transform(prune());
await io.write(new URL("./work/locomotion-mixamo.glb", import.meta.url).pathname, doc);
const d2 = await io.read(new URL("./sources/Michelle.glb", import.meta.url).pathname);
for (const anim of d2.getRoot().listAnimations()) if (anim.getName() !== "TPose") anim.dispose();
await d2.transform(prune());
await io.write(new URL("./work/michelle.glb", import.meta.url).pathname, d2);
