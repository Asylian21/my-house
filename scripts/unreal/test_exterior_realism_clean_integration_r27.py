"""Actual saved-donor receipts and CPU counterfactual fixtures; no R27 native proof."""
import ast
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('r27_cpu_guard',ROOT/'scripts/unreal/exterior-realism-clean-integration-guards-r27.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g);b=g.load_donors()


def compose(reports=None):
 r=reports or b['reports'];return g.compose_original_fields(b['before'],b['base'],r['leaf'],r['visibility'],r['neighbors'])


class CleanIntegrationScope(unittest.TestCase):
 def test_actual_four_saved_donors59_packages37_original_templates(self):
  self.assertEqual(set(b['reports']),{'leaf','visibility','neighbors','foreground'})
  self.assertEqual(len(b['packages']),59);self.assertEqual(len(b['templates']),37)
  self.assertEqual(len(b['before']),5306)
  self.assertFalse(any('/RoofPbr' in r['source']or'/CurvedGrass' in r['source']for r in b['packages']))
 def test_all_original_grass_counts_frames_and_cull_population_preserved(self):
  expected,audit=compose();self.assertEqual(expected,b['expectedOriginal']);self.assertEqual(audit['retainedCullInstances'],501890)
  self.assertEqual(audit['grassRemovedMembers'],0);g.verify_grass_preservation(b['before'],expected,b['base'])
  self.assertEqual(sum(r['instances']for r in b['originalGeometryAfter']['groups'].values()),632026)
 def test_leaf_bark_slot_and_duplicate_target_rejected(self):
  for mode in ('bark','duplicate'):
   r=copy.deepcopy(b['reports'])
   if mode=='bark':r['leaf']['componentBindings'][0]['slot']=0
   else:r['leaf']['componentBindings'][0]=r['leaf']['componentBindings'][1]
   with self.assertRaises(RuntimeError):compose(r)
 def test_visibility_distance_population_and_duplicate_target_rejected(self):
  for mode in ('distance','population','duplicate'):
   r=copy.deepcopy(b['reports']);delta=r['visibility']['componentCullOverrides'][0]
   if mode=='distance':delta['afterCullCm']=[18000,100000]
   elif mode=='population':delta['instances']-=1
   else:r['visibility']['componentCullOverrides'][0]=r['visibility']['componentCullOverrides'][1]
   with self.assertRaises(RuntimeError):compose(r)
 def test_original_neighbor_partition_scope_rejected(self):
  r=copy.deepcopy(b['reports']);r['neighbors']['componentChanges'][0]['sourceMeshId']='unapproved-house'
  with self.assertRaises(RuntimeError):compose(r)
 def test_clean_template_uses_actual_red_roof_and_rejects_excluded_donor(self):
  roofs=[r for k,r in b['templates'].items()if k.endswith('_neighbor_roof_red')]
  self.assertEqual(len(roofs),4)
  for row in roofs:
   part=next(c for c in row['witness']['components']if c.get('mesh'))
   self.assertEqual(part['overrideMaterials'],[]);self.assertIn('/NeighborFinish',part['materials'][0])
  r=dict(b['reports']);r['roof']={}
  with self.assertRaises(RuntimeError):g.added_templates(b['before'],r)
 def test_original_grass_removal_reorder_hash_or_policy_mutation_rejected(self):
  identity=next(iter(g.GRASS_GROUPS));actor=b['base']['geometry']['groups'][identity]['actor']
  for field,value in (('instanceCount',2229),('orderedInstanceTransformsSha256','0'*64),('instancingRandomSeed',1)):
   expected=copy.deepcopy(b['expectedOriginal']);g.component(expected,actor,'Instances')[field]=value
   with self.assertRaises(RuntimeError):g.verify_grass_preservation(b['before'],expected,b['base'])
 def test_added_actor_identity_collision_or_omission_rejected(self):
  mapping={key:'/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.R27Fixture_'+str(i)for i,key in enumerate(b['templates'])}
  self.assertEqual(len(g.compose_all_expected(b['expectedOriginal'],b['templates'],mapping)),5343)
  mapping[next(iter(mapping))]=next(iter(b['before']))
  with self.assertRaises(RuntimeError):g.compose_all_expected(b['expectedOriginal'],b['templates'],mapping)
 def test_content_map_camera_only_and59_immutable_packages(self):
  before=b['content'];after=copy.deepcopy(before)
  after.update({r['relativeContentPath']:{'sha256':r['sha256'],'bytes':r['bytes']}for r in b['packages']})
  after['Brezi/Maps/Brezi.umap']={'sha256':'0'*64,'bytes':1};after['Data/viewpoints.json']={'sha256':'1'*64,'bytes':2}
  self.assertEqual(g.validate_content(before,after,b['packages'],'1'*64)['newUassetPackages'],59)
  for key in (next(k for k in before if k not in ('Brezi/Maps/Brezi.umap','Data/viewpoints.json')),b['packages'][0]['relativeContentPath']):
   changed=copy.deepcopy(after);changed[key]['sha256']='2'*64
   with self.assertRaises(RuntimeError):g.validate_content(before,changed,b['packages'],'1'*64)
 def test_native_has_no_original_member_or_seed_mutator_and_frozen_first_order(self):
  source=(ROOT/'scripts/unreal/exterior-realism-clean-integration-native-r27.py').read_text();tree=ast.parse(source)
  called={node.func.attr for node in ast.walk(tree)if isinstance(node,ast.Call)and isinstance(node.func,ast.Attribute)}
  self.assertFalse(called&{'remove_instances','clear_instances','update_instance_transform','add_instance'})
  self.assertNotIn("set_editor_property('per_instance_sm_data'",source)
  self.assertNotIn("set_editor_property('instancing_random_seed'",source)
  self.assertNotIn('exterior-curved-grass-native',source);self.assertNotIn('exterior-roof-pbr-native',source)
  helpers=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='helpers')
  self.assertIn('g.frozen_modules',ast.unparse(helpers.body[0]))


if __name__=='__main__':unittest.main(verbosity=2)
