"""Bounded stdlib R36 source/raw-counterfactual adversarial fixtures.

The constructed matrices below are CPU fixtures, not a native measurement.
The writer must obtain actual wrapped transient matrices before mutation.
"""
import copy
import importlib.util
import json
import math
from pathlib import Path
import struct
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('r36_test_actual_guards',ROOT/'scripts/unreal/exterior-garden-periwinkle-native-guards-r36.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)


def fixtures(bundle):
 byid={identity:(c,i)for c in bundle['originalControls'].values()for i,identity in enumerate(c['rootIds'])};result={}
 for model in g.MODELS:
  fits=[r for r in bundle['source']['placements']if r['model']==model];inputs=[];matrices=[]
  for fit in fits:
   old,i=byid[fit['rootId']];q=old['recoveredValues'][i][1];x,y,z,w=q;scale=fit['uniformScale'];p=old['recoveredValues'][i][0][:2]+[fit['positionCm'][2]]
   inputs.append([p,q,fit['scale']])
   # Explicit fixture quaternion rotation, row-vector convention. No UE call.
   matrices.append([[scale*(1-2*(y*y+z*z)),scale*2*(x*y+z*w),scale*2*(x*z-y*w),0.],
    [scale*2*(x*y-z*w),scale*(1-2*(x*x+z*z)),scale*2*(y*z+x*w),0.],
    [scale*2*(x*z+y*w),scale*2*(y*z-x*w),scale*(1-2*(x*x+y*y)),0.],p+[1.]])
  result[model]={'rootIds':[r['rootId']for r in fits],'inputValues':inputs,'recoveredValues':copy.deepcopy(inputs),'storedMatrices':matrices,
   'actualUnregisteredMeshlessTransientMeasurement':True,'wrappedOriginalXYAndRotationCopied':True,
   'hostQuaternionReconstructionPerformed':False,'sourceUniformScaleAssigned':True,'nativeNormalTangentReadbackAvailable':False}
 return result


class Guards(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  at=time.monotonic();cls.b=g.validate_source();cls.m=fixtures(cls.b);print('actualSourceBindingSeconds',round(time.monotonic()-at,3),flush=True)

 def test_01_actual_r34_scope_and_clone(self):
  b=self.b;self.assertEqual(len(b['base']['witness']),5354);self.assertEqual([len(x['control']['rootIds'])for x in b['groups'].values()],[58,47,146,133])
  self.assertEqual(sum(len(x['rootIds'])for x in b['originalControls'].values()),437)
  self.assertEqual(sum(len(x['rootIds'])for x in b['oldFernMeasurements'].values()),36)
  self.assertEqual(g.validate_clone(b['base'])['sha256'],'24a2afa5e0f239edd236fa401b4dda59a034eff5deb93718bb2329b69f8c84ee')
  self.assertEqual(g.material_readiness()['tests']['passed'],11)

 def test_02_original_all_attributes_and_mesh_names(self):
  self.assertEqual(list(self.b['source']['models']),list(g.MODELS));self.assertEqual(sum(m['triangles']for m in self.b['source']['models'].values()),34350)
  self.assertEqual({m['originalSourceMeshName']for m in self.b['source']['models'].values()},{'tree','tree.001','tree.002','tree.003','tree.004','tree.048'})
  for m in self.b['source']['models'].values():
   self.assertEqual(set(m['attributes']),{'POSITION','NORMAL','TEXCOORD_0','TEXCOORD_1','COLOR_0','COLOR_1'})
   self.assertFalse(m['nativeColor1ReadbackAvailable']);self.assertFalse(m['nativeNormalTangentReadbackAvailable'])

 def altered_glb(self,mutate):
  proposal=copy.deepcopy(self.b['source']['proposal']);raw=bytearray(Path(proposal['sourceGlb']['path']).read_bytes());jl=struct.unpack_from('<I',raw,12)[0]
  doc=json.loads(raw[20:20+jl]);data=bytes(raw[28+jl:]);doc,data=mutate(doc,data)
  encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
  new=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(data))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(data),0x004e4942)+data
  with tempfile.TemporaryDirectory(prefix='brezi-r36-mutant-')as directory:
   path=Path(directory)/'mutated.glb';path.write_bytes(new);proposal['sourceGlb']=g.pin(path)
   with self.assertRaises(RuntimeError):g.decode_models(proposal)

 def test_03_changed_original_bin_rejected(self):
  self.altered_glb(lambda d,b:(d,bytes([b[0]^1])+b[1:]))

 def test_04_mirrored_node_rejected(self):
  def mirror(d,b):d['nodes'][0]['scale']=[-1,1,1];return d,b
  self.altered_glb(mirror)

 def test_05_missing_uv1_rejected(self):
  def uv(d,b):del d['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_1'];return d,b
  self.altered_glb(uv)

 def test_06_original_raw_signed_zero_rejected(self):
  controls=copy.deepcopy(self.b['originalControls']);actor=next(iter(controls));controls[actor]['storedMatrices'][0][0][3]=-0.
  with self.assertRaises(RuntimeError):g.validate_native_controls(controls,self.b)

 def test_07_original_seed_and_custom_rejected(self):
  for key,value in (('mainRandomSeed',0),('numCustomDataFloats',1),('customData',[.5])):
   controls=copy.deepcopy(self.b['originalControls']);controls[next(iter(controls))][key]=value
   with self.assertRaises(RuntimeError):g.validate_native_controls(controls,self.b)

 def test_08_whole_empty_only_four_counts_and_preserve_controls(self):
  before=self.b['base']['witness'];expected=g.expected_original(before,self.b);empty=g.empty_controls(self.b);selected={x['actor']for x in self.b['groups'].values()}
  self.assertEqual(sum(len(c['rootIds'])for c in empty.values()),53)
  for actor,row in before.items():
   if actor not in selected:self.assertEqual(row,expected[actor])
   else:
    c=g.component(expected[actor],'Instances');self.assertEqual(c['instanceCount'],0);self.assertEqual(c['orderedInstanceTransformsSha256'],g.digest([]))
    self.assertEqual(empty[actor]['mainRandomSeed'],self.b['originalControls'][actor]['mainRandomSeed'])
  self.assertEqual(len(expected),5354)

 def test_09_added_owner_scope_from_actual_template(self):
  model=g.MODELS[0];actor=self.b['base']['report']['newOwnedGroups']['fern_02_a']['actor'];template=self.b['base']['witness'][actor]
  row=g.added_expected(template,actor,'/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.R36_fixture',model,'own-mesh','own-material',self.m[model])
  self.assertEqual(row['tags'],['BreziGardenPeriwinkleR36:','BreziGenerated']);self.assertFalse(row['actorTick']);self.assertFalse(row['detailDensityScaling'])
  self.assertEqual(g.component(row,'Instances')['instanceCount'],72);self.assertEqual(g.component(row,'Instances')['materials'],['own-material'])

 def test_10_measured_input_xy_quaternion_scale_rejected(self):
  self.assertTrue(g.validate_measurements(self.m,self.b))
  for array,index in ((0,0),(1,2),(2,0)):
   m=copy.deepcopy(self.m);m[g.MODELS[0]]['inputValues'][0][array][index]+=.01
   with self.assertRaises(RuntimeError):g.validate_measurements(m,self.b)

 def test_11_wrong_root_order_and_stored_z_rejected(self):
  for variant in ('order','z'):
   m=copy.deepcopy(self.m)
   if variant=='order':m[g.MODELS[0]]['rootIds'][0:2]=list(reversed(m[g.MODELS[0]]['rootIds'][0:2]))
   else:m[g.MODELS[0]]['storedMatrices'][0][3][2]+=.01
   with self.assertRaises(RuntimeError):g.validate_measurements(m,self.b)

 def test_12_complete_fixture_masks_and_reject_expanded_crown(self):
  rows=g.source_footprints(self.m,self.b);self.assertEqual(len(rows),384);self.assertEqual(sum(r['decodedSourceF32VerticesChecked']for r in rows),1981184)
  self.assertTrue(all(r['allVerticesAndFullCircleInOriginalBed']and r['fullCircleExcludesOriginalSteps']for r in rows))
  self.assertTrue(all(abs(r['contactArithmeticDeltaCm'])<=1e-7 for r in rows))
  m=copy.deepcopy(self.m)
  for i in range(3):
   for j in range(3):m[g.MODELS[0]]['storedMatrices'][0][i][j]*=100
  with self.assertRaises(RuntimeError):g.source_footprints(m,self.b)


if __name__=='__main__':unittest.main(verbosity=2)
