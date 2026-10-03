"""Independent saved GLB, fine morphology, continuous cover and edge evidence."""
from copy import deepcopy
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import tempfile
import unittest

import numpy as np
import shapely

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('fine_turf', HERE/'exterior-lawn-fine.py')
fine = importlib.util.module_from_spec(spec); spec.loader.exec_module(fine)
OUTPUT = Path(os.environ.get('BREZI_LAWN_FINE', ROOT/'output/unreal/exterior-lawn-fine-20260930-r1'))
GEOMETRY = ROOT/'output/unreal/realism-20260926-r5/geometry'
RURAL = ROOT/'output/unreal/exterior-20260930-r5/geometry/rural-context-geometry.json'
ORIGINAL = ROOT/'output/unreal/exterior-lawn-natural-20260930-r1/lawn-natural-plan.json'
PRIOR = ROOT/'output/unreal/exterior-lawn-natural-20260930-r3d'


def decode_glb(path):
    raw = Path(path).read_bytes(); magic, version, length = struct.unpack_from('<4sII', raw)
    if (magic, version, length) != (b'glTF', 2, len(raw)): raise AssertionError('Bad GLB header')
    size, kind = struct.unpack_from('<II', raw, 12)
    if kind != 0x4e4f534a: raise AssertionError('Bad GLB JSON')
    doc = json.loads(raw[20:20+size]); offset = 20+size
    binsize, kind = struct.unpack_from('<II', raw, offset)
    if kind != 0x004e4942 or offset+8+binsize != len(raw): raise AssertionError('Bad binary chunk')
    binary = raw[offset+8:]
    def decode(index):
        a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
        width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        return np.frombuffer(binary, dtype={5126: '<f4', 5125: '<u4'}[a['componentType']], count=a['count']*width,
            offset=v.get('byteOffset', 0)+a.get('byteOffset', 0)).reshape(-1, width)
    return doc, decode


