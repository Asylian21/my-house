"""Unbound native kernels for clean garden plus fourteen saved yard packages.

No standalone native launch is possible. A future selected-base owner must
bind the exact saved garden report/clone/preflight and full byte/witness gates.
No map loading, inactive WorldFactory, import or actor duplication is used.
"""
import copy
import importlib.util
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-yard-integration-native-draft.py'
spec = importlib.util.spec_from_file_location('clean_garden_yard_draft_source',
 ROOT/'scripts/unreal/exterior-garden-yard-integration-source-draft.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
require, exact = g.require, g.exact
PLANES = ('x_plane', 'y_plane', 'z_plane', 'w_plane')


def value(transform):
 return [[float(getattr(v, axis)) for axis in axes]
         for v, axes in ((transform.translation, 'xyz'), (transform.rotation, 'xyzw'),
                         (transform.scale3d, 'xyz'))]


def raw_matrices(component):
 return [[[float(getattr(getattr(row.get_editor_property('transform'), plane), axis))
           for axis in 'xyzw'] for plane in PLANES]
         for row in component.get_editor_property('per_instance_sm_data')]


def control(component, h):
 count = component.get_instance_count()
 return {'instanceCount': count,
  'recoveredValues': [value(h['rural'].instance_value(component, i)) for i in range(count)],
  'storedMatrices': raw_matrices(component),
  'mainRandomSeed': int(component.get_editor_property('instancing_random_seed')),
  'numCustomDataFloats': int(component.get_editor_property('num_custom_data_floats')),
  'customData': [float(v) for v in component.get_editor_property('per_instance_sm_custom_data')],
  'additionalRandomSeedsReadbackAvailable': False, 'seedRangesReconstructed': False}


def replay_wrapped_source_rows(u, donors, h):
 """Native original constructors, then exact saved triple-array comparison.

 Only source position/yaw/scale enter Transform construction. Matrix/quat
 coefficients recorded from native are never fed back into constructors.
 """
 result, observations, keep_alive = {}, {}, []
 for model, group in donors['yardGroups'].items():
  c = u.new_object(u.HierarchicalInstancedStaticMeshComponent)
  require(c and c.get_owner() is None and c.get_path_name().startswith('/Engine/Transient.')
          and c.get_editor_property('static_mesh') is None,
          'Unregistered meshless unowned replay HISM required')
  transforms = [h['rural'].instance_transform(u, h['r32'].root_record(row))
                for row in group['sourceRows']]
  inputs = [value(t) for t in transforms]
  require(list(c.add_instances(transforms, True, False, False)) == list(range(len(transforms))),
          'Source constructor replay root order changed')
  got = control(c, h)
  observations[model] = g.replay_record(model, inputs, got['recoveredValues'], got['storedMatrices'], donors)
  rows = list(c.get_editor_property('per_instance_sm_data'))
  require(len(rows) == len(transforms), 'Native wrapped source row count changed')
  result[model] = rows
  keep_alive.append(c)
 require(sum(len(rows) for rows in result.values()) == 1274,
         'Exact1274 replayed source wrapped rows required before candidate mutation')
 return result, observations, keep_alive


def copy_wrapped_rows(component, model, rows, donors, h):
 """The final group receives raw native structs; no add/recompose on transfer."""
 require(component.get_instance_count() == 0, 'Only a new empty HISM may receive donor rows')
 expected = donors['yardGroups'][model]['savedControl']
 require(expected['numCustomDataFloats'] == 0 and expected['customData'] == [],
         'Source transfer supports only actual zero-custom-data yard groups')
 actor = component.get_owner()
 require(actor and actor.actor_has_tag(g.TAG), 'Only a newly owned integration actor may receive rows')
 component.set_editor_property('per_instance_sm_data', rows)
 # Random seed setter is confined to a NEW component, never a survivor.
 component.set_editor_property('instancing_random_seed', expected['mainRandomSeed'])
 actor.synchronize_instance_bounds()
 got = control(component, h)
 exact(got['storedMatrices'], expected['storedMatrices'], 'Native wrapped-copy matrix bits changed')
 exact(got['recoveredValues'], expected['recoveredValues'], 'Native wrapped-copy recovered frames changed')
 require(got == expected, 'New group main-seed/custom/member controls differ from actual saved donor')
 return got


def verify_new_raw_groups(u, donors, h, mapping):
 observed = {}
 for model, group in donors['yardGroups'].items():
  actor = mapping[group['actor']]
  c = h['cleanNative'].component_lookup(u, actor, 'Instances')
  got = control(c, h)
  expected = group['savedControl']
  exact(got['storedMatrices'], expected['storedMatrices'], 'Saved/reloaded copied matrices changed')
  exact(got['recoveredValues'], expected['recoveredValues'], 'Saved/reloaded copied frames changed')
  require(got == expected, 'Saved/reloaded member/main-seed/custom controls changed')
  observed[actor] = got
 return observed


def original_ecology_control(u, donors, h):
 """Read current selected-map controls and bind all eight to actual donor."""
 result = {}
 for group, expected in donors['ecologyOriginal'].items():
  actor = donors['retirements'][group]['actor']
  c = h['cleanNative'].component_lookup(u, actor, 'Instances')
  got = control(c, h)
  exact(got['storedMatrices'], expected['storedMatrices'], 'Original ecology raw matrix bits differ')
  exact(got['recoveredValues'], expected['recoveredValues'], 'Original ecology recovered frame bits differ')
  require(got == {key: expected[key] for key in got},
          'Selected original ecology matrices/order/mainseed/custom differ from actual donor')
  result[group] = expected
 return result


def retire_exact_original_members(u, donors, h, original):
 """Frozen R35 RemoveAtSwap and surviving-existing-struct reorder kernel."""
 groups = {key: {'actor': row['actor'], 'component': 'Instances',
                 'selectedSourceIndices': row['removedOriginalSourceIndices']}
           for key, row in donors['retirements'].items()}
 scope = {'ecologyGroups': groups}
 return h['r35'].remove_original_members(u, scope, h, original)


def apply_original_component_changes(u, donors, h):
 """No old transforms/render/cull/random/architecture fields are assigned."""
 targets = donors['inventory']['changedOriginalActorTargets']
 for actor, target in targets.items():
  if target['recordedRetirement'] is not None:
   continue
  wanted = target['recordedFinalYardWitness']['components'][0]
  c = h['cleanNative'].component_lookup(u, actor, wanted['name'])
  paths = target['allowedChangesFromOriginalR34']
  if '/components/0/mesh' in paths:
   mesh = u.EditorAssetLibrary.load_asset(wanted['mesh'])
   require(mesh and c.set_static_mesh(mesh), 'Cannot bind exact saved donor floor master')
  if '/components/0/materials/0' in paths:
   material = u.EditorAssetLibrary.load_asset(wanted['materials'][0])
   require(material, 'Exact saved donor material missing')
   c.set_material(0, material)
  if '/components/0/visible' in paths:
   require(paths == ['/components/0/hiddenInGame', '/components/0/visible']
           and wanted['visible'] is False and wanted['hiddenInGame'] is True,
           'Only exact old worn-edge hide pair allowed')
   c.set_visibility(False, False)
   c.set_hidden_in_game(True, False)


def configure_new_actor(u, actor, template, h):
 """Copy the declared saved component policy onto an exclusively NEW actor."""
 row = template['components'][0]
 actor.tags = [u.Name(t) for t in sorted(template['tags']+[g.TAG])]
 actor.set_actor_label(template['label'])
 actor.set_actor_tick_enabled(False)
 c = actor.get_component_by_class(u.StaticMeshComponent)
 require(c and actor.get_editor_property('root_component') == c and c.get_owner() == actor,
         'Only one own generated root mesh component permitted')
 h['rural'].new_component_policy(u, c)
 mesh = u.EditorAssetLibrary.load_asset(row['mesh'])
 require(mesh and c.set_static_mesh(mesh), 'Copied native source mesh missing')
 # All source templates have identity actor/component frames and no attachment.
 require(template['transform'] == [[0., 0., 0.], [0., 0., 0., 1.], [1., 1., 1.]]
         and row['transform'] == template['transform'] and row['attachParent'] is None,
  'Only recorded identity source actor/component frames allowed')
 if 'instanceCount' not in row:
  # The reflected setter computes its VisibleAnywhere cache before observation.
  c.set_cull_distance(row['maxDrawDistanceCm'])
 for section in ('renderFlags', 'passFlags', 'drawPolicy', 'additionalRenderFlags'):
  for key, val in row[section].items():
   if key == 'cached_max_draw_distance':
    require(c.get_editor_property(key) == val, 'Derived draw-distance cache differs')
   else:
    c.set_editor_property(key, val)
 require(row['visible'] is True and row['hiddenInGame'] is False and not template['hidden']
         and row['navigation'] is False and row['overrideMaterials'] == [],
         'Recorded new component visible/nav/material policy differs')
 if 'instanceCount' in row:
  c.set_cull_distances(*row['instanceCullCm'])
  require(actor.set_detail_density_scaling(template['detailDensityScaling']),
          'New actor exact source detail policy unavailable')
 return c


def spawn_fresh_templates(u, before, donors, wrapped, h):
 """Spawn into the already loaded candidate; no world/actor duplication."""
 system = u.get_editor_subsystem(u.EditorActorSubsystem)
 mapping, results, declared_new = {}, {}, {}
 for old_actor, template in donors['inventory']['addedYardActorTemplates'].items():
  cls = u.load_class(None, template['class'])
  require(cls, 'Recorded native actor class unavailable')
  a = system.spawn_actor_from_class(cls, u.Vector(0, 0, 0), u.Rotator())
  require(a and a.get_path_name() not in before and a.get_path_name() not in mapping.values(),
          'Every new template must have a fresh disjoint native actor identity')
  mapping[old_actor] = a.get_path_name()
  # Build the expected dictionary from immutable templates before configuration.
  declared_new[a.get_path_name()] = g.relocate_template(old_actor, a.get_path_name(), template)
  c = configure_new_actor(u, a, template, h)
  if 'instanceCount' in template['components'][0]:
   model = template['label'].removeprefix('EX_yard_ground_r32_')
   results[model] = copy_wrapped_rows(c, model, wrapped[model], donors, h)
 require(len(mapping) == 4, 'Only four new saved-yard actor templates may spawn')
 # The bound owner must compare the complete expected_scene once before save
 # and again after reload; this kernel does not replay all676k members per actor.
 return mapping, results, declared_new


if __name__ == '__main__':
 g.pending_native_gate()
