import assert from 'node:assert/strict';

/** Nominal self-weight only. This module never selects a slab, rib or reinforcement. */
const OFFICIAL_SHEET = 'https://www.leier.sk/wp-content/uploads/2025/07/Technicky-list-LP10-NF.pdf';
const LINKED_SHEET = 'https://www.vastap.cz/files/download/ZSMA4AgCN2EdFPpyhLgdnfRSjO6pOTHy';
const PRODUCT_PAGE = 'https://www.vastap.cz/leier-leierplan-10-p10-P/';
const EXPECTED_CODES = ['AK-01', 'AK-02'];
const RECT_KEYS = ['x0', 'y0', 'x1', 'y1'];
const clean = value => Number(value.toFixed(9));
const close = (actual, expected, label) => assert(
  Number.isFinite(actual) && Math.abs(actual - expected) <= 1e-8 * Math.max(1, Math.abs(expected)),
  `${label}: ${actual} != ${expected}`,
);

function rectangle(value, label) {
  assert(value && RECT_KEYS.every(key => Number.isFinite(value[key])), `${label}: missing finite rectangle`);
  assert(value.x1 > value.x0 && value.y1 > value.y0, `${label}: empty rectangle`);
  return Object.fromEntries(RECT_KEYS.map(key => [key, value[key]]));
}

function centerline(rect, axis) {
  return axis === 'y'
    ? [[(rect.x0 + rect.x1) / 2, rect.y0], [(rect.x0 + rect.x1) / 2, rect.y1]]
    : [[rect.x0, (rect.y0 + rect.y1) / 2], [rect.x1, (rect.y0 + rect.y1) / 2]];
}

function weight(kgPerM2, heightMm, lengthMm, gravityMPerS2) {
  const kgPerM = kgPerM2 * heightMm / 1000;
  return {
    kgPerM2,
    kgPerM: clean(kgPerM),
    kNPerM: clean(kgPerM * gravityMPerS2 / 1000),
    totalKg: clean(kgPerM * lengthMm / 1000),
  };
}

function additions(woolThicknessMm) {
  return [
    {id: 'MORTAR_AND_BEDDING', totalKg: null,
      note: 'For bricksOnly add the selected adhesive/mortar and bedding. The catalogue unplastered value is a separate basis; its difference from brick mass is not a verified mortar mass and must not be counted twice.'},
    {id: 'PLASTER_AND_SURFACE_FINISHES', thicknessMm: null, densityKgPerM3: null, totalKg: null,
      note: 'Faces, products and thicknesses of plaster and surface finishes remain unspecified for SA30.'},
    {id: 'MINERAL_WOOL', thicknessMm: woolThicknessMm, product: null, densityKgPerM3: null, totalKg: null,
      note: 'Use the selected wool product; thickness alone does not determine mass.'},
    {id: 'BATHROOM_WATERPROOFING_ADHESIVE_AND_TILES', thicknessMm: null, totalKg: null,
      note: 'Add the actual extent and products on the bathroom side of AK-02.'},
    {id: 'CONNECTIONS_AND_ATTACHED_EQUIPMENT', totalKg: null, pointLoadsKn: null,
      note: 'Include connectors and any attached equipment or sanitary frame with its actual load path.'},
  ];
}

/**
 * Reads drawingSource().interiorMeshes, whose entries are {mesh, kind}.
 * Requires one full-height rectangular mesh per leaf. Missing/split/stepped
 * leaves fail explicitly rather than inventing a height or ignoring an opening.
 */
