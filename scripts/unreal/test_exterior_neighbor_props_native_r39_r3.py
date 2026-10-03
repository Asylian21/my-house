"""Five focused new-local zero-bit/calibrated-pose/binding cases; no UE."""
import copy
import importlib.util
import struct
from pathlib import Path
from types import SimpleNamespace
import unittest
ROOT=Path(__file__).resolve().parents[2]
def load(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/file);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
n=load('_r39r3_new_native_kernels','exterior-neighbor-props-native-r39-r3.py')

class LocalNumericIdenticalStruct:
    def __init__(self,values):self.values=dict(values);self.writes=[]
    def __getattr__(self,key):return self.values[key]
    def get_editor_property(self,key):return self.values[key]
    def set_editor_property(self,key,value):
        self.writes.append((key,value))
        if self.values[key]!=value:self.values[key]=float(value)

class NewLocalTransform:
    def __init__(self):
        self.translation=LocalNumericIdenticalStruct(dict(zip('xyz',[0.,0.,0.])))
        self.rotation=LocalNumericIdenticalStruct(dict(zip('xyzw',[0.,-0.,0.,1.])))
        self.scale3d=LocalNumericIdenticalStruct(dict(zip('xyz',[1.,1.,1.])))
    def get_editor_property(self,key):return getattr(self,key)
    def set_editor_property(self,key,value):setattr(self,key,value)

class CalibrationContracts(unittest.TestCase):
    BUNDLE=None
    @classmethod
    def setUpClass(cls):
        if cls.BUNDLE is None:cls.BUNDLE=n.g.load_contract(validate_current=False)
        cls.b=cls.BUNDLE
    def reject(self,function,*args):
        with self.assertRaises(RuntimeError):function(*args)
    def test_01_only_different_zero_bits_use_finite_intermediate(self):
        cell=LocalNumericIdenticalStruct({'y':-0.});n.write_new_local_scalar(cell,'y',0.)
        self.assertEqual(cell.writes,[('y',1.),('y',0.)]);self.assertEqual(struct.pack('<d',cell.y),struct.pack('<d',0.))
        cell=LocalNumericIdenticalStruct({'x':0.});n.write_new_local_scalar(cell,'x',-0.)
        self.assertEqual(cell.writes,[('x',1.),('x',-0.)]);self.assertEqual(struct.pack('<d',cell.x),struct.pack('<d',-0.))
    def test_02_exact_zero_and_nonzero_fields_are_unadapted(self):
        for before,requested in [(0.,0.),(-0.,-0.),(5.,5.),(0.,6.431593745946884),(1.,0.)]:
            cell=LocalNumericIdenticalStruct({'x':before});n.write_new_local_scalar(cell,'x',requested)
            self.assertEqual(cell.writes,[('x',float(requested))]);self.assertEqual(struct.pack('<d',cell.x),struct.pack('<d',requested))
        cell=LocalNumericIdenticalStruct({'x':0.});self.reject(n.write_new_local_scalar,cell,'x',float('nan'))
        self.assertEqual(cell.writes,[])
    def test_03_six_authored_roots_keep_original_plus_zero_and_all_nonzero_bits(self):
        u=SimpleNamespace(Transform=NewLocalTransform)
        for row in self.b['source']['proposal']['placements']:
            got=n.authored_root(u,row);recorded=self.b['constructorCalibration']['sixRootConstructors'][row['id']]['actualValues']
            n.exact(n.transform_value(got),recorded,'Observed exact root differs')
            self.assertEqual(struct.pack('<d',got.rotation.y),struct.pack('<d',0.))
            self.assertIn(('y',1.),got.rotation.writes)
            self.assertEqual(self.b['source']['proposal']['placements'][0]['yawDegrees'],171.63730441942735)
    def proof(self):
        result={}
        for key,row in self.b['constructorCalibration']['compositions'].items():
            m={k:copy.deepcopy(row[k]) for k in ('assemblyRootIds','assemblyInputValues','originalImportedNodeValues',
                'independentRootTransformPointValues','composedInputValues','recoveredValues','storedMatrices')}
            model,index=key.rsplit(':',1);selected=[r for r in self.b['source']['proposal']['placements'] if r['modelId']==model]
            m.update(part=key,modelId=model,nodeIndex=int(index),actualMeshlessTransientMeasured=True,
                originalWholeSourceNodeTransformComposed=True,intendedSixAuthoredAssembliesIndependentlyCompared=True,
                authoredAssemblyInputs=[{k:r[k]for k in ('id','modelId','positionCm','yawDegrees','uniformScale')}for r in selected])
            result[key]=m
        return result
    def test_04_eight_actual_calibrated_arrays_preserve_recorded_native_roundtrip(self):
        proof=self.proof();self.assertTrue(n.validate_measurement_receipt(self.b,proof))
        self.assertEqual(sum(len(r['assemblyRootIds'])for r in proof.values()),8)
        first=next(iter(proof))
        for field in ('assemblyInputValues','originalImportedNodeValues','composedInputValues','recoveredValues','storedMatrices'):
            changed=copy.deepcopy(proof);changed[first][field][0][0][0]+=1e-9
            self.reject(n.g.validate_constructor_measurements,changed,self.b)
        original=copy.deepcopy(proof);n.g.validate_constructor_measurements(proof,self.b);self.assertEqual(proof,original)
    def test_05_private_material_adapter_authenticates_r3_without_recipe_or_kernel_change(self):
        maps=n.material_module();self.assertIs(maps.binding_guard(),n.g)
        packet=n.material_packet(self.b);self.assertEqual(set(packet),{'source','base','binding'})
        self.assertIs(maps.validate_binding(packet,self.b['binding']),self.b['source'])
        self.assertEqual(self.b['binding']['schemaVersion'],3)
        wrong=copy.deepcopy(self.b['binding']);wrong['schemaVersion']=2
        self.reject(maps.validate_binding,packet,wrong)
        fixtures=load('_r39r3_original_unchanged_material_mocks','test_exterior_neighbor_props_materials_r39.py')
        u=fixtures.MockNative();objects,report=maps.build_materials(u,packet,self.b['binding'],u.graph)
        self.assertEqual(maps.verify_materials(u,packet,self.b['binding'],report,u.graph),objects)
        self.assertEqual(report['nativeBinding'],self.b['binding']);self.assertEqual(len(report['newPackageAssets']),14)
        self.assertTrue(all(row['instancedStaticMeshUsage']for row in report['materials'].values()))
        self.assertFalse(n.material_adapter_evidence()['originalModulesOrSourceFilesMutated'])

if __name__=='__main__':unittest.main(verbosity=2)
