"""Component-local raster fallback for thin timber deck Nanite shadow artifacts.

Native A/B on the accepted R3 package isolates repeated board-end dark triangles
to the Nanite/shadow path. This stage keeps the existing complete fallback mesh,
source packages, materials and collisions; global Nanite/shadows remain enabled.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/photoreal-deck-shadow.py'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def select_targets(scene):
    require(scene.get('activeDesign') == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'},
            'Deck shadow correction requires C/B/B')
    expected = {t['id'] for t in scene['terraces']} | {scene['poolDeck']['id']}
    require(len(expected) == 4, 'Review changed deck semantic coverage')
    result = []
    for row in scene['objects']:
        if not row.get('enabled'):
            continue
        entity = row.get('metadata', {}).get('entityId')
        if entity not in expected or row['materialNames'] != [entity+' · PBR materiál']:
            continue
        require(row['group'] in ('Decking', 'Pool') and row['instances'] == 1
                and len(row['materialSlots']) == 1 and not row['metadata'].get('doorMotion'),
                'Unexpected deck board component')
        box = row['boundsMm']
        require(abs(box['min'][2]+8) < .01 and abs(box['max'][2]-20) < .01,
                'Review changed 28mm deck board thickness')
        result.append({'id': row['id'], 'entityId': entity, 'sourceId': row['sourceId'],
                       'name': row['name'], 'triangles': row['triangles']})
    require(len(result) == 4 and {r['entityId'] for r in result} == expected,
            'Missing or duplicate semantic timber deck')
    return result


def components(u, ids):
    result = {}
    for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        matches = set(map(str, actor.get_editor_property('tags'))) & ids
        if not matches or actor.actor_has_tag('BreziWalkSupportProxy'):
            continue
        require(len(matches) == 1, 'Ambiguous deck actor')
        key = next(iter(matches))
        parts = list(actor.get_components_by_class(u.StaticMeshComponent))
        require(key not in result and len(parts) == 1, 'Ambiguous deck source component')
        result[key] = parts[0]
    require(set(result) == ids, 'Missing native timber deck component')
    return result


def transform(value):
    return {name: [round(float(getattr(getattr(value, name), axis)), 7) for axis in axes]
            for name, axes in [('translation', 'xyz'), ('rotation', 'xyzw'), ('scale3d', 'xyz')]}


def witness(u, parts):
    result = {}
    for key, c in parts.items():
        mesh = c.get_editor_property('static_mesh')
        actor = c.get_owner()
        settings = mesh.get_editor_property('nanite_settings')
        origin, extent, _ = u.SystemLibrary.get_component_bounds(c)
        result[key] = {
            'mesh': mesh.get_path_name(), 'triangles': mesh.get_num_triangles(0),
            'sections': mesh.get_num_sections(0), 'component': c.get_name(),
            'transform': transform(c.get_world_transform()), 'actorTransform': transform(actor.get_actor_transform()),
            'bounds': [round(float(getattr(v, a)), 5) for v in (origin, extent) for a in 'xyz'],
            'materials': [c.get_material(i).get_path_name() if c.get_material(i) else None
                          for i in range(c.get_num_materials())],
            'meshMaterials': [mesh.get_material(i).get_path_name() if mesh.get_material(i) else None
                              for i in range(c.get_num_materials())],
            'collision': str(c.get_collision_enabled()), 'profile': str(c.get_collision_profile_name()),
            'responses': {name: str(c.get_collision_response_to_channel(getattr(u.CollisionChannel, name)))
                          for name in dir(u.CollisionChannel) if name.startswith('ECC_') and name != 'ECC_MAX'},
            'visible': bool(c.is_visible()), 'hiddenInGame': bool(c.get_editor_property('hidden_in_game')),
            'actorHidden': bool(actor.get_editor_property('hidden')),
            'tags': sorted(map(str, c.get_editor_property('component_tags'))),
            'actorTags': sorted(map(str, actor.get_editor_property('tags'))),
            'castShadow': bool(c.get_editor_property('cast_shadow')),
            'nanite': {name: str(settings.get_editor_property(name)) if name == 'fallback_target'
                       else settings.get_editor_property(name) for name in
                       ['enabled', 'fallback_target', 'fallback_percent_triangles', 'fallback_relative_error']}}
    return result


def correction_plan(u, targets, parts, source):
    result = []
    for row in targets:
        c = parts[row['id']]
        state = source[row['id']]
        enabled = bool(state['nanite']['enabled'])
        require(state['triangles'] == row['triangles'] and state['visible'] and not state['hiddenInGame']
                and not state['actorHidden'], 'Deck source state changed')
        require(c.get_editor_property('disallow_nanite') is False, 'Deck raster override already exists')
        if enabled:
            require(state['nanite']['fallback_target'] == str(u.NaniteFallbackTarget.PERCENT_TRIANGLES)
                    and state['nanite']['fallback_percent_triangles'] == 1.0
                    and state['nanite']['fallback_relative_error'] == 0.0,
                    'Deck requires existing full-resolution fallback')
        result.append({**row, 'mesh': state['mesh'], 'component': state['component'],
                       'beforeDisallowNanite': False, 'afterDisallowNanite': enabled,
                       'reason': 'thin-board Nanite shadow artifact' if enabled else 'source already uses raster'})
    require(sum(r['afterDisallowNanite'] for r in result) == 3, 'Review changed native deck Nanite policy')
    return result


def save(geometry, report):
    (Path(geometry).parent/'photoreal-deck-shadow-report.json').write_text(
        json.dumps(report, indent=2, ensure_ascii=False)+'\n')


def apply_deck(scene, geometry):
    import unreal as u
    geometry = Path(geometry)
    require(u.SystemLibrary.get_console_variable_int_value('r.Nanite') == 1, 'Keep global Nanite enabled')
    targets = select_targets(scene)
    parts = components(u, {r['id'] for r in targets})
    source = witness(u, parts)
    bindings = correction_plan(u, targets, parts, source)
    for row in bindings:
        if row['afterDisallowNanite']:
            parts[row['id']].set_editor_property('disallow_nanite', True)
    require(witness(u, parts) == source, 'Deck raster override changed protected source state')
    require(all(parts[r['id']].get_editor_property('disallow_nanite') == r['afterDisallowNanite']
                for r in bindings), 'Deck raster override readback differs')
    report = {'schemaVersion': 1, 'owner': OWNER, 'status': 'authored-reload-pending',
              'sourceManifestSha256': sha(geometry/'scene.json'), 'sourceObjSha256': sha(geometry/'dom-mm.obj'),
              'pipelineFiles': {OWNER: sha(__file__)}, 'bindings': bindings, 'sourceWitness': source,
              'componentOverrides': 3, 'meshAssetsModified': False, 'sourceGeometryModified': False,
              'collisionModified': False, 'materialsModified': False, 'globalNanite': 1,
              'savedReloaded': False, 'nativeRenderedVerified': False,
              'diagnosis': 'Same-pose R3 artifact vanishes with shadows off and with Nanite off; no lawn dependency.',
              'scope': 'Existing complete raster fallback on three timber board components; no global render downgrade.'}
    save(geometry, report)
    return report


def verify_deck(scene, geometry, report):
    import unreal as u
    geometry = Path(geometry)
    require(report['owner'] == OWNER and report['sourceManifestSha256'] == sha(geometry/'scene.json')
            and report['sourceObjSha256'] == sha(geometry/'dom-mm.obj'), 'Deck correction source changed')
    for name, expected in report['pipelineFiles'].items():
        require(sha(ROOT/name) == expected, 'Deck correction helper changed')
    targets = select_targets(scene)
    require(targets == [{k: r[k] for k in targets[0]} for r in report['bindings']], 'Deck correction selection changed')
    parts = components(u, {r['id'] for r in targets})
    require(witness(u, parts) == report['sourceWitness'], 'Deck source state changed after reload')
    require(all(parts[r['id']].get_editor_property('disallow_nanite') == r['afterDisallowNanite']
                for r in report['bindings']), 'Deck component raster override was not saved')
    require(u.SystemLibrary.get_console_variable_int_value('r.Nanite') == 1, 'Global Nanite changed')
    report.update(status='saved-reloaded-validated', savedReloaded=True)
    save(geometry, report)
    return report
