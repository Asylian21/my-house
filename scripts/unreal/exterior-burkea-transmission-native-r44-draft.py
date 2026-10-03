"""UNBOUND R44 native kernels: one own Material, one existing slot1 override.

No native entry is runnable in this draft. A separately reviewed bound owner
must authenticate the future image-selected saved R43b and an independent
clone. Historical R39 source observations never select that future base.
"""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-burkea-transmission-native-r44-draft.py'
SCHEMA = 'brezi-unbound-single-burkea-leaf-material-native-contract-r44'
PROPOSAL = ROOT/'output/unreal/exterior-burkea-transmission-20261002-r44-source-proposal/burkea-transmission-source-proposal.json'
PROPOSAL_SHA = '94d8cfcea6ada48380d87e66b2295c361f42e4599c53b23c1ede703ff0a317d7'
SOURCE = ROOT/'scripts/unreal/exterior-burkea-transmission-draft-r44.py'
SOURCE_SHA = '00860160d0c479cc84da5f89bf79646a8611fa123a1700596c495878cca8ec5f'
R43_NATIVE = ROOT/'scripts/unreal/exterior-context-parcel-boundary-native-r43-r2.py'
R43_NATIVE_SHA = '488553a3cdba3963196ad106565a2874d040acf1c9915e97c8f4eb8021bda763'
TREE_READER = ROOT/'scripts/unreal/exterior-original-tree-materials.py'
TREE_READER_SHA = '9cad9bc1f8b47b7d08b8aa294b370f9c8ac0059e7513d9a66639e6d93242305c'
MAP = '/Game/Brezi/Maps/Brezi'
LEAF = '/Game/Brezi/OriginalTree20261002R24/Materials/M_ph_original_tree_small_02_leaves_r24.M_ph_original_tree_small_02_leaves_r24'
ACTOR = '/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.BreziVegetationPatch_2312'
COMPONENT = ACTOR+'.Instances'
OWN = '/Game/Brezi/BurkeaTransmission20261002R44/Materials/M_burkea_leaf_transmission_r44.M_burkea_leaf_transmission_r44'
ROLE = 'BreziOriginalTreeR24:ph_original_tree_small_02_leaves_r24:strength'
OLD = struct.unpack('<f', struct.pack('<f', .08))[0]
NEW = struct.unpack('<f', struct.pack('<f', .24))[0]
FUTURE_BINDING = {'selectedNativeReport': None, 'selectedNativeProcess': None,
    'selectedRawProcess': None, 'selectedCurrentByteAudit': None,
    'rootR43ImageDecision': None, 'projectClone': None, 'candidateProject': None,
    'selectedNativePlan': None, 'selectedPreflight': None,
    'selectedTerminalSourcePinCount': None, 'selectedCounts': None,
    'nativePlan': None, 'nativePreflight': None}


def require(ok, message):
    if not ok: raise RuntimeError(message)
def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
def pin(path):
    p = Path(path).resolve();return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}
def checked(row):
    require(type(row) is dict and set(row) == {'path', 'sha256', 'bytes'}, 'Exact immutable pin required')
    p = Path(row['path']);require(p.is_absolute() and p.resolve() == p and not p.is_symlink() and pin(p) == row,
        'Immutable consumed pin differs');return p
def module(name, path, expected):
    require(sha(path) == expected, 'Frozen source reader changed')
    s = importlib.util.spec_from_file_location(name, path);m = importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def exact(a, b, message):
    if isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)) and not isinstance(b, bool):
        require(math.isfinite(a) and math.isfinite(b) and struct.pack('<d', float(a)) == struct.pack('<d', float(b)), message)
    elif isinstance(a, (list, tuple)) and type(a) is type(b):
        require(len(a) == len(b), message)
        for x, y in zip(a, b): exact(x, y, message)
    elif isinstance(a, dict) and isinstance(b, dict):
        require(set(a) == set(b), message)
        for k in a: exact(a[k], b[k], message)
    else: require(type(a) is type(b) and a == b, message)
def persist(directory, name, value):
    path = Path(directory)/(name+'.json')
    with path.open('x') as f: json.dump(value, f, indent=2, sort_keys=True, allow_nan=False);f.write('\n')
    return pin(path)


