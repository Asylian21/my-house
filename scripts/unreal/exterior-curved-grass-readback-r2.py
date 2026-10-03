"""Separate R20-owned group readback; never spoof original exterior ownership."""
import copy


def split_original_record(record, require):
    group_ids = {'EX_curved_grass_r20_'+kind for kind in ('small_a','small_b','tall_c')}
    present = group_ids & set(record['groups'])
    if not present:
        return record, {}
    require(present == group_ids, 'Incomplete owned curved-grass group scope')
    original = copy.deepcopy(record)
    own = {key:original['groups'].pop(key) for key in sorted(group_ids)}
    new_mesh_ids = {'curved_grass_r20_'+kind for kind in ('small_a','small_b','tall_c')}
    require(new_mesh_ids <= set(original['meshes']), 'Three original grass master bindings missing')
    for key in new_mesh_ids: original['meshes'].pop(key)
    return original, own


def delegated_readback(u, importer, record, require, digest, tag, prefix):
    original, own = split_original_record(record, require)
    if not own:
        return importer.readback(u, record)
    delegated = importer.readback(u, original)
    require(delegated['groupCount'] == 1980 and delegated['instanceCount'] == 631962,
            'Original ownership/deletion delegated readback differs')
    actors = {a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
    require({path for path,a in actors.items() if a.actor_has_tag(tag)} == {row['actor'] for row in own.values()},
            'Exact separate three-group grass ownership differs')
    instances = 0
    for key,row in own.items():
        actor = actors[row['actor']]
        component = actor.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        require(actor.get_class().get_path_name() == '/Script/BreziTwin.BreziVegetationPatch'
                and actor.actor_has_tag('BreziLawnDetail') and actor.get_detail_density_scaling(),
                'Owned original-grass actor quality policy differs')
        require(component and component.get_instance_count() == row['instances']
                and component.get_editor_property('static_mesh').get_path_name() == row['mesh']
                and row['mesh'].startswith(prefix+'/'), 'Owned grass model/member binding differs')
        require([component.get_editor_property(k) for k in ('instance_start_cull_distance','instance_end_cull_distance')]
                == [row['cullStartCm'],row['cullEndCm']] == [7200,9000], 'Owned grass original culls changed')
        require(component.get_collision_enabled() == u.CollisionEnabled.NO_COLLISION
                and not component.get_editor_property('can_ever_affect_navigation')
                and not component.get_editor_property('cast_shadow') and not component.get_editor_property('visible_in_ray_tracing'),
                'Owned grass collision/nav/authored quality flags differ')
        actual = [importer.base.instance_value(component,index) for index in range(component.get_instance_count())]
        require(digest(actual) == row['transformsSha256'], 'Owned grass ordered source root transforms changed')
        require(row['instances'] == (16 if key.endswith('tall_c') else 24), 'Owned fixed64mix differs')
        instances += row['instances']
    require(instances == 64, 'Exactly64owned replacement roots required')
    return {'meshCount':len(record['meshes']), 'groupCount':len(record['groups']),
        'instanceCount':delegated['instanceCount']+instances, 'allNewVisualsNoCollision':True,
        'originalOwnershipDelegation':delegated,'separateOwnedGroupReadback':{'groups':3,'instances':64,
            'originalExteriorOwnershipSpoofed':False,'orderedNativeTransformsVerified':True}}
