"""Focused R32 native-contract counterexamples; no Unreal/native launch."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('r32_native_contract',ROOT/'scripts/unreal/exterior-context-yard-ground-native-guards-r32.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)


class NativeScope(unittest.TestCase):
 def scope(self):
  before={};targets={}
  for role in('entry_walk','service_court','worn_edge'):
   path='actor_'+role;c={'name':'Ground','mesh':'old_'+role,'materials':['old_material'], 'overrideMaterials':[],
    'visible':True,'hiddenInGame':False,'drawPolicy':{'ld_max_draw_distance':24000.},'navigation':False,'transform':[0,0,0]}
   before[path]={'label':role,'components':[c],'architectureSentinel':'untouched'}
   targets[role]={'actor':path,'component':'Ground','originalMesh':c['mesh'],'originalMaterials':c['materials']}
  before['other']={'architecture':[3,0,0],'grass':[1,2,3]}
  meshes={k:'new_'+k for k in ('yard_ground_r32_entry_walk','yard_ground_r32_service_court','yard_ground_r32_yard_substrate')}
  materials={'yard_gravel_r32':'new_gravel','yard_substrate_r32':'new_substrate'}
  return before,targets,meshes,materials

 def test_exact_declared_old_fields_only(self):
  before,t,m,a=self.scope();old=copy.deepcopy(before);got=g.expected_original(before,t,m,a)
  self.assertEqual(before,old)
  for role in('entry_walk','service_court'):
   c=got[t[role]['actor']]['components'][0];c['mesh']=t[role]['originalMesh'];c['materials']=t[role]['originalMaterials'];c['overrideMaterials']=[]
  c=got[t['worn_edge']['actor']]['components'][0];c['visible']=True;c['hiddenInGame']=False
  self.assertEqual(got,before)

 def test_unknown_fourth_old_target_rejected(self):
  b,t,m,a=self.scope();t['arbitrary_building']=t['entry_walk']
  with self.assertRaisesRegex(Exception,'Exact three'):g.expected_original(b,t,m,a)

 def test_wrong_saved_old_floor_binding_rejected(self):
  b,t,m,a=self.scope();b[t['entry_walk']['actor']]['components'][0]['mesh']='wrong'
  with self.assertRaisesRegex(Exception,'old binding'):g.expected_original(b,t,m,a)

 def test_worn_hide_cannot_hide_already_changed_component(self):
  b,t,m,a=self.scope();b[t['worn_edge']['actor']]['components'][0]['visible']=False
  with self.assertRaisesRegex(Exception,'visibility'):g.expected_original(b,t,m,a)

 def content(self):
  before={f'base_{i}.uasset':{'sha256':str(i),'bytes':1}for i in range(4077)};before['Brezi/Maps/Brezi.umap']={'sha256':'old','bytes':1}
  packages=[g.PREFIX+'/Geometry/m'+str(i)for i in range(3)]+[g.PREFIX+'/Materials/m'+str(i)for i in range(2)]+[g.PREFIX+'/Pipeline/'+x for x in('Assets','Materials','Level')]
  after=copy.deepcopy(before);after['Brezi/Maps/Brezi.umap']={'sha256':'new','bytes':1}
  after.update({p.removeprefix('/Game/')+'.uasset':{'sha256':'owned','bytes':1}for p in packages})
  return before,after,packages

 def test_exact_map_plus_eight_owned_packages(self):
  b,a,p=self.content();r=g.validate_content(b,a,p);self.assertEqual(r['savedContentFiles'],4086)

 def test_old_material_package_mutation_rejected(self):
  b,a,p=self.content();a['base_0.uasset']['sha256']='changed'
  with self.assertRaisesRegex(Exception,'outside own map'):g.validate_content(b,a,p)

 def test_ninth_extra_asset_rejected(self):
  b,a,p=self.content();a['Brezi/unapproved.uasset']={'sha256':'x','bytes':1}
  with self.assertRaisesRegex(Exception,'declared new owned'):g.validate_content(b,a,p)

 def test_foreign_prefix_rejected(self):
  b,a,p=self.content();old=p[0].removeprefix('/Game/')+'.uasset';a.pop(old);p[0]='/Game/Unapproved/new';a['Unapproved/new.uasset']={'sha256':'x','bytes':1}
  with self.assertRaisesRegex(Exception,'declared new owned'):g.validate_content(b,a,p)

 def test_duplicate_package_rejected(self):
  b,a,p=self.content();p[-1]=p[0]
  with self.assertRaisesRegex(Exception,'8 fresh packages'):g.validate_content(b,a,p)

 def test_binary64_signed_zero_not_equivalent(self):
  n=g.module('r32_owned_exact_frame','exterior-context-yard-ground-native-r32.py')
  with self.assertRaisesRegex(Exception,'frame'):n.exact([0.],[-0.],'frame drift')


if __name__=='__main__':unittest.main(verbosity=2)