def require_native_binding(bundle):
    # A caller cannot fill these public arguments to make this draft runnable.
    # The future bound owner is a NEW source revision with exact root pins.
    require(all(v is not None for v in FUTURE_BINDING.values()),
        'UNBOUND R44: actual saved R43b/image selection/clone/native plan remain absent')
    require(set(bundle) == {'source', 'base', 'binding'} and bundle['binding'] == FUTURE_BINDING,
        'Exact future three-key bound packet required')
    require(sha(PROPOSAL) == PROPOSAL_SHA and bundle['source']['proposalPin'] == pin(PROPOSAL)
        and bundle['source']['proposal'] == read(PROPOSAL), 'Frozen scalar-only proposal differs')
    b = bundle['base'];r = read(checked(FUTURE_BINDING['selectedNativeReport']))
    require(r == b['report'] and r['owner'] == 'scripts/unreal/exterior-context-parcel-boundary-native-r43-r2.py'
        and r['schemaVersion'] == 2 and r['status'] == 'verified-saved-three-authored-open-boundary-masters'
        and r['nativeApplied'] is True and r['savedMapUnloadedReloaded'] is True
        and r['sourceInputsUnchanged'] is True, 'Actual saved R43b required')
    # Root process, current byte audit, scoped image decision, clone rows and
    # terminal input set must additionally be authenticated by the NEW bound
    # producer against their actual schemas; no draft field invents that proof.
    raise RuntimeError('UNBOUND draft cannot authenticate future report/process/audit/decision/clone schemas')


def _source_math(): return module('_r44_private_frozen_source_math', SOURCE, SOURCE_SHA)
def _r43(): return module('_r44_private_frozen_full_readers', R43_NATIVE, R43_NATIVE_SHA)
def _leaf_graph(u, h, material):
    require(sha(TREE_READER) == TREE_READER_SHA, 'Specialized full tree reader changed')
    return h['treeMaterials'].graph_snapshot(u, material, h['existing'].graph_snapshot)
def _usage(u, h, material):
    return {'instancedStaticMeshes': bool(u.MaterialEditingLibrary.has_material_usage(material,
        h['existing'].native_enum(u.MaterialUsage, 'INSTANCEDSTATICMESHES'))),
        'nanite': bool(u.MaterialEditingLibrary.has_material_usage(material, u.MaterialUsage.MATUSAGE_NANITE))}
def _mesh_defaults(mesh):
    return [m.get_editor_property('material_interface').get_path_name()
        if m.get_editor_property('material_interface') else None for m in mesh.get_editor_property('static_materials')]
