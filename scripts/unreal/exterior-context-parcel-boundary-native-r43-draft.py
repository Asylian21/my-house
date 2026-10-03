"""UNBOUND R43 authored boundary import/readback design.

Three merged wood/metal/gravel source masters are proposed. There is no
launchable entry point, native success claim, placeholder verified callback,
or source export here. A final bound owner must authenticate the accepted
source, original maps, independent clone and complete selected scene packet.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-parcel-boundary-native-r43-draft.py'
spec = importlib.util.spec_from_file_location('_r43_unbound_guards', ROOT/'scripts/unreal/exterior-context-parcel-boundary-guards-r43-draft.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
MAP = '/Game/Brezi/Maps/Brezi'
FUTURE_CANDIDATE = ROOT/'output/unreal/exterior-20261002-r43a'
FUTURE_REPORT = None
ACTUAL_NATIVE_PROCESS_ID = None


def cyclic(face):
    return min(tuple(face[i:] + face[:i]) for i in range(3))


def expected_corners(row):
    g.validate_export_mesh(row)
    return [cyclic([tuple(row['expectedNativeVerticesCm'][i] + row['uv0'][i])
                    for i in row['indices'][at:at+3]])
            for at in range(0, len(row['indices']), 3)]


def read_native_corners(u, mesh, row):
    """Real full native P/UV0/section/winding readback, before scene additions."""
    g.require(mesh and mesh.get_class().get_path_name() == '/Script/Engine.StaticMesh'
              and mesh.get_path_name().startswith(g.PREFIX+'/Geometry/')
              and mesh.get_num_lods() == 1
              and len(mesh.get_editor_property('static_materials')) == 1,
              'Only owned one-LOD, one-section source master permitted')
    desc = mesh.get_static_mesh_description(0)
    count = len(row['indices'])//3
    g.require(desc and desc.get_triangle_count() == mesh.get_num_triangles(0) == count
              and mesh.get_num_sections(0) == 1,
              'Complete source/native triangle and section census required')
    actual = []
    for ordinal in range(count):
        triangle = u.TriangleID(id_value=ordinal)
        g.require(int(desc.get_triangle_polygon_group(triangle).id_value) == 0,
                  'Ordered single-material section identity differs')
        face = []
        for corner in range(3):
            vi = desc.get_triangle_vertex_instance(triangle, corner)
            p = desc.get_vertex_position(desc.get_vertex_instance_vertex(vi))
            uv = desc.get_vertex_instance_uv(vi, 0)
            face.append(tuple(float(getattr(p, key)) for key in 'xyz')
                        + tuple(float(getattr(uv, key)) for key in 'xy'))
        actual.append(cyclic(face))
    g.exact(actual, expected_corners(row), 'Full ordered authored native P/UV0/section/winding differs')
    return {'id': row['id'], 'material': row['material'], 'asset': mesh.get_path_name(),
            'triangles': count, 'fullOrderedNativeF32PositionUv0SectionWindingSha256': g.digest(actual),
            'sourceWasAuthored': True, 'providerGeometryClaimed': False,
            'nativeNormalTangentNumericReadbackPerformed': False,
            'contactCollisionOrAppearanceAccepted': False}


def bind_full_geometry(u, meshes, rows):
    """Counts prune candidates; complete corners establish the unique identity."""
    g.require(len(rows) == len(meshes) == 3
              and {row['material'] for row in rows} == set(g.MATERIAL_ROLES)
              and len({row['id'] for row in rows}) == 3
              and len({mesh.get_path_name() for mesh in meshes}) == 3,
              'Three distinct owned material-specific masters required')
    result, proof = {}, []
    for mesh in meshes:
        candidates = [row for row in rows if len(row['indices'])//3 == mesh.get_num_triangles(0)]
        matches = []
        for row in candidates:
            try:
                observation = read_native_corners(u, mesh, row)
            except RuntimeError:
                continue
            matches.append((row, observation))
        g.require(len(matches) == 1, 'Exactly one complete authored source identity must match')
        row, observation = matches[0]
        g.require(row['material'] not in result, 'Duplicate merged source identity')
        result[row['material']] = mesh
        proof.append(observation)
    g.require(set(result) == set(g.MATERIAL_ROLES), 'Every authored merged source master must match')
    return result, proof


def import_pipeline_options(u, pipelines):
    """Proven owned pipeline settings; existing pipeline assets are never edited."""
    g.require(len(pipelines) == 3 and all(p.get_path_name().startswith(g.PREFIX+'/Pipeline/') for p in pipelines),
              'Three owned pipeline copies required')
    mesh = pipelines[0].get_editor_property('mesh_pipeline')
    for key, value in {'combine_static_meshes_behavior': u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE,
                       'collision': False, 'build_nanite': False, 'generate_lightmap_u_vs': False}.items():
        mesh.set_editor_property(key, value)
    common = pipelines[0].get_editor_property('common_meshes_properties')
    for key, value in {'bake_meshes': False, 'bake_pivot_meshes': False, 'import_lods': False,
                       'remove_degenerates': False, 'recompute_normals': False,
                       'recompute_tangents': True, 'use_full_precision_u_vs': True}.items():
        common.set_editor_property(key, value)
    material = pipelines[0].get_editor_property('material_pipeline')
    material.set_editor_property('import_materials', False)
    material.get_editor_property('texture_pipeline').set_editor_property('import_textures', False)
    pipelines[2].set_editor_property('scene_hierarchy_type', u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)


def new_visual_component_policy(u, actor, mesh, material, role, original_actor_paths):
    """Restricted proposed new actor route; no existing UObject setters."""
    g.require(role in g.MATERIAL_ROLES and actor.get_class().get_path_name() == '/Script/Engine.StaticMeshActor'
              and actor.get_path_name() not in original_actor_paths
              and g.TAG+role in [str(tag) for tag in actor.get_editor_property('tags')],
              'An already tagged new authored StaticMeshActor is required')
    component = actor.get_editor_property('static_mesh_component')
    g.require(component and component.get_owner() == actor
              and actor.get_editor_property('root_component') == component,
              'The sole new rendering component must own the actor identity pose')
    g.require(component.set_static_mesh(mesh), 'Cannot assign own authored master')
    component.set_material(0, material)
    # Installed PrimitiveComponent.h SetCollisionEnabled is void.
    component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    component.set_visibility(True)
    component.set_hidden_in_game(False)
    return component


def require_actual_preservation(before, saved, expected, raw_before, raw_saved,
                                material_before, material_saved, textures_before, textures_saved):
    """Compare supplied complete actual observations, never mark a callback true."""
    g.exact(saved, expected, 'Complete old scene plus source-bound three additions differs')
    g.require(len(before) == g.RECORDED_SELECTED_BASE_COUNTS['actors'], 'Actual selected before census differs')
    for actor, row in before.items():
        g.require(g.digest(saved[actor]) == g.digest(row), 'Original actor witness changed: '+actor)
    g.exact(raw_saved, raw_before, 'Any original wrapped matrix/order/seed/custom state changed')
    g.exact(material_saved, material_before, 'Any original full graph/aux/usage changed')
    g.exact(textures_saved, textures_before, 'Any original visible texture setting/source identity changed')
    return True


def import_geometry(*_args, **_kwargs):
    g.require_native_binding()


def apply_native(*_args, **_kwargs):
    g.require_native_binding()


if __name__ == '__main__':
    g.require_native_binding()
