"""Actual native focus receipts and narrow R7 evidence boundary checks."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('greenery_evidence',HERE/'exterior-greenery-audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
R5=ROOT/'output/unreal/exterior-validation-20260930-r1/qa/before-exterior-greenery-r6-1790783346386/exterior-garden-day-retina-cinematic-static-d9f0366f-e0b0-4d3d-974a-25a95e92a09b'
R6A=ROOT/'output/unreal/exterior-validation-20260930-r1/qa/after-exterior-r6a-1790787880169/exterior-garden-day-retina-cinematic-static-24839dc5-9439-4725-9633-d6a44953ccd5'


class GreeneryEvidence(unittest.TestCase):
    def test_actual_complete_foreground_receipt_is_eligible_but_not_performance_acceptance(self):
        r,q=audit.read(R5/'runtime.json'),audit.read(R5/'qa.json')
        result=audit.timing_evidence(r,q)
        self.assertTrue(result['timingValid']);self.assertFalse(result['timingInvalid'])
        self.assertEqual(result['sampleCount'],300);self.assertFalse(result['performanceAccepted'])

    def test_actual_locked_r6a_focus_zero_is_rejected_in_default_mode(self):
        r,q=audit.read(R6A/'runtime.json'),audit.read(R6A/'qa.json')
        self.assertEqual(r['focusDuringBenchmark']['applicationForegroundSamples'],0)
        with self.assertRaisesRegex(RuntimeError,'Timing invalid'):audit.timing_evidence(r,q)

    def test_actual_locked_r6a_artifacts_keep_explicit_invalid_timing(self):
        r,q=audit.read(R6A/'runtime.json'),audit.read(R6A/'qa.json')
        result=audit.timing_evidence(r,q,artifact_only=True)
        self.assertTrue(result['timingInvalid']);self.assertFalse(result['timingValid'])
        self.assertFalse(result['performanceAccepted']);self.assertIn('cannot establish',result['timingInvalidReason'])
        self.assertEqual(result['applicationForegroundSamples'],0)

    def test_window_only_or_partial_application_focus_never_satisfies_default(self):
        actual=audit.read(R5/'runtime.json');original=audit.read(R5/'qa.json')
        for field,value in [('gameWindowActiveSamples',299),('applicationForegroundSamples',299)]:
            runtime,qa=deepcopy(actual),deepcopy(original);runtime['focusDuringBenchmark'][field]=value
            qa['foreground']=deepcopy(runtime['focusDuringBenchmark'])
            with self.assertRaisesRegex(RuntimeError,'Timing invalid'):audit.timing_evidence(runtime,qa)
            self.assertTrue(audit.timing_evidence(runtime,qa,True)['timingInvalid'])

    def test_actual_r6a_import_cannot_be_mistaken_for_exact_r7_scope(self):
        with self.assertRaisesRegex(RuntimeError,'recipe count'):audit.audit_materials(ROOT/'output/unreal/exterior-20260930-r6a',audit.read(ROOT/'output/unreal/exterior-20260930-r6a/exterior-import-report.json'))

    def test_frozen_r7_plan_and_library_pins_are_current_exact_inputs(self):
        for name,value in [('geometry-manifest.json',audit.MASTER_SHA),('material-manifest.json',audit.MATERIAL_SHA),('asset-manifest.json',audit.ASSET_SHA)]:
            self.assertEqual(audit.sha(audit.ASSETS/name),value)
        for path,value in audit.PLANS.values():self.assertEqual(audit.sha(ROOT/'output/unreal'/path),value)


if __name__=='__main__':unittest.main()
