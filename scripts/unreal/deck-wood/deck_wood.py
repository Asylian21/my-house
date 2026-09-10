"""Photographed terrace wood on derived UV1; canonical geometry and UV0 stay intact.

Import is CPU-only. Native authoring is called explicitly by import_scene.py.
The source scan is a finish proposal, not a measurement of the installed product.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'lib/twin-site.ts').is_file())
HERE = Path(__file__).resolve().parent
OWNER = 'scripts/unreal/deck-wood/deck_wood.py'
PREFIX = '/Game/Brezi/Materials/DeckPhotoWood'
SCENE_SHA = '61ba228f4b72a5ee5fc754e60e112ff70d03605f8cf56fec97bccc3519b8863b'
OBJ_SHA = 'a42e9eb169d929bc67056ad21bf3885e3f1a32838f15c328cb98bacd008fa455'
SLOTS = {'DOM_01708': 'MAT_0095', 'DOM_01710': 'MAT_0096', 'DOM_01713': 'MAT_0097',
         'DOM_01719': 'MAT_0098', 'DOM_01779': 'MAT_0104'}
MAPS = {
    'Diffuse': ('diff', 'fe10e7c311899ce8024b5f5f782b67fc41560143c4341e314536cd2833d877cd', 9032189),
    'nor_gl': ('nor_gl', '6ce429e9bee8f1aabadf141dc34f9a89d1af9f688d2ea07431760e6a4e54ae73', 12680748),
    'Rough': ('rough', 'aa39b2acc6ebb7f216ee3b802e131528e630d3a7eb9736b462f40f88da236804', 4169187),
}
CODES = {
    # The discarded end joint occupies 2% at each end of the scan. UV1 U has
    # a 1440 mm period, so this crop retains the 1500 mm photographic scale.
    'sampleUV': 'return float2(0.02 + 0.96 * frac(UV.x), UV.y);',
    'gradientX': 'return ddx(UV) * float2(0.96, 1.0);',
    'gradientY': 'return ddy(UV) * float2(0.96, 1.0);',
    'normal': 'return normalize(float3(MapNormal.xy * 0.35, max(MapNormal.z, 0.001)));',
}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def verify_inputs(scene, geometry_dir):
    geometry_dir = Path(geometry_dir)
    require(sha(geometry_dir / 'scene.json') == SCENE_SHA and sha(geometry_dir / 'dom-mm.obj') == OBJ_SHA,
            'Deck source geometry changed; regenerate and review its UV recipe')
    loaded = json.loads((geometry_dir / 'scene.json').read_text())
    require(digest(scene) == digest(loaded), 'Deck supplied scene differs from canonical file')
    records = {o['id']: o for o in scene['objects']}
    require(len(records) == len(scene['objects']), 'Duplicate canonical source IDs')
    for id_, slot in SLOTS.items():
        require(records[id_]['enabled'] and records[id_]['materialSlots'] == [slot], 'Deck object/material scope changed: ' + id_)
    maps = {}
    for role, (name, expected, size) in MAPS.items():
        path = ROOT / ('output/unreal/deck-material-study/wood_planks/' + name + '-4k.jpg')
        require(path.is_file() and path.stat().st_size == size and sha(path) == expected,
                'Deck photo map absent or changed: run python3 scripts/unreal/deck-wood/restore_inputs.py')
        maps[role] = {'path': str(path.relative_to(ROOT)), 'sha256': expected}
    paths = [HERE / 'deck_wood.py', HERE / 'source_geometry.py', HERE / 'restore_inputs.py',
             ROOT / 'scripts/unreal/tv-oak/tv_oak.py',
             ROOT / 'unreal/BreziTwin/Source/BreziTwin/BreziDeckUVLibrary.h',
             ROOT / 'unreal/BreziTwin/Source/BreziTwin/BreziDeckUVLibrary.cpp']
    pipeline = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    pipeline.update({v['path']: v['sha256'] for v in maps.values()})
    recipe = {'revision': 'deck-photo-uv1-1', 'sceneSha256': SCENE_SHA, 'objSha256': OBJ_SHA,
              'pipelineFiles': pipeline, 'mapSizeMm': 1500, 'retainedUPeriodMm': 1440,
              'stripStarts': [.021, .263, .5895], 'normalStrength': .35,
              'finishMeasuredAtSite': False, 'roughness': 'photographed map, unmodified'}
    return {'recipe': recipe, 'recipeSha256': digest(recipe), 'pipelineFiles': pipeline,
            'candidate': {'maps': maps}, 'records': {i: records[i] for i in SLOTS}}


def graph_links():
    return ([('uv1', '', role, 'UV') for role in ('sampleUV', 'gradientX', 'gradientY')]
            + [(source, '', role, pin) for role in ('albedo', 'normalMap', 'roughMap')
               for source, pin in (('sampleUV', 'UVs'), ('gradientX', 'DDX(UVs)'), ('gradientY', 'DDY(UVs)'))]
            + [('normalMap', 'RGB', 'normal', 'MapNormal')])


def material_proof(u, material, contract, slot, base):
    lib, assets = u.MaterialEditingLibrary, u.EditorAssetLibrary
    require(isinstance(material, u.Material) and assets.get_metadata_tag(material, 'BreziGeneratedBy') == OWNER,
            'Deck material ownership/type differs')
    require(assets.get_metadata_tag(material, 'BreziDeckRecipe') == contract['recipeSha256']
            and assets.get_metadata_tag(material, 'source_material_slot') == slot, 'Deck material recipe/slot differs')
    require(lib.has_material_usage(material, u.MaterialUsage.MATUSAGE_NANITE), 'Deck material lacks Nanite usage')
    for key, value in {'blend_mode': u.BlendMode.BLEND_OPAQUE, 'shading_model': u.MaterialShadingModel.MSM_DEFAULT_LIT,
                       'two_sided': False, 'tangent_space_normal': True, 'use_material_attributes': False}.items():
        require(material.get_editor_property(key) == value, 'Deck material policy differs: ' + key)
    expressions = list(lib.get_material_expressions(material))
    nodes = {str(assets.get_metadata_tag(n, 'BreziOakNodeRole')): n for n in expressions}
    require(len(nodes) == len(expressions) == 10 and set(nodes) == {'uv1', *CODES, 'albedo', 'normalMap', 'roughMap', 'metallic', 'specular'},
            'Deck material graph roles differ')
    require(isinstance(nodes['uv1'], u.MaterialExpressionTextureCoordinate)
            and nodes['uv1'].get_editor_property('coordinate_index') == 1
            and nodes['uv1'].get_editor_property('u_tiling') == 1
            and nodes['uv1'].get_editor_property('v_tiling') == 1, 'Deck lost physical UV1 mapping')
    for role, code in CODES.items():
        require(isinstance(nodes[role], u.MaterialExpressionCustom) and nodes[role].get_editor_property('code') == code,
                'Deck shader code differs: ' + role)
    for source, output, target, pin in graph_links():
        names = [str(v) for v in lib.get_material_expression_input_names(nodes[target])]
        sources = list(lib.get_inputs_for_material_expression(material, nodes[target]))
        require(pin in names and len(names) == len(sources) and sources[names.index(pin)] == nodes[source], 'Deck graph connection differs')
        actual = lib.get_input_node_output_name_for_material_expression(nodes[target], nodes[source])
        if isinstance(actual, tuple) and len(actual) == 2 and actual[0] is True:
            actual = actual[1]
        expected = output or list(lib.get_material_expression_output_names(nodes[source]))[0]
        require(actual == expected, 'Deck graph output channel differs')
    for prop, role in {'BASE_COLOR': 'albedo', 'ROUGHNESS': 'roughMap', 'NORMAL': 'normal',
                       'METALLIC': 'metallic', 'SPECULAR': 'specular'}.items():
        property_id = getattr(u.MaterialProperty, 'MP_' + prop)
        require(lib.get_material_property_input_node(material, property_id) == nodes[role],
                'Deck material output differs: ' + prop)
        expected = {'BASE_COLOR': 'RGB', 'ROUGHNESS': 'R'}.get(prop)
        if expected is None:
            expected = list(lib.get_material_expression_output_names(nodes[role]))[0]
        actual = lib.get_material_property_input_node_output_name(material, property_id)
        if isinstance(actual, tuple) and len(actual) == 2 and actual[0] is True:
            actual = actual[1]
        require(actual == expected, 'Deck material output channel differs: ' + prop)
    for prop in ('WORLD_POSITION_OFFSET', 'OPACITY', 'OPACITY_MASK', 'EMISSIVE_COLOR'):
        require(lib.get_material_property_input_node(material, getattr(u.MaterialProperty, 'MP_' + prop)) is None,
                'Deck unexpected geometry/optical output')
    for role, expected in (('metallic', 0), ('specular', .5)):
        require(float(nodes[role].get_editor_property('r')) == expected, 'Deck scalar differs')
    textures = {}
    for role, source_role, sampler in (('albedo', 'Diffuse', u.MaterialSamplerType.SAMPLERTYPE_COLOR),
                                      ('normalMap', 'nor_gl', u.MaterialSamplerType.SAMPLERTYPE_NORMAL),
                                      ('roughMap', 'Rough', u.MaterialSamplerType.SAMPLERTYPE_MASKS)):
        node = nodes[role]
        require(isinstance(node, u.MaterialExpressionTextureSample) and node.get_editor_property('sampler_type') == sampler
                and node.get_editor_property('mip_value_mode') == u.TextureMipValueMode.TMVM_DERIVATIVE,
                'Deck texture sampling/derivative policy differs')
        textures[role] = base.texture_proof(u, node.get_editor_property('texture'), role, MAPS[source_role][1], OWNER)
    return {'asset': material.get_path_name(), 'uvChannel': 1, 'nodes': len(nodes), 'textures': textures,
            'explicitUnwrappedGradients': True, 'sourceTangentBasisRetained': True, 'renderedVerified': False}


def create_material(u, contract, slot, base):
    profile = {'owner': OWNER, 'materialName': 'M_Deck_' + slot, 'palette': (1, 1, 1), 'basisCode': 'UV1'}
    prefix = PREFIX + '/R_' + contract['recipeSha256'][:16]
    writer = base.Writer(u, prefix, contract, profile)
    name, path = profile['materialName'], prefix + '/Materials/' + profile['materialName']
    material = writer.existing(path)
    if material:
        material_proof(u, material, contract, slot, base)
        writer.paths.add(material.get_path_name())
        for n in writer.lib.get_material_expressions(material):
            if isinstance(n, u.MaterialExpressionTextureSample):
                writer.paths.add(n.get_editor_property('texture').get_path_name())
        return material, writer.paths
    material = u.AssetToolsHelpers.get_asset_tools().create_asset(name, prefix + '/Materials', u.Material, u.MaterialFactoryNew())
    require(material is not None, 'Deck material creation failed')
    for key, value in {'BreziGeneratedBy': OWNER, 'source_material_slot': slot, 'BreziDeckRecipe': contract['recipeSha256']}.items():
        writer.assets.set_metadata_tag(material, key, value)
    material.set_editor_property('tangent_space_normal', True)
    writer.lib.set_base_material_usage(material, u.MaterialUsage.MATUSAGE_NANITE, True)
    writer.node(material, 'uv1', u.MaterialExpressionTextureCoordinate, coordinate_index=1, u_tiling=1, v_tiling=1)
    for role, code in CODES.items():
        writer.custom(material, role, code, ['MapNormal' if role == 'normal' else 'UV'],
                      u.CustomMaterialOutputType.CMOT_FLOAT3 if role == 'normal' else u.CustomMaterialOutputType.CMOT_FLOAT2)
    for role, source_role, sampler in (('albedo', 'Diffuse', u.MaterialSamplerType.SAMPLERTYPE_COLOR),
                                      ('normalMap', 'nor_gl', u.MaterialSamplerType.SAMPLERTYPE_NORMAL),
                                      ('roughMap', 'Rough', u.MaterialSamplerType.SAMPLERTYPE_MASKS)):
        writer.node(material, role, u.MaterialExpressionTextureSample, texture=writer.texture(role, source_role),
                    sampler_type=sampler, mip_value_mode=u.TextureMipValueMode.TMVM_DERIVATIVE)
    for role, value in (('metallic', 0), ('specular', .5)):
        writer.node(material, role, u.MaterialExpressionConstant, r=value)
    for origin, output, dest, pin in graph_links():
        require(writer.lib.connect_material_expressions(writer.nodes[origin], output, writer.nodes[dest], pin), 'Deck connection failed')
    for prop, role, channel in (('BASE_COLOR', 'albedo', 'RGB'), ('ROUGHNESS', 'roughMap', 'R'), ('NORMAL', 'normal', ''),
                                ('METALLIC', 'metallic', ''), ('SPECULAR', 'specular', '')):
        require(writer.lib.connect_material_property(writer.nodes[role], channel, getattr(u.MaterialProperty, 'MP_' + prop)), 'Deck output failed')
    errors = list(writer.lib.recompile_material(material))
    require(not errors, 'Deck material compile failed: ' + str(errors))
    writer.save(material)
    material_proof(u, material, contract, slot, base)
    return material, writer.paths


def apply_deck_wood(scene, assets_by_id, geometry_dir):
    import unreal as u
    from materials import _asset_hashes
    contract = verify_inputs(scene, geometry_dir)
    geometry = module('brezi_deck_source_geometry', HERE / 'source_geometry.py')
    source = geometry.read_source(Path(geometry_dir) / 'dom-mm.obj')
    base = module('brezi_deck_photo_base', ROOT / 'scripts/unreal/tv-oak/tv_oak.py')
    require(hasattr(u, 'BreziDeckUVLibrary'), 'Rebuild the editor target with the deck UV bridge before import')
    plans, bindings, generated, proofs = {}, {}, set(), {}
    # Read every source mesh first. No native geometry has changed at this point.
    for id_, slot in SLOTS.items():
        mesh = assets_by_id[id_]
        require(isinstance(mesh, u.StaticMesh) and mesh.get_num_sections(0) == 1, 'Expected single-slot deck static mesh')
        plans[id_] = geometry.read_and_plan(u, mesh, id_, source)
        bindings[id_] = mesh.get_material(0)
    materials = {}
    for slot in SLOTS.values():
        materials[slot], paths = create_material(u, contract, slot, base)
        generated.update(paths)
    for id_, slot in SLOTS.items():
        mesh, plan = assets_by_id[id_], plans[id_]
        # The native descriptor guard includes current material identity.
        mesh.set_material(0, materials[slot])
        inspected = json.loads(u.BreziDeckUVLibrary.inspect_deck_mesh(mesh))
        require(inspected.get('status') == 'deck-mesh-inspected', 'Deck native inspection failed: ' + str(inspected))
        result = json.loads(u.BreziDeckUVLibrary.apply_deck_uv1(mesh, plan['ids'],
            [u.Vector2D(x=p[0], y=p[1]) for p in plan['uv1']], inspected['baselineSignature'], contract['recipeSha256']))
        require(result.get('status') in ('deck-uv1-applied', 'deck-uv1-already-current') and result.get('assetSaveAllowed') is True,
                'Deck UV-only commit rejected: ' + str(result))
        require(u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False), 'Deck mesh save failed')
        proofs[id_] = {'geometry': plan['proof'], 'uvCommit': result,
                       'material': material_proof(u, materials[slot], contract, slot, base)}
    return {'status': 'deck-wood-authored-validated', 'recipeSha256': contract['recipeSha256'],
            'pipelineFiles': contract['pipelineFiles'], 'assetHashes': _asset_hashes(generated),
            'assignedMeshHashes': _asset_hashes([assets_by_id[i].get_path_name() for i in SLOTS]),
            'objects': proofs, 'savedReloadVerified': False, 'renderedVerified': False,
            'source': 'https://polyhaven.com/a/wood_planks', 'license': 'CC0-1.0',
            'limitations': ['Photographed finish proposal, not measured installed wood.',
                            'Cropped longitudinal repeats and coarse mip gutters require native visual review.',
                            'Hatch remains the source single box; no construction joints are invented.']}
