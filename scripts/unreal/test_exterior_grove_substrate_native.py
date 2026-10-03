"""Pinned-source and unsafe-geometry rejection checks; no native editor jobs."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('grove_substrate_native_test', HERE / 'exterior-grove-substrate-native.py')
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
PLAN = M.ROOT / 'output/unreal/exterior-grove-substrate-20260930-r3/grove-substrate-plan.json'
CONTEXT = M.ROOT / 'output/unreal/exterior-context-20260927-r8/context-plan.json'


def read(path):
    return json.loads(Path(path).read_text())


def rectangle(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]


class GroveSubstrateNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan, cls.context = read(PLAN), read(CONTEXT)

    def validate(self, plan=None, context=None):
        return M.validated_substrate(plan or self.plan, context or self.context,
            self.context['sourceSceneSha256'], self.context['sourceObjSha256'])

    def changed_plan(self):
        # The large unchanged geometry remains shared in rejection cases.
        plan = deepcopy({k: v for k, v in self.plan.items() if k != 'meshes'})
        plan['meshes'] = self.plan['meshes']
        return plan

    def changed_mesh(self, index=0):
        plan = self.changed_plan()
        plan['meshes'] = list(self.plan['meshes'])
        plan['meshes'][index] = deepcopy(plan['meshes'][index])
        return plan, plan['meshes'][index]

    def test_actual_full_geometry_provider_maps_original_78_ground_and_read_only_inputs(self):
        before = M.digest(self.plan), M.digest(self.context)
        result = self.validate()
        audit = result['audit']
        self.assertEqual(audit['status'], 'verified-source-grove-substrate')
        self.assertEqual((audit['meshes'], audit['vertices'], audit['triangles']), (53, 216024, 406669))
        self.assertAlmostEqual(audit['areaM2'], 3055.2104873855205, places=6)
        self.assertEqual((audit['existingTrees'], audit['deletedTrees'], audit['hiddenOriginalActors']), (78, 0, 0))
        self.assertEqual((audit['nativePhotographicMaps'], audit['offlineProviderDisplacementMaps']), (3, 1))
        self.assertTrue(audit['providerPixelsUnchanged'] and audit['sourceGroundUnchanged'])
        self.assertFalse(audit['sourceElevationMeasured'] or audit['nativeAppearanceAccepted'])
        self.assertEqual(set(audit['actualRenderedGroundSources']), {'context_unresolved_flat_backdrop'})
        self.assertGreater(audit['fullInteriorVertices'], 0)
        self.assertGreater(audit['outerAlphaZeroVertices'], 0)
        self.assertEqual((M.digest(self.plan), M.digest(self.context)), before)

    def test_owner_frame_setbacks_context_root_order_and_forged_domain_rejected(self):
        changes = [lambda p: p.update(owner='scripts/unreal/unsafe.py'),
            lambda p: p.update(sourceObjSha256='0' * 64),
            lambda p: p['activeDesign'].update(variant='A'),
            lambda p: p['housePlacement'].update(eastSetbackMm=2999),
            lambda p: p['trees'].reverse(),
            lambda p: p.update(domainCm=json.dumps({'type': 'Polygon', 'coordinates': [rectangle(0, 0, 100, 100)]}))]
        for change in changes:
            plan = self.changed_plan()
            change(plan)
            with self.assertRaises(RuntimeError):
                self.validate(plan)
        context = deepcopy(self.context)
        context['regionalVegetationPlacements'][0]['positionCm'][0] += .01
        with self.assertRaisesRegex(RuntimeError, 'original source context'):
            self.validate(context=context)

    def test_source_ground_or_building_optional_pin_substitution_rejected(self):
        for key in ('sourceTerrain', 'sourceBuildings', 'sourceEcology', 'sourceScene'):
            plan = self.changed_plan()
            plan[key] = deepcopy(plan['sourceContext'])
            with self.assertRaises((RuntimeError, KeyError)):
                self.validate(plan)
        plan = self.changed_plan()
        plan['inputFiles'][plan['sourceScene']['path']] = '0' * 64
        with self.assertRaisesRegex(RuntimeError, 'path/hash'):
            self.validate(plan)

    def test_whole_triangle_rejects_small_hole_missed_by_vertices_and_all_midpoints(self):
        hole = rectangle(2.8, 2.8, 3.2, 3.2)
        domain = M._PolygonIndex({'type': 'Polygon', 'coordinates': [rectangle(0, 0, 10, 10), hole]})
        triangle = [[0, 0], [0, 10], [10, 0]]
        samples = triangle + [[0, 5], [5, 5], [5, 0], [10 / 3, 10 / 3]]
        self.assertTrue(all(domain.contains(point) for point in samples))
        with self.assertRaisesRegex(RuntimeError, 'boundary/hole'):
            domain.triangle_inside(triangle)
        domain.triangle_inside([[0, 0], [0, 1], [1, 0]])

    def test_spatial_boundary_crown_and_blocker_checks_have_no_box_only_shortcut(self):
        domain = M._PolygonIndex({'type': 'Polygon', 'coordinates': [rectangle(0, 0, 1000, 1000)]})
        self.assertTrue(domain.contains([0, 400]))
        self.assertTrue(domain.contains([500, 500]))
        self.assertFalse(domain.contains([-1, 400]))
        self.assertAlmostEqual(domain.distance([40, 400]), 40)
        crowns = M._Crowns([{'positionCm': [0, 0, -25], 'radiusCm': 100},
                            {'positionCm': [150, 0, -25], 'radiusCm': 100}])
        self.assertTrue(crowns.contains([75, 0]))
        self.assertFalse(crowns.contains([75, 100]))
        blockers = M._Blockers([M.base._Geo({'type': 'Polygon', 'coordinates': [rectangle(0, 0, 10, 10)]})])
        for point in ([5, 5], [0, 5]):
            with self.assertRaisesRegex(RuntimeError, 'exclusion'):
                blockers.outside(point)
        blockers.outside([11, 5])

    def test_actual_collision_shadow_cull_winding_duplicate_or_out_of_range_index_rejected(self):
        changes = [lambda m: m.update(collision='BlockAll'), lambda m: m.update(castShadow=True),
            lambda m: m.update(maxDrawDistanceCm=18001), lambda m: m.update(material='context_meadow'),
            lambda m: m['indices'].__setitem__(0, len(m['verticesCm'])),
            lambda m: m['indices'].__setitem__(slice(0, 3), m['indices'][:3][::-1]),
            lambda m: m['indices'].extend(m['indices'][:3])]
        for change in changes:
            plan, mesh = self.changed_mesh()
            change(mesh)
            with self.assertRaisesRegex(RuntimeError, 'policy|index|winding|duplicate'):
                self.validate(plan)

    def test_actual_core_hole_opaque_edge_uv_seam_low_relief_and_fake_measured_ground_rejected(self):
        for kind in ('core', 'edge', 'height', 'normal', 'ground'):
            selected = next(i for i, mesh in enumerate(self.plan['meshes']) if any(uv[0] == 1 for uv in mesh['uvs'])) if kind == 'core' else 0
            plan, mesh = self.changed_mesh(selected)
            if kind == 'core':
                index = next(i for i, uv in enumerate(mesh['uvs']) if uv[0] == 1)
                mesh['uvs'][index][0] = .5
            elif kind == 'edge':
                index = min(range(len(mesh['uvs'])), key=lambda i: mesh['uvs'][i][0])
                mesh['uvs'][index][0] = 1
            elif kind == 'height':
                mesh['verticesCm'][0][2] += 2
                mesh['bounds']['max'][2] = max(p[2] for p in mesh['verticesCm'])
                mesh['bounds']['min'][2] = min(p[2] for p in mesh['verticesCm'])
            elif kind == 'normal':
                mesh['normals'][0] = [0, 0, -1]
            else:
                mesh['sourceGround']['measuredElevation'] = True
            with self.assertRaisesRegex(RuntimeError, 'alpha|edge|relief|normal|elevation'):
                self.validate(plan)

    def test_official_provider_response_or_map_identity_forgery_rejected(self):
        acquisition = M.read_pin(self.plan['acquisitionManifest'])
        original = M.read_pin
        changes = [lambda a: a['filesApi'].update(sha256='0' * 64),
            lambda a: a.update(physicalTileCm=151),
            lambda a: a['maps']['normal'].update(providerRole='nor_dx'),
            lambda a: a['maps']['albedo'].update(md5='0' * 32),
            lambda a: a['maps']['roughness'].update(width=1024)]
        for change in changes:
            unsafe = deepcopy(acquisition)
            change(unsafe)
            with patch.object(M, 'read_pin', side_effect=lambda pin: unsafe
                if pin == self.plan['acquisitionManifest'] else original(pin)):
                with self.assertRaisesRegex(RuntimeError, 'provider|metadata|acquisition'):
                    M._validate_photographic_sources(self.plan)

    def test_recipe_random_holes_rotation_wrong_map_far_fade_and_policy_claim_rejected(self):
        recipes = M.read_pin(self.plan['materialManifest'])
        original = M.read_pin
        for key, value in (('stochasticGround', True), ('yawDegrees', 20), ('distanceFadeCm', [1, 2]),
                           ('tileCm', 200), ('featherUV', False)):
            unsafe = deepcopy(recipes)
            unsafe[M.MATERIAL][key] = value
            with patch.object(M, 'read_pin', side_effect=lambda pin: unsafe
                if pin == self.plan['materialManifest'] else original(pin)):
                with self.assertRaisesRegex(RuntimeError, 'material'):
                    M._validate_photographic_sources(self.plan)
        plan = self.changed_plan()
        plan['policy']['sourceGroundUnchanged'] = False
        with self.assertRaisesRegex(RuntimeError, 'policy'):
            M._validate_policy(plan)


if __name__ == '__main__':
    unittest.main()
