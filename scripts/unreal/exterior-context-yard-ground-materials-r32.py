"""Two isolated copies of existing PBR graphs; no texture import or source edits.

R5 geometry carries UV1.R temporal coverage and UV1.G earth fraction. Only the
three existing Earth/Cover Amount links are rerouted in the substrate copy.
The historical native texture witness is a material-policy input, not a future
R30 base selection or native/appearance acceptance for this pending trial.
"""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-ground-materials-r32.py'
PREFIX = '/Game/Brezi/ContextYardGround20261002R32'
TAG = 'BreziYardGroundR32:'
SCHEMA = 'brezi-context-yard-two-existing-pbr-material-copies-r32'
DITHER = '/Engine/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA.DitherTemporalAA'
PLAN = ROOT/'output/unreal/exterior-context-yard-ground-20261002-r32-study-r5/yard-ground-study-plan.json'
PLAN_SHA = '8378d06f00e9a11dceff51e4eb12a270eff492d6f729f09d3dfd804de326f650'
PROPOSALS_SHA = 'd35663e89439a3686dc86844f109eee357e166ccbe7bd306643ea38331bbf08f'
ORIGINAL = ROOT/'output/unreal/exterior-20261001-r16a/exterior-import-report.json'
ORIGINAL_SHA = '1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122'
TEXTURE_WITNESS = ROOT/'output/unreal/exterior-20261002-r29a/tree-group-checkpoint/materials-before.json'
TEXTURE_WITNESS_SHA = 'd02893c16607bbfd3f9f84c86fe5e34c9b3524192c595099091a959da38eff38'
ROLES = {'yard_gravel_r32': 'context_track', 'yard_substrate_r32': 'context_garden_soil'}
MIX_ROLES = ['BreziExterior:groundcover-'+role for role in ('albedo', 'normal', 'roughness')]
COVER_CODE = 'return 1.0-SoilFraction;'
TEXTURE_FIELDS = ('srgb', 'flip_green_channel', 'compression_settings', 'address_x', 'address_y',
    'lod_bias', 'max_texture_size', 'virtual_texture_streaming', 'mip_gen_settings', 'power_of_two_mode',
    'do_scale_mips_for_alpha_coverage', 'never_stream')