def _target(u, before, historical_target):
    source = _source_math();source.expected_scene(before, historical_target)
    scene = {a.get_path_name(): a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
    require(ACTOR in scene, 'Authenticated existing tree actor missing')
    cs = [c for c in scene[ACTOR].get_components_by_class(u.HierarchicalInstancedStaticMeshComponent)
        if c.get_path_name() == COMPONENT]
    require(len(cs) == 1 and cs[0].get_instance_count() == 4, 'Exact existing four-member component required')
    c = cs[0];require(c.get_material(1).get_path_name() == LEAF
        and list(c.get_editor_property('override_materials')) == [], 'Original default leaf slot required')
    defaults = _mesh_defaults(c.get_editor_property('static_mesh'))
    require(len(defaults) == 3 and defaults[1] == LEAF, 'Original branches/leaves/trunk mesh defaults required')
    return c, defaults


def _old_assets(u, bundle, h):
    """Fresh all-old graph/aux/usage/texture readback; no old asset setters.

    Future producer constructs exact fixed routes from selected R43 saved
    receipts. Never pick a reduced reader based on a runtime graph's shape.
    Unrecorded old auxiliary/usage fields are before/saved comparisons only.
    """
    base = bundle['base'];graphs = {}
    require(set(base['materialRecords']) == set(base['expectedMaterialAssets']), 'Closed actual old material set required')
    for asset, expected in sorted(base['materialRecords'].items()):
        m = u.EditorAssetLibrary.load_asset(asset);require(isinstance(m, u.Material), 'Old Material missing')
        route = expected['route'];require(route in ('basic', 'neighbor', 'tree'), 'Unknown full graph reader denied')
        observed = {'graph': base['native'].graph_snapshot(u, m, h, route),
            'aux': h['materials'].aux_snapshot(u, m), 'usage': _usage(u, h, m)}
        exact(observed['graph'], expected['graph'], 'Full selected old graph differs: '+asset)
        require(digest(observed['graph']) == expected['graphSha256'], 'Selected graph hash differs')
        if expected['aux'] is not None: exact(observed['aux'], expected['aux'], 'Recorded old sampler/world-position fields differ')
        for key, value in expected['recordedUsage'].items(): require(observed['usage'][key] == value, 'Recorded old usage differs')
        observed['selectedMetadata'] = {k: u.EditorAssetLibrary.get_metadata_tag(m, k) for k in expected['metadata']}
        require(observed['selectedMetadata'] == expected['metadata'], 'Selected old metadata differs')
        graphs[asset] = observed
    textures = {}
    require(set(base['textureRecords']) == set(base['expectedTextureAssets']), 'Closed actual old texture set required')
    for asset, expected in sorted(base['textureRecords'].items()):
        t = u.EditorAssetLibrary.load_asset(asset);require(isinstance(t, u.Texture2D), 'Old texture missing')
        observed = h['materials'].texture_snapshot(u, t)
        if 'partialSnapshot' in expected:
            _r43().g.texture_subset(observed, expected['partialSnapshot'])
            observed['selectedMetadata'] = {k: u.EditorAssetLibrary.get_metadata_tag(t, k) for k in expected['metadata']}
            require(observed['selectedMetadata'] == expected['metadata'], 'Original photo metadata differs')
        else: exact(observed, expected, 'Selected complete old texture policy differs')
        textures[asset] = observed
    return {'graphs': graphs, 'textures': textures}


def _create_own_material(u, bundle, h, original_record):
    assets = u.EditorAssetLibrary;old = assets.load_asset(LEAF)
    require(isinstance(old, u.Material) and not assets.does_asset_exist(OWN.split('.')[0]), 'Exact old Material and fresh own namespace required')
    source = _source_math();expected = source.proposed_graph(original_record)
    graph_before = _leaf_graph(u, h, old);exact(graph_before, original_record['graph'], 'Actual full leaf graph differs')
    require(len(graph_before['nodes']) == 10 and _usage(u, h, old) == {'instancedStaticMeshes': True, 'nanite': True},
        'Exact original graph and inherited usage required')
    aux = h['materials'].aux_snapshot(u, old);own = assets.duplicate_asset(LEAF.split('.')[0], OWN.split('.')[0])
    require(isinstance(own, u.Material) and own.get_path_name() == OWN, 'Only exact own Material copy required')
    exact(_leaf_graph(u, h, own), graph_before, 'Full initial graph copy differs')
    nodes = [n for n in u.MaterialEditingLibrary.get_material_expressions(own) if str(n.get_editor_property('desc')) == ROLE]
    require(len(nodes) == 1 and isinstance(nodes[0], u.MaterialExpressionConstant), 'One original strength Constant required')
    exact(float(nodes[0].get_editor_property('r')), OLD, 'Original encoded coefficient differs')
    nodes[0].set_editor_property('r', NEW)
    metadata = {'BreziGeneratedBy': OWNER, 'BreziR44SourceProposalSha256': PROPOSAL_SHA,
        'BreziR44OriginalLeafAsset': LEAF, 'BreziR44ArtisticTransmissionF32': repr(NEW)}
    for k, value in metadata.items(): assets.set_metadata_tag(own, k, value)
    errors = list(u.MaterialEditingLibrary.recompile_material(own));require(errors == [], 'Owned graph compile diagnostics report errors')
    graph = _leaf_graph(u, h, own);exact(graph, expected, 'Only one F32 transmission coefficient may differ')
    exact(_leaf_graph(u, h, old), graph_before, 'Original leaf graph changed')
    require(_usage(u, h, own) == _usage(u, h, old) and h['materials'].aux_snapshot(u, own) == aux,
        'Inherited material usage/sampler/world-position policy differs')
    require(assets.save_loaded_asset(own, only_if_is_dirty=False), 'Cannot save single own Material package')
    return own, {'asset': OWN, 'originalAsset': LEAF, 'graph': graph, 'graphSha256': digest(graph),
        'aux': aux, 'usage': _usage(u, h, own), 'metadata': metadata, 'compileErrors': errors,
        'oldEncodedF32': OLD, 'newArtisticEncodedF32': NEW, 'newPackageAssets': [OWN], 'newTextureObjects': 0,
        'materialPackagesIndependentlyUnloaded': False, 'numericNativeNormalTangentReadbackPerformed': False,
        'physicalLeafOpticsAccepted': False, 'nativeAppearanceAccepted': False}


def _verify_own_material(u, h, original_record, report):
    require(report['asset'] == OWN and report['newPackageAssets'] == [OWN] and report['newTextureObjects'] == 0,
        'Exactly one own material package required')
    old, own = (u.EditorAssetLibrary.load_asset(p) for p in (LEAF, OWN))
    require(isinstance(old, u.Material) and isinstance(own, u.Material), 'Saved original/owned materials missing')
    exact(_leaf_graph(u, h, old), original_record['graph'], 'Saved original leaf graph differs')
    graph = _leaf_graph(u, h, own);exact(graph, _source_math().proposed_graph(original_record), 'Saved scalar-only graph differs')
    exact(graph, report['graph'], 'Saved own graph differs from pre-save observation')
    require(digest(graph) == report['graphSha256'] and _usage(u, h, own) == _usage(u, h, old) == report['usage'], 'Saved hash/usage differs')
    exact(h['materials'].aux_snapshot(u, own), report['aux'], 'Saved own sampler/world-position auxiliaries differ')
    for k, value in report['metadata'].items(): require(u.EditorAssetLibrary.get_metadata_tag(own, k) == value, 'Owned metadata differs')
    return own


def _inventory(project):
    content, protected = {}, {}
    for p in Path(project).rglob('*'):
        if not p.is_file(): continue
        rel = p.relative_to(project).as_posix()
        if rel.split('/')[0] not in ('Content', 'Config', 'Source', 'Binaries') and rel != 'BreziTwin.uproject': continue
        require(not p.is_symlink(), 'Project symlink forbidden');row = {'sha256': sha(p), 'bytes': p.stat().st_size}
        (content if rel.startswith('Content/') else protected)[rel[8:] if rel.startswith('Content/') else rel] = row
    return content, protected
def _project_delta(bundle, after=False):
    base = bundle['base'];project = Path(bundle['binding']['candidateProject']);content, protected = _inventory(project)
    require(_inventory(base['project']) == (base['content'], base['protected']) and protected == base['protected']
        and len(protected) == 132, 'Original base and protected132 must remain exact')
    for row in base['clone']['files']:
        require(Path(row['source']).stat().st_ino != Path(row['destination']).stat().st_ino, 'Independent file inodes required')
    if not after: require(content == base['content'], 'Pristine clone bytes required');return content
    wanted = OWN.split('.')[0].replace('/Game/', '')+'.uasset'
    require(set(content)-set(base['content']) == {wanted} and set(base['content']) <= set(content), 'Only one new Material package permitted')
    require(sorted(k for k in base['content'] if content[k] != base['content'][k]) == ['Brezi/Maps/Brezi.umap'],
        'Only original map may change; all geometry/photos/old material packages exact')
    return content


def apply_trial(u, bundle, checkpoint):
    require_native_binding(bundle)  # Always rejects this unbound draft.
    r43 = _r43();h = r43.helpers(bundle);base = bundle['base'];directory = Path(checkpoint)
    require(not directory.exists(), 'Fresh native observations required');directory.mkdir()
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    _project_delta(bundle);require(levels.load_level(MAP), 'Cannot load own cloned map')
    before = r43.full(u, h);exact(before, base['savedWitness'], 'Complete selected before scene differs')
    raw = base['native'].raw_instance_controls(u, before)
    require(len(raw) == 2329 and sum(r['instances'] for r in raw.values()) == 678205, 'Actual all2329 raw controls required')
    exact(raw, base['rawControls'], 'Selected raw matrices/order/mainseed/custom state differs')
    assets_before = _old_assets(u, bundle, h);source = _source_math()
    target_record = base['historicalTarget'];c, defaults = _target(u, before, target_record)
    expected = source.expected_scene(before, target_record)
    evidence = {name: persist(directory, name, row) for name, row in [
        ('before-actors', before), ('expected-actors', expected), ('raw-before', raw), ('assets-before', assets_before)]}
    material, material_report = _create_own_material(u, bundle, h, base['originalLeafRecord'])
    evidence['new-material'] = persist(directory, 'new-material', material_report)
    c.set_material(1, material)  # Sole existing-component setter; no mesh/default/raw setter.
    require([v.get_path_name() if v else None for v in c.get_editor_property('override_materials')] == [None, OWN], 'Exact sparse [None,new] override required')
    exact(_mesh_defaults(c.get_editor_property('static_mesh')), defaults, 'Original mesh default slots changed')
    exact(r43.full(u, h), expected, 'Complete declared slot-only counterfactual differs before save')
    require(levels.save_current_level(), 'Cannot save owned slot override map')
    require(u.EditorLoadingAndSavingUtils.new_blank_map(False) and levels.load_level(MAP), 'Cannot unload/reload saved map')
    saved = r43.full(u, h);evidence['saved-actors'] = persist(directory, 'saved-actors', saved)
    exact(saved, expected, 'Complete saved slot-only counterfactual differs')
    scene = {a.get_path_name(): a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
    c = scene[ACTOR].get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
    require(c and c.get_path_name() == COMPONENT and c.get_instance_count() == 4, 'Saved exact four-tree component required')
    exact(_mesh_defaults(c.get_editor_property('static_mesh')), defaults, 'Saved original mesh default slots changed')
    material_saved = _verify_own_material(u, h, base['originalLeafRecord'], material_report)
    saved_material = {'asset': material_saved.get_path_name(), 'graph': _leaf_graph(u, h, material_saved),
        'aux': h['materials'].aux_snapshot(u, material_saved), 'usage': _usage(u, h, material_saved),
        'metadata': {k: u.EditorAssetLibrary.get_metadata_tag(material_saved, k) for k in material_report['metadata']}}
    evidence['new-material-saved'] = persist(directory, 'new-material-saved', saved_material)
    raw_saved = base['native'].raw_instance_controls(u, saved)
    evidence['raw-saved'] = persist(directory, 'raw-saved', raw_saved)
    exact(raw_saved, raw, 'All2329 raw state changed across save/reload')
    assets_saved = _old_assets(u, bundle, h)
    evidence['assets-saved'] = persist(directory, 'assets-saved', assets_saved)
    exact(assets_saved, assets_before, 'Any old graph/aux/usage/photo settings changed across save/reload')
    content = _project_delta(bundle, after=True)
    evidence['after-content'] = persist(directory, 'after-content', content)
    return {'schema': SCHEMA, 'owner': OWNER, 'binding': bundle['binding'], 'materialReport': material_report,
        'savedMapUnloadedReloaded': True, 'wholeActorCounterfactualValidated': True,
        'beforeActorWitnessSha256': digest(before), 'expectedActorWitnessSha256': digest(expected),
        'savedActorWitnessSha256': digest(saved), 'beforeActorWitness': evidence['before-actors'],
        'expectedActorWitness': evidence['expected-actors'], 'savedActorWitness': evidence['saved-actors'],
        'rawInstanceControlsBefore': evidence['raw-before'], 'rawInstanceControlsSaved': evidence['raw-saved'],
        'originalAssetWitnessBefore': evidence['assets-before'], 'originalAssetWitnessSaved': evidence['assets-saved'],
        'newMaterialReport': evidence['new-material'], 'savedNewMaterialReadback': evidence['new-material-saved'],
        'afterContentInventory': evidence['after-content'],
        'rawMatrixOrderMainseedCustomBeforeSavedExact': True, 'oldMaterialAndTextureSettersCalled': False,
        'oldGeometryOrMeshDefaultSlotsChanged': False, 'materialPackagesIndependentlyUnloaded': False,
        'additionalSeedRangesPreservationClaimed': False, 'nativeAppearanceAccepted': False,
        'fullPhotorealismAccepted': False, 'performanceAccepted': False, 'shippingVerified': False, 'activeOutputPromoted': False}


if __name__ == '__main__':
    raise RuntimeError('UNBOUND R44 has no native launch/producer entry')
