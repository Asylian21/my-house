"""CPU source/clone fixtures; no staging, native execution or new visibility proof."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('r23_camera_stage_test', ROOT/'scripts/unreal/exterior-context-yard-camera-stage-r23.py')
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


class CameraCases(unittest.TestCase):
    def test_frozen_r18_camera_payload_and_historical_audit(self):
        supplement = s.validated_supplement()
        self.assertEqual(supplement['view']['id'], s.VIEW_ID)
        self.assertEqual(supplement['view']['horizontalFovDegrees'], 76)
        self.assertFalse(supplement['sourceCameraAudit']['nativeOcclusionOrPlantVisibilityMeasured'])

    def test_two_actual_independent_clone_receipts_without_staging(self):
        for row in s.SOURCE_CASES.values():
            source, output = row['source'], row['output']
            report = s.read(row['report'])
            content = s.read(s.c.checked(report['afterContentInventory']))
            proof = s.read(s.c.checked(report['protectedProjectProof']))
            clone = s.read(output/'context-yard-camera-project-clone-r23.json')
            s.validate_clone(clone, source, output/'Project/BreziTwin', content, proof)

    def test_rehashed_clone_cannot_change_pending_owner_or_source_identity(self):
        row = next(iter(s.SOURCE_CASES.values()))
        clone = s.read(row['output']/'context-yard-camera-project-clone-r23.json')
        report = s.read(row['report'])
        content = s.read(s.c.checked(report['afterContentInventory']))
        proof = s.read(s.c.checked(report['protectedProjectProof']))
        for key, value in [('schema', 'unknown'), ('fullSavedSourceReaderValidationPending', False),
                           ('fileCount', 1), ('sourceKind', 'saved-r32a-resolved-yard-ground-low-detail-candidate')]:
            fixture = copy.deepcopy(clone)
            fixture[key] = value
            with self.assertRaises(AssertionError):
                s.validate_clone(fixture, row['source'], row['output']/'Project/BreziTwin', content, proof)

    def test_unknown_native_source_rejects_before_reader_or_data_mutation(self):
        with self.assertRaises(AssertionError):
            s.actual_source(ROOT/'output/unreal/exterior-20261002-r32-unknown')


if __name__ == '__main__':
    unittest.main()
