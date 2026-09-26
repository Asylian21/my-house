"""Two-process, asset-only Nanite study on a fresh verified Shipping clone.

The map, actor bindings, materials and historical donor remain byte-identical.
This does not accept the experiment or change a production quality recipe.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts/unreal'))
from nanite_study_policy import MAX_MESHES, TARGET_MESHES, asset_file, asset_path, ranked_records, require, validate_changes, validate_derived_bounds

spec = importlib.util.spec_from_file_location('performance_optimize', ROOT/'scripts/unreal/performance-optimize.py')
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
read, write, sha, digest = P.read, P.write, P.sha, P.digest
REPORT = 'nanite-study-report.json'
STATE = 'nanite-study-state.json'
SHAPE_ARRAYS = ('sphere_elems', 'box_elems', 'sphyl_elems', 'convex_elems', 'tapered_capsule_elems',
                'level_set_elems', 'skinned_level_set_elems', 'ml_level_set_elems', 'skinned_triangle_mesh_elems')


def now():
    return datetime.now(timezone.utc).isoformat()


def text(value):
    result = value.export_text()
    require(isinstance(result, str) and result, 'Missing reflected struct witness')
    return result


def opaque(u, material):
    visited = set()
    while isinstance(material, u.MaterialInstance):
        require(material.get_path_name() not in visited, 'Cyclic material parent')
        visited.add(material.get_path_name())
        overrides = material.get_editor_property('base_property_overrides')
        if overrides.get_editor_property('override_blend_mode'):
            return overrides.get_editor_property('blend_mode') == u.BlendMode.BLEND_OPAQUE
        material = material.get_editor_property('parent')
    return isinstance(material, u.Material) and material.get_editor_property('blend_mode') == u.BlendMode.BLEND_OPAQUE


def source_geometry(u, mesh, subsystem):
    require(subsystem.get_lod_count(mesh) == 1 and mesh.get_num_lods() == 1, 'Study requires exactly one source/render LOD')
    desc = mesh.get_static_mesh_description(0)
    require(desc and 0 < desc.get_triangle_count() < 512, 'Missing bounded source MeshDescription')
    channels = subsystem.get_num_uv_channels(mesh, 0)
    require(0 < channels <= 8, 'Invalid source UV channel count')
    rows, instances = [], set()
    for index in range(desc.get_triangle_count()):
        tri = u.TriangleID(id_value=index)
        require(desc.is_triangle_valid(tri), 'Sparse source triangle ids require separate review')
        corners = []
        for corner in range(3):
            instance = desc.get_triangle_vertex_instance(tri, corner)
            require(desc.is_vertex_instance_valid(instance), 'Invalid source vertex instance')
            vertex = desc.get_vertex_instance_vertex(instance)
            require(desc.is_vertex_valid(vertex), 'Invalid source vertex')
            position = desc.get_vertex_position(vertex)
            uvs = [desc.get_vertex_instance_uv(instance, channel) for channel in range(channels)]
            corners.append({'vertexId': int(vertex.id_value), 'instanceId': int(instance.id_value),
                            'positionCm': P.vec(position), 'uvs': [[float(uv.x), float(uv.y)] for uv in uvs]})
            instances.add(int(instance.id_value))
        rows.append({'triangleId': index, 'polygonGroup': int(desc.get_triangle_polygon_group(tri).id_value), 'corners': corners})
    require(len(instances) == desc.get_vertex_instance_count(), 'Incomplete source vertex-instance coverage')
    return {'rows': rows, 'vertices': desc.get_vertex_count(), 'instances': len(instances), 'uvChannels': channels}


def mesh_witness(u, mesh, subsystem):
    body = mesh.get_editor_property('body_setup')
    require(body, 'Missing source BodySetup')
    agg = body.get_editor_property('agg_geom')
    require(all(len(agg.get_editor_property(name)) == 0 for name in SHAPE_ARRAYS), 'Study excludes every simple collision shape')
    require(mesh.get_editor_property('complex_collision_mesh') is None, 'Study excludes alternate complex collision meshes')
    build = subsystem.get_lod_build_settings(mesh, 0)
    require(not build.get_editor_property('generate_lightmap_u_vs'), 'Study excludes generated UV channels')
    materials = []
    for slot in mesh.get_editor_property('static_materials'):
        material = slot.get_editor_property('material_interface')
        require(material and opaque(u, material), 'Study requires every native mesh material to be opaque')
        materials.append({'path': material.get_path_name(), 'slot': str(slot.get_editor_property('material_slot_name')),
                          'importedSlot': str(slot.get_editor_property('imported_material_slot_name'))})
    sections = [{'material': subsystem.get_lod_material_slot(mesh, 0, i),
                 'collision': subsystem.is_section_collision_enabled(mesh, 0, i)} for i in range(mesh.get_num_sections(0))]
    body_fields = {name: str(body.get_editor_property(name)) for name in
                   ('collision_trace_flag', 'never_needs_cooked_collision_data', 'double_sided_geometry')}
    physical = body.get_editor_property('phys_material')
    body_fields.update(path=body.get_path_name(), physMaterial=physical.get_path_name() if physical else None,
                       aggregate=text(agg), defaultInstance=text(body.get_editor_property('default_instance')))
    return {'sourceGeometry': source_geometry(u, mesh, subsystem), 'materials': materials, 'sections': sections,
            'body': body_fields, 'lodForCollision': int(mesh.get_editor_property('lod_for_collision')),
            'buildSettings': text(build), 'reductionSettings': text(subsystem.get_lod_reduction_settings(mesh, 0)),
            'renderTriangles': mesh.get_num_triangles(0), 'renderSections': mesh.get_num_sections(0)}


def derived_bounds(mesh):
    return [P.vec(mesh.get_bounds().origin), P.vec(mesh.get_bounds().box_extent)]


def mesh_exclusion(u, mesh, subsystem):
    """Known safety exclusions are skipped; missing/native API failures still abort."""
    body = mesh.get_editor_property('body_setup')
    if not body:
        return 'missing BodySetup'
    agg = body.get_editor_property('agg_geom')
    if any(len(agg.get_editor_property(name)) for name in SHAPE_ARRAYS):
        return 'simple collision shape'
    if mesh.get_editor_property('complex_collision_mesh') is not None:
        return 'alternate complex collision mesh'
    if subsystem.get_lod_count(mesh) != 1 or mesh.get_num_lods() != 1:
        return 'multiple source/render LODs'
    if subsystem.get_lod_build_settings(mesh, 0).get_editor_property('generate_lightmap_u_vs'):
        return 'generated source UV channels'
    if not all(opaque(u, slot.get_editor_property('material_interface')) for slot in mesh.get_editor_property('static_materials')):
        return 'nonopaque native mesh material'
    return None


def select(u, actors, scene, doors, subsystem):
    references = {}
    for actor in actors.get_all_level_actors():
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = component.get_editor_property('static_mesh')
            if mesh:
                references.setdefault(mesh.get_path_name(), []).append((actor, component, mesh))
    selected, excluded = [], {}
    for record in ranked_records(scene, doors):
        identity = record['id']
        refs = references.get(asset_path(identity), [])
        if len(refs) != 1:
            excluded[identity] = 'missing or shared asset reference'
            continue
        actor, component, mesh = refs[0]
        if (not actor.actor_has_tag('BreziGenerated') or not actor.actor_has_tag(identity)
                or isinstance(component, u.InstancedStaticMeshComponent)
                or component.get_collision_enabled() != u.CollisionEnabled.NO_COLLISION
                or component.get_editor_property('disallow_nanite')
                or component.get_editor_property('mobility') != u.ComponentMobility.STATIC
                or actor.get_editor_property('hidden') or component.get_editor_property('hidden_in_game')
                or not component.get_editor_property('visible')):
            excluded[identity] = 'component is not a visible static collisionless source actor'
            continue
        if mesh.get_editor_property('nanite_settings').get_editor_property('enabled'):
            excluded[identity] = 'already Nanite'
            continue
        if not all(opaque(u, component.get_material(i)) for i in range(component.get_num_materials())):
            excluded[identity] = 'nonopaque current component material'
            continue
        reason = mesh_exclusion(u, mesh, subsystem)
        if reason:
            excluded[identity] = reason
            continue
        require(u.EditorAssetLibrary.get_metadata_tag(mesh, 'source_object_id') == identity, 'Mesh source identity differs')
        snapshot = mesh_witness(u, mesh, subsystem)
        require(len(snapshot['sourceGeometry']['rows']) == record['triangles'], 'Native source triangle count differs')
        selected.append({'sourceId': identity, 'asset': mesh.get_path_name(), 'actor': actor.get_path_name(),
                         'name': record['name'], 'sourceBoundsMm': record['boundsMm'], 'naniteEnabledInitially': False,
                         'componentDisallowNanite': False,
                         'file': asset_file(identity), 'triangles': record['triangles'], 'witness': snapshot,
                         'witnessSha256': digest(snapshot), 'derivedBoundsBeforeCm': derived_bounds(mesh)})
        if len(selected) == TARGET_MESHES:
            break
    require(selected, 'No eligible opaque collisionless small interior mesh cohort')
    return selected, excluded


def finish(u, levels):
    world = levels.get_current_level().get_outer()
    u.SystemLibrary.execute_console_command(world, 'Editor.AsyncStaticMeshCompilation 0')
    require(u.SystemLibrary.get_console_variable_int_value('Editor.AsyncStaticMeshCompilation') == 0,
            'Study requires synchronous static mesh compilation')
    u.SystemLibrary.execute_console_command(world, 'Editor.AsyncStaticMeshCompilationFinishAll')


def preflight(u, levels, subsystem, candidates, excluded):
    """Try at most 128 meshes in memory; never save a mesh outside the bounds gate."""
    accepted = []
    for row in candidates:
        mesh = u.load_asset(row['asset'])
        settings = mesh.get_editor_property('nanite_settings')
        previous = settings.export_text()
        changes = [('enabled', True), ('keep_percent_triangles', 1.0), ('trim_relative_error', 0.0),
                   ('fallback_target', u.NaniteFallbackTarget.PERCENT_TRIANGLES),
                   ('fallback_percent_triangles', 1.0), ('fallback_relative_error', 0.0)]
        original_values = [(name, settings.get_editor_property(name)) for name, value in changes]
        for name, value in changes:
            settings.set_editor_property(name, value)
        desired = settings.export_text()
        mesh.set_editor_property('nanite_settings', settings)
        finish(u, levels)
        require(mesh_witness(u, mesh, subsystem) == row['witness'], 'Nanite changed protected source mesh witness: '+row['sourceId'])
        bounds = derived_bounds(mesh)
        try:
            validate_derived_bounds(row['derivedBoundsBeforeCm'], bounds)
        except RuntimeError as error:
            excluded[row['sourceId']] = {'reason': str(error), 'derivedBoundsBeforeCm': row['derivedBoundsBeforeCm'],
                                         'derivedBoundsAfterCm': bounds, 'protectedSourceWitnessUnchanged': True,
                                         'assetSaved': False}
            restored = mesh.get_editor_property('nanite_settings')
            for name, value in original_values:
                restored.set_editor_property(name, value)
            mesh.set_editor_property('nanite_settings', restored)
            finish(u, levels)
            require(mesh.get_editor_property('nanite_settings').export_text() == previous, 'Preflight Nanite settings did not restore')
            require(mesh_witness(u, mesh, subsystem) == row['witness'], 'Preflight changed protected source after restore')
            continue
        row['naniteBefore'], row['naniteExpected'] = previous, desired
        accepted.append(row)
    require(accepted, 'Every bounded candidate failed native preflight; do not broaden the study gate')
    return accepted


def main():
    import unreal as u
    require(os.environ.get('BREZI_MODEL_OUTPUT') and os.environ.get('BREZI_PERFORMANCE_SOURCE'), 'Explicit study source/output required')
    stage = os.environ.get('BREZI_NANITE_STUDY_STAGE')
    require(stage in ('apply', 'verify'), 'Explicit apply or verify stage required')
    source, output = P.checked_paths(ROOT/os.environ['BREZI_PERFORMANCE_SOURCE'], ROOT/os.environ['BREZI_MODEL_OUTPUT'])
    project = output/'Project/BreziTwin'
    require(Path(u.Paths.project_dir()).resolve() == project, 'Wrong native project')
    require(not (output/'performance-scene-report.json').exists(), 'Nanite study cannot combine with map migration')
    profile, donor = read(output/'profile.json'), read(source/'model-package.json')
    require(profile['gameConfiguration'] == donor['gameConfiguration'] == 'Shipping', 'Study requires identical Shipping configuration')
    require(donor['status'] == 'current-model-packaged' and not donor.get('experimentalStudy'), 'Study requires a verified nonexperimental donor')
    content, source_content = project/'Content', source/'Project/BreziTwin/Content'
    files = [Path(__file__), ROOT/'scripts/unreal/nanite_study_policy.py', ROOT/'scripts/unreal/performance-optimize.py',
             ROOT/'scripts/unreal/performance_scene_policy.py']
    pipeline = {str(p): sha(p) for p in files}
    inputs = {str(output/'geometry'/name): sha(output/'geometry'/name) for name in ('scene.json', 'doors.json')}
    scene, doors = read(output/'geometry/scene.json'), read(output/'geometry/doors.json')
    require(doors['sourceManifestSha256'] == inputs[str(output/'geometry/scene.json')], 'Stale door/source contract')
    levels, actors = u.get_editor_subsystem(u.LevelEditorSubsystem), u.get_editor_subsystem(u.EditorActorSubsystem)
    require(levels.load_level(P.MAP), 'Cannot load study map')
    subsystem = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    if subsystem is None:
        u.load_module('StaticMeshEditor')
        subsystem = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    require(subsystem is not None, 'StaticMeshEditor subsystem unavailable')
    finish(u, levels)
    report_file = output/REPORT
    if stage == 'apply':
        require(not report_file.exists() and not (output/STATE).exists(), 'Study output already used; preserve it and start fresh')
        before = P.inventory(content)
        require(before == P.inventory(source_content), 'Study Content must be the exact verified donor clone')
        candidates, excluded = select(u, actors, scene, doors, subsystem)
        original = P.witness(u, actors)
        selected = preflight(u, levels, subsystem, candidates, excluded)
        require(P.inventory(content) == before, 'Transient preflight unexpectedly saved Content')
        require(P.witness(u, actors) == original, 'Transient preflight changed protected actor witness')
        state = {'beforeContent': before, 'actors': original, 'selected': selected}
        write(output/STATE, state)
        report = {'schemaVersion': 1, 'owner': 'scripts/unreal/nanite-study.py', 'status': 'pending',
                  'experimental': True, 'accepted': False, 'renderedVerified': False, 'performanceAccepted': False,
                  'sourceOutput': str(source), 'project': str(project), 'mutationProcessId': os.getpid(),
                  'pipelineFiles': pipeline, 'inputFiles': inputs, 'stateFileSha256': sha(output/STATE),
                  'donorPackageSha256': sha(source/'model-package.json'), 'beforeAssetHashes': {str(content/p): h for p, h in before.items()},
                  'cohortLimit': MAX_MESHES, 'attemptedCohortCount': len(candidates), 'excludedSourceCandidates': excluded,
                  'limitations': ['Raw source normals/tangents and cooked Chaos bytes are not exposed to this Python witness.',
                                  'Cohort has no gameplay collision; exact source topology/positions/all UVs, build settings, material and collision configuration are witnessed.',
                                  'Derived mesh bounds allow at most one float32 ULP per coordinate, capped at 0.0002 cm; source vertex positions must remain exact.',
                                  'Nanite position quantization and rendered shading require separate visual A/B; no acceptance is inferred.',
                                  'Use the original donor as A with Nanite enabled in both A and B; global r.Nanite=0 is not an isolated comparator.']}
        write(report_file, report)
        try:
            for row in selected:
                mesh = u.load_asset(row['asset'])
                require(mesh.get_editor_property('nanite_settings').export_text() == row['naniteExpected'], 'Preflight settings changed before save')
                require(mesh_witness(u, mesh, subsystem) == row['witness'], 'Nanite changed protected mesh witness: '+row['sourceId'])
                validate_derived_bounds(row['derivedBoundsBeforeCm'], derived_bounds(mesh))
                require(u.EditorAssetLibrary.save_loaded_asset(mesh, False), 'Cannot save study mesh')
            require(P.witness(u, actors) == original, 'Nanite changed actor/material/collision/instance witness')
            after = P.inventory(content)
            validate_changes(before, after, [row['sourceId'] for row in selected])
            require(P.inventory(source_content) == before, 'Historical donor Content changed')
            report.update(status='nanite-study-applied-native-verification-pending', appliedAt=now(),
                          selected=[{k: v for k, v in row.items() if k != 'witness'} for row in selected],
                          afterAssetHashes={str(content/p): h for p, h in after.items()})
        except Exception as error:
            report.update(status='failed', error=str(error))
            raise
        finally:
            write(report_file, report)
    else:
        report = read(report_file)
        require(report['status'] == 'nanite-study-applied-native-verification-pending', 'No successful pending study application')
        require(report['pipelineFiles'] == pipeline and report['inputFiles'] == inputs, 'Study inputs/pipeline changed between processes')
        require(sha(output/STATE) == report['stateFileSha256'], 'Study witness state changed')
        require(sha(source/'model-package.json') == report['donorPackageSha256'], 'Study donor receipt changed')
        state = read(output/STATE)
        try:
            require(P.witness(u, actors) == state['actors'], 'Fresh-process actor/material/collision/instance witness differs')
            saved = []
            for row, wanted in zip(report['selected'], state['selected']):
                require(row['sourceId'] == wanted['sourceId'], 'Study cohort changed')
                mesh = u.load_asset(row['asset'])
                actual = mesh_witness(u, mesh, subsystem)
                require(actual == wanted['witness'], 'Fresh-process protected mesh witness differs: '+row['sourceId'])
                bounds = derived_bounds(mesh)
                bounds_error = validate_derived_bounds(wanted['derivedBoundsBeforeCm'], bounds)
                require(mesh.get_editor_property('nanite_settings').export_text() == row['naniteExpected'], 'Saved Nanite settings differ')
                require(mesh.get_editor_property('nanite_settings').get_editor_property('enabled'), 'Saved Nanite enable flag false')
                saved.append({'sourceId': row['sourceId'], 'beforeWitnessSha256': digest(wanted['witness']),
                              'afterWitnessSha256': digest(actual), 'naniteEnabled': True,
                              'derivedBoundsBeforeCm': wanted['derivedBoundsBeforeCm'], 'derivedBoundsAfterCm': bounds,
                              'derivedBoundsMaxErrorCm': bounds_error})
            require(len(saved) == len(state['selected']) == len(report['selected']), 'Study cohort coverage differs')
            after = P.inventory(content)
            validate_changes(state['beforeContent'], after, [row['sourceId'] for row in saved])
            require({str(content/p): h for p, h in after.items()} == report['afterAssetHashes'], 'Study content changed between processes')
            require(P.inventory(source_content) == state['beforeContent'], 'Historical donor Content changed')
            report.update(status='nanite-study-validated-unaccepted', nativeProcessId=os.getpid(), generatedAt=now(),
                          savedReloaded=True, protectedContentUnchanged=True, mapUnchanged=True,
                          actorCount=len(state['actors']), actorWitnessSha256=digest(state['actors']),
                          savedActorWitnessSha256=digest(P.witness(u, actors)), savedMeshReadback=saved,
                          sourceGeometryMaterialsAndCollisionPreserved=True)
        except Exception as error:
            report.update(status='failed', error=str(error), generatedAt=now())
            raise
        finally:
            write(report_file, report)
    for path, value in pipeline.items():
        require(sha(path) == value, 'Study pipeline changed while running')


if __name__ == '__main__':
    main()
