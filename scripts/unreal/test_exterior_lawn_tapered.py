"""Decode both study GLBs independently: anatomy, frames, unchanged roots and honest cover."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import unittest

import numpy as np
import shapely
from PIL import Image

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('tapered_study', HERE/'exterior-lawn-tapered.py')
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


class TaperedStudy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = study.read(OUTPUT/'lawn-tapered-plan.json'); cls.bundle = study.read(OUTPUT/'lawn-tapered-manifest.json')
        cls.proof = study.read(OUTPUT/'lawn-tapered-prototypes.json'); cls.old = study.read(study.PRIOR/'lawn-natural-plan.json')
        cls.old_proof = {r['nodeName']: r for r in study.read(study.PRIOR/'lawn-natural-prototypes.json')}
        cls.old_doc, cls.old_actual = decode(study.PRIOR/'lawn-natural.glb')
        cls.docs = {}; cls.actual = {}; cls.libraries = {}
        for name in ('tapered', 'folded'):
            cls.docs[name], cls.actual[name] = decode(OUTPUT/(name+'.glb'))
            cls.libraries[name] = study.read(OUTPUT/(name+'-geometry-manifest.json'))
        source = ROOT/'output/unreal/realism-20260926-r5/geometry'
        cls.scene, _, _, _, _, cls.domain, _, _, _ = study.prior.cover.managed_source(source,
            Path(cls.old['managedLawnPlan']['path']), Path(cls.old['derivedFrom']['path']))

    def test_all_source_pins_recipe_roots_groups_design_and_old_geometry_are_preserved(self):
        for path, expected in self.plan['inputFiles'].items(): self.assertEqual(study.sha(path), expected, path)
        self.assertEqual(self.plan['generatorSha256'], study.sha(HERE/'exterior-lawn-tapered.py'))
        for field in ('plan', 'geometryProof', 'materialManifest', 'preview'):
            e = self.bundle[field]; self.assertEqual(study.sha(e['path']), e['sha256'])
        for v in self.bundle['variants'].values():
            for field in ('glb', 'geometryManifest'):
                e = v[field]; self.assertEqual(study.sha(e['path']), e['sha256'])
        for field in ('coverageReceipt', 'boundaryCoverageReceipt'):
            self.assertNotIn(field, self.plan)
            self.assertEqual(self.plan['baseline'+field[0].upper()+field[1:]], self.old[field])
            for library in self.libraries.values():
                self.assertNotIn(field, library)
                self.assertEqual(library['baseline'+field[0].upper()+field[1:]], self.old[field])
        self.assertEqual(self.plan['lawnPlacements'], self.old['lawnPlacements'])
        self.assertEqual(self.plan['groups'], self.old['groups'])
        for field in ('activeDesign', 'housePlacement', 'sourceSceneSha256', 'sourceObjSha256', 'lawnDomainSourceMm',
                      'sourceLawnDomainSourceMm', 'exclusions', 'managedLawnKeepPolygonsCm', 'renderingPolicy', 'replacementPolicy'):
            self.assertEqual(self.plan[field], self.old[field])
        self.assertEqual(self.plan['activeDesign'], {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'})
        self.assertEqual(self.plan['housePlacement']['streetSetbackMm'], 3000)
        self.assertEqual(self.plan['housePlacement']['eastSetbackMm'], 3000)
        self.assertEqual((OUTPUT/'material-manifest.json').read_bytes(), (study.PRIOR/'material-manifest.json').read_bytes())
        recipe = study.read(OUTPUT/'material-manifest.json')['lawn_natural_blade']
        for doc in self.docs.values():
            self.assertEqual(doc['materials'][0]['pbrMetallicRoughness']['baseColorFactor'], [*recipe['linearColor'], 1.])
            self.assertEqual(doc['materials'][0]['pbrMetallicRoughness']['roughnessFactor'], .86)
            self.assertIs(doc['materials'][0]['doubleSided'], True)

    def test_decoded_taper_maximum_width_is_early_and_every_tip_root_and_leaf_survives_all_lods(self):
        for name in ('tapered', 'folded'):
            self.assertEqual(len(self.actual[name]), 60); self.assertEqual(len(self.libraries[name]['meshes']), 20)
            for record in self.proof[name]:
                actual = self.actual[name][record['nodeName']]; p = actual['positionsCm']; old = self.old_proof[record['nodeName']]
                np.testing.assert_allclose(p, record['positionsCm'], atol=.000005, rtol=0)
                np.testing.assert_array_equal(actual['triangles'], record['triangles'])
                self.assertEqual(len(record['bladeRanges']), 48 if record['edgeMaster'] else 64)
                self.assertEqual(sum(r['low'] for r in record['bladeRanges']), len(record['bladeRanges'])//4)
                for b, before in zip(record['bladeRanges'], old['bladeRanges']):
                    self.assertEqual(b['rootCm'], before['rootCm']); self.assertEqual(b['heightCm'], before['heightCm'])
                    self.assertEqual(b['reachCm'], before['reachCm']); self.assertGreaterEqual(b['peakT'], .30); self.assertLessEqual(b['peakT'], .45)
                    self.assertGreaterEqual(b['widthCm'], .20); self.assertLessEqual(b['widthCm'], .30)
                    self.assertEqual(b['tipWidthCm'], 0.); self.assertEqual(b['rootWidthFraction'], .45)
                    n = 7 if name == 'folded' else 5; count = 6 if name == 'folded' else 3
                    self.assertEqual((b['vertexCount'], b['triangleCount']), (n, count))
                    v = p[b['vertexOffset']:b['vertexOffset']+n]; uv = actual['uv0'][b['vertexOffset']:b['vertexOffset']+n]
                    np.testing.assert_allclose(v[-1], b['centerlineCm'][-1], atol=.000005)
                    np.testing.assert_allclose(uv[-1], [.5, 1.], atol=1e-7)
                    root_span = np.linalg.norm(v[0]-v[2 if name == 'folded' else 1])
                    shoulder_span = np.linalg.norm(v[3 if name == 'folded' else 2]-v[5 if name == 'folded' else 3])
                    self.assertAlmostEqual(shoulder_span, b['widthCm'], delta=.000005)
                    self.assertAlmostEqual(root_span/shoulder_span, .45, delta=.00004)
                self.assertGreaterEqual(float(p[:, 2].min()), -.000005)
                self.assertLessEqual(float(p[:, 2].max()), old['expectedBoundsCm']['max'][2]+.000005)
            for m in self.libraries[name]['meshes']:
                first = self.actual[name][m['id']+'_LOD0']
                for lod in (1, 2):
                    other = self.actual[name][m['id']+'_LOD'+str(lod)]
                    for field in ('positionsCm', 'triangles', 'normals', 'tangents', 'uv0', 'uv1', 'colors'):
                        np.testing.assert_array_equal(first[field], other[field])

    def test_v_fold_is_actual_nonflat_cross_section_not_a_shader_or_metadata_claim(self):
        for record in self.proof['folded']:
            actual = self.actual['folded'][record['nodeName']]; p = actual['positionsCm']
            for b in record['bladeRanges']:
                v = p[b['vertexOffset']:b['vertexOffset']+7]
                root_ridge = np.linalg.norm(v[1]-(v[0]+v[2])*.5)
                shoulder_ridge = np.linalg.norm(v[4]-(v[3]+v[5])*.5)
                self.assertGreater(root_ridge, .006); self.assertGreater(shoulder_ridge, .015)
                self.assertIs(b['actualLongitudinalVSection'], True)
                self.assertGreaterEqual(b['foldRad'], .16); self.assertLessEqual(b['foldRad'], .24)

    def test_decoded_frames_uvs_winding_and_restrained_colour_mean_are_independent_of_claims(self):
        for name, records in self.proof.items():
            for record in records:
                a = self.actual[name][record['nodeName']]; p, n, t, uv = (a[k] for k in ('positionsCm', 'normals', 'tangents', 'uv0'))
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
                signs = np.where((np.cross(expected_n, expected_t)*expected_b).sum(axis=1) < 0, -1., 1.)
                np.testing.assert_array_equal(t[:, 3], signs)
                before = self.old_actual[record['nodeName']]
                for b, old_b in zip(record['bladeRanges'], self.old_proof[record['nodeName']]['bladeRanges']):
                    color = a['colors'][b['vertexOffset']:b['vertexOffset']+b['vertexCount'], :3]
                    old_color = before['colors'][old_b['vertexOffset']:old_b['vertexOffset']+old_b['vertexCount'], :3]
                    np.testing.assert_allclose(color.mean(axis=0), old_color.mean(axis=0), atol=1e-7)
                    np.testing.assert_allclose(color[-1]/color[0], [1.12]*3, atol=1e-6)
                self.assertTrue((a['colors'] >= 0).all() and (a['colors'] <= 1).all())

    def test_decoded_all_lod_crowns_exact_domain_and_truthful_double_cost(self):
        self.assertAlmostEqual(self.domain.area/10000, 143.598800884, places=7)
        rows = self.plan['lawnPlacements']; self.assertEqual(len(rows), 102011); self.assertEqual(len(self.plan['groups']), 40)
        self.assertEqual(rows, [{'meshId': g['meshId'], **r} for g in self.plan['groups'] for r in g['instances']])
        xy = np.asarray([r['positionCm'][:2] for r in rows]); distance = shapely.distance(shapely.points(xy), self.domain.boundary)
        self.assertTrue(shapely.contains_xy(self.domain, *xy.T).all())
        for name in ('tapered', 'folded'):
            lookup = self.actual[name]; envelopes = {m['id']: max(np.linalg.norm(lookup[l['nodeName']]['positionsCm'][:, :2], axis=1).max() for l in m['lods']) for m in self.libraries[name]['meshes']}
            radius = np.array([envelopes[r['meshId']]*r['scale'][0] for r in rows]); clearance = float(((distance-radius)*10-1).min())
            self.assertGreater(clearance, 0.)
            measurements = self.bundle['variants'][name]['measurements']
            self.assertAlmostEqual(clearance, measurements['minimumAdditionalCrownClearanceMm'], places=8)
            budgets = [sum(len(g['instances'])*len(lookup[g['meshId']+'_LOD'+str(i)]['triangles']) for g in self.plan['groups']) for i in range(3)]
            self.assertEqual(budgets, [18571200 if name == 'tapered' else 37142400]*3)
            self.assertEqual(budgets, measurements['allInstancesTriangleBudgetByLod'])
            self.assertIs(measurements['withinOriginal20MTriangleBudget'], name == 'tapered')
        self.assertTrue(all(r['positionCm'][2] == -6.5 for r in rows))

    def test_actual_glb_reraster_reports_interior_loss_without_relaxing_boundary_gates(self):
        for name in ('tapered', 'folded'):
            records = list(self.actual[name].values()); measurement = self.bundle['variants'][name]['measurements']
            for window in measurement['physicalCoverage']:
                got, _ = study.prior.cover.raster_coverage(records, self.plan['lawnPlacements'], window['centerCm'])
                for actual, saved in zip(got['lods'], window['lods']):
                    self.assertAlmostEqual(actual['projectedCoverage'], saved['projectedCoverage'], delta=.00001)
                    self.assertAlmostEqual(actual['tenCmBinCoverageP10'], saved['tenCmBinCoverageP10'], delta=.00001)
                    self.assertEqual(actual['bareTenCmBins'], saved['bareTenCmBins'])
                    self.assertLess(actual['projectedCoverage'], .75)
                    self.assertIs(saved['studyTargetsMet'], False)
            for window in measurement['boundaryCoverage']:
                got, _ = study.prior.boundary_raster(records, self.plan['lawnPlacements'], window['originCm'], window['axisUnitXY'],
                    window['inwardUnitXY'], window['widthCm'], window['lengthCm'])
                for actual, saved in zip(got['lods'], window['lods']):
                    for band, claimed, gate in zip(actual['boundaryBands'], saved['boundaryBands'], (.12, .40, .50)):
                        self.assertAlmostEqual(band['physicalCoverFraction'], claimed['physicalCoverFraction'], delta=.00001)
                        self.assertGreater(band['physicalCoverFraction'], gate)
                    self.assertIs(saved['studyTargetsMet'], True)
            self.assertIs(measurement['interiorTargetsMet'], False); self.assertIs(measurement['boundaryTargetsMet'], True)

    def test_preserved_legacy_40437_and_offline_preview_do_not_imply_native_acceptance(self):
        legacy, _ = study.prior.legacy_source_proof(); self.assertEqual(legacy, self.plan['audit']['legacyLawnProof'])
        self.assertEqual(legacy['retainedInstances'], 40437); self.assertIs(legacy['nativeMutationPerformed'], False)
        for name in ('tapered', 'folded'):
            self.assertIs(self.bundle['variants'][name]['nativeAccepted'], False)
            self.assertIs(self.bundle['variants'][name]['measurements']['nativeAppearanceAccepted'], False)
        for key in ('nativeVerified', 'nativeAppearanceAccepted', 'performanceAccepted', 'integrationAuthorized'):
            self.assertIs(self.plan['audit'][key], False)
        with Image.open(OUTPUT/'anatomy-side-by-side.png') as preview:
            self.assertEqual(preview.size, (2040, 1320))
        with self.assertRaisesRegex(ValueError, 'immutable'): study.build(OUTPUT)


if __name__ == '__main__': unittest.main()