export function derivePartitionLoads(d) {
  assert(Array.isArray(d?.acousticWalls), 'Partition loads require acousticWalls from source.tsx');
  assert(Array.isArray(d.acousticAssemblies), 'Partition loads require acousticAssemblies from source.tsx');
  assert(Array.isArray(d.walls), 'Partition loads require canonical walls from source.tsx');
  assert(Array.isArray(d.interiorMeshes), 'Partition loads require INTERIOR_WALL_MESHES as interiorMeshes from source.tsx');
  const assemblies = d.acousticAssemblies.filter(a => a.code === 'SA30');
  assert.equal(assemblies.length, 1, 'Expected one current SA30 assembly');
  const assembly = assemblies[0];
  assert([LINKED_SHEET, OFFICIAL_SHEET].includes(assembly.technicalSheetUrl), 'SA30 product sheet changed: review the mass basis');
  assert.equal(assembly.productUrl, PRODUCT_PAGE, 'SA30 product changed: review the mass basis');
  const layerFacts = assembly.layers.map(l => [l.id, l.material, l.thicknessMm]);
  assert.deepEqual(layerFacts, [
    ['LEAF-W', 'masonry', 100], ['WOOL', 'mineral-wool', 100], ['LEAF-E', 'masonry', 100],
  ], 'This verified mass basis applies only to the selected SA30 100/100/100 assembly');
  assert.equal(assembly.totalMm, 300);
  const specs = d.acousticWalls.filter(s => s.assembly?.code === 'SA30')
    .slice().sort((a, b) => a.mark < b.mark ? -1 : a.mark > b.mark ? 1 : 0);
  assert.deepEqual(specs.map(s => s.mark), EXPECTED_CODES, 'Review the load scope if current SA30 walls change');
  assert.equal(new Set(specs.map(s => s.wallId)).size, specs.length, 'Duplicate SA30 wall source');

  const basis = {
    status: 'DECLARED_PRODUCT_VALUES_NOMINAL_CALCULATION',
    product: 'LeierPLAN 10 N+F', factory: 'Devecser',
    productDimensionsMm: {length: 500, width: 100, height: 249},
    brickMassKg: 9, brickConsumptionPerM2: 8,
    bricksOnlyOneLeafKgPerM2: 9 * 8,
    unplasteredOneLeafKgPerM2: 73,
    thinJointMortarOneLeafLitresPerM2: 0.8,
    mortarMassIncludedInUnplasteredKgPerM2: null,
    gravityMPerS2: 9.81,
    note: '72 kg/m² is the nominal brick-only calculation; 73 kg/m² is the separately declared unplastered masonry value. Neither is finished SA30 or a weighed delivery. The difference does not establish mortar mass.',
  };
  const sources = {
    officialUrl: OFFICIAL_SHEET,
    linkedTechnicalSheetUrl: assembly.technicalSheetUrl,
    productUrl: assembly.productUrl,
    verifiedDate: '2026-09-14',
    facts: [
      {field: 'brickMassKg', value: 9, unit: 'kg/piece', label: 'Hmotnosť', url: OFFICIAL_SHEET},
      {field: 'brickConsumptionPerM2', value: 8, unit: 'pieces/m²', label: 'Spotreba materiálu', url: OFFICIAL_SHEET},
      {field: 'unplasteredOneLeafKgPerM2', value: 73, unit: 'kg/m²', label: 'Hmotnosť muriva m² bez omietky', url: OFFICIAL_SHEET},
      {field: 'thinJointMortarOneLeafLitresPerM2', value: 0.8, unit: 'l/m²', label: 'Spotreba malty na tenkú škáru', url: OFFICIAL_SHEET},
    ],
    geometry: [
      'lib/acoustic-walls.ts:ACOUSTIC_WALL_SPECS/ACOUSTIC_ASSEMBLY',
      'lib/floor-plan-concept.ts:C-OPEN-HALL-N/C-OPEN-HALL-S',
      'lib/plan-export.ts:INTERIOR_WALL_MESHES',
      'scripts/construction-documentation/source.tsx:drawingSource',
    ],
  };
  const walls = specs.map(spec => {
    assert.deepEqual(spec.assembly.layers.map(l => [l.id, l.material, l.thicknessMm]), layerFacts, `${spec.mark}: assembly mismatch`);
    assert.equal(spec.assembly.technicalSheetUrl, assembly.technicalSheetUrl, `${spec.mark}: product sheet mismatch`);
    const matches = d.walls.filter(w => w.id === spec.wallId);
    assert.equal(matches.length, 1, `${spec.mark}: missing or duplicate canonical wall`);
    const wall = matches[0];
    assert.equal(wall.role, 'PARTITION', `${spec.mark}: SA30 must remain a non-load-bearing partition`);
    assert(['x', 'y'].includes(spec.axis), `${spec.mark}: missing layer direction`);
    const rectMm = rectangle(wall.rectMm, spec.wallId);
    const alongAxis = spec.axis === 'x' ? 'y' : 'x';
    close(rectMm[`${spec.axis}1`] - rectMm[`${spec.axis}0`], assembly.totalMm, `${spec.mark}: assembly thickness`);
    const lengthMm = clean(rectMm[`${alongAxis}1`] - rectMm[`${alongAxis}0`]);
    let offset = rectMm[`${spec.axis}0`];
    const leaves = [];
    for (const layer of assembly.layers) {
      const expectedRect = {...rectMm, [`${spec.axis}0`]: offset, [`${spec.axis}1`]: offset + layer.thicknessMm};
      offset += layer.thicknessMm;
      if (layer.material !== 'masonry') continue;
      const meshes = d.interiorMeshes.filter(entry => entry.kind === 'acoustic' && entry.mesh && (
        entry.mesh.name.startsWith(`Vnútorná stena ${wall.id} · `) ||
        entry.mesh.name.startsWith(`Vnútorná stena ${wall.id}-PART-`)
      ) && entry.mesh.name.includes(` · ${assembly.code} · ${layer.id} · `));
      assert.equal(meshes.length, 1, `${spec.mark}/${layer.id}: need exactly one full leaf mesh; do not infer height from a ceiling or bridge missing/split geometry`);
      const mesh = meshes[0].mesh;
      const leafRect = rectangle(mesh.rect, mesh.name);
      for (const key of RECT_KEYS) close(leafRect[key], expectedRect[key], `${spec.mark}/${layer.id}: mesh ${key}`);
      assert(Number.isFinite(mesh.z0) && Number.isFinite(mesh.z1) && mesh.z1 > mesh.z0, `${mesh.name}: missing positive mesh height`);
      const heightMm = clean(mesh.z1 - mesh.z0);
      leaves.push({
        id: layer.id, material: layer.material, thicknessMm: layer.thicknessMm,
        rectMm: leafRect, centerlineMm: centerline(leafRect, alongAxis),
        modelMeshIds: [mesh.id], modelMeshNames: [mesh.name],
        baseZmm: mesh.z0, topZmm: mesh.z1, heightMm, lengthMm,
        areaM2: clean(lengthMm * heightMm / 1e6),
        bricksOnly: weight(basis.bricksOnlyOneLeafKgPerM2, heightMm, lengthMm, basis.gravityMPerS2),
        unplastered: weight(basis.unplasteredOneLeafKgPerM2, heightMm, lengthMm, basis.gravityMPerS2),
      });
    }
    assert.equal(leaves.length, 2, `${spec.mark}: expected two masonry leaves`);
    close(leaves[0].baseZmm, leaves[1].baseZmm, `${spec.mark}: different leaf bases require separate interval calculation`);
    close(leaves[0].topZmm, leaves[1].topZmm, `${spec.mark}: different leaf tops require separate interval calculation`);
    const heightMm = leaves[0].heightMm;
    return {
      wallId: wall.id, code: spec.mark, assemblyCode: assembly.code, role: wall.role,
      location: spec.location, rectMm, alongAxis, centerlineMm: centerline(rectMm, alongAxis),
      heightMm, lengthMm, areaM2: clean(lengthMm * heightMm / 1e6),
      areaDefinition: 'One wall elevation; both leaf areas are combined in the load values, not in areaM2.',
      wallIntervalsMm: [{axis: alongAxis, fromMm: rectMm[`${alongAxis}0`], toMm: rectMm[`${alongAxis}1`],
        baseZmm: leaves[0].baseZmm, topZmm: leaves[0].topZmm, heightMm}],
      leaves,
      bricksOnly: weight(2 * basis.bricksOnlyOneLeafKgPerM2, heightMm, lengthMm, basis.gravityMPerS2),
      unplastered: weight(2 * basis.unplasteredOneLeafKgPerM2, heightMm, lengthMm, basis.gravityMPerS2),
      missingAdditions: additions(assembly.layers.find(l => l.id === 'WOOL').thicknessMm),
      finalDesignLineLoad: null, finalDesignApproved: false,
    };
  });
  const result = {
    status: 'NOMINAL_PARTITION_SELF_WEIGHT_NOT_FOR_CONSTRUCTION', basis, sources, walls,
    totals: {
      bricksOnlyKg: clean(walls.reduce((sum, wall) => sum + wall.bricksOnly.totalKg, 0)),
      unplasteredKg: clean(walls.reduce((sum, wall) => sum + wall.unplastered.totalKg, 0)),
    },
    finalDesignLineLoad: null, finalDesignApproved: false,
  };
  verifyPartitionLoads(result);
  return result;
}

