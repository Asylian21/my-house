"""Independent exported-triangle checks for the fuller early taper study."""
import importlib.util
import json
from pathlib import Path
import struct
import unittest

import numpy as np
import shapely
from PIL import Image

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('covered_taper_study', HERE/'exterior-lawn-tapered-covered.py')
study = importlib.util.module_from_spec(spec); spec.loader.exec_module(study)
OUTPUT = study.OUTPUT


def decode(path):
    raw = Path(path).read_bytes(); magic, version, length = struct.unpack_from('<4sII', raw)
    if (magic, version, length) != (b'glTF', 2, len(raw)): raise AssertionError('Bad GLB header')
    count, kind = struct.unpack_from('<II', raw, 12)
    if kind != 0x4e4f534a: raise AssertionError('No GLB document')
    doc = json.loads(raw[20:20+count]); size, kind = struct.unpack_from('<II', raw, 20+count)
    if kind != 0x004e4942 or 28+count+size != len(raw): raise AssertionError('No GLB binary')
    binary = raw[28+count:]
    def values(index):
        a = doc['accessors'][index]; view = doc['bufferViews'][a['bufferView']]
        width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        return np.frombuffer(binary, dtype={5126: '<f4', 5125: '<u4'}[a['componentType']], count=a['count']*width,
            offset=view.get('byteOffset', 0)+a.get('byteOffset', 0)).reshape(-1, width)
    records = {}
    for node in doc['nodes']:
        p = doc['meshes'][node['mesh']]['primitives'][0]; a = p['attributes']; tangent = values(a['TANGENT'])
        records[node['name']] = {'nodeName': node['name'], 'positionsCm': (values(a['POSITION'])[:, [0, 2, 1]]*100).astype(float),
            'triangles': values(p['indices']).reshape(-1, 3)[:, [0, 2, 1]], 'normals': values(a['NORMAL'])[:, [0, 2, 1]].astype(float),
            'tangents': np.column_stack([tangent[:, :3][:, [0, 2, 1]], -tangent[:, 3]]).astype(float),
            'uv0': values(a['TEXCOORD_0']).astype(float), 'uv1': values(a['TEXCOORD_1']).astype(float), 'colors': values(a['COLOR_0']).astype(float)}
    return doc, records


