"""Actual photo-lawn integration and adversarial source delta tests (stdlib)."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT/'output/unreal/exterior-lawn-photo-integration-20261001-r1'


def module():
    spec = importlib.util.spec_from_file_location('photo_native_under_test', ROOT/'scripts/unreal/exterior-lawn-photo-native.py')
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def read(path):
    return json.loads(Path(path).read_text())


def write_glb(path, document, binary):
    body = json.dumps(document, separators=(',', ':'), allow_nan=False).encode()
    body += b' '*(-len(body) % 4)
    path.write_bytes(struct.pack('<4sII', b'glTF', 2, 28+len(body)+len(binary))
        +struct.pack('<II', len(body), 0x4e4f534a)+body
        +struct.pack('<II', len(binary), 0x004e4942)+binary)


class PhotographicLawnIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = module(); cls.plan = read(OUTPUT/'lawn-natural-plan.json')
        cls.full = read(OUTPUT/'geometry-manifest.json'); cls.extension = read(OUTPUT/'photo-geometry-manifest.json')
        cls.old_plan = read(cls.native.DONOR/'lawn-natural-plan.json')
        cls.original = read(cls.native.DONOR/'geometry-manifest.json')
        cls.coverage = read(cls.native.SELECTED/'photographic-alpha-coverage-receipt.json')
        cls.old_coverage = read(cls.native.DONOR/'lawn-coverage-receipt.json')
        cls.old_boundary = read(cls.native.DONOR/'lawn-boundary-coverage-receipt.json')
        cls.recipe = read(OUTPUT/'photo-material-manifest.json')[cls.native.MATERIAL]
        cls.photo_path = Path(cls.extension['meshes'][0]['glbPath'])
        cls.original_path = cls.native.DONOR/'lawn-natural.glb'

    def coverage_check(self, value):
        return self.native._coverage(value, self.old_coverage, self.old_boundary, self.recipe)

    def delta(self, path):
        return self.native.geometry_delta(self.original_path, path, self.original, self.extension)

    def changed_glb(self, change):
        document, binary, nodes = self.native._glb(self.photo_path)
        binary = bytearray(binary)
        change(document, binary, nodes)
        temporary = tempfile.TemporaryDirectory(prefix='photo-native-test-', dir=ROOT/'output/unreal')
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name)/'changed.glb'
        write_glb(path, document, binary)
        return path

    def test_actual120_master_adapter_preserves_ordered102011_roots_and40_groups(self):
        validation = self.native.validate_photo(self.plan, self.extension, self.full,
            self.plan['sourceSceneSha256'], self.plan['sourceObjSha256'])
        self.assertEqual(len(validation['groups']), 40)
        self.assertEqual(sum(len(g['instances']) for g in validation['groups']), 102011)
        self.assertEqual(validation['audit']['status'], 'verified-source-photographic-managed-lawn')
        for old, new in zip(self.old_plan['groups'], validation['groups']):
            self.assertEqual(new['meshId'], self.native.MAPPING[old['meshId']])
            self.assertEqual(new['instances'], [{k: row[k] for k in ('positionCm', 'yawDeg', 'scale')} for row in old['instances']])
            self.assertEqual((new['cullEndCm'], new['qualityDetail']), (4000, True))
        self.assertEqual(validation['audit']['allPopulationTriangleBudgets'], [18571200]*3)
        self.assertGreaterEqual(validation['audit']['minimumProjectedAlphaCoverage'], .75)
        self.assertFalse(validation['audit']['nativeVerified'])

    def test_original24_recipe_bytes_and_separate_exact_photo_recipe(self):
        self.assertEqual((OUTPUT/'material-manifest.json').read_bytes(), (self.native.BASE/'material-manifest.json').read_bytes())
        original = read(self.native.BASE/'material-manifest.json')
        self.assertEqual(len(original), 24)
        self.assertEqual(read(OUTPUT/'photo-material-manifest.json'), {self.native.MATERIAL: original['ph_grass_medium_02']})
        self.assertEqual(self.recipe['normalConvention'], 'DirectX')
        self.assertEqual(self.recipe['opacityMaskClipValue'], .333)
        self.assertNotIn('sourceEncodingOverride', self.recipe)

    def test_all60_decoded_nodes_change_only_permitted_uv_and_regenerated_tangents(self):
        proof = self.delta(self.photo_path)
        self.assertEqual((proof['meshes'], proof['lods']), (20, 60))
        self.assertEqual((proof['allLodGeometryVertices'], proof['allLodGeometryTriangles']), (18240, 10944))
        self.assertEqual(len(proof['changedBufferRanges']), 120)
        self.assertTrue(proof['rawPositionNormalColorUv1IndexBytesPreserved'])
        self.assertTrue(proof['decodedAllPrimitivesAndAccessors'])

    def test_repinned_position_normal_color_uv1_and_index_edits_are_rejected(self):
        for attribute in self.native.PRESERVED:
            with self.subTest(attribute=attribute):
                def change(document, binary, nodes):
                    start = next(iter(nodes.values()))['ranges'][attribute][0]
                    binary[start:start+4] = struct.pack('<I', 1) if attribute == 'indices' else struct.pack('<f', .125)
                with self.assertRaisesRegex(RuntimeError, 'bytes|index|inventory'):
                    self.delta(self.changed_glb(change))

    def test_extra_primitive_and_node_transform_rejected(self):
        for alteration in ('primitive', 'transform'):
            with self.subTest(alteration=alteration):
                def change(document, binary, nodes):
                    if alteration == 'primitive':
                        document['meshes'][0]['primitives'].append(deepcopy(document['meshes'][0]['primitives'][0]))
                    else:
                        document['nodes'][0]['translation'] = [0, .01, 0]
                with self.assertRaisesRegex(RuntimeError, 'primitive|transform'):
                    self.delta(self.changed_glb(change))

    def test_body_uv_repin_outside_measured_provider_strip_rejected(self):
        def change(document, binary, nodes):
            start = next(iter(nodes.values()))['ranges']['TEXCOORD_0'][0]
            binary[start:start+4] = struct.pack('<f', .77)
        with self.assertRaisesRegex(RuntimeError, 'body UV'):
            self.delta(self.changed_glb(change))

    def test_incorrect_tangent_handedness_and_nonorthogonal_frames_rejected(self):
        for alteration in ('handedness', 'direction'):
            with self.subTest(alteration=alteration):
                def change(document, binary, nodes):
                    start = next(iter(nodes.values()))['ranges']['TANGENT'][0]
                    if alteration == 'handedness':
                        value = struct.unpack_from('<f', binary, start+12)[0]
                        struct.pack_into('<f', binary, start+12, -value)
                    else:
                        struct.pack_into('<f', binary, start, 0.)
                with self.assertRaisesRegex(RuntimeError, 'tangent|handedness'):
                    self.delta(self.changed_glb(change))

    def test_wrong_mapping_height_material_lod_or_extra_master_rejected(self):
        for field in ('sourceMeshId', 'heightCm', 'materialKeys', 'lodScreenSizes', 'population'):
            value = deepcopy(self.extension)
            if field == 'population': value['meshes'].append(deepcopy(value['meshes'][0]))
            elif field == 'heightCm': value['meshes'][0][field] += .001
            elif field == 'materialKeys': value['meshes'][0][field] = ['lawn_natural_blade']
            elif field == 'lodScreenSizes': value['meshes'][0][field] = [1., .15, .04]
            else: value['meshes'][0][field] = 'lawn_natural_1_0'
            with self.subTest(field=field), self.assertRaisesRegex(RuntimeError, 'master|mapping|policy'):
                self.native._manifest_delta(self.original, value)

    def test_numeric_alpha_coverage_resolution_and_boolean_claims_rejected(self):
        for alteration in ('coverage', 'p10', 'resolution', 'boolean'):
            value = deepcopy(self.coverage); window = value['physicalCoverage']['windows'][0]
            if alteration == 'resolution': window['resolution'] = 3999
            else:
                for row in window['lods']:
                    if alteration == 'coverage': row['projectedCoverage'] = .74999
                    elif alteration == 'p10': row['tenCmBinCoverageP10'] = .54
                    else: row['projectedCoverage'] = True
            with self.subTest(alteration=alteration), self.assertRaisesRegex(RuntimeError, 'coverage|frame'):
                self.coverage_check(value)

    def test_actual_boundary_alpha_bands_frame_and_lod_loss_rejected(self):
        for alteration in ('band', 'frame', 'lod'):
            value = deepcopy(self.coverage); window = value['boundaryCoverage']['windows'][0]
            if alteration == 'band':
                for row in window['lods']: row['boundaryBands'][0]['physicalCoverFraction'] = .11999
            elif alteration == 'frame': window['originCm'][0] += .01
            else: window['lods'].pop()
            with self.subTest(alteration=alteration), self.assertRaisesRegex(RuntimeError, 'boundary'):
                self.coverage_check(value)

    def test_failed_actual_r2_raster_cannot_be_accepted_by_only_changing_pass_flags(self):
        value = read(ROOT/'output/unreal/exterior-lawn-photo-variants-20261001-r2-study/photographic-alpha-coverage-receipt.json')
        value.update(status=self.native.COVER_STATUS, allTargetsMet=True)
        for window in value['physicalCoverage']['windows']:
            for row in window['lods']: row['studyTargetsMet'] = True
        with self.assertRaisesRegex(RuntimeError, 'physical coverage gate'):
            self.coverage_check(value)

    def test_full_library_cannot_mutate_original100_or_add_foreign_master(self):
        for alteration in ('old', 'extra', 'frame'):
            value = deepcopy(self.full)
            if alteration == 'old': value['meshes'][0]['heightCm'] += .01
            elif alteration == 'extra': value['meshes'].append(deepcopy(value['meshes'][-1]))
            else: value['axes'] = 'Z-up'
            with self.subTest(alteration=alteration), self.assertRaisesRegex(RuntimeError, 'library'):
                self.native.validated_base_library(value)

    def test_exact_pinned_original100_subset_keeps_organic_and_all_other_source_records(self):
        original = self.native.validated_base_library(self.full)
        self.assertEqual(original, read(self.native.BASE/'geometry-manifest.json'))
        self.assertEqual(len(original['meshes']), 100)
        self.assertEqual(self.full['meshes'][:100], original['meshes'])
        organic = [row for row in original['meshes'] if row['id'].startswith('garden_') and '_organic_' in row['id']]
        self.assertEqual(len(organic), 4)

    def test_changed_active_root_transform_and_false_owner_status_rejected(self):
        wrong = deepcopy(self.plan); wrong['status'] = 'MEASURED_TAPERED_MANAGED_LAWN_NOT_NATIVE_ACCEPTED'
        with self.assertRaisesRegex(RuntimeError, 'owner/status'):
            self.native.validate_photo(wrong, self.extension, None, wrong['sourceSceneSha256'], wrong['sourceObjSha256'])
        wrong = deepcopy(self.plan); wrong['groups'][0]['instances'][0]['yawDeg'] += .001
        with self.assertRaisesRegex(RuntimeError, 'active roots'):
            self.native.validate_photo(wrong, self.extension, None, wrong['sourceSceneSha256'], wrong['sourceObjSha256'])


if __name__ == '__main__':
    unittest.main()