/** Exported for the main verifier; also runs on every derivation. */
export function verifyPartitionLoads(result) {
  assert.equal(result.status, 'NOMINAL_PARTITION_SELF_WEIGHT_NOT_FOR_CONSTRUCTION');
  assert.equal(result.finalDesignLineLoad, null);
  assert.equal(result.finalDesignApproved, false);
  const b = result.basis;
  close(b.bricksOnlyOneLeafKgPerM2, b.brickMassKg * b.brickConsumptionPerM2, 'Brick-only basis');
  assert.equal(b.bricksOnlyOneLeafKgPerM2, 72);
  assert.equal(b.unplasteredOneLeafKgPerM2, 73);
  assert.equal(b.mortarMassIncludedInUnplasteredKgPerM2, null, 'Do not infer mortar mass from the catalogue difference');
  assert.deepEqual(result.walls.map(w => w.code), EXPECTED_CODES);
  for (const wall of result.walls) {
    assert.equal(wall.role, 'PARTITION');
    assert.equal(wall.finalDesignLineLoad, null);
    assert.equal(wall.finalDesignApproved, false);
    assert(wall.heightMm > 0 && wall.lengthMm > 0);
    close(wall.areaM2, wall.lengthMm * wall.heightMm / 1e6, `${wall.code}: elevation area`);
    assert.equal(wall.leaves.length, 2);
    assert.equal(wall.wallIntervalsMm.length, 1);
    const interval = wall.wallIntervalsMm[0];
    close(interval.toMm - interval.fromMm, wall.lengthMm, `${wall.code}: interval length`);
    close(interval.topZmm - interval.baseZmm, wall.heightMm, `${wall.code}: interval height`);
    for (const [key, oneLeaf] of [['bricksOnly', b.bricksOnlyOneLeafKgPerM2], ['unplastered', b.unplasteredOneLeafKgPerM2]]) {
      const load = wall[key];
      close(load.kgPerM2, 2 * oneLeaf, `${wall.code}/${key}: two leaves exactly once`);
      close(load.kgPerM, load.kgPerM2 * wall.heightMm / 1000, `${wall.code}/${key}: kg/m`);
      close(load.kNPerM, load.kgPerM * b.gravityMPerS2 / 1000, `${wall.code}/${key}: kN/m`);
      close(load.totalKg, load.kgPerM * wall.lengthMm / 1000, `${wall.code}/${key}: total`);
      close(load.totalKg, wall.leaves.reduce((sum, leaf) => sum + leaf[key].totalKg, 0), `${wall.code}/${key}: leaf sum`);
      for (const leaf of wall.leaves) {
        close(leaf.heightMm, leaf.topZmm - leaf.baseZmm, `${wall.code}/${leaf.id}: actual mesh height`);
        close(leaf.heightMm, wall.heightMm, `${wall.code}/${leaf.id}: same full height`);
        close(leaf.lengthMm, wall.lengthMm, `${wall.code}/${leaf.id}: full length`);
        close(leaf[key].kgPerM2, oneLeaf, `${wall.code}/${leaf.id}/${key}: one leaf`);
        close(leaf[key].totalKg, oneLeaf * leaf.areaM2, `${wall.code}/${leaf.id}/${key}: leaf area`);
      }
    }
    assert(wall.missingAdditions.length > 0 && wall.missingAdditions.every(item => item.totalKg === null));
  }
  close(result.totals.bricksOnlyKg, result.walls.reduce((sum, w) => sum + w.bricksOnly.totalKg, 0), 'Total brick-only mass');
  close(result.totals.unplasteredKg, result.walls.reduce((sum, w) => sum + w.unplastered.totalKg, 0), 'Total unplastered mass');
  return true;
}
