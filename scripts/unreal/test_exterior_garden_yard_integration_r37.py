"""Bound CPU mutation fixtures. No native scene, raw transfer or visual evidence."""
import ast
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import unittest
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('r37_bound_fixture_native',ROOT/'scripts/unreal/exterior-garden-yard-integration-native-r37.py')
n=importlib.util.module_from_spec(s);s.loader.exec_module(n);g=n.guard


class Bound(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.b=g.selected_base();g.validate_clone(cls.b)
  cls.d=cls.b['donors'];cls.src=cls.b['draftSource'];cls.k=cls.b['draftNative'];cls.before=cls.b['before']
  cls.mapping={old:'/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.'+('BreziVegetationPatch_'+str(3000+i)
    if 'instanceCount'in row['components'][0]else'StaticMeshActor_9000')
    for i,(old,row)in enumerate(cls.d['inventory']['addedYardActorTemplates'].items())}

 def test_01_actual_selected_counts_and_exact_twelve_original_targets(self):
  counts=g.counts(self.before,self.d,self.b['report'])
  self.assertEqual([counts[k]for k in ('savedActors','fullHismComponents','fullHismInstances','contentFiles','scopedMaterialGraphs','scopedTextureObjects')],
                   [5364,2325,678197,4100,64,96])
  expected=self.src.expected_scene(self.before,self.d,self.mapping)
  self.assertEqual({p for p in self.before if self.before[p]!=expected[p]},set(self.d['inventory']['changedOriginalActorTargets']))
  self.assertEqual(len(expected)-len(self.before),4)

 def test_02_actual_r36_periwinkle_identity_collision_rejected(self):
  bad=dict(self.mapping);old=next(iter(self.mapping));bad[old]=next(v['actor']for v in self.b['report']['newOwnedGroups'].values())
  with self.assertRaises(RuntimeError):self.src.expected_scene(self.before,self.d,bad)

 def test_03_original_hero_or_architecture_field_widening_rejected(self):
  target=next(iter(self.d['inventory']['changedOriginalActorTargets']));before=copy.deepcopy(self.before)
  before[target]['components'][0]['navigation']=True
  with self.assertRaises(RuntimeError):self.src.expected_scene(before,self.d,self.mapping)
  expected=self.src.expected_scene(self.before,self.d,self.mapping)
  for p,row in self.before.items():
   if p not in self.d['inventory']['changedOriginalActorTargets']:self.assertEqual(expected[p],row)

 def test_04_cloned_package_set_and_old_asset_mutation_reject(self):
  before=self.b['content'];prepared=self.b['preparedContent'];after=copy.deepcopy(prepared)
  after['Brezi/Maps/Brezi.umap']={'sha256':'fixture-map','bytes':1}
  self.assertEqual(self.src.validate_packages(before,prepared,after,self.d)['newPackages'],14)
  for path in (next(p for p in before if p!='Brezi/Maps/Brezi.umap'),self.d['inventory']['packages'][0]['relativeContentPath']):
   bad=copy.deepcopy(after);bad[path]['sha256']='changed'
   with self.assertRaises(RuntimeError):self.src.validate_packages(before,prepared,bad,self.d)
  after['Brezi/Unexpected.uasset']={'sha256':'extra','bytes':1}
  with self.assertRaises(RuntimeError):self.src.validate_packages(before,prepared,after,self.d)

 def test_05_actual_clone_wrong_selection_pending_flags_and_package_row_reject(self):
  actual=g.read(g.CLONE_PIN['path']);original=g.read
  for mutate in (lambda c:c.update(nativeExecuted=True),lambda c:c.update(nativeBaseReport={}),
                 lambda c:c['copiedDonorPackages'][0].update(independentInodes=False)):
   bad=copy.deepcopy(actual);mutate(bad)
   def read(path):return bad if str(path)==g.CLONE_PIN['path']else original(path)
   with patch.object(g,'read',side_effect=read):
    with self.assertRaises(RuntimeError):g.validate_clone(self.b)

 def test_06_three_constructor_arrays_all1274_and_binary_mutations(self):
  self.assertEqual(sum(len(v['sourceRows'])for v in self.d['yardGroups'].values()),1274)
  for model,group in self.d['yardGroups'].items():
   m=group['measurement'];self.src.replay_record(model,m['preInsertionValues'],m['recoveredValues'],m['actualMatrices'],self.d)
   for field in ('preInsertionValues','recoveredValues','actualMatrices'):
    bad=copy.deepcopy(m);bad[field][0][0][0]+=1e-9
    with self.assertRaises(RuntimeError):self.src.replay_record(model,bad['preInsertionValues'],bad['recoveredValues'],bad['actualMatrices'],self.d)
  with self.assertRaises(RuntimeError):self.src.exact([-0.0],[0.0],'binary sign')

 def test_07_replay_before_any_old_mutation_and_no_import_or_donor_world(self):
  tree=ast.parse((ROOT/n.OWNER).read_text());functions={f.name:f for f in tree.body if isinstance(f,ast.FunctionDef)}
  body=ast.unparse(functions['apply_declared_scene']);self.assertLess(body.index('replay_wrapped_source_rows'),body.index('apply_original_component_changes'))
  self.assertLess(body.index('replay_wrapped_source_rows'),body.index('retire_exact_original_members'))
  source=(ROOT/n.OWNER).read_text()
  for token in ('import_scene(', 'WorldFactory(', 'duplicate_actors(', 'set_actor_transform('):self.assertNotIn(token,source)

 def test_08_saved_whole_counterfactual_verifier_valid_and_corrupted_field(self):
  expected=self.src.expected_scene(self.before,self.d,self.mapping)
  applied={'expected':expected,'mapping':self.mapping};h={'cleanNative':NS(full_witness=lambda u,h:expected),
     'r35':NS(captured_remaining_ecology=lambda *a:self.d['ecologyRetained'])}
  with patch.object(self.k,'verify_new_raw_groups',return_value={'fixtureOnly':True}):
   n.verify_reloaded_scene(None,self.b,h,applied,{'ecology':{}})
   bad=copy.deepcopy(expected);bad[next(iter(self.before))]['label']='undeclared change';h['cleanNative'].full_witness=lambda u,h:bad
   with self.assertRaises(RuntimeError):n.verify_reloaded_scene(None,self.b,h,applied,{'ecology':{}})

 def test_09_new_saved_raw_group_verifier_exact_and_corrupted_matrix(self):
  lookup={self.mapping[v['actor']]:v['savedControl']for v in self.d['yardGroups'].values()}
  h={'cleanNative':NS(component_lookup=lambda u,path,name:path)}
  with patch.object(self.k,'control',side_effect=lambda c,h:lookup[c]):self.k.verify_new_raw_groups(None,self.d,h,self.mapping)
  first=next(iter(lookup));lookup[first]=copy.deepcopy(lookup[first]);lookup[first]['storedMatrices'][0][0][0]+=1e-10
  with patch.object(self.k,'control',side_effect=lambda c,h:lookup[c]):
   with self.assertRaises(RuntimeError):self.k.verify_new_raw_groups(None,self.d,h,self.mapping)

 def test_10_material_census_records_exact61_graphs96_textures_and_conflict_reject(self):
  graphs={};textures=set();n._material_records(g.read(g.checked(self.b['report']['originalProtectedControlsSaved'])),graphs,textures)
  n._material_records(self.b['report']['materialReport'],graphs,textures)
  self.assertEqual((len(graphs),len(textures)),(61,96))
  asset=next(iter(graphs))
  with self.assertRaises(RuntimeError):n._material_records({'asset':asset,'graphSha256':'invalid'},graphs,textures)

 def test_11_fresh_identity_tags_and_component_path_only(self):
  for old,row in self.d['inventory']['addedYardActorTemplates'].items():
   new=self.mapping[old];expected=self.src.relocate_template(old,new,row)
   self.assertEqual(expected['tags'],sorted(row['tags']+[self.src.TAG]))
   restore=copy.deepcopy(expected);restore['tags'].remove(self.src.TAG)
   for c in restore['components']:c['path']=old+c['path'][len(new):]
   self.assertEqual(restore,row)

 def test_12_save_and_reload_gates_follow_full_scene_not_loosely_after(self):
  tree=ast.parse((ROOT/n.OWNER).read_text());main=next(f for f in tree.body if isinstance(f,ast.FunctionDef)and f.name=='main');body=ast.unparse(main)
  self.assertLess(body.index('apply_declared_scene'),body.index('save_current_level'))
  self.assertLess(body.index('save_current_level'),body.index('verify_reloaded_scene'))
  self.assertIn('controls_saved == controls_before',body)
  self.assertIn('material_readback(u, bundle, h, packet) == materials',body)
  self.assertIn('geometry_readback(u, bundle, h, packet) == geometry',body)


if __name__=='__main__':unittest.main(verbosity=2)