META = ('BreziGeneratedBy', 'source_sha256', 'BreziSourceLicense', 'BreziSourcePage', 'BreziSourceEncodingOverride')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(row):
    return hashlib.sha256(json.dumps(row, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def check_file(path, expected):
    p = Path(path).resolve()
    require(p.is_file() and p.is_relative_to(ROOT) and sha(p) == expected, 'Frozen material input differs: '+str(p))
    return p


def pin(path):
    p = Path(path).resolve()
    return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}


def load_contract():
    plan = read(check_file(PLAN, PLAN_SHA))
    require(plan['schema'] == 'brezi-context-yard-resolved-edge-and-clipped-low-growth-source-r32-r5'
        and plan['status'] == 'source-only-layout-and-geometry-review-native-pending'
        and plan['selectedNativeBase'] is None and plan['selectedNativeBasePending'] is True,
        'Exact source-only R5 plan required; future native base remains unselected here')
    row = plan['materialCopyProposals']
    proposals = read(check_file(row['path'], PROPOSALS_SHA))
    require(row['sha256'] == PROPOSALS_SHA, 'Typed material proposal pin differs')
    original = read(check_file(ORIGINAL, ORIGINAL_SHA))['materials']['materials']
    witness = read(check_file(TEXTURE_WITNESS, TEXTURE_WITNESS_SHA))['clean']['original']['textures']
    require([r['id'] for r in proposals] == list(ROLES), 'Only the two reviewed PBR copies allowed')
    graphs = {}
    for row in proposals:
        old = original[ROLES[row['id']]]
        require(row['duplicateSource'] == old['asset'] and row['sourceGraphSha256'] == old['graphSha256']
            and row['baseRecipe'] == old['recipe'] and digest(old['graph']) == row['sourceGraphSha256']
            and row['newTextureObjects'] == 0, 'Exact existing graph/recipe required')
        graphs[row['id']] = old['graph']
    textures = {r['asset']: r for r in witness.values()}
    assets = {n['values']['texture'] for g in graphs.values() for n in g['nodes']
        if n['class'] == 'MaterialExpressionTextureSample'}
    require(assets <= set(textures), 'Historical shared-texture observations incomplete')
    return proposals, graphs, {k: textures[k] for k in sorted(assets)}


def validate_proposals(proposals):
    expected, graphs, textures = load_contract()
    require(proposals == expected, 'Material proposals must equal the frozen reviewed recipes')
    return graphs, textures


def new_asset(identity):
    require(identity in ROLES, 'Unknown material identity')
    name = 'M_'+identity
    return PREFIX+'/Materials/'+name+'.'+name


def validate_graph(identity, original, variant):
    require(identity in ROLES and set(variant) == set(original) == {'nodes', 'roots', 'flags'}, 'Closed graph schema required')
    node_tag = TAG+identity+':'
    require(len({n['role'] for n in variant['nodes']}) == len(variant['nodes']), 'Unique node roles required')
    extras = {n['role'][len(node_tag):]: n for n in variant['nodes'] if n['role'].startswith(node_tag)}
    wanted = {'uv1', 'coverage-r', 'temporal-dither'}
    if identity == 'yard_substrate_r32':
        wanted |= {'soil-g', 'cover-amount'}
    require(set(extras) == wanted and len(variant['nodes']) == len(original['nodes'])+len(wanted), 'Exact3/5 new nodes only')
    expected_old = copy.deepcopy(original['nodes'])
    if identity == 'yard_substrate_r32':
        by = {n['role']: n for n in expected_old}
        require(set(MIX_ROLES) <= set(by), 'All three original ground layer mixes required')
        for role in MIX_ROLES:
            node = by[role]
            require(node['class'] == 'MaterialExpressionCustom'
                and node['values']['code'] == 'return lerp(Earth,Cover,Amount);', 'Original PBR blend equation changed')
            links = [link for link in node['inputs'] if link[0] == 'Amount']
            require(links == [['Amount', 'BreziExterior:irregular-ground-cover', '']], 'Original layer amount link differs')
            links[0][1] = node_tag+'cover-amount'
    require([n for n in variant['nodes'] if not n['role'].startswith(node_tag)] == expected_old,
        'Old nodes/texture references/transfer functions changed outside the exact three Amount links')
    uv = extras['uv1']
    require(uv['class'] == 'MaterialExpressionTextureCoordinate'
        and uv['values'] == {'coordinate_index': 1, 'u_tiling': 1., 'v_tiling': 1.} and uv['inputs'] == [], 'UV1 route/scale differs')
    for role, channel in [('coverage-r', 'r')]+([('soil-g', 'g')] if identity == 'yard_substrate_r32' else []):
        node = extras[role]
        require(node['class'] == 'MaterialExpressionComponentMask'
            and node['values'] == {k: k == channel for k in 'rgba'}
            and node['inputs'] == [['None', node_tag+'uv1', '']], 'Coverage/earth channel route differs')
    dither = extras['temporal-dither'];alpha = [v for v in dither['inputs'] if 'alpha' in v[0].lower()]
    require(dither['class'] == 'MaterialExpressionMaterialFunctionCall' and dither['values'] == {'material_function': DITHER}
        and len(alpha) == 1 and alpha[0][1:] == [node_tag+'coverage-r', '']
        and all(v[1:] == [None, None] for v in dither['inputs'] if v not in alpha), 'Native DitherTemporalAA route differs')
    if identity == 'yard_substrate_r32':
        node = extras['cover-amount']
        require(node['class'] == 'MaterialExpressionCustom'
            and node['values'] == {'code': COVER_CODE, 'output_type': '<CustomMaterialOutputType.CMOT_FLOAT1: 0>'}
            and node['inputs'] == [['SoilFraction', node_tag+'soil-g', '']], 'Earth fraction must coherently map to 1-UV1.G')
    roots = copy.deepcopy(original['roots']);roots['OPACITY_MASK'] = [node_tag+'temporal-dither', 'Result']
    flags = copy.deepcopy(original['flags']);flags.update(blend_mode='<BlendMode.BLEND_MASKED: 1>', opacity_mask_clip_value=.5)
    require(variant['roots'] == roots and variant['flags'] == flags, 'Original PBR roots/flags changed outside owned opacity mask')
    return {'retainedOriginalNodes': len(original['nodes']), 'newNodes': len(wanted),
        'oldPbrRootsExactExceptOpacityMask': True, 'existingTextureReferencesExact': True,
        'changedOriginalAmountLinks': 3 if identity == 'yard_substrate_r32' else 0,
        'coherentAlbedoNormalRoughnessEarthFraction': identity == 'yard_substrate_r32',
        'sourceUvFeatherNativePixelsVerified': False}


def texture_snapshot(u, expected):
    result = {}
    for path in expected:
        tex = u.EditorAssetLibrary.load_asset(path)
        require(isinstance(tex, u.Texture2D) and tex.get_path_name() == path, 'Shared original Texture2D missing')
        values = {}
        for key in TEXTURE_FIELDS:
            value = tex.get_editor_property(key)
            values[key] = value if isinstance(value, (bool, int, float, str)) else str(value)
        coverage = tex.get_editor_property('alpha_coverage_thresholds')
        values['alphaCoverageThresholds'] = [float(getattr(coverage, k)) for k in 'xyzw']
        values['size'] = [tex.blueprint_get_size_x(), tex.blueprint_get_size_y()]
        values['sourceEncoding'] = str(tex.get_editor_property('source_color_settings').get_editor_property('encoding_override'))
        metadata = {k: u.EditorAssetLibrary.get_metadata_tag(tex, k) for k in META}
        result[path] = {'asset': path, 'values': values, 'metadata': metadata}
    validate_shared_textures(result, expected)
    return result


def validate_shared_textures(actual, expected):
    require(actual == expected, 'Original shared texture pixels provenance/settings/encoding/normal/alpha policy changed')


def preflight_enums(u):
    # Only actual proven direct enum names, no substring/fuzzy aliases.
    return {'blendMode': u.BlendMode.BLEND_MASKED, 'opacityRoot': u.MaterialProperty.MP_OPACITY_MASK,
        'scalarOutput': u.CustomMaterialOutputType.CMOT_FLOAT1,
        'classes': [u.MaterialExpressionTextureCoordinate, u.MaterialExpressionComponentMask,
            u.MaterialExpressionMaterialFunctionCall, u.MaterialExpressionCustom], 'customInput': u.CustomInput}


def usage_snapshot(u, h, material):
    enums = {'instancedStaticMeshes': h['existing'].native_enum(u.MaterialUsage, 'INSTANCEDSTATICMESHES'),
        'nanite': u.MaterialUsage.MATUSAGE_NANITE}
    return {k: bool(u.MaterialEditingLibrary.has_material_usage(material, value)) for k,value in enums.items()}


def _source_materials(u, h, proposals, base_materials, graphs):
    require(set(base_materials) == set(ROLES.values()), 'Exact two original Material objects required')
    offsets = {}
    for row in proposals:
        old = base_materials[ROLES[row['id']]]
        require(isinstance(old, u.Material) and old.get_path_name() == row['duplicateSource']
            and h['existing'].graph_snapshot(u, old) == graphs[row['id']], 'Actual source material differs')
        offsets[row['id']] = h['r21'].world_position_offsets(u, old)
    return offsets


def prepare(u, h, material_proposals, base_materials):
    enums = preflight_enums(u)
    graphs, expected_textures = validate_proposals(material_proposals)
    offsets = _source_materials(u, h, material_proposals, base_materials, graphs)
    before = texture_snapshot(u, expected_textures)
    assets, lib = u.EditorAssetLibrary, u.MaterialEditingLibrary
    require(all(not assets.does_asset_exist(new_asset(row['id'])) for row in material_proposals), 'Fresh owned two-material namespace required')
    materials, records = {}, {}
    for row in material_proposals:
        identity = row['id'];tag = TAG+identity+':'
        usage = usage_snapshot(u, h, base_materials[ROLES[identity]])
        m = assets.duplicate_asset(row['duplicateSource'], new_asset(identity).split('.')[0])
        require(m and h['existing'].graph_snapshot(u, m) == graphs[identity]
            and h['r21'].world_position_offsets(u, m) == offsets[identity], 'Initial copy changed original graph/world positions')
        def node(role, cls, **props):
            v = lib.create_material_expression(m, cls, -700, 800);require(v, 'Cannot add owned node')
            v.set_editor_property('desc', tag+role)
            for k, value in props.items():v.set_editor_property(k, value)
            return v
        uv = node('uv1', u.MaterialExpressionTextureCoordinate, coordinate_index=1, u_tiling=1., v_tiling=1.)
        coverage = node('coverage-r', u.MaterialExpressionComponentMask, r=True, g=False, b=False, a=False)
        dither = node('temporal-dither', u.MaterialExpressionMaterialFunctionCall)
        function = assets.load_asset(DITHER)
        require(function and dither.set_material_function(function), 'Installed native dither missing')
        alpha = [str(v) for v in lib.get_material_expression_input_names(dither) if 'alpha' in str(v).lower()]
        require(len(alpha) == 1 and [str(v) for v in lib.get_material_expression_input_names(coverage)] == ['None'], 'Native mask/dither ports differ')
        require(lib.connect_material_expressions(uv, '', coverage, '')
            and lib.connect_material_expressions(coverage, '', dither, alpha[0])
            and lib.connect_material_property(dither, 'Result', enums['opacityRoot']), 'Cannot connect UV1.R native feather')
        if identity == 'yard_substrate_r32':
            soil = node('soil-g', u.MaterialExpressionComponentMask, r=False, g=True, b=False, a=False)
            port = u.CustomInput();port.set_editor_property('input_name', 'SoilFraction')
            amount = node('cover-amount', u.MaterialExpressionCustom, code=COVER_CODE, description=tag+'cover-amount',
                inputs=[port], output_type=enums['scalarOutput'])
            require(lib.connect_material_expressions(uv, '', soil, '')
                and lib.connect_material_expressions(soil, '', amount, 'SoilFraction'), 'Cannot connect UV1.G scalar earth fraction')
            existing = {str(v.get_editor_property('desc')): v for v in lib.get_material_expressions(m)}
            for role in MIX_ROLES:
                require(role in existing and lib.connect_material_expressions(amount, '', existing[role], 'Amount'),
                    'Cannot coherently reroute all three original PBR layer mixes')
        m.set_editor_property('blend_mode', enums['blendMode']);m.set_editor_property('opacity_mask_clip_value', .5)
        errors = list(lib.recompile_material(m));require(not errors, 'New isolated material compile errors')
        graph = h['existing'].graph_snapshot(u, m);delta = validate_graph(identity, graphs[identity], graph)
        require(h['r21'].world_position_offsets(u, m) == offsets[identity], 'Original world-position shader offset mode changed')
        require(usage_snapshot(u, h, m) == usage, 'Copied original material usage changed')
        metadata = {'BreziGeneratedBy': OWNER, 'BreziR32MaterialRole': identity, 'BreziR32SourceRecipeSha256': digest(row)}
        for k, value in metadata.items():assets.set_metadata_tag(m, k, value)
        require(assets.save_loaded_asset(m, only_if_is_dirty=False), 'Cannot save isolated material')
        materials[identity] = m
        records[identity] = {'asset': m.get_path_name(), 'recipe': row, 'graph': graph, 'graphSha256': digest(graph),
            'worldPositionOffsets': offsets[identity], 'graphDelta': delta, 'metadata': metadata, 'compileErrors': errors,
            'usage': usage,
            'sharedTextureAssets': sorted({n['values']['texture'] for n in graphs[identity]['nodes']
                if n['class'] == 'MaterialExpressionTextureSample'}), 'newTextureObjects': 0}
    require(texture_snapshot(u, expected_textures) == before, 'Shared textures changed while copying graphs')
    _source_materials(u, h, material_proposals, base_materials, graphs)
    report = {'schema': SCHEMA, 'owner': OWNER, 'status': 'native-two-material-copies-created-saved-reload-pending',
        'sourceStudy': pin(PLAN), 'materialProposals': pin(PLAN.parent/'material-copy-proposals.json'),
        'historicalOriginalTextureWitness': pin(TEXTURE_WITNESS), 'materials': records,
        'newPackageAssets': sorted(new_asset(k) for k in ROLES), 'newMaterialGraphs': 2, 'newTextureObjects': 0,
        'sharedTextureWitnessBefore': before, 'sharedTexturesUnchanged': True, 'sourceOnlyFeatherCm': {'gravel': 6, 'substrate': 18},
        'sourceOnlySoilFractionRange': [.08, .35], 'sourceOnlyCoverFractionRange': [.65, .92],
        'originalSourceTexturePixelsReimportedOrEdited': False, 'newWorldPositionNodes': 0,
        'actualNativeTextureSourcePixelsDecoded': False, 'actualNativeTextureGpuPixelFormatVerified': False,
        'nativeDitherCoveragePixelsMeasured': False, 'materialPackagesIndependentlyUnloaded': False,
        'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False,
        'shippingVerified': False, 'packageVerified': False}
    verify_saved(u, h, material_proposals, base_materials, report)
    return materials, report


def verify_saved(u, h, material_proposals, base_materials, report):
    graphs, textures = validate_proposals(material_proposals)
    offsets = _source_materials(u, h, material_proposals, base_materials, graphs)
    require(report['schema'] == SCHEMA and report['owner'] == OWNER and report['sourceStudy'] == pin(PLAN)
        and set(report['materials']) == set(ROLES) and report['newPackageAssets'] == sorted(new_asset(k) for k in ROLES)
        and report['newMaterialGraphs'] == 2 and report['newTextureObjects'] == 0, 'Exact owned two-material saved receipt required')
    require(texture_snapshot(u, textures) == report['sharedTextureWitnessBefore'], 'Shared texture native settings/metadata changed')
    result = {}
    for row in material_proposals:
        identity = row['id'];record = report['materials'][identity]
        require(record['asset'] == new_asset(identity) and record['recipe'] == row and record['compileErrors'] == [], 'Saved recipe/asset differs')
        m = u.EditorAssetLibrary.load_asset(record['asset']);require(isinstance(m, u.Material), 'Saved material missing')
        graph = h['existing'].graph_snapshot(u, m)
        require(graph == record['graph'] and digest(graph) == record['graphSha256']
            and validate_graph(identity, graphs[identity], graph) == record['graphDelta'], 'Saved graph counterfactual differs')
        require(h['r21'].world_position_offsets(u, m) == offsets[identity] == record['worldPositionOffsets'], 'Saved original world-position mode differs')
        require(usage_snapshot(u, h, m) == record['usage'] == usage_snapshot(u, h, base_materials[ROLES[identity]]),
            'Saved material usage differs from original')
        wanted = {'BreziGeneratedBy': OWNER, 'BreziR32MaterialRole': identity, 'BreziR32SourceRecipeSha256': digest(row)}
        require(record['metadata'] == wanted and all(u.EditorAssetLibrary.get_metadata_tag(m, k) == v for k,v in wanted.items()), 'Owned material provenance differs')
        result[identity] = m
    for key in ('nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified', 'packageVerified',
        'actualNativeTextureSourcePixelsDecoded', 'actualNativeTextureGpuPixelFormatVerified', 'nativeDitherCoveragePixelsMeasured',
        'materialPackagesIndependentlyUnloaded'):
        require(report[key] is False, 'Material copy cannot grant unavailable acceptance/readback')
    return result
