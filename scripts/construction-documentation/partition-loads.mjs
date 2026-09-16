import assert from 'node:assert/strict';

/** Current geometry only until the ordinary 300 mm brick product is selected.
 * A superseded SA30 mass must never become a load for the single-leaf wall. */
const EXPECTED_CODES = ['AK-01', 'AK-02'];
const RECT_KEYS = ['x0', 'y0', 'x1', 'y1'];
const unknownWeight = () => ({kgPerM2:null, kgPerM:null, kNPerM:null, totalKg:null});

export function derivePartitionLoads(d) {
  const assemblies = d.acousticAssemblies.filter(a => a.code === 'SM30');
  assert.equal(assemblies.length, 1, 'Expected one current SM30 assembly');
  const assembly = assemblies[0];
  assert.deepEqual(assembly.layers.map(l => [l.id,l.material,l.thicknessMm]), [['MASONRY','masonry',300]]);
  assert.equal(assembly.totalMm, 300);
  const specs = d.acousticWalls.filter(s => s.assembly.code === assembly.code).slice().sort((a,b) => a.mark.localeCompare(b.mark));
  assert.deepEqual(specs.map(s => s.mark), EXPECTED_CODES);
  const walls = specs.map(spec => {
    const matches = d.walls.filter(w => w.id === spec.wallId);
    assert.equal(matches.length, 1);
    const wall = matches[0], rectMm = wall.rectMm;
    assert.equal(wall.role, 'PARTITION', 'Material replacement does not approve a roof/ceiling support');
    assert(RECT_KEYS.every(key => Number.isFinite(rectMm[key])));
    assert(rectMm.x1 > rectMm.x0 && rectMm.y1 > rectMm.y0);
    assert.equal(spec.axis, 'x');
    assert.equal(rectMm.x1 - rectMm.x0, assembly.totalMm);
    assert.deepEqual(spec.assembly.layers, assembly.layers);
    const meshes = d.interiorMeshes.filter(entry => entry.kind === 'acoustic' && entry.mesh.name.startsWith(`Vnútorná stena ${wall.id} · `)
      && entry.mesh.name.includes(` · ${assembly.code} · MASONRY · `));
    assert.equal(meshes.length, 1, `${spec.mark}: require one full masonry mesh`);
    const mesh = meshes[0].mesh;
    for (const key of RECT_KEYS) assert(Math.abs(mesh.rect[key] - rectMm[key]) < 0.001, `${spec.mark}: mesh ${key}`);
    assert(Number.isFinite(mesh.z0) && Number.isFinite(mesh.z1) && mesh.z1 > mesh.z0);
    const heightMm = mesh.z1 - mesh.z0, lengthMm = rectMm.y1 - rectMm.y0;
    const centerlineMm = [[(rectMm.x0+rectMm.x1)/2,rectMm.y0],[(rectMm.x0+rectMm.x1)/2,rectMm.y1]];
    const areaM2 = lengthMm * heightMm / 1e6;
    return {
      wallId:wall.id, code:spec.mark, assemblyCode:assembly.code, role:wall.role, location:spec.location,
      rectMm, alongAxis:'y', centerlineMm, heightMm, lengthMm, areaM2,
      areaDefinition:'One wall elevation, one continuous 300 mm masonry layer.',
      wallIntervalsMm:[{axis:'y',fromMm:rectMm.y0,toMm:rectMm.y1,baseZmm:mesh.z0,topZmm:mesh.z1,heightMm}],
      leaves:[{id:'MASONRY',material:'masonry',thicknessMm:300,rectMm,centerlineMm,
        modelMeshIds:[mesh.id],modelMeshNames:[mesh.name],baseZmm:mesh.z0,topZmm:mesh.z1,heightMm,lengthMm,areaM2,
        bricksOnly:unknownWeight(),unplastered:unknownWeight()}],
      bricksOnly:unknownWeight(),unplastered:unknownWeight(),
      missingAdditions:[
        {id:'SELECTED_300_MM_BRICK_AND_MORTAR',totalKg:null,note:'Specify the same ordinary 300 mm brick as the exterior masonry and its declared mass.'},
        {id:'PLASTER_AND_SURFACE_FINISHES',totalKg:null,note:'Room plaster and bathroom waterproofing, adhesive and tiles are additional finishes.'},
        {id:'CONNECTIONS_AND_ATTACHED_EQUIPMENT',totalKg:null,note:'Include the sanitary frame, connections and equipment with the actual load path.'},
      ],
      finalDesignLineLoad:null,finalDesignApproved:false,
    };
  });
  const result = {
    status:'PRODUCT_SELECTION_REQUIRED',
    basis:{status:'PRODUCT_SELECTION_REQUIRED',product:assembly.product,
      note:'Single 300 mm ceramic masonry. The previous SA30 two-leaf mass is superseded; no current product mass or final design load is established.'},
    sources:{geometry:['lib/acoustic-walls.ts','lib/floor-plan-concept.ts','lib/plan-export.ts'],revision:'CLIENT-SM30-20260916'},
    walls,totals:{bricksOnlyKg:null,unplasteredKg:null},finalDesignLineLoad:null,finalDesignApproved:false,
  };
  verifyPartitionLoads(result);
  return result;
}

export function verifyPartitionLoads(result) {
  assert.equal(result.status, 'PRODUCT_SELECTION_REQUIRED');
  assert.equal(result.basis.status, 'PRODUCT_SELECTION_REQUIRED');
  assert.equal(result.finalDesignLineLoad, null);
  assert.equal(result.finalDesignApproved, false);
  assert.deepEqual(result.totals, {bricksOnlyKg:null,unplasteredKg:null});
  assert.deepEqual(result.walls.map(w => w.code), EXPECTED_CODES);
  for (const wall of result.walls) {
    assert.equal(wall.assemblyCode, 'SM30');
    assert.equal(wall.role, 'PARTITION');
    assert.equal(wall.leaves.length, 1);
    const leaf = wall.leaves[0], interval = wall.wallIntervalsMm[0];
    assert.equal(leaf.thicknessMm, 300);
    assert(wall.heightMm > 0 && wall.lengthMm > 0);
    assert.equal(wall.areaM2, wall.heightMm * wall.lengthMm / 1e6);
    assert.equal(interval.toMm - interval.fromMm, wall.lengthMm);
    assert.equal(interval.topZmm - interval.baseZmm, wall.heightMm);
    assert.equal(leaf.heightMm, wall.heightMm);
    assert.equal(leaf.lengthMm, wall.lengthMm);
    assert.deepEqual(leaf.rectMm, wall.rectMm);
    assert.deepEqual(leaf.centerlineMm, wall.centerlineMm);
    for (const key of ['bricksOnly','unplastered']) {
      assert.deepEqual(wall[key], unknownWeight());
      assert.deepEqual(leaf[key], unknownWeight());
    }
    assert.equal(wall.finalDesignLineLoad, null);
    assert.equal(wall.finalDesignApproved, false);
    assert(wall.missingAdditions.every(item => item.totalKg === null));
  }
  return true;
}
