"""Actual frozen candidate plus targeted adversarial stdlib guard tests."""
from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]


class ContinuousMeadowGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / 'scripts/unreal/exterior-meadow-continuous-native.py'
        spec = importlib.util.spec_from_file_location('actual_continuous_guard', path)
        cls.guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.guard)
        cls.plan, cls.receipt, cls.sources, cls.sidecars = cls.guard._bundle()
        cls.context, cls.neighborhood, cls.transition = [cls.sources[name] for name in
            ('context-plan.json', 'neighborhood-details.json', 'transition-plan.json')]
        cls.spatial = cls.guard._spatial(cls.plan, cls.context, cls.neighborhood, cls.sources['building-plan.json'])
        cls.measured = cls.guard._prototypes(cls.plan, cls.sources['prototypes.json'], cls.sources['nativeReceipt'])

    def invoke(self, plan=None, context=None, neighborhood=None, transition=None):
        return self.guard.validated_layout(self.plan if plan is None else plan, self.context if context is None else context,
            self.neighborhood if neighborhood is None else neighborhood, self.transition if transition is None else transition,
            self.plan['sourceSceneSha256'], self.plan['sourceObjSha256'])

    def identity(self, value, context=None, neighborhood=None, transition=None):
        self.guard._validate_identity(value, self.context if context is None else context,
            self.neighborhood if neighborhood is None else neighborhood, self.transition if transition is None else transition,
            self.plan['sourceSceneSha256'], self.plan['sourceObjSha256'], self.plan, self.sources)

    def test_actual_complete_layout_and_original_arrays_unchanged(self):
        before = self.guard.digest(self.context)
        result = self.invoke()
        audit = result['audit']
        self.assertEqual((len(result['restoredGroups']), sum(len(g['instances']) for g in result['restoredGroups'])), (164, 39834))
        self.assertEqual(audit['allChangedWhole141mmCrownsRechecked'], 259641)
        self.assertEqual(audit['retainedHeightOnlyOverrides'], 219807)
        self.assertEqual(audit['retainedArrayCounts'], {'meadowBladePlacements': 348231, 'meadowUnderstoryPlacements': 73941, 'groundCoverPlacements': 2547})
        self.assertEqual((len(result['neighborhoodMeshes']), audit['neighborhoodTriangles']), (143, 142105))
        self.assertEqual(audit['soilTriangleCentroidMembershipRechecked'], 106193)
        self.assertEqual(audit['retainedCultivatedSoilTriangles'], 2801)
        self.assertEqual(audit['restoredAllLodSourceTriangles'], [10197504, 2549376, 956016])
        self.assertEqual(len(result['materialBindings65']), 65)
        self.assertEqual(self.guard.digest(self.context), before)
        self.assertTrue(all(g['canEverAffectNavigation'] is False and g['navigation'] is False and g['qualityDetail'] is True and
            g['collision'] == 'NoCollision' and (g['cullStartCm'], g['cullEndCm']) == (7200, 9000) for g in result['restoredGroups']))
        self.assertTrue(audit['sourceInputsValidated'])
        self.assertFalse(audit['domainBooleanUnionRecomputedHere'])
        self.assertFalse(audit['nativeGeometryDecodedOrSaved'])
        self.assertTrue(all(audit[k] is False for k in ('nativeApplied', 'nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted')))
        self.assertEqual([(r['historicalSourceGroups'], r['historicalSourceInstances'], r['placementsReturnedForUse'])
            for r in result['retirementHistoricalSourcePlans']], [(158, 7000, 0), (101, 33483, 0)])
        self.assertTrue(all(r['retirementActuallyAppliedToNative'] is False for r in result['retirementHistoricalSourcePlans']))
        del result

    def test_typed_owner_hash_status_and_native_claims_rejected(self):
        for key, value in (('owner', 'scripts/unreal/exterior-meadow-infill-pilot.py'), ('generatorSha256', '0'*64),
                           ('status', 'NATIVE_ACCEPTED'), ('schemaVersion', True), ('nativeApplied', True),
                           ('nativeAppearanceAccepted', True), ('fullPhotorealismAccepted', True), ('integrationAuthorized', True),
                           ('performanceAccepted', 0)):
            plan = dict(self.plan); plan[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(RuntimeError, 'typed|claim'):
                self.identity(plan)

    def test_repinned_mask_design_binding_and_retirement_not_accepted(self):
        for key in ('targetGroundDomainCm', 'activeDesign', 'housePlacement', 'materialBindingProposal', 'rootPolicy', 'futureVisualRetirement'):
            plan = dict(self.plan); plan[key] = {}
            with self.subTest(key=key), self.assertRaisesRegex(RuntimeError, 'frozen plan'):
                self.identity(plan)

    def test_original_context_xy_root_order_and_removals_rejected(self):
        context = dict(self.context)
        context['meadowBladePlacements'] = list(self.context['meadowBladePlacements'])
        context['meadowBladePlacements'][0] = deepcopy(context['meadowBladePlacements'][0])
        context['meadowBladePlacements'][0]['positionCm'][0] += .01
        with self.assertRaisesRegex(RuntimeError, 'unfiltered frozen R8'):
            self.identity(self.plan, context=context)
        context['meadowBladePlacements'] = list(self.context['meadowBladePlacements'])
        context['meadowBladePlacements'][0], context['meadowBladePlacements'][1] = context['meadowBladePlacements'][1], context['meadowBladePlacements'][0]
        with self.assertRaisesRegex(RuntimeError, 'unfiltered frozen R8'):
            self.identity(self.plan, context=context)
        neighborhood = dict(self.neighborhood)
        neighborhood['groundDetailRemovedPlacementIndices'] = dict(neighborhood['groundDetailRemovedPlacementIndices'])
        neighborhood['groundDetailRemovedPlacementIndices']['meadowBladePlacements'] = neighborhood['groundDetailRemovedPlacementIndices']['meadowBladePlacements'][1:]
        with self.assertRaisesRegex(RuntimeError, 'neighborhood/removal'):
            self.identity(self.plan, neighborhood=neighborhood)

    def test_pin_escape_and_sidecar_hash_drift_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'escaped path'):
            self.guard.pinned('/private/etc/hosts', '0'*64)
        with self.assertRaisesRegex(RuntimeError, 'type/format'):
            self.guard.pinned(self.guard.STUDY/'restored-roots.json', True)
        with patch.object(self.guard, 'sha', return_value='0'*64), self.assertRaisesRegex(RuntimeError, 'pin drift'):
            self.invoke()

    def test_mixed_cultivated_uv_material_and_indices_change_rejected(self):
        original = self.sidecars['cultivated-soil-subsets.json']
        for key in ('uvs', 'material', 'indices', 'normals'):
            rows = list(original); rows[0] = deepcopy(original[0])
            if key == 'uvs': rows[0]['uvs'][0][0] += .01
            elif key == 'indices': rows[0]['indices'][0], rows[0]['indices'][1] = rows[0]['indices'][1], rows[0]['indices'][0]
            elif key == 'normals': rows[0]['normals'] = [[0, 0, 1]]
            else: rows[0]['material'] = 'context_continuous_unbuilt_ground'
            with self.subTest(key=key), self.assertRaisesRegex(RuntimeError, 'vertices/UV|indices/winding'):
                self.guard._soil(self.plan, self.neighborhood, rows, self.context)

    def test_soil_partition_missing_duplicate_or_reclassified_triangle_rejected(self):
        for mutation in ('missing', 'duplicate', 'crop'):
            plan = dict(self.plan); plan['soilOverlayProposal'] = deepcopy(self.plan['soilOverlayProposal'])
            row = next(r for r in plan['soilOverlayProposal']['triangles'] if r['omittedTriangleCount'] and r['retainedTriangleCount'])
            if mutation == 'missing': row['omitSourceTriangleOrdinals'].pop()
            elif mutation == 'duplicate': row['keepSourceTriangleOrdinals'].append(row['keepSourceTriangleOrdinals'][0])
            else:
                index = row['omitSourceTriangleOrdinals'].pop(0); row['keepSourceTriangleOrdinals'].append(index)
                row['keepSourceTriangleOrdinals'].sort(); row['omittedTriangleCount'] -= 1; row['retainedTriangleCount'] += 1
            with self.subTest(mutation=mutation), self.assertRaisesRegex(RuntimeError, 'partition|centroid'):
                self.guard._soil(plan, self.neighborhood, self.sidecars['cultivated-soil-subsets.json'], self.context)

    def test_original_prototype_uv_normal_and_connectivity_decoder_rejected(self):
        for key in ('uv0', 'normals', 'faces'):
            source = list(self.sources['prototypes.json']); source[0] = deepcopy(source[0])
            if key == 'uv0': source[0][key][0][0] = math.nan
            elif key == 'normals': source[0][key][0] = [0, 0, 0]
            else: source[0][key][0] = [0, 0, 0]
            with self.subTest(key=key), self.assertRaisesRegex(RuntimeError, 'UV decoder|normal decoder|degenerate'):
                self.guard._prototypes(self.plan, source, self.sources['nativeReceipt'])

    def test_restoration_order_original_position_and_scale_rejected(self):
        original = self.sidecars['restored-roots.json']
        for mutation in ('order', 'xy', 'scale', 'height'):
            rows = list(original)
            if mutation == 'order': rows[0], rows[1] = rows[1], rows[0]
            else:
                rows[0] = deepcopy(original[0])
                if mutation == 'xy': rows[0]['positionCm'][0] += .01
                elif mutation == 'scale': rows[0]['scale'][2] *= 1.01
                else: rows[0]['proposedHeightCm'] += .1
            with self.subTest(mutation=mutation), self.assertRaisesRegex(RuntimeError, 'membership/order|original XY|scale/group|growth field'):
                self.guard._restored(self.plan, rows, self.sidecars['restored-groups.json'], self.context, self.neighborhood, self.measured, self.spatial)

    def test_full_crown_boundary_private_road_and_building_exclusions_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'whole 14.1cm crown'):
            self.guard._crown([999999, 999999, 0], self.spatial)
        for mask in self.spatial[1]:
            polygon = mask.polygons[0]
            a, b = polygon[0][0], polygon[0][1]
            point = [(a[i]+b[i])/2 for i in (0, 1)]
            with self.subTest(margin=mask.margin), self.assertRaisesRegex(RuntimeError, 'exclusion'):
                mask.outside(point, 14.1)
        rows = self.sidecars['restored-roots.json']
        point = list(rows[0]['positionCm']); point[2] += .01
        with self.assertRaisesRegex(RuntimeError, 'root Z'):
            self.guard._crown(point, self.spatial, rows[0]['sourceGroundMeshId'], point[2])

    def test_height_override_types_removed_index_and_order_rejected(self):
        original = self.sidecars['retained-height-overrides.json']
        for mutation in ('type', 'order', 'removed'):
            value = dict(original); value['arrays'] = dict(original['arrays'])
            rows = list(value['arrays']['meadowBladePlacements']); value['arrays']['meadowBladePlacements'] = rows
            rows[0] = list(rows[0])
            if mutation == 'type': rows[0][1] = True
            elif mutation == 'order': rows[0], rows[1] = rows[1], rows[0]
            else:
                rows[0][0] = self.neighborhood['groundDetailRemovedPlacementIndices']['meadowBladePlacements'][0]
                rows.sort(key=lambda r:r[0])
            with self.subTest(mutation=mutation), self.assertRaisesRegex(RuntimeError, 'typed|index order|include removed'):
                self.guard._retained(self.context, self.neighborhood, value, self.spatial)

    def test_ordered_native_group_transforms_collision_navigation_culls_rejected(self):
        expected = self.sidecars['restored-groups.json']
        for key in ('navigation', 'collision', 'cullStartCm', 'qualityDetail', 'instances'):
            groups = list(expected); groups[0] = deepcopy(expected[0])
            if key == 'navigation': groups[0][key] = True
            elif key == 'collision': groups[0][key] = 'BlockAll'
            elif key == 'cullStartCm': groups[0][key] = 3200
            elif key == 'qualityDetail': groups[0][key] = 1
            else: groups[0][key][0], groups[0][key][1] = groups[0][key][1], groups[0][key][0]
            with self.subTest(key=key), self.assertRaisesRegex(RuntimeError, 'ordered native group transforms/policies'):
                self.guard._native_groups(groups, expected)


if __name__ == '__main__':
    unittest.main()