class FineTurf(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = fine.read(OUTPUT/'lawn-natural-plan.json'); cls.manifest = fine.read(OUTPUT/'lawn-natural-manifest.json')
        cls.library = fine.read(OUTPUT/'geometry-manifest.json'); cls.records = fine.read(OUTPUT/'lawn-natural-prototypes.json')
        cls.lookup = {row['id']: row for row in cls.library['meshes']}; cls.doc, decoder = decode_glb(OUTPUT/'lawn-natural.glb')
        cls.decode = staticmethod(decoder)
        cls.actual = {}; cls.envelopes = {}
        for node in cls.doc['nodes']:
            primitive = cls.doc['meshes'][node['mesh']]['primitives'][0]; attr = primitive['attributes']
            p = cls.decode(attr['POSITION'])[:, [0, 2, 1]]*100
            face = cls.decode(primitive['indices']).reshape(-1, 3)[:, [0, 2, 1]]
            cls.actual[node['name']] = {'nodeName': node['name'], 'positionsCm': p.tolist(), 'triangles': face.tolist(),
                                      'attributes': attr, 'primitive': primitive}
            mid = node['name'].rsplit('_LOD', 1)[0]
            cls.envelopes[mid] = max(cls.envelopes.get(mid, 0), float(np.linalg.norm(p[:, :2], axis=1).max()))
        cls.scene, _, _, _, cls.source, cls.domain, cls.exclusions, _, _ = fine.cover.managed_source(GEOMETRY, RURAL, ORIGINAL)

    def test_source_frame_masks_pins_recipe_and_original_preservation(self):
        p = self.plan
        self.assertEqual(p['owner'], fine.OWNER); self.assertEqual(p['generatorSha256'], fine.sha(HERE/'exterior-lawn-fine.py'))
        for path, expected in p['inputFiles'].items(): self.assertEqual(fine.sha(path), expected, path)
        for key in ('plan', 'glb', 'geometryManifest', 'materialManifest', 'geometryProof', 'coverageReceipt', 'boundaryCoverageReceipt'):
            row = self.manifest[key]; self.assertEqual(fine.sha(row['path']), row['sha256'])
        self.assertEqual(p['coverageReceipt'], self.library['coverageReceipt']); self.assertEqual(p['coverageReceipt'], self.manifest['coverageReceipt'])
        self.assertEqual(p['boundaryCoverageReceipt'], self.library['boundaryCoverageReceipt'])
        self.assertEqual(p['boundaryCoverageReceipt'], self.manifest['boundaryCoverageReceipt'])
        self.assertEqual(p['activeDesign'], {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'})
        self.assertEqual(p['housePlacement'], self.scene['house']['placement'])
        self.assertEqual(p['housePlacement']['eastSetbackMm'], 3000); self.assertEqual(p['housePlacement']['streetSetbackMm'], 3000)
        self.assertEqual(p['sourceSceneSha256'], fine.sha(GEOMETRY/'scene.json')); self.assertEqual(p['sourceObjSha256'], fine.sha(GEOMETRY/'dom-mm.obj'))
        self.assertEqual(p['managedLawnKeepPolygonsCm'], fine.read(RURAL)['managedLawnKeepPolygonsCm'])
        self.assertEqual(p['sourceLawnDomainSourceMm'], fine.read(ORIGINAL)['lawnDomainSourceMm'])
        self.assertEqual(p['exclusions'], json.loads(json.dumps(self.exclusions)))
        self.assertAlmostEqual(self.domain.area/10000, 143.598800884, places=7)
        self.assertTrue(shapely.equals_exact(fine.cover.native_shape(shapely.from_geojson(p['lawnDomainSourceMm'])), self.domain, 1e-7))
        old = fine.read(PRIOR/'lawn-natural-plan.json')
        self.assertEqual(p['replacementPolicy'], old['replacementPolicy']); self.assertEqual(p['renderingPolicy'], old['renderingPolicy'])
        recipe = fine.read(OUTPUT/'material-manifest.json')
        self.assertEqual(list(recipe), ['lawn_natural_blade']); self.assertEqual(recipe['lawn_natural_blade']['maps'], {})
        self.assertEqual(recipe['lawn_natural_blade']['linearColor'], [.04, .075, .025]); self.assertEqual(recipe['lawn_natural_blade']['subsurfaceScale'], .08)

    def test_actual_glb_fine_leaf_width_curve_roll_and_complete_lod_identity(self):
        self.assertEqual(len(self.actual), 60); self.assertEqual(len(self.library['meshes']), 20)
        for record in self.records:
            actual = self.actual[record['nodeName']]; p = np.asarray(actual['positionsCm'])
            np.testing.assert_allclose(p, record['positionsCm'], atol=.000004, rtol=0)
            np.testing.assert_array_equal(actual['triangles'], record['triangles'])
            count = 48 if record['edgeMaster'] else 64
            self.assertEqual(len(record['bladeRanges']), count); self.assertEqual(sum(b['low'] for b in record['bladeRanges']), count*3//4)
            self.assertLess(float(p[:, 2].max()), 4.6); self.assertGreater(float(p[:, 2].max()), 2.5)
            self.assertGreater(float(p[:, 2].min()), -.01)
            for b in record['bladeRanges']:
                self.assertLessEqual(b['widthCm'], .24); self.assertGreater(b['widthCm'], .08); self.assertGreaterEqual(b['segments'], 2)
                center = np.asarray(b['centerlineCm']); t = np.linspace(0, 1, len(center))[:, None]
                self.assertGreater(float(np.linalg.norm(center-(center[0]+t*(center[-1]-center[0])), axis=1).max()), .04)
                section = np.asarray(b['sectionNormals'])
                self.assertGreater(float(np.linalg.norm(section-section[0], axis=1).max()), .04)
                self.assertTrue(.91999 <= b['lodProjectedAreaWidthScale'] <= 1.14001)
            for key, fn in [('min', np.min), ('max', np.max)]: np.testing.assert_allclose(fn(p, axis=0), record['expectedBoundsCm'][key], atol=.000004)
        for mesh in self.library['meshes']:
            self.assertEqual(mesh['placementPolicy'], 'explicit-only'); self.assertEqual(mesh['materialKeys'], ['lawn_natural_blade'])
            self.assertEqual(mesh['lodScreenSizes'], [1, .025, .007])
            r = [next(r for r in self.records if r['nodeName'] == mesh['id']+'_LOD'+str(lod)) for lod in range(3)]
            self.assertEqual([b['rootCm'] for b in r[0]['bladeRanges']], [b['rootCm'] for b in r[1]['bladeRanges']])
            self.assertEqual([b['rootCm'] for b in r[1]['bladeRanges']], [b['rootCm'] for b in r[2]['bladeRanges']])
            expected = [96, 96, 96] if mesh['edgeMaster'] and mesh['id'].endswith('_0') else [144, 144, 144] if mesh['edgeMaster'] else [384, 256, 192]
            self.assertEqual([lod['triangles'] for lod in mesh['lods']], expected)

    def test_decoded_glb_face_frames_and_actual_all_lod_crown_exclusions_budget(self):
        for record in self.records:
            actual = self.actual[record['nodeName']]; attr = actual['attributes']; p = np.asarray(actual['positionsCm'])
            n = self.decode(attr['NORMAL'])[:, [0, 2, 1]]; tangent = self.decode(attr['TANGENT'])
            t = tangent[:, :3][:, [0, 2, 1]]
            np.testing.assert_allclose(np.linalg.norm(n, axis=1), 1, atol=1e-6); np.testing.assert_allclose(np.linalg.norm(t, axis=1), 1, atol=1e-6)
            np.testing.assert_allclose((n*t).sum(axis=1), 0, atol=1e-6)
            self.assertTrue(np.isfinite(self.decode(attr['TEXCOORD_0'])).all()); self.assertTrue(np.isfinite(tangent).all())
            face = np.asarray(actual['triangles']); q = p[face]; cross = np.cross(q[:, 1]-q[:, 0], q[:, 2]-q[:, 0])
            self.assertGreater(float(np.linalg.norm(cross, axis=1).min()), 1e-9)
            self.assertTrue((np.einsum('ij,ij->i', cross, n[face].mean(axis=1)) > 0).all())
        rows = self.plan['lawnPlacements']; self.assertTrue(38000 < len(rows) < 75000)
        self.assertEqual(rows, [{'meshId': group['meshId'], **r} for group in self.plan['groups'] for r in group['instances']])
        xy = np.array([r['positionCm'][:2] for r in rows]); distance = shapely.distance(shapely.points(xy), self.domain.boundary)
        radius = np.array([self.envelopes[r['meshId']]*r['scale'][0] for r in rows])
        self.assertTrue(shapely.contains_xy(self.domain, *xy.T).all()); self.assertGreater(float(((distance-radius)*10-1).min()), 0)
        for row in rows:
            self.assertEqual(row['positionCm'][2], -6.5); self.assertEqual(row['scale'], [row['scale'][0]]*3)
        budgets = [sum(len(g['instances'])*self.lookup[g['meshId']]['lods'][lod]['triangles'] for g in self.plan['groups']) for lod in range(3)]
        self.assertEqual(budgets, self.plan['audit']['allInstancesTriangleBudgetByLod']); self.assertLessEqual(budgets[0], 20000000)

    def test_decoded_physical_cover_every_lod_and_independent_boundary_bands(self):
        records = list(self.actual.values()); rows = self.plan['lawnPlacements']
        for window in fine.read(OUTPUT/'lawn-coverage-receipt.json')['windows']:
            actual, _ = fine.cover.raster_coverage(records, rows, window['centerCm'])
            for got, saved in zip(actual['lods'], window['lods']):
                self.assertAlmostEqual(got['projectedCoverage'], saved['projectedCoverage'], delta=.0001)
                self.assertGreater(got['projectedCoverage'], .70); self.assertGreater(got['tenCmBinCoverageP10'], .55)
                self.assertEqual(got['bareTenCmBins'], 0)
            self.assertGreater(actual['lods'][2]['projectedCoverage'], actual['lods'][0]['projectedCoverage']*.94)
        boundary = fine.read(OUTPUT/'lawn-boundary-receipt.json'); self.assertEqual(len(boundary['windows']), 2)
        for window in boundary['windows']:
            actual, _ = fine.boundary_raster(records, rows, window['originCm'], window['axisUnitXY'], window['inwardUnitXY'], window['widthCm'], window['lengthCm'])
            for got, saved, old in zip(actual['lods'], window['lods'], window['rejectedR7Study']):
                for index, (g, s) in enumerate(zip(got['boundaryBands'], saved['boundaryBands'])):
                    self.assertAlmostEqual(g['physicalCoverFraction'], s['physicalCoverFraction'], delta=.0002)
                    self.assertGreater(g['physicalCoverFraction'], [.12, .40, .50][index])
                self.assertGreater(got['boundaryBands'][1]['physicalCoverFraction'], old['boundaryBands'][1]['physicalCoverFraction']+.10)

    def test_single_stochastic_population_and_truthful_physical_density(self):
        rows = self.plan['lawnPlacements']; interior = np.array([r['positionCm'][:2] for r in rows if not r['edge']])*10
        phase = np.abs(np.exp(2j*np.pi*interior/60).mean(axis=0)); self.assertLess(float(phase.max()), .025)
        np.testing.assert_allclose(phase, self.plan['audit']['interiorSixtyMmLatticePhaseAmplitudeXY'], atol=1e-10)
        whole = np.array([r['positionCm'][:2] for r in rows])*10
        np.testing.assert_allclose(np.abs(np.exp(2j*np.pi*whole/60).mean(axis=0)), self.plan['audit']['sixtyMmLatticePhaseAmplitudeXY'], atol=1e-10)
        self.assertIn('no independent border row', self.plan['audit']['placementMethod'])
        self.assertGreater(np.std([r['clearanceMm'] for r in rows if r['edge']]), 10)
        expected = sum(48 if r['edge'] else 64 for r in rows)/(self.domain.area/10000)
        self.assertAlmostEqual(expected, self.plan['audit']['bladesPerM2EveryLod'], places=8)

    def test_changed_architectural_frame_and_overwrite_rejected(self):
        with self.assertRaisesRegex(ValueError, 'immutable'): fine.build(GEOMETRY, RURAL, ORIGINAL, PRIOR, OUTPUT)
        for change in (lambda r: r['metadata']['activeDesign'].update(variant='A'),
                       lambda r: r['metadata']['housePlacement'].update(eastSetbackMm=2999)):
            with tempfile.TemporaryDirectory(dir=ROOT/'output/unreal') as tmp:
                folder = Path(tmp); r = deepcopy(fine.read(RURAL)); change(r)
                p = folder/'rural-context-geometry.json'; p.write_text(json.dumps(r))
                (folder/'scene.json').symlink_to(RURAL.parent/'scene.json'); (folder/'dom-mm.obj').symlink_to(RURAL.parent/'dom-mm.obj')
                with self.assertRaises(ValueError): fine.cover.managed_source(GEOMETRY, p, ORIGINAL)


if __name__ == '__main__': unittest.main()