class CoveredTaperStudy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = study.read(OUTPUT/'lawn-tapered-plan.json'); cls.bundle = study.read(OUTPUT/'lawn-tapered-manifest.json')
        cls.proof = study.read(OUTPUT/'lawn-tapered-prototypes.json')
        cls.old = study.read(study.r1.PRIOR/'lawn-natural-plan.json')
        cls.old_proof = {r['nodeName']: r for r in study.read(study.r1.PRIOR/'lawn-natural-prototypes.json')}
        cls.old_doc, cls.old_actual = decode(study.r1.PRIOR/'lawn-natural.glb')
        cls.doc, cls.actual = decode(OUTPUT/'tapered-covered.glb')
        cls.library = study.read(OUTPUT/'geometry-manifest.json')
        source = ROOT/'output/unreal/realism-20260926-r5/geometry'
        cls.scene, _, _, _, _, cls.domain, _, _, _ = study.prior.cover.managed_source(source,
            Path(cls.old['managedLawnPlan']['path']), Path(cls.old['derivedFrom']['path']))

    def test_source_pins_r1_recipe_root_groups_and_cbb_stay_exact(self):
        for path, expected in self.plan['inputFiles'].items(): self.assertEqual(study.sha(path), expected, path)
        self.assertEqual(study.sha(study.R1_SOURCE), study.R1_SHA)
        self.assertEqual(study.sha(study.R1/'lawn-tapered-manifest.json'), study.R1_MANIFEST_SHA)
        self.assertEqual(self.plan['generatorSha256'], study.sha(HERE/'exterior-lawn-tapered-covered.py'))
        for field in ('plan', 'geometryProof', 'materialManifest', 'preview', 'priorTaperStudy'):
            e = self.bundle[field]; self.assertEqual(study.sha(e['path']), e['sha256'])
        for field in ('glb', 'geometryManifest'):
            e = self.bundle['variant'][field]; self.assertEqual(study.sha(e['path']), e['sha256'])
        for field in ('coverageReceipt', 'boundaryCoverageReceipt'):
            self.assertNotIn(field, self.plan); self.assertNotIn(field, self.library)
            self.assertEqual(self.plan['baseline'+field[0].upper()+field[1:]], self.old[field])
            self.assertEqual(self.library['baseline'+field[0].upper()+field[1:]], self.old[field])
        for field in ('lawnPlacements', 'groups', 'activeDesign', 'housePlacement', 'sourceSceneSha256', 'sourceObjSha256',
                      'lawnDomainSourceMm', 'sourceLawnDomainSourceMm', 'exclusions', 'managedLawnKeepPolygonsCm',
                      'renderingPolicy', 'replacementPolicy'):
            self.assertEqual(self.plan[field], self.old[field])
        self.assertEqual(self.plan['activeDesign'], {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'})
        self.assertEqual(self.plan['housePlacement']['streetSetbackMm'], 3000)
        self.assertEqual(self.plan['housePlacement']['eastSetbackMm'], 3000)
        self.assertEqual((OUTPUT/'material-manifest.json').read_bytes(), (study.r1.PRIOR/'material-manifest.json').read_bytes())
        recipe = study.read(OUTPUT/'material-manifest.json')['lawn_natural_blade']
        self.assertEqual(self.doc['asset']['generator'], study.OWNER)
        self.assertEqual(self.doc['materials'][0]['pbrMetallicRoughness']['baseColorFactor'], [*recipe['linearColor'], 1.])
        self.assertEqual(self.doc['materials'][0]['pbrMetallicRoughness']['roughnessFactor'], .86)
        self.assertIs(self.doc['materials'][0]['doubleSided'], True)

    def test_decoded_early_maximum_prolonged_point_and_source_leaf_roots_height_limits(self):
        self.assertEqual(len(self.actual), 60); self.assertEqual(len(self.library['meshes']), 20)
        for record in self.proof:
            actual = self.actual[record['nodeName']]; p = actual['positionsCm']; old = self.old_proof[record['nodeName']]
            np.testing.assert_allclose(p, record['positionsCm'], atol=.000005, rtol=0)
            np.testing.assert_array_equal(actual['triangles'], record['triangles'])
            self.assertEqual(len(record['bladeRanges']), 48 if record['edgeMaster'] else 64)
            self.assertEqual(sum(b['low'] for b in record['bladeRanges']), len(record['bladeRanges'])//4)
            for b, before in zip(record['bladeRanges'], old['bladeRanges']):
                self.assertEqual(b['rootCm'], before['rootCm']); self.assertEqual(b['heightCm'], before['heightCm'])
                self.assertEqual(b['reachCm'], before['reachCm']); self.assertGreaterEqual(b['peakT'], .36); self.assertLessEqual(b['peakT'], .45)
                self.assertGreaterEqual(b['widthCm'], .32); self.assertLessEqual(b['widthCm'], .46)
                self.assertEqual(b['tipWidthCm'], 0.); self.assertIs(b['clipped'], False)
                self.assertGreaterEqual(b['rootWidthFraction'], .56); self.assertLessEqual(b['rootWidthFraction'], .62)
                self.assertEqual((b['vertexCount'], b['triangleCount']), (5, 3))
                v = p[b['vertexOffset']:b['vertexOffset']+5]; uv = actual['uv0'][b['vertexOffset']:b['vertexOffset']+5]
                np.testing.assert_allclose(v[-1], b['centerlineCm'][-1], atol=.000005)
                np.testing.assert_allclose(uv[-1], [.5, 1.], atol=1e-7)
                np.testing.assert_allclose(uv[:2, 1], [0., 0.], atol=1e-7)
                np.testing.assert_allclose(uv[2:4, 1], [b['peakT']]*2, atol=1e-7)
                root_span = np.linalg.norm(v[0]-v[1]); shoulder_span = np.linalg.norm(v[2]-v[3])
                self.assertAlmostEqual(shoulder_span, b['widthCm'], delta=.000005)
                self.assertAlmostEqual(root_span/shoulder_span, b['rootWidthFraction'], delta=.00004)
                self.assertLessEqual(root_span, before['widthCm']*.82+.000005)
                np.testing.assert_allclose(v[:2, :2].mean(axis=0), b['rootCm'], atol=.000005)
            self.assertGreaterEqual(float(p[:, 2].min()), -.000005)
            self.assertLessEqual(float(p[:, 2].max()), self.old_actual[record['nodeName']]['positionsCm'][:, 2].max()+.000005)

    def test_all_lods_have_same_actual_leaf_inventory_geometry_uv_and_normal_frames(self):
        for m in self.library['meshes']:
            first = self.actual[m['id']+'_LOD0']
            for lod in (1, 2):
                other = self.actual[m['id']+'_LOD'+str(lod)]
                for field in ('positionsCm', 'triangles', 'normals', 'tangents', 'uv0', 'uv1', 'colors'):
                    np.testing.assert_array_equal(first[field], other[field])
        for record in self.proof:
            a = self.actual[record['nodeName']]; p, n, t, uv = (a[k] for k in ('positionsCm', 'normals', 'tangents', 'uv0'))
            self.assertTrue(all(np.isfinite(a[k]).all() for k in ('positionsCm', 'normals', 'tangents', 'uv0', 'uv1', 'colors')))
            np.testing.assert_allclose(np.linalg.norm(n, axis=1), 1., atol=1e-6)
            np.testing.assert_allclose(np.linalg.norm(t[:, :3], axis=1), 1., atol=1e-6)
            np.testing.assert_allclose((n*t[:, :3]).sum(axis=1), 0., atol=1e-6)
            expected_n = np.zeros_like(p); expected_t = np.zeros_like(p); expected_b = np.zeros_like(p)
            for face in a['triangles']:
                q = p[face]; edge1, edge2 = q[1]-q[0], q[2]-q[0]; cross = np.cross(edge1, edge2)
                self.assertGreater(np.linalg.norm(cross), 1e-9); self.assertGreater(cross@n[face].mean(axis=0), 0.)
                du, dv = uv[face[1]]-uv[face[0]], uv[face[2]]-uv[face[0]]; det = du[0]*dv[1]-du[1]*dv[0]
                self.assertGreater(abs(det), 1e-8)
                expected_n[face] += cross
                expected_t[face] += (edge1*dv[1]-edge2*du[1])/det
                expected_b[face] += (edge2*du[0]-edge1*dv[0])/det
            expected_n /= np.linalg.norm(expected_n, axis=1)[:, None]
            expected_t -= expected_n*(expected_t*expected_n).sum(axis=1)[:, None]
            expected_t /= np.linalg.norm(expected_t, axis=1)[:, None]
            np.testing.assert_allclose(n, expected_n, atol=.00003)
            np.testing.assert_allclose(t[:, :3], expected_t, atol=.00003)
            np.testing.assert_array_equal(t[:, 3], np.where((np.cross(expected_n, expected_t)*expected_b).sum(axis=1) < 0, -1., 1.))

    def test_leaf_colour_mean_is_preserved_without_repeated_old_root_tip_brightness(self):
        for record in self.proof:
            actual = self.actual[record['nodeName']]; old = self.old_actual[record['nodeName']]
            for b, old_b in zip(record['bladeRanges'], self.old_proof[record['nodeName']]['bladeRanges']):
                color = actual['colors'][b['vertexOffset']:b['vertexOffset']+5, :3]
                old_color = old['colors'][old_b['vertexOffset']:old_b['vertexOffset']+old_b['vertexCount'], :3]
                np.testing.assert_allclose(color.mean(axis=0), old_color.mean(axis=0), atol=1e-7)
                np.testing.assert_allclose(color[-1]/color[0], [1.12]*3, atol=1e-6)
            self.assertTrue((actual['colors'] >= 0).all() and (actual['colors'] <= 1).all())

    def test_every_decoded_crown_plus_1mm_fits_exact_source_domain_at_same_cost_and_density(self):
        rows = self.plan['lawnPlacements']; self.assertEqual((len(rows), len(self.plan['groups'])), (102011, 40))
        self.assertEqual(rows, [{'meshId': g['meshId'], **r} for g in self.plan['groups'] for r in g['instances']])
        self.assertAlmostEqual(self.domain.area/10000, 143.598800884, places=7)
        xy = np.asarray([r['positionCm'][:2] for r in rows]); distance = shapely.distance(shapely.points(xy), self.domain.boundary)
        self.assertTrue(shapely.contains_xy(self.domain, *xy.T).all())
        envelopes = {m['id']: max(np.linalg.norm(self.actual[l['nodeName']]['positionsCm'][:, :2], axis=1).max() for l in m['lods']) for m in self.library['meshes']}
        radius = np.array([envelopes[r['meshId']]*r['scale'][0] for r in rows]); clearance = float(((distance-radius)*10-1).min())
        self.assertGreater(clearance, 0.)
        measured = self.bundle['variant']['measurements']
        self.assertAlmostEqual(clearance, measured['minimumAdditionalCrownClearanceMm'], places=8)
        budgets = [sum(len(g['instances'])*len(self.actual[g['meshId']+'_LOD'+str(i)]['triangles']) for g in self.plan['groups']) for i in range(3)]
        self.assertEqual(budgets, [18571200]*3); self.assertEqual(budgets, measured['allInstancesTriangleBudgetByLod'])
        self.assertIs(measured['withinOriginal20MTriangleBudget'], True)
        self.assertTrue(all(r['positionCm'][2] == -6.5 for r in rows))

    def test_actual_triangles_reraster_all_windows_and_boundary_gates_without_reusing_r1_cover(self):
        records = list(self.actual.values()); measured = self.bundle['variant']['measurements']
        self.assertEqual(len(measured['physicalCoverage']), 4); self.assertEqual(len(measured['boundaryCoverage']), 2)
        targets = []
        for window in measured['physicalCoverage']:
            got, _ = study.prior.cover.raster_coverage(records, self.plan['lawnPlacements'], window['centerCm'])
            self.assertEqual(got['resolution'], 4000)
            for actual, saved in zip(got['lods'], window['lods']):
                for field in ('projectedCoverage', 'tenCmBinCoverageP10', 'tenCmBinCoverageMinimum'):
                    self.assertAlmostEqual(actual[field], saved[field], delta=.00001)
                self.assertEqual(actual['bareTenCmBins'], saved['bareTenCmBins'])
                target = actual['projectedCoverage'] >= .75 and actual['tenCmBinCoverageP10'] >= .55 and actual['bareTenCmBins'] == 0
                self.assertEqual(saved['studyTargetsMet'], target); targets.append(target)
                self.assertGreaterEqual(actual['projectedCoverage'], .75)
                self.assertGreaterEqual(actual['tenCmBinCoverageP10'], .55)
        self.assertEqual(measured['interiorTargetsMet'], all(targets)); self.assertTrue(all(targets))
        edge_targets = []
        for window in measured['boundaryCoverage']:
            got, _ = study.prior.boundary_raster(records, self.plan['lawnPlacements'], window['originCm'], window['axisUnitXY'],
                window['inwardUnitXY'], window['widthCm'], window['lengthCm'])
            for actual, saved in zip(got['lods'], window['lods']):
                for band, claimed in zip(actual['boundaryBands'], saved['boundaryBands']):
                    self.assertAlmostEqual(band['physicalCoverFraction'], claimed['physicalCoverFraction'], delta=.00001)
                target = all(b['physicalCoverFraction'] > gate for b, gate in zip(actual['boundaryBands'], (.12, .40, .50)))
                self.assertEqual(saved['studyTargetsMet'], target); edge_targets.append(target)
        self.assertEqual(measured['boundaryTargetsMet'], all(edge_targets)); self.assertTrue(all(edge_targets))

    def test_original_legacy_40437_and_cpu_preview_never_claim_native_acceptance(self):
        legacy, _ = study.prior.legacy_source_proof(); self.assertEqual(legacy, self.plan['audit']['legacyLawnProof'])
        self.assertEqual(legacy['retainedInstances'], 40437); self.assertIs(legacy['nativeMutationPerformed'], False)
        self.assertIs(self.bundle['variant']['nativeAccepted'], False)
        self.assertIs(self.bundle['variant']['measurements']['nativeAppearanceAccepted'], False)
        for key in ('nativeVerified', 'nativeAppearanceAccepted', 'performanceAccepted', 'integrationAuthorized'):
            self.assertIs(self.plan['audit'][key], False)
        with Image.open(OUTPUT/'anatomy-side-by-side.png') as preview: self.assertEqual(preview.size, (2040, 1320))
        with self.assertRaisesRegex(ValueError, 'immutable'): study.build(OUTPUT)
        with self.assertRaisesRegex(ValueError, 'immutable'): study.build(study.R1)


if __name__ == '__main__': unittest.main()
