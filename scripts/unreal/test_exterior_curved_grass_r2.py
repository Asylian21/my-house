"""CPU rejection fixtures for measured R20 repair; no native/GPU execution."""
import copy
import importlib.util
import math
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
n=load('r20_test_r2_native','exterior-curved-grass-native-r2.py');g=n.guard
r=load('r20_test_r2_readback','exterior-curved-grass-readback-r2.py')


class MeasuredRepair(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=g.read(ROOT/'output/unreal/exterior-curved-grass-20261002-r1-study/curved-grass-plan.json')
        cls.rows=g.read(cls.plan['geometry']['path'])['meshes'];cls.originals=g.original_meshes()
        cls.selected=g.read(cls.plan['rootSelection']['path'])

    def test_all_66_measured_differences_accepted_without_rewriting_source(self):
        proof=g.measured_probe();self.assertEqual(len(g.ALLOWED_PATHS),66)
        for row in proof['mismatches']:
            g.exact_except_measured(row['saved'],row['derived'],row['path'])
        before=copy.deepcopy(self.rows);g.validate_geometry(self.rows,self.originals);self.assertEqual(self.rows,before)

    def test_full_original_plan_geometry_selection_material_validation(self):
        result=n.validate_plan(self.plan,Path(self.plan['geometry']['path']).with_name('curved-grass-plan.json'))
        self.assertEqual(len(result[5]),64);self.assertEqual(result[4],self.rows)

    def test_three_ulp_rejected_even_when_float32_equal(self):
        value=10.960253892518633;other=value
        for _ in range(3):other=math.nextafter(other,math.inf)
        with self.assertRaises(RuntimeError):g.exact_except_measured(value,other,'$.geometry[0].rootedRadialEnvelopeCm')

    def test_absolute_cap_independent_of_ulp_cap(self):
        value=30.;other=math.nextafter(value,math.inf)
        for _ in range(1):other=math.nextafter(other,math.inf)
        self.assertEqual(abs(g.differ.ordered_double(value)-g.differ.ordered_double(other)),2)
        self.assertGreater(abs(value-other),4e-15)
        with self.assertRaises(RuntimeError):g.exact_except_measured(value,other,'$.geometry[0].rootedRadialEnvelopeCm')

    def test_unmeasured_geometry_radius_index_rejected(self):
        rows=copy.deepcopy(self.rows);rows[1]['rootedRadialEnvelopeCm']=math.nextafter(rows[1]['rootedRadialEnvelopeCm'],math.inf)
        with self.assertRaises(RuntimeError):g.validate_geometry(rows,self.originals)

    def test_root_xyz_yaw_height_scale_changes_rejected(self):
        for path in ('$.selection[0].newSourceRow.positionCm[0]','$.selection[0].newSourceRow.yawDeg',
                     '$.selection[0].authoredHeightCm','$.selection[0].uniformScale'):
            with self.assertRaises(RuntimeError):g.exact_except_measured(1.,math.nextafter(1.,math.inf),path)

    def test_integer_boolean_and_string_types_rejected(self):
        for a,b in ((1,1.),(False,0),('small_a','small_b')):
            with self.assertRaises(RuntimeError):g.exact_except_measured(a,b,'$.selection[0].kind')

    def test_attribute_normal_uv_tangent_index_mutations_rejected(self):
        for key in ('positionMetersYUp','normalYUp','uv0','tangentYUp','expectedNativeVerticesCm','expectedNativeNormals'):
            rows=copy.deepcopy(self.rows);rows[0][key][0][0]=math.nextafter(rows[0][key][0][0],math.inf)
            with self.assertRaises(RuntimeError):g.validate_geometry(rows,self.originals)
        rows=copy.deepcopy(self.rows);rows[0]['indices'][0]+=1
        with self.assertRaises(RuntimeError):g.validate_geometry(rows,self.originals)

    def test_signed_zero_attribute_bits_preserved(self):
        rows=copy.deepcopy(self.rows)
        zeros=[(i,j) for i,p in enumerate(rows[0]['positionMetersYUp']) for j,v in enumerate(p) if v==0.]
        self.assertTrue(zeros);i,j=zeros[0];rows[0]['positionMetersYUp'][i][j]=-rows[0]['positionMetersYUp'][i][j]
        with self.assertRaises(RuntimeError):g.attribute_bits(rows,self.rows)

    def test_added_missing_structural_field_rejected(self):
        for a,b in (({'a':1},{'a':1,'b':0}),([1,2],[1]),({'a':1},{'b':1})):
            with self.assertRaises(RuntimeError):g.exact_except_measured(a,b,'$.geometry')

    def test_nonfinite_radius_rejected(self):
        for value in (math.inf,-math.inf,math.nan):
            with self.assertRaises(RuntimeError):g.exact_except_measured(10.,value,'$.geometry[0].rootedRadialEnvelopeCm')

    def test_partial_owned_scope_rejected_and_original_delegates_unchanged(self):
        record={'groups':{'original':{}},'meshes':{'old':'path'}}
        old,own=r.split_original_record(record,g.require);self.assertIs(old,record);self.assertEqual(own,{})
        bad=copy.deepcopy(record);bad['groups']['EX_curved_grass_r20_small_a']={}
        with self.assertRaises(RuntimeError):r.split_original_record(bad,g.require)

    def test_separate_ownership_scope_keeps_original_record_unchanged(self):
        record={'actors':{'old':'original'},'groups':{'old':{'actor':'old-path'}},'meshes':{'old':'old-mesh'}}
        for kind in ('small_a','small_b','tall_c'):
            record['groups']['EX_curved_grass_r20_'+kind]={'actor':'own-'+kind}
            record['meshes']['curved_grass_r20_'+kind]='new-'+kind
        before=copy.deepcopy(record);old,own=r.split_original_record(record,g.require)
        self.assertEqual(record,before);self.assertEqual(set(old['groups']),{'old'});self.assertEqual(set(old['meshes']),{'old'})
        self.assertEqual(old['actors'],{'old':'original'});self.assertEqual(len(own),3)


if __name__=='__main__':unittest.main(verbosity=2)
