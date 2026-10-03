"""Source-only raw matrix shape/order/binary64 and actual original8949 guards."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('coverage_raw_guard_tests',ROOT/'scripts/unreal/exterior-realism-grass-coverage-probe-guards-r2.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
_,bundle,_,original,_=g.source_basis()
M=[[1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.],[100.,200.,300.,1.]]
ns=importlib.util.spec_from_file_location('coverage_probe_seed_tests',ROOT/'scripts/unreal/exterior-realism-grass-coverage-probe-r2.py')
native=importlib.util.module_from_spec(ns);ns.loader.exec_module(native)


class MatrixCapture(unittest.TestCase):
    def test_actual_original8949_ordered_native_values(self):
        g.validate_original_values(original,bundle['base'],original)
        self.assertEqual(sum(map(len,original.values())),8949)

    def test_source_group_member_reordering_rejected(self):
        values=copy.deepcopy(original);group=next(iter(values));values[group][0],values[group][1]=values[group][1],values[group][0]
        with self.assertRaises(RuntimeError):g.validate_original_values(values,bundle['base'],original)

    def test_missing_member_or_unapproved_group_rejected(self):
        values=copy.deepcopy(original);values[next(iter(values))].pop()
        with self.assertRaises(RuntimeError):g.validate_original_values(values,bundle['base'],original)
        values=copy.deepcopy(original);values['unapproved']=[]
        with self.assertRaises(RuntimeError):g.validate_original_values(values,bundle['base'],original)

    def test_native_binary64_identity_preserves_signed_zero(self):
        other=copy.deepcopy(M);other[0][1]=-0.
        self.assertFalse(g.binary64_equal([M],[other]));self.assertNotEqual(g.binary64_matrix_hash([M]),g.binary64_matrix_hash([other]))
        self.assertTrue(g.binary64_equal([M],copy.deepcopy([M])))

    def test_nonfinite_nonfloat_and_invalid_matrix_shape_rejected(self):
        for mutation in ('nan','int','shape'):
            changed=copy.deepcopy(M)
            if mutation=='nan':changed[0][0]=float('nan')
            elif mutation=='int':changed[0][0]=1
            else:changed[0].pop()
            with self.subTest(mutation=mutation),self.assertRaises(RuntimeError):g.binary64_matrix_hash([changed])

    def test_full_matrix_order_and_tiny_double_difference_detected(self):
        second=copy.deepcopy(M);second[3][0]+=1e-11
        self.assertFalse(g.binary64_equal([M],[second]));self.assertNotEqual(g.binary64_matrix_hash([M,second]),g.binary64_matrix_hash([second,M]))

    def test_exact_cpp_property_and_struct_names_only(self):
        calls=[]
        class Row:
            def get_editor_property(self,key):
                calls.append(key);return {'StartInstanceIndex':17,'RandomSeed':601}[key]
        class Component:
            def get_editor_property(self,key):
                calls.append(key);selftest.assertEqual(key,'AdditionalRandomSeeds');return [Row()]
        selftest=self;result=native.additional_seed_observation(Component())
        self.assertEqual(calls,['AdditionalRandomSeeds','StartInstanceIndex','RandomSeed'])
        self.assertEqual(result,{'available':True,'cppPropertyName':'AdditionalRandomSeeds','ranges':[{'startInstanceIndex':17,'randomSeed':601}]})

    def test_unavailable_seed_ranges_are_not_invented_empty(self):
        class Component:
            def get_editor_property(self,key):raise RuntimeError('Not exposed by installed reflection')
        result=native.additional_seed_observation(Component())
        self.assertFalse(result['available']);self.assertNotIn('ranges',result)
        self.assertFalse(result['rangeValuesObserved']);self.assertFalse(result['rangePreservationClaimed'])


if __name__=='__main__':unittest.main(verbosity=2)
