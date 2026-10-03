"""Source/CPU fixtures. Native replay/wrapped-copy acceptance remains pending."""
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

ROOT = Path(__file__).resolve().parents[2]


def module(name, filename):
 s = importlib.util.spec_from_file_location(name, ROOT/'scripts/unreal'/filename)
 m = importlib.util.module_from_spec(s)
 s.loader.exec_module(m)
 return m


g = module('clean_yard_source_fixtures', 'exterior-garden-yard-integration-source-draft.py')
n = module('clean_yard_native_fixtures', 'exterior-garden-yard-integration-native-draft.py')


class Draft(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.b = g.load_donors()
  report = cls.b['reports']['gardenR34']
  cls.before = g.read_pin(report['savedActorWitness'])
  cls.content = g.read_pin(report['afterContentInventory'])
  cls.mapping = {old: '/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.'+
                ('BreziVegetationPatch_'+str(3000+i) if 'instanceCount' in row['components'][0]
                 else 'StaticMeshActor_9000')
                for i, (old, row) in enumerate(cls.b['inventory']['addedYardActorTemplates'].items())}

 def test_01_no_pending_native_launch_or_counts(self):
  self.assertIsNone(g.SELECTED_BASE)
  self.assertIsNone(g.CANDIDATE)
  self.assertIsNone(g.SELECTED_PLAN)
  with self.assertRaisesRegex(RuntimeError, 'pending'):
   g.pending_native_gate()
  self.assertEqual(len(self.b['inventory']['packages']), 14)

 def test_02_actual_r34_targets_and_exact_four_actor_counterfactual(self):
  expected = g.expected_scene(self.before, self.b, self.mapping)
  self.assertEqual(len(expected), len(self.before)+4)
  targets = set(self.b['inventory']['changedOriginalActorTargets'])
  self.assertEqual({a for a in self.before if self.before[a] != expected[a]}, targets)
  self.assertEqual(set(expected)-set(self.before), set(self.mapping.values()))
  for a in self.before:
   if a not in targets:
    self.assertEqual(expected[a], self.before[a])

 def test_03_existing_target_policy_or_geometry_widening_rejected(self):
  target = next(iter(self.b['inventory']['changedOriginalActorTargets']))
  for key, value in (('navigation', True), ('visible', False), ('mesh', '/Game/Foreign.Mesh')):
   before = copy.deepcopy(self.before)
   before[target]['components'][0][key] = value
   with self.assertRaises(RuntimeError):
    g.expected_scene(before, self.b, self.mapping)

 def test_04_existing_r36_id_collision_is_not_a_relocation(self):
  # Synthetic reservation only; this fixture is not an actual R36 witness.
  reserved = copy.deepcopy(self.before)
  old = next(iter(self.mapping))
  occupied = '/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.BreziVegetationPatch_2318'
  reserved[occupied] = {'fixtureOnlyReservation': True}
  mapping = dict(self.mapping)
  mapping[old] = occupied
  with self.assertRaises(RuntimeError):
   g.expected_scene(reserved, self.b, mapping)
  mapping[old] = self.mapping[old]
  self.assertEqual(g.expected_scene(reserved, self.b, mapping)[occupied], reserved[occupied])

 def test_05_relocation_changes_only_owned_paths_and_new_provenance_tag(self):
  for old, row in self.b['inventory']['addedYardActorTemplates'].items():
   new = self.mapping[old]
   relocated = g.relocate_template(old, new, row)
   restored = copy.deepcopy(relocated)
   restored['tags'].remove(g.TAG)
   for c in restored['components']:
    c['path'] = old+c['path'][len(new):]
   self.assertEqual(restored, row)
  old, row = next(iter(self.b['inventory']['addedYardActorTemplates'].items()))
  altered = copy.deepcopy(row)
  altered['components'][0]['attachParent'] = '/Game/Existing.ExternalRoot'
  with self.assertRaises(RuntimeError):
   g.relocate_template(old, self.mapping[old], altered)

 def test_06_package_scope_exact_old_bytes_map_only(self):
  additions = {r['relativeContentPath']: {k: r['source'][k] for k in ('sha256', 'bytes')}
               for r in self.b['inventory']['packages']}
  copied = {**self.content, **additions}
  after = copy.deepcopy(copied)
  after['Brezi/Maps/Brezi.umap'] = {'sha256': 'fixture-map-hash', 'bytes': 123}
  self.assertEqual(g.validate_packages(self.content, copied, after, self.b)['newPackages'], 14)
  for kind in ('old', 'new', 'extra', 'missing'):
   bad = copy.deepcopy(after)
   if kind == 'old':
    bad[next(p for p in self.content if p != 'Brezi/Maps/Brezi.umap')]['sha256'] = 'changed'
   elif kind == 'new':
    bad[next(iter(additions))]['sha256'] = 'changed'
   elif kind == 'extra':
    bad['Brezi/Undeclared.uasset'] = {'sha256': 'extra', 'bytes': 1}
   else:
    bad.pop(next(iter(additions)))
   with self.assertRaises(RuntimeError):
    g.validate_packages(self.content, copied, bad, self.b)

 def test_07_all1274_saved_replay_triple_arrays_and_one_bit_mutations(self):
  self.assertEqual(sum(len(v['sourceRows']) for v in self.b['yardGroups'].values()), 1274)
  for model, group in self.b['yardGroups'].items():
   m = group['measurement']
   proof = g.replay_record(model, m['preInsertionValues'], m['recoveredValues'], m['actualMatrices'], self.b)
   self.assertFalse(proof['wrappedRowTransferActuallyExecuted'])
   for field in ('preInsertionValues', 'recoveredValues', 'actualMatrices'):
    altered = copy.deepcopy(m)
    altered[field][0][0][0] += 1e-6
    with self.assertRaises(RuntimeError):
     g.replay_record(model, altered['preInsertionValues'], altered['recoveredValues'], altered['actualMatrices'], self.b)
  with self.assertRaises(RuntimeError):
   g.exact([-0.0], [0.0], 'Signed-zero binary drift')

 def test_08_native_raw_transfer_assigns_wrapped_rows_not_transform_additions(self):
  model, group = next(iter(self.b['yardGroups'].items()))
  expected = group['savedControl']
  marker = [object() for _ in range(expected['instanceCount'])]
  properties = {'per_instance_sm_data': [], 'instancing_random_seed': 0}
  actor = NS(synchronize_instance_bounds=lambda: None, actor_has_tag=lambda tag: tag == g.TAG)
  calls = []
  def assign(key, value):
   calls.append(key)
   properties[key] = value
  component = NS(get_instance_count=lambda: len(properties['per_instance_sm_data']),
                 set_editor_property=assign, get_owner=lambda: actor)
  from unittest.mock import patch
  with patch.object(n, 'control', return_value=expected):
   result = n.copy_wrapped_rows(component, model, marker, self.b, {})
  self.assertIs(properties['per_instance_sm_data'], marker)
  self.assertEqual(calls, ['per_instance_sm_data', 'instancing_random_seed'])
  self.assertEqual(result, expected)
  # Fixture stubs observations; it makes no actual native transfer claim.

 def test_09_unapproved_existing_member_seed_or_transform_setter_absent(self):
  import ast
  tree = ast.parse((ROOT/n.OWNER).read_text())
  kernels = {x.name: x for x in tree.body if isinstance(x, ast.FunctionDef)}
  body = ast.unparse(kernels['retire_exact_original_members'])
  self.assertIn('remove_original_members', body)
  self.assertNotIn('set_editor_property', body)
  self.assertNotIn('add_instances', body)
  self.assertNotIn('instance_transform', body)
  calls = {node.func.attr for node in ast.walk(tree)
           if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
  self.assertFalse(calls & {'duplicate_actors', 'WorldFactory', 'load_level', 'load_map'})

 def test_10_saved_raw_readback_and_original_ecology_binary_gate(self):
  from unittest.mock import patch
  h = {'cleanNative': NS(component_lookup=lambda *args: object())}
  controls = {self.mapping[group['actor']]: group['savedControl']
              for group in self.b['yardGroups'].values()}
  with patch.object(n, 'control', side_effect=list(controls.values())):
   self.assertEqual(n.verify_new_raw_groups(None, self.b, h, self.mapping), controls)
  corrupted = copy.deepcopy(list(controls.values()))
  corrupted[0]['storedMatrices'][0][0][0] += 1e-6
  with patch.object(n, 'control', side_effect=corrupted), self.assertRaises(RuntimeError):
   n.verify_new_raw_groups(None, self.b, h, self.mapping)
  original = self.b['ecologyOriginal']
  raw = [{key: expected[key] for key in ('instanceCount', 'recoveredValues', 'storedMatrices',
           'mainRandomSeed', 'numCustomDataFloats', 'customData',
           'additionalRandomSeedsReadbackAvailable', 'seedRangesReconstructed')}
         for expected in original.values()]
  with patch.object(n, 'control', side_effect=raw):
   self.assertEqual(n.original_ecology_control(None, self.b, h), original)
  changed = copy.deepcopy(raw)
  self.assertEqual(changed[0]['storedMatrices'][0][0][3], 0.0)
  changed[0]['storedMatrices'][0][0][3] = -0.0
  with patch.object(n, 'control', side_effect=changed), self.assertRaises(RuntimeError):
   n.original_ecology_control(None, self.b, h)

 def test_11_new_floor_observes_derived_cache_after_cull_setter(self):
  template = next(row for row in self.b['inventory']['addedYardActorTemplates'].values()
                  if 'instanceCount' not in row['components'][0])
  properties = {'cached_max_draw_distance': 0.0}
  calls = []
  actor = NS()
  def setter(key, value):
   self.assertNotEqual(key, 'cached_max_draw_distance')
   calls.append(('property', key))
   properties[key] = value
  def cull(distance):
   calls.append(('cull', distance))
   properties['cached_max_draw_distance'] = distance
  c = NS(get_editor_property=lambda key: properties[key], set_editor_property=setter,
         set_cull_distance=cull, set_static_mesh=lambda mesh: True, get_owner=lambda: actor)
  actor.get_component_by_class = lambda cls: c
  actor.get_editor_property = lambda key: c
  actor.set_actor_label = lambda label: None
  actor.set_actor_tick_enabled = lambda enabled: None
  u = NS(Name=lambda text: text, StaticMeshComponent=object,
         EditorAssetLibrary=NS(load_asset=lambda asset: object()))
  h = {'rural': NS(new_component_policy=lambda *args: None)}
  self.assertIs(n.configure_new_actor(u, actor, template, h), c)
  self.assertEqual(calls[0], ('cull', 24000.0))
  self.assertEqual(actor.tags, sorted(template['tags']+[g.TAG]))


if __name__ == '__main__':
 unittest.main(verbosity=2)
