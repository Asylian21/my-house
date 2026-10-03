"""Four measured-node/binding changes only; no inherited thirty-suite replay."""
import copy
import importlib.util
from pathlib import Path
import struct
import unittest
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('_r39r2_calibration_guards',
    ROOT/'scripts/unreal/exterior-neighbor-props-guards-r39-r2.py')
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)


class CalibrationContracts(unittest.TestCase):
    BUNDLE = None

    @classmethod
    def setUpClass(cls):
        if cls.BUNDLE is None:
            cls.BUNDLE = g.load_contract(validate_current=False)
        cls.b = cls.BUNDLE
        cls.parts = {p['key']: p for rows in cls.b['source']['parts'].values() for p in rows}

    def rejection(self, function, *args):
        with self.assertRaises(RuntimeError):
            function(*args)

    def test_01_actual_double_coil_route_and_original_source_preserved(self):
        part = self.parts['garden_hose_wall_mounted_01:1']
        expected = [-1.3036099262535572, 6.431593745946884, -5.608365684747696]
        self.assertEqual(g.native_node_translation(part), expected)
        self.assertNotEqual(expected, part['proposedNativeNodeTranslationCm'])
        self.assertEqual(part['proposedNativeNodeTranslationCm'], g.c.native_vec(part['sourceNodeTranslationMeters']))
        measured = self.b['nodePoseCalibration'][part['key']]
        self.assertTrue(g.binary_equal(expected, measured['actualObservedNativeNodePose'][0]))
        self.assertTrue(measured['futureFullOriginalCornerIdentityRequired'])
        self.assertFalse(measured['checkpointLabelsUsedForFutureGeometryIdentity'])
        self.assertFalse(measured['epsilonOrToleranceUsed'])
        original = copy.deepcopy(part)
        g.native_node_translation(part)
        self.assertEqual(part, original)
        changed = copy.deepcopy(part); changed['sourceNodeTranslationMeters'][0] += 1e-8
        self.rejection(g.native_node_translation, changed)

    def test_02_no_epsilon_or_count_name_acceptance(self):
        part = self.parts['garden_hose_wall_mounted_01:1']
        value = g.native_node_translation(part)
        wrong = value.copy()
        bits = struct.unpack('<Q', struct.pack('<d', wrong[1]))[0]
        wrong[1] = struct.unpack('<d', struct.pack('<Q', bits+1))[0]
        self.assertFalse(g.binary_equal(value, wrong))
        self.assertFalse(g.binary_equal([0.], [-0.]))
        changed = copy.deepcopy(part); changed['nodeName'] = 'arbitrary_same_count'
        self.rejection(g.native_node_translation, changed)
        evidence = g.repair_evidence()
        self.assertEqual(evidence['failedNativeProcessId'], 29845)
        self.assertEqual(evidence['failedNativeExitCode'], 255)
        self.assertEqual(evidence['inheritedExecutedR1TestCount'], 30)
        self.assertFalse(evidence['nativeFullGeometryAcceptedFromFailure'])
        self.assertFalse(evidence['originalMapSaveReached'])
        self.assertEqual(set(self.b['nodePoseCalibration']), set(self.parts))
        for key, row in self.b['nodePoseCalibration'].items():
            self.assertEqual(row['sourceNodeTranslationMeters'], self.parts[key]['sourceNodeTranslationMeters'])
            if row['actualNodePoseObservedInR1Failure']:
                self.assertIn('actualObservedNativeNodePose', row)
            else:
                self.assertNotIn('actualObservedNativeNodePose', row)

    def test_03_only_new_actual_repair_fresh_clone_binding(self):
        binding = self.b['binding']
        self.assertTrue(g.require_native_binding(binding))
        self.assertEqual(binding['schemaVersion'], 2)
        self.assertEqual(binding['candidateProject'], str(g.PROJECT))
        self.assertEqual(binding['repairSchema'], g.REPAIR_SCHEMA)
        for key, value in (('schemaVersion', 1), ('nativeOwner', g.old.NATIVE_OWNER),
                           ('candidateProject', str(g.old.PROJECT)), ('activeOutputPromoted', True)):
            wrong = copy.deepcopy(binding); wrong[key] = value
            self.rejection(g.require_native_binding, wrong)
        wrong = copy.deepcopy(binding)
        wrong['measuredNodePoseRepairEvidence']['failedNativeProcessId'] = 72504
        self.rejection(g.require_native_binding, wrong)

    def test_04_no_failed_partial_map_or_old_clone_reuse(self):
        clone = g.read(g.CLONE); base = self.b['base']; binding = self.b['binding']
        g.validate_clone_header(clone, binding, base['content'], base['protected'])
        for key, value in (('schemaVersion', 1), ('nativeExecuted', True),
                           ('wholeOriginalPropsNativePending', False)):
            wrong = copy.deepcopy(clone); wrong[key] = value
            self.rejection(g.validate_clone_header, wrong, binding, base['content'], base['protected'])
        wrong = copy.deepcopy(clone)
        wrong['measuredNodePoseRepairEvidence']['partialFailedProjectMapCopied'] = True
        self.rejection(g.validate_clone_header, wrong, binding, base['content'], base['protected'])
        wrong = copy.deepcopy(clone)
        wrong['measuredNodePoseRepairEvidence']['observedOriginalNodeCheckpoint']['sha256'] = '0'*64
        self.rejection(g.validate_clone_header, wrong, binding, base['content'], base['protected'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
