"""Focused source/adversarial checks; no Unreal, scientific imports or images accepted."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('transition_native_under_test',
    ROOT / 'scripts/unreal/exterior-neighborhood-transition-native.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


def png_bytes(rows, width=1024, height=1024):
    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)) + \
        chunk(b'IDAT', zlib.compress(b''.join(b'\0' + row for row in rows))) + chunk(b'IEND', b'')


def changed_glb(raw, edit_json=None, edit_binary=None):
    size, _ = struct.unpack_from('<II', raw, 12)
    document = json.loads(raw[20:20 + size])
    offset = 20 + size
    binary_size, _ = struct.unpack_from('<II', raw, offset)
    binary = bytearray(raw[offset + 8:offset + 8 + binary_size])
    if edit_binary: edit_binary(document, binary)
    if edit_json: edit_json(document)
    text = json.dumps(document, separators=(',', ':')).encode()
    text += b' ' * (-len(text) % 4)
    return struct.pack('<4sII', b'glTF', 2, 28 + len(text) + len(binary)) + \
        struct.pack('<II', len(text), 0x4e4f534a) + text + struct.pack('<II', len(binary), 0x004e4942) + binary


class TransitionNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads((native.STUDY / 'transition-plan.json').read_text())
        cls.context = native.read_pin(cls.plan['sourceContext'])
        cls.neighborhood = native.read_pin(cls.plan['sourceNeighborhood'])
        cls.merged = json.loads((ROOT / 'output/unreal/exterior-assets-shape-20261001-r1/geometry-manifest.json').read_text())
        cls.original = json.loads((ROOT / 'output/unreal/exterior-assets-greenery-20260930-r5/geometry-manifest.json').read_text())
        cls.report = json.loads((ROOT / 'output/unreal/exterior-20261001-r10/exterior-import-report.json').read_text())
        cls.meshes = native._source_meshes(cls.context, cls.neighborhood)
        cls.measured = native._library(cls.plan['prototypes'], cls.merged, cls.original)
        buildings = json.loads((ROOT / 'output/unreal/exterior-buildings-20260926-r2/building-plan.json').read_text())
        cls.domains, cls.blocked = native._spatial(cls.plan, cls.context, cls.neighborhood, buildings)
        cls.ground = native._Ground(cls.meshes)
        cls.result = native.validated_transition(cls.plan, cls.context, cls.merged,
                                               cls.plan['sourceSceneSha256'], cls.plan['sourceObjSha256'])

    def validate(self, plan=None, context=None, merged=None):
        return native.validated_transition(plan or self.plan, context or self.context, merged or self.merged,
                                          self.plan['sourceSceneSha256'], self.plan['sourceObjSha256'])

    def test_actual_r11_subset_source_crowns_pixels_and_preservation(self):
        result, audit = self.result, self.result['audit']
        self.assertEqual((len(result['materialBindings']), len(result['groups']), audit['instances']), (65, 158, 7000))
        self.assertEqual(audit['allLodTriangles'], [6351095, 3487981, 1584502])
        self.assertEqual(audit['condition']['actualRedRange'], [38, 217])
        self.assertTrue(audit['condition']['all1048576ConditionPixelsVerified'])
        self.assertEqual((audit['originalRemovalIndicesPreserved'], audit['originalVegetationRestoredOrMoved']), (47203, 0))
        self.assertEqual(audit['sourceGlbInventory'], {'nodes': 15, 'primitives': 15, 'accessors': 75,
                                                     'allPrimitiveAccessorsIncluded': True, 'selectedLodNodes': 9})
        self.assertEqual(audit['decodedPrototypeVertexInventory']['grass_medium_02_b'],
                         {'actual': [1575, 1082, 602], 'historicalManifest': [1575, 1059, 700]})
        self.assertFalse(audit['nativeVisualAccepted'])
        self.assertFalse(audit['performanceAccepted'])
        self.assertTrue(audit['sourceGeometryAndOriginalMaterialsUnchanged'])

    def test_owner_status_typed_frame_acceptance_and_pinned_plan_drift_rejected(self):
        changes = [lambda p: p.update(owner='scripts/unreal/exterior-context.py'),
                   lambda p: p.update(status='native-accepted'),
                   lambda p: p['housePlacement'].update(streetSetbackMm=2999),
                   lambda p: p.update(nativeVisualAccepted=True),
                   lambda p: p['summary'].update(transitionInstances=True),
                   lambda p: p['transitionPlacements'][0].update(yawDeg=0)]
        for change in changes:
            plan = copy.deepcopy(self.plan);change(plan)
            with self.subTest(change=change), self.assertRaises(RuntimeError): self.validate(plan)
        context = copy.deepcopy(self.context);context['meshes'][0]['verticesCm'][0][2] += .001
        with self.assertRaisesRegex(RuntimeError, 'source context'): self.validate(context=context)

    def test_exact65_source_material_native_actor_and_geometry_bindings(self):
        native._bindings(self.plan['materialBindingProposal'], self.meshes, self.report)
        edits = [lambda r: r.pop(), lambda r: r.append(copy.deepcopy(r[0])),
                 lambda r: r[0].update(expectedMaterialKey='context_arable'),
                 lambda r: r[0].update(sourceGeometrySha256='0' * 64),
                 lambda r: r[0].update(nativeActor=r[1]['nativeActor']),
                 lambda r: r[0].update(nativeMesh=r[1]['nativeMesh']),
                 lambda r: r[0].update(sourceVerticesAndIndicesUnchanged=1)]
        for edit in edits:
            rows = copy.deepcopy(self.plan['materialBindingProposal']);edit(rows)
            with self.subTest(edit=edit), self.assertRaises(RuntimeError): native._bindings(rows, self.meshes, self.report)

    def test_imported_current_prototype_subset_not_old_whole_manifest_identity(self):
        self.assertEqual(len(self.merged['meshes']), 100)
        # The guard checks precisely these3 preserved originals, allowing the
        # unrelated R11 organic/tapered library rows to differ from old96.
        self.assertEqual(set(native._library(self.plan['prototypes'], self.merged, self.original)), native.IDS)
        for key, value in [('materialKeys', ['garden_blade_green']), ('heightCm', 9000)]:
            merged = copy.deepcopy(self.merged)
            next(r for r in merged['meshes'] if r['id'] == 'grass_medium_02_a')[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(RuntimeError, 'prototype'): native._library(self.plan['prototypes'], merged, self.original)
        merged = copy.deepcopy(self.merged);merged['meshes'].append(copy.deepcopy(merged['meshes'][0]))
        with self.assertRaisesRegex(RuntimeError, 'duplicated'): native._library(self.plan['prototypes'], merged, self.original)

    def test_repinned_actual_glb_bounds_frames_accessors_and_node_changes_rejected(self):
        source = Path(self.plan['prototypes'][0]['glbPath']);raw = source.read_bytes()
        def move_position(document, binary):
            primitive = document['meshes'][0]['primitives'][0]
            accessor = document['accessors'][primitive['attributes']['POSITION']]
            view = document['bufferViews'][accessor['bufferView']]
            struct.pack_into('<f', binary, view['byteOffset'], 20.)
        def nan_normal(document, binary):
            primitive = document['meshes'][0]['primitives'][0]
            accessor = document['accessors'][primitive['attributes']['NORMAL']]
            view = document['bufferViews'][accessor['bufferView']]
            struct.pack_into('<f', binary, view['byteOffset'], math.nan)
        cases = [(None, move_position), (None, nan_normal),
                 (lambda d: d['nodes'][0].update(translation=[1, 0, 0]), None),
                 (lambda d: d['meshes'][0]['primitives'][0].update(targets=[{'POSITION': 0}]), None),
                 (lambda d: d['accessors'][0].update(count=644), None),
                 (lambda d: d['bufferViews'][0].update(byteStride=12), None)]
        with tempfile.TemporaryDirectory(prefix='transition-native-glb-', dir=ROOT / 'output/unreal') as folder:
            for i, (edit_json, edit_binary) in enumerate(cases):
                path = Path(folder) / str(i);path.write_bytes(changed_glb(raw, edit_json, edit_binary))
                prototypes = copy.deepcopy(self.plan['prototypes'])
                for row in prototypes: row.update(glbPath=str(path), glbSha256=native.sha(path))
                authority = {'meshes': copy.deepcopy(prototypes)}
                with self.subTest(case=i), self.assertRaises(RuntimeError): native._library(prototypes, authority, authority)

    def test_full_circular_crown_small_holes_and_source_buffers(self):
        geometry = {'type': 'Polygon', 'coordinates': [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]],
                                                     [[6, 4], [6.2, 4], [6.2, 4.2], [6, 4.2], [6, 4]]]}
        domain = native.substrate._PolygonIndex(geometry, cell=1.)
        native._circle_inside(domain, [2, 2], .5)
        # Root and common cardinal samples can remain inside while a tiny
        # off-axis hole is completely crossed by the full circular envelope.
        self.assertTrue(domain.contains([5, 5]))
        with self.assertRaisesRegex(RuntimeError, 'full crown'): native._circle_inside(domain, [5, 5], 1.7)
        with self.assertRaisesRegex(RuntimeError, 'full crown'): native._circle_inside(domain, [.2, 2], .3)
        blocker = native._BlockedCircles([geometry['coordinates']], margin=1., cell=1.)
        blocker.outside([-2, 5], .5)
        with self.assertRaisesRegex(RuntimeError, 'source exclusion'): blocker.outside([-.6, 5], .1)

    def test_actual_radius_ground_contact_scales_and_geometry_budget(self):
        edits = [lambda r: r[0]['scale'].__setitem__(1, r[0]['scale'][0] + .01),
                 lambda r: r[0].update(radiusCm=r[0]['radiusCm'] - .1),
                 lambda r: r[0].update(actualHeightCm=30),
                 lambda r: r[0].update(sourceGroundZCm=r[0]['sourceGroundZCm'] + .1),
                 lambda r: r[0]['positionCm'].__setitem__(2, r[0]['positionCm'][2] + .1),
                 lambda r: r[0].update(sourceGroundMeshId='DOM_00001'),
                 lambda r: r[0].update(wholeCrownOutsideSoilExposure=1)]
        for edit in edits:
            rows = copy.deepcopy(self.plan['transitionPlacements']);edit(rows)
            with self.subTest(edit=edit), self.assertRaises(RuntimeError):
                native._placements(rows, self.measured, self.domains, self.blocked, self.ground)
        measured = copy.deepcopy(self.measured);measured['grass_medium_02_a']['triangles'][0] += 1
        with self.assertRaisesRegex(RuntimeError, 'triangle budget'):
            native._placements(self.plan['transitionPlacements'], measured, self.domains, self.blocked, self.ground)

    def test_native_group_order_policies_and_original_clumps_not_restored(self):
        native._groups(self.plan['groups'], self.plan['transitionPlacements'])
        edits = [lambda g: g[0].update(collision='QueryOnly'), lambda g: g[0].update(castShadow=True),
                 lambda g: g[0].update(qualityDetail=True), lambda g: g[0].update(cullEndCm=9000),
                 lambda g: g[0]['instances'].reverse(), lambda g: g[0].update(id='EX_meadow_restored'),
                 lambda g: g.append(copy.deepcopy(g[0]))]
        for edit in edits:
            groups = copy.deepcopy(self.plan['groups']);edit(groups)
            with self.subTest(edit=edit), self.assertRaises(RuntimeError): native._groups(groups, self.plan['transitionPlacements'])

    def test_actual_png_repinned_channels_world_pixels_extent_and_crc(self):
        original = native._png_rgba(self.plan['conditionTexture']['path'])
        with tempfile.TemporaryDirectory(prefix='transition-native-png-', dir=ROOT / 'output/unreal') as folder:
            for index, channel in enumerate((0, 1, 2, 3)):
                rows = list(original);row = bytearray(rows[0]);row[channel] = (row[channel] + 1) % 256;rows[0] = bytes(row)
                path = Path(folder) / str(index);path.write_bytes(png_bytes(rows))
                with self.subTest(channel=channel), self.assertRaisesRegex(RuntimeError, 'channels|world-field'):
                    native._condition_pixels(str(path), native.sha(path))
            bad_crc = bytearray(Path(self.plan['conditionTexture']['path']).read_bytes());bad_crc[-1] ^= 1
            path = Path(folder) / 'crc';path.write_bytes(bad_crc)
            with self.assertRaisesRegex(RuntimeError, 'CRC'): native._png_rgba(path)
            path = Path(folder) / 'size';path.write_bytes(png_bytes(original, width=1023))
            with self.assertRaisesRegex(RuntimeError, '1024'): native._png_rgba(path)
        texture = copy.deepcopy(self.plan['conditionTexture']);texture['worldCmToUvRows'][0][2] += .01
        with self.assertRaisesRegex(RuntimeError, 'frame'): native._condition_texture(texture, self.plan['conditionTexture'])

    def test_bounded_pbr_response_source_pixels_proof_and_stdlib_only(self):
        for key in ('coverAmount', 'albedoScale', 'normalStrength', 'reuseExactly'):
            plan = copy.deepcopy(self.plan);plan['sharedPbrResponseProposal'][key] = 'unsafe replacement'
            with self.subTest(key=key), self.assertRaisesRegex(RuntimeError, 'frozen'): self.validate(plan)
        audit = self.result['audit']
        self.assertTrue(audit['futureSharedMaterialMustPreserveFieldMacroAndProtectedCameraOrtho'])
        for key in ('context_meadow', 'context_fallow'):
            recipe = self.report['materials']['materials'][key]['recipe']
            self.assertEqual(audit['originalSourceGroundRecipes'][key], native.digest(recipe))
            self.assertIn('fieldMacro', recipe)
        for path, expected in audit['inputFiles'].items(): self.assertEqual(native.sha(path), expected)
        self.assertFalse(any(name == prefix or name.startswith(prefix + '.')
                             for name in sys.modules for prefix in ('numpy', 'shapely', 'PIL', 'unreal')))


if __name__ == '__main__': unittest.main()
