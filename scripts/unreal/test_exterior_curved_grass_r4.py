"""CPU adversarial guards against altering a faithfully measured native root."""
import copy
import importlib.util
import math
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True


def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


t=load('r20_r4_tests_transform_guard','exterior-curved-grass-transform-guards-r4.py')
n=load('r20_r4_tests_native','exterior-curved-grass-native-r4.py')
p=ROOT/'output/unreal/exterior-curved-grass-20261002-r1-study/curved-grass-plan.json'
result=n.validate_plan(n.read(p),p);rows,selected=result[4:6]
probe,lookup=t.validated_probe(selected,rows)
original=t.read(t.check_pin(probe['originalMembersBefore']))


class TransformRepair(unittest.TestCase):
    def setUp(self):
        self.source=next(r for r in selected if r['kind']=='small_a')
        self.reference=copy.deepcopy(lookup[(self.source['groupId'],self.source['instanceIndex'])])
        self.old=self.reference['originalNativeValue']
        self.actual=copy.deepcopy(self.reference['recoveredNativeValue'])
        self.matrix=copy.deepcopy(self.reference['actualStoredMatrixFullVertexFootprint']['actualNativeStoredDoubleMatrix'])
        self.mesh=copy.deepcopy(next(r for r in rows if r['id']==self.source['newMasterId']))

    def verify(self):
        return t.verify_root(self.source,self.old,self.actual,self.mesh,self.matrix,self.reference)

    def test_actual64_faithful_native_references_pass(self):
        for row in selected:
            ref=lookup[(row['groupId'],row['instanceIndex'])];mesh=next(m for m in rows if m['id']==row['newMasterId'])
            proof=t.verify_root(row,ref['originalNativeValue'],ref['recoveredNativeValue'],mesh,
                ref['actualStoredMatrixFullVertexFootprint']['actualNativeStoredDoubleMatrix'],ref)
            self.assertTrue(proof['storedMatrixExactMeasuredBinary64']);self.assertLessEqual(proof['actualStoredMatrixAllVertexRadiusCm'],14.)

    def test_one_ulp_root_translation_rejected(self):
        self.actual[0][0]=math.nextafter(self.actual[0][0],math.inf)
        with self.assertRaises(RuntimeError):self.verify()

    def test_one_ulp_recovered_quaternion_rejected(self):
        self.actual[1][2]=math.nextafter(self.actual[1][2],math.inf)
        with self.assertRaises(RuntimeError):self.verify()

    def test_one_ulp_recovered_scale_rejected(self):
        self.actual[2][0]=math.nextafter(self.actual[2][0],math.inf)
        with self.assertRaises(RuntimeError):self.verify()

    def test_one_ulp_actual_matrix_rejected(self):
        self.matrix[0][0]=math.nextafter(self.matrix[0][0],math.inf)
        with self.assertRaises(RuntimeError):self.verify()

    def test_numeric_negative_zero_not_implicitly_equal(self):
        self.actual[1][0]=-0.0
        with self.assertRaises(RuntimeError):self.verify()

    def test_nonfinite_or_nonfloat_native_value_rejected(self):
        for value in (float('nan'),float('inf'),False,0):
            a=copy.deepcopy(self.actual);a[1][0]=value
            with self.assertRaises(RuntimeError):t.exact_numeric(a,self.reference['recoveredNativeValue'],'bad')

    def test_wrong_selected_original_identity_rejected(self):
        self.source=copy.deepcopy(self.source);self.source['instanceIndex']+=1
        with self.assertRaises(RuntimeError):self.verify()

    def test_original_native_yaw_changed_rejected(self):
        self.old=copy.deepcopy(self.old);self.old[1][2]=math.nextafter(self.old[1][2],math.inf)
        with self.assertRaises(RuntimeError):self.verify()

    def test_source_authored_height_change_rejected(self):
        self.source=copy.deepcopy(self.source);self.source['authoredHeightCm']+=.01
        with self.assertRaises(RuntimeError):self.verify()

    def test_source_uniform_fit_change_rejected(self):
        self.source=copy.deepcopy(self.source);self.source['uniformScale']=math.nextafter(self.source['uniformScale'],math.inf)
        with self.assertRaises(RuntimeError):self.verify()

    def test_larger_fullvertex_footprint_rejected(self):
        self.mesh['expectedNativeVerticesCm']=[[v*2 for v in row]for row in self.mesh['expectedNativeVerticesCm']]
        with self.assertRaises(RuntimeError):self.verify()

    def test_unfaithful_constructor_probe_not_accepted(self):
        bad=copy.deepcopy(probe);bad['allPreInsertionRotationExactCopies']=False
        with self.assertRaises(RuntimeError):t.validate_observations(bad,selected,rows,original)

    def test_missing_actual_stored_matrix_rejected(self):
        bad=copy.deepcopy(probe);bad['nativeStoredMatrixReadback']['small_a']['available']=False
        with self.assertRaises(RuntimeError):t.validate_observations(bad,selected,rows,original)

    def test_source_root_order_or_duplicate_changes_rejected(self):
        bad=copy.deepcopy(selected);bad[0],bad[1]=bad[1],bad[0]
        with self.assertRaises(RuntimeError):t.validate_observations(probe,bad,rows,original)
        bad=copy.deepcopy(selected);bad[0]=bad[1]
        with self.assertRaises(RuntimeError):t.validate_observations(probe,bad,rows,original)

    def test_original_geometry_material_camera_scope_unchanged(self):
        self.assertEqual(n.read(p)['geometry']['sha256'],'dbcdd923db3e108af02f8ccb34ced8519e19f2792e64c6f18fd01b2c461b03e3')
        self.assertEqual(n.read(p)['sourceGlb']['sha256'],'11076f0272caf99a3a8bb75ffe27444045956475f159915af91ab484175a834b')
        self.assertEqual(len(selected),64);self.assertEqual(result[6],n.maps.canonical_recipe())
        self.assertEqual(n.read(p)['camera']['eyeCm'],[-5500,4700,230])
        self.assertIsNone(t.policy()['quaternionEpsilon']);self.assertIsNone(t.policy()['scaleEpsilon'])


if __name__=='__main__':unittest.main(verbosity=2)
