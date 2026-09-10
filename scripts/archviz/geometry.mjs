export function classify(name, material) {
  const text = `${name} ${material}`.toLowerCase();
  if (/foundation|základ/.test(text)) return "Foundations";
  if (/pool|bazén|šachta/.test(text)) return "Pool";
  if (/fence|oplot|plot |brána|bránka/.test(text)) return "Fence";
  if (/roof|strech|krov|krytina|solar|fotovolt|žľab/.test(text)) return "Roof";
  if (/glass|window|okno|presklen|opening/.test(text)) return "Windows";
  if (/hedge|plant|grass|lawn|tráv|zeleň|ker |krík/.test(text))
    return "Landscape";
  if (/deck|terrace|terasa|terasy|real-timber/.test(text)) return "Decking";
  if (/road|paving|gravel|street|asfalt|dlaž|štrk|spevnen/.test(text))
    return "Hardscape";
  if (/parcel|terén|terrain/.test(text)) return "Site";
  if (/real-wall|omiet|fasád|murivo|stena|steny/.test(text)) return "Walls";
  if (/floor|podlah/.test(text)) return "Floors";
  if (/water|sewer|rainwater|utility|potrub|kanal|vodovod|elektr/.test(text))
    return "Services";
  return "Interior";
}

export function transformPoint(p, m) {
  return [
    p[0] * m[0] + p[1] * m[4] + p[2] * m[8] + m[12],
    p[0] * m[1] + p[1] * m[5] + p[2] * m[9] + m[13],
    p[0] * m[2] + p[1] * m[6] + p[2] * m[10] + m[14],
  ];
}
export function exportPoint(p, m) {
  const q = transformPoint(p, m);
  return [q[0] * 1000, -q[2] * 1000, q[1] * 1000];
}
const fmt = (n) => Number(n.toFixed(6)).toString();

// Winding is repaired against source vertex normals, including mirrored and
// non-uniformly scaled instances. No rounding to whole mm or mesh decimation.
export function* serializeObj(meshes, manifest) {
  yield "# DOM source geometry. Millimetres. Z up. See scene.json.\nmtllib dom-mm.mtl\n";
  let vertexOffset = 1,
    uvOffset = 1,
    normalOffset = 1;
  const materialIds = new Map();
  for (const [index, mesh] of meshes.entries()) {
    const id = `DOM_${String(index).padStart(5, "0")}`;
    const materialNames = mesh.materials.map((m) => m.name);
    const slots = mesh.materials.map((m) => {
      const signature = JSON.stringify(m);
      if (!materialIds.has(signature)) {
        const key = `MAT_${String(materialIds.size).padStart(4, "0")}`;
        materialIds.set(signature, key);
        manifest.materials[key] = m;
      }
      return materialIds.get(signature);
    });
    const bounds = {
      min: [Infinity, Infinity, Infinity],
      max: [-Infinity, -Infinity, -Infinity],
    };
    let triangles = 0;
    yield `\n# ${mesh.name.replace(/[\r\n]/g, " ")}\no ${id}\ng ${classify(mesh.name, materialNames[0] ?? "")}\n`;
    for (const [instance, m] of mesh.transforms.entries()) {
      const points = [];
      const normals = [];
      const nm = mesh.normalTransforms[instance];
      for (let i = 0; i < mesh.positions.length; i += 3) {
        const p = exportPoint(mesh.positions.slice(i, i + 3), m);
        points.push(p);
        p.forEach((v, j) => {
          bounds.min[j] = Math.min(bounds.min[j], v);
          bounds.max[j] = Math.max(bounds.max[j], v);
        });
        yield `v ${p.map(fmt).join(" ")}\n`;
      }
      for (let i = 0; i < mesh.uvs.length; i += 2)
        yield `vt ${fmt(mesh.uvs[i])} ${fmt(mesh.uvs[i + 1])}\n`;
      for (let i = 0; i < mesh.normals.length; i += 3) {
        const p = mesh.normals.slice(i, i + 3);
        const n = [
          p[0] * nm[0] + p[1] * nm[4] + p[2] * nm[8],
          -(p[0] * nm[2] + p[1] * nm[6] + p[2] * nm[10]),
          p[0] * nm[1] + p[1] * nm[5] + p[2] * nm[9],
        ];
        const len = Math.hypot(...n) || 1;
        normals.push(n.map((x) => x / len));
        yield `vn ${n.map((v) => fmt(v / len)).join(" ")}\n`;
      }
      const subs = mesh.subMeshes.length
        ? mesh.subMeshes
        : [{ start: 0, count: mesh.indices.length, material: 0 }];
      for (const sub of subs) {
        yield `usemtl ${slots[sub.material] ?? slots[0]}\ns 1\n`;
        for (let i = sub.start; i < sub.start + sub.count; i += 3) {
          const f = mesh.indices.slice(i, i + 3);
          const [a, b, c] = f.map((j) => points[j]);
          if (!a || !b || !c)
            throw new Error(`Invalid triangle in ${mesh.name}`);
          const u = b.map((v, j) => v - a[j]),
            v = c.map((w, j) => w - a[j]);
          const cross = [
            u[1] * v[2] - u[2] * v[1],
            u[2] * v[0] - u[0] * v[2],
            u[0] * v[1] - u[1] * v[0],
          ];
          const n = normals[f[0]];
          if (n && cross.reduce((s, x, j) => s + x * n[j], 0) < 0)
            [f[1], f[2]] = [f[2], f[1]];
          const refs = f.map((j) => {
            const v = String(j + vertexOffset),
              uv = String(j + uvOffset),
              n = String(j + normalOffset);
            return normals.length
              ? `${v}/${mesh.uvs.length ? uv : ""}/${n}`
              : mesh.uvs.length
                ? `${v}/${uv}`
                : v;
          });
          yield `f ${refs.join(" ")}\n`;
          triangles++;
        }
      }
      vertexOffset += points.length;
      uvOffset += mesh.uvs.length / 2;
      normalOffset += normals.length;
    }
    manifest.objects.push({
      id,
      name: mesh.name,
      sourceId: mesh.sourceId,
      group: classify(mesh.name, materialNames[0] ?? ""),
      enabled: mesh.enabled,
      metadata: mesh.metadata,
      boundsMm: bounds,
      materialNames,
      materialSlots: slots,
      instances: mesh.transforms.length,
      triangles,
    });
  }
}
