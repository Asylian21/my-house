"""Measured three audit1ULP portability boundary; camera bytes remain exact."""
import copy
import importlib.util
import math
from pathlib import Path
import tempfile
import json
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('r3_numeric_guards',ROOT/'scripts/unreal/exterior-neighbor-finish-diagnostic-r3.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)


class DiagnosticR3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.probe=d.measured_probe();cls.expected={'view':cls.probe['expectedView'],'audit':cls.probe['expectedAudit']};cls.actual={'view':cls.probe['actualView'],'audit':cls.probe['actualAudit']}

    def test_actual_native_probe_three1ulp_fields_pass(self):
        self.assertNotEqual(self.expected,self.actual);self.assertTrue(d.compare_camera(self.expected,self.actual));self.assertEqual(self.expected['view'],self.actual['view']);self.assertEqual(len(self.probe['differences']),3)

    def test_2ulp_in_one_allowlisted_distance_rejected(self):
        actual=copy.deepcopy(self.expected);v=actual['audit']['protectedPrivateDistanceCm'];actual['audit']['protectedPrivateDistanceCm']=math.nextafter(math.nextafter(v,math.inf),math.inf)
        self.assertFalse(d.compare_camera(self.expected,actual))

    def test_absolute_cap_rejected_even_if_one_ulp(self):
        self.assertFalse(d.compare_camera(1e6,math.nextafter(1e6,math.inf),'$.audit.protectedPrivateDistanceCm'))

    def test_one_ulp_camera_drift_rejected(self):
        actual=copy.deepcopy(self.expected);actual['view']['eyeCm'][0]=math.nextafter(actual['view']['eyeCm'][0],math.inf);self.assertFalse(d.compare_camera(self.expected,actual))

    def test_one_ulp_unobserved_audit_drift_rejected(self):
        actual=copy.deepcopy(self.expected);actual['audit']['selectedEyeDistancesCm']['BU.572063']=math.nextafter(actual['audit']['selectedEyeDistancesCm']['BU.572063'],math.inf);self.assertFalse(d.compare_camera(self.expected,actual))

    def test_boolean_integer_string_and_added_keys_remain_exact(self):
        for key,value in [('sourceBuildingsChecked',651.0),('observedStreetAccessClaimed',0),('selectedBuildingId','BU.572063')]:
            actual=copy.deepcopy(self.expected);actual['audit'][key]=value
            with self.subTest(key=key):self.assertFalse(d.compare_camera(self.expected,actual))
        actual=copy.deepcopy(self.expected);actual['audit']['newfield']=True;self.assertFalse(d.compare_camera(self.expected,actual))

    def test_nonfinite_distance_rejected(self):
        for v in [float('nan'),float('inf')]:
            actual=copy.deepcopy(self.expected);actual['audit']['protectedPrivateDistanceCm']=v
            with self.subTest(value=str(v)):self.assertFalse(d.compare_camera(self.expected,actual))

    def test_real_r3_payload_and_all_lineage_pins_pass(self):
        s=d.validated_supplement();self.assertEqual(s['appendedViewpoints']['sha256'],'25d591b3309a6a0b2297f3eb1fef4d6785379b639662d68049ccc13a12bcd846');self.assertEqual(s['view'],self.probe['expectedView']);self.assertFalse(s['nativeApplied'])

    def test_supplement_false_flag_cannot_be_rebound_to_integer_zero(self):
        s=d.read(d.OUTPUT/'neighbor-finish-diagnostic-supplement.json');s['nativeApplied']=0
        with tempfile.TemporaryDirectory(prefix='r3-typed-flag-') as folder:
            p=Path(folder)/'supplement.json';p.write_text(json.dumps(s))
            with self.assertRaisesRegex(ValueError,'semantics/types'):d.validated_supplement(p)


if __name__=='__main__':unittest.main(verbosity=2)
