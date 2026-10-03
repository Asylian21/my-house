"""Small actual-geometry and adversarial tests for the additive meadow guard."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT/'output/unreal/exterior-meadow-infill-integration-20261001-r1'


def read(path): return json.loads(Path(path).read_text())


class AdditiveMeadowGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('meadow_actual_guard', ROOT/'scripts/unreal/exterior-meadow-infill-native.py')
        cls.native = importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.native)
        cls.plan = read(OUTPUT/'meadow-infill-plan.json'); cls.full = read(OUTPUT/'geometry-manifest.json')
        cls.extension = read(OUTPUT/'infill-geometry-manifest.json')
        cls.source = cls.native.read_pin(cls.plan['sourceInfillPlan'])
        cls.source_geo = cls.native.read_pin(cls.source['geometryManifest'])
        cls.prototypes = read(cls.native.STUDY/'meadow-prototypes.json')
        cls.decoded = cls.native._glb(cls.native.STUDY/'low-meadow.glb')
        cls.measured = cls.native._geometry(cls.source_geo, cls.prototypes, cls.decoded)
        cls.context, neighborhood, buildings = [cls.native.read_pin(cls.source[k]) for k in
            ('sourceContext', 'sourceNeighborhood', 'sourceBuildingPlan')]
        cls.spatial = cls.native._spatial(cls.source, cls.context, neighborhood, buildings)

    def test_actual126_library_and_all33483_decoded_crowns(self):
        result = self.native.validated_infill(self.plan, self.extension, self.full,
            self.plan['sourceSceneSha256'], self.plan['sourceObjSha256'], self.context)
        self.assertEqual((len(result['groups']), sum(len(g['instances']) for g in result['groups'])), (101, 33483))
        self.assertEqual(result['audit']['allLodTriangles'], [1607184, 1406286, 1205388])
        self.assertGreaterEqual(result['audit']['minimumFullCrownSourceClearanceCm'], .1)
        self.assertLess(result['audit']['maximumRootGroundErrorCm'], .000002)
        self.assertFalse(result['audit']['uniformFullGroundCoverClaim'])
        self.assertFalse(result['audit']['nativeAppearanceAccepted'])
        self.assertTrue(all(g['collision'] == 'NoCollision' and g['canEverAffectNavigation'] is False
            and g['densityScaling'] is True and (g['cullStartCm'], g['cullEndCm']) == (3200, 4000) for g in result['groups']))
        subsets = self.native.validated_libraries(self.full)
        self.assertEqual((len(subsets['original120']['meshes']), len(subsets['original100']['meshes'])), (120, 100))
        self.assertEqual(subsets['original120']['owner'], 'scripts/unreal/exterior-lawn-photo-integration.py')

    def test_swapped_original120_and_new_recipe_or_census_claim_rejected(self):
        value = deepcopy(self.full); value['meshes'][0], value['meshes'][1] = value['meshes'][1], value['meshes'][0]
        with self.assertRaisesRegex(RuntimeError, 'original120'): self.native.validated_libraries(value)
        value = deepcopy(self.full); value['nativeAppearanceAccepted'] = True
        with self.assertRaisesRegex(RuntimeError, 'metadata'): self.native.validated_libraries(value)
        value = deepcopy(self.extension); value['meshes'][0]['materialKeys'] = ['lawn_photographic_blade']
        with self.assertRaisesRegex(RuntimeError, 'meshes'): self.native.validated_infill(self.plan, value, None,
            self.plan['sourceSceneSha256'], self.plan['sourceObjSha256'])

    def test_repinned_mask_policy_and_old_removals_are_not_accepted(self):
        for field in ('allowedDomainCm', 'pilotDomainCm', 'policy', 'preservation'):
            value = deepcopy(self.plan); value[field] = {}
            with self.subTest(field=field), self.assertRaisesRegex(RuntimeError, 'domain|policy'):
                self.native.validated_infill(value, self.extension, None, value['sourceSceneSha256'], value['sourceObjSha256'])

    def test_direct_spatial_checks_reject_source_private_and_ground_changes(self):
        triangle = self.context['protectedTrianglesCm'][0]
        point = [sum(p[i] for p in triangle)/3 for i in range(2)]
        with self.assertRaisesRegex(RuntimeError, 'exclusion'):
            self.spatial[2][0].outside(point, .1)
        for mutation in ('z', 'scale', 'crown'):
            rows = deepcopy(self.source['infillPlacements'])
            if mutation == 'z': rows[0]['positionCm'][2] += 1
            elif mutation == 'scale': rows[0]['scale'][1] *= 1.01
            else: rows[0]['radiusCm'] *= .1
            with self.subTest(mutation=mutation), self.assertRaisesRegex(RuntimeError, 'ground|scale|crown'):
                self.native._placements(rows, self.measured, *self.spatial)

    def test_decoded_normal_tangent_and_true_lod_leaf_topology_rejected(self):
        for attribute in ('NORMAL', 'TANGENT', 'indices'):
            decoded = deepcopy(self.decoded); node = next(iter(decoded.values()))
            if attribute == 'NORMAL': node[attribute][0] = (0., 0., 0.)
            elif attribute == 'TANGENT': node[attribute][0] = (1., 1., 1., 0.)
            else: node[attribute][0] = node[attribute][1]
            with self.subTest(attribute=attribute), self.assertRaises(RuntimeError):
                self.native._geometry(self.source_geo, self.prototypes, decoded)

    def test_ordered_group_transforms_and_full_collision_policy_rejected(self):
        groups = deepcopy(self.source['groups']); groups[0]['instances'][0], groups[0]['instances'][1] = groups[0]['instances'][1], groups[0]['instances'][0]
        with self.assertRaisesRegex(RuntimeError, 'ordered101'): self.native._groups(groups, self.source['infillPlacements'])
        plan = deepcopy(self.plan); plan['groups'][0]['densityScaling'] = False
        with self.assertRaisesRegex(RuntimeError, 'canonical group'):
            self.native.validated_infill(plan, self.extension, None, plan['sourceSceneSha256'], plan['sourceObjSha256'])


if __name__ == '__main__': unittest.main()
