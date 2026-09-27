"""CPU animation, scope and graph readback tests; no Unreal process or edits."""
import copy
import importlib.util
import math
from pathlib import Path
import types
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('realism_stove_materials', Path(__file__).with_name('realism-stove-materials.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class Node:
    def __init__(self):
        self.props = {'ignore_pause': False, 'override_period': False, 'period': 0., 'coordinate_index': 0,
                      'u_tiling': 1., 'v_tiling': 1., 'un_mirror_u': False, 'un_mirror_v': False,
                      'mip_value_mode': 'DEFAULT'}
        self.inputs = {}

    def set_editor_property(self, key, value):
        self.props[key] = value

    def get_editor_property(self, key):
        return self.props[key]

    def get_class(self):
        return types.SimpleNamespace(get_name=lambda: self.__class__.__name__)


class Material(Node):
    def __init__(self, path):
        super().__init__()
        self.path, self.nodes, self.roots, self.metadata = path, [], {}, {}
        self.props.update(blend_mode='OPAQUE', shading_model='DEFAULT_LIT', two_sided=False,
                          tangent_space_normal=True, use_material_attributes=False)

    def get_path_name(self):
        return self.path


class Library:
    def create_material_expression(self, material, cls, *args):
        n = cls()
        n.material = material
        material.nodes.append(n)
        return n

    def connect_material_expressions(self, source, channel, target, pin):
        target.inputs[pin] = (source, channel)
        return True

    def connect_material_property(self, node, channel, prop):
        node.material.roots[prop] = (node, channel)
        return True

    def get_material_expressions(self, material):
        return material.nodes

    def get_inputs_for_material_expression(self, material, node):
        return [v[0] for v in node.inputs.values()]

    def get_material_expression_input_names(self, node):
        return list(node.inputs)

    def get_input_node_output_name_for_material_expression(self, node, source):
        return next(v[1] for v in node.inputs.values() if v[0] is source)

    def get_material_property_input_node(self, material, prop):
        return material.roots.get(prop, (None, ''))[0]

    def get_material_property_input_node_output_name(self, material, prop):
        return material.roots[prop][1]

    def has_material_usage(self, material, usage):
        return False

    def recompile_material(self, material):
        return []


class Assets:
    def __init__(self):
        self.values, self.saved = {}, []

    def does_asset_exist(self, path):
        return path in self.values

    def create_asset(self, name, prefix, *args):
        path = prefix+'/'+name
        m = Material(path)
        self.values[path] = m
        return m

    def load_asset(self, path):
        return self.values.get(path)

    def get_metadata_tag(self, obj, key):
        return obj.metadata.get(key, '')

    def set_metadata_tag(self, obj, key, value):
        obj.metadata[key] = value

    def save_loaded_asset(self, obj, **kwargs):
        self.saved.append(obj)
        return True


def fake_unreal():
    u = types.SimpleNamespace(MaterialEditingLibrary=Library(), EditorAssetLibrary=Assets(), StaticMeshComponent=object)
    for name in ('Constant', 'Constant3Vector', 'Custom', 'TextureSample', 'Time', 'TextureCoordinate', 'WorldPosition'):
        setattr(u, 'MaterialExpression'+name, type('MaterialExpression'+name, (Node,), {}))
    u.CustomInput = Node
    u.Material, u.MaterialFactoryNew = Material, object
    u.AssetToolsHelpers = types.SimpleNamespace(get_asset_tools=lambda: u.EditorAssetLibrary)
    u.LinearColor = lambda r, g, b, a: types.SimpleNamespace(r=r, g=g, b=b, a=a)
    u.BlendMode = types.SimpleNamespace(BLEND_ADDITIVE='ADDITIVE', BLEND_OPAQUE='OPAQUE')
    u.MaterialShadingModel = types.SimpleNamespace(MSM_UNLIT='UNLIT', MSM_DEFAULT_LIT='DEFAULT_LIT')
    u.MaterialSamplerType = types.SimpleNamespace(SAMPLERTYPE_COLOR='COLOR')
    u.TextureMipValueMode = types.SimpleNamespace(TMVM_DERIVATIVE='DERIVATIVE')
    u.CustomMaterialOutputType = types.SimpleNamespace(**{'CMOT_FLOAT'+str(i): 'FLOAT'+str(i) for i in range(1, 5)})
    u.MaterialProperty = types.SimpleNamespace(**{'MP_'+name: name for name in
        ('BASE_COLOR', 'NORMAL', 'ROUGHNESS', 'METALLIC', 'SPECULAR', 'AMBIENT_OCCLUSION', 'WORLD_POSITION_OFFSET', 'OPACITY', 'EMISSIVE_COLOR')})
    u.MaterialUsage = types.SimpleNamespace(MATUSAGE_NANITE='NANITE')
    return u


def source_actors(u):
    values = []
    for id_ in M.SOURCE_IDS:
        material = Material('/Game/Original/'+('glass' if id_ == 'DOM_00557' else 'shell'))
        u.EditorAssetLibrary.values[material.path] = material
        mesh = types.SimpleNamespace(metadata={'source_object_id': id_})
        component = types.SimpleNamespace(get_editor_property=lambda key, mesh=mesh: mesh,
                                          get_num_materials=lambda: 1, get_material=lambda slot, mat=material: mat,
                                          get_path_name=lambda id_=id_: '/Level/'+id_+'.Mesh')
        actor = types.SimpleNamespace(get_components_by_class=lambda cls, c=component: [c],
                                      get_path_name=lambda id_=id_: '/Level/'+id_)
        values.append(actor)
    return values


class StoveMaterialTests(unittest.TestCase):
    def test_two_phases_remain_partition_of_unity_within_atlas(self):
        for card in range(3):
            for step in range(401):
                rows = M.frame_state((step-100)/37, card)
                self.assertAlmostEqual(sum(r['weight'] for r in rows), 1., places=12)
                for row in rows:
                    self.assertTrue(0 <= row['low'] <= row['high'] <= 35)
                    self.assertTrue(0 <= row['fraction'] < 1)
        for bad in (math.inf, math.nan):
            with self.assertRaises(RuntimeError):
                M.frame_state(bad)
        with self.assertRaises(RuntimeError):
            M.frame_state(0, 3)

    def test_loop_and_adjacent_frame_changes_are_continuous(self):
        # A different signal for every atlas tile exposes frame jumps; black
        # texture or constant test input would conceal a broken loop blend.
        def sample(u, v):
            frame = math.floor(v*6)*6+math.floor(u*6)
            return .12+.8*((frame*13) % 37)/37
        for card in range(3):
            for frame in range(36):
                for offset in (0, .5):
                    t = (frame/35-card*M.RECIPE['cardPhaseStep']-offset)/M.RECIPE['cycleHz']
                    a = M.evaluate_flame(t-1e-8, card, .43, .4, sample)
                    b = M.evaluate_flame(t+1e-8, card, .43, .4, sample)
                    self.assertLess(max(abs(x-y) for x, y in zip(a, b)), 1e-5)
        for card in range(3):
            a = M.evaluate_flame(.713, card, .43, .4, sample)
            b = M.evaluate_flame(.713+1/M.RECIPE['cycleHz'], card, .43, .4, sample)
            self.assertLess(max(abs(x-y) for x, y in zip(a, b)), 1e-12)

    def test_atlas_coordinates_keep_each_frame_and_invert_native_vertical(self):
        for frame in range(36):
            col, row = frame % 6, frame//6
            for u in (0, .5, 1):
                bottom, top = M.atlas_uv(frame, u, 0), M.atlas_uv(frame, u, 1)
                for uv in (bottom, top):
                    self.assertTrue(col/6 < uv[0] < (col+1)/6)
                    self.assertTrue(row/6 < uv[1] < (row+1)/6)
                self.assertGreater(bottom[1], top[1])
        self.assertAlmostEqual(M.atlas_uv(0, 0, 1)[0], .001)

    def test_black_atlas_edges_and_buried_roots_emit_no_rectangles(self):
        self.assertEqual(M.flame_rgb(0), (0, 0, 0))
        for u in (0, .25, .5, .75, 1):
            for v in (0, .08, 1):
                self.assertEqual(M.evaluate_flame(.3, 0, u, v, lambda *_: 1), (0, 0, 0))
        for v in (.2, .4, .8):
            self.assertEqual(M.envelope(0, v), 0)
            self.assertEqual(M.envelope(1, v), 0)
        self.assertGreater(sum(M.evaluate_flame(.3, 0, .5, .35, lambda *_: 1)), .1)
        self.assertEqual(M.evaluate_flame(.3, 1, .5, .35, lambda *_: 0), (0, 0, 0))

    def test_flame_graph_is_additive_readonly_texture_samples_and_ordinary_time(self):
        u = fake_unreal()
        textures = {name: Material(M.TEXTURE_PREFIX+'/'+name) for name in M.TEXTURES}
        material = M.Writer(u, textures).create('flames')
        graph = M.graph_snapshot(u, material)
        self.assertEqual(graph['flags']['blend_mode'], 'ADDITIVE')
        self.assertEqual(graph['flags']['shading_model'], 'UNLIT')
        self.assertTrue(graph['flags']['two_sided'])
        self.assertIsNone(graph['roots']['WORLD_POSITION_OFFSET'])
        self.assertEqual(set(material.roots), {'EMISSIVE_COLOR', 'OPACITY'})
        samples = [n for n in material.nodes if n.get_class().get_name() == 'MaterialExpressionTextureSample']
        self.assertEqual(len(samples), 4)
        for n in samples:
            self.assertIs(n.props['texture'], textures['T_Fire_SubUV'])
            self.assertEqual(n.props['mip_value_mode'], 'DERIVATIVE')
            self.assertEqual(set(n.inputs), {'UVs', 'DDX(UVs)', 'DDY(UVs)'})
        clock = next(n for n in material.nodes if n.props['desc'] == M.TAG+'flame-clock')
        self.assertFalse(clock.props['ignore_pause'])
        self.assertFalse(clock.props['override_period'])
        self.assertEqual(u.EditorAssetLibrary.saved, [material])
        with self.assertRaisesRegex(RuntimeError, 'Refusing to replace'):
            M.Writer(u, textures).create('flames')

    def test_exact_19_stove_sources_protect_glass_and_shell_without_bindings(self):
        u = fake_unreal()
        actors = source_actors(u)
        original = M.native_sources(u, actors)
        self.assertEqual(set(original), set(M.SOURCE_IDS))
        self.assertTrue(original['DOM_00557']['material'].endswith('glass'))
        self.assertEqual(M.native_sources(u, actors), original)
        with self.assertRaisesRegex(RuntimeError, 'incomplete'):
            M.native_sources(u, actors[1:])
        with self.assertRaisesRegex(RuntimeError, 'Ambiguous'):
            M.native_sources(u, actors+[actors[0]])

    def test_save_reload_witness_rejects_clock_uv_and_source_material_changes(self):
        u = fake_unreal()
        actors = source_actors(u)
        sources = M.native_sources(u, actors)
        textures = {name: Material(M.TEXTURE_PREFIX+'/'+name) for name in M.TEXTURES}
        writer = M.Writer(u, textures)
        material = writer.create('flames')
        original = {r['material']: M.graph_snapshot(u, u.EditorAssetLibrary.load_asset(r['material'])) for r in sources.values()}
        report = {'sourceBindings': sources, 'materials': {'shell': sources['DOM_00553']['material'], 'flames': material.path},
                  'graphs': {material.path: M.graph_snapshot(u, material)}, 'originalGraphs': original, 'textures': {}}
        self.assertTrue(M.verify(u, actors, report)['savedReloaded'])
        for role, key, changed in (('flame-clock', 'override_period', True), ('flame-card-uv', 'v_tiling', -1.)):
            node = next(n for n in material.nodes if n.props['desc'] == M.TAG+role)
            before = node.props[key]
            node.props[key] = changed
            with self.assertRaisesRegex(RuntimeError, 'graph changed'):
                M.verify(u, actors, report)
            node.props[key] = before
        glass = u.EditorAssetLibrary.load_asset(sources['DOM_00557']['material'])
        glass.props['two_sided'] = True
        with self.assertRaisesRegex(RuntimeError, 'original stove graph'):
            M.verify(u, actors, report)

    def test_surface_scope_retains_dark_nonmetallic_nonemissive_logs(self):
        u = fake_unreal()
        textures = {name: Material(M.TEXTURE_PREFIX+'/'+name) for name in M.TEXTURES}
        writer = M.Writer(u, textures)
        for role in ('chamber', 'logs', 'embers'):
            material = writer.create(role)
            self.assertEqual(material.props['blend_mode'], 'OPAQUE')
            self.assertEqual(material.props['shading_model'], 'DEFAULT_LIT')
            self.assertIsNone(material.roots.get('WORLD_POSITION_OFFSET'))
            self.assertGreaterEqual(M.SURFACES[role]['roughness'], .95)
            self.assertEqual(M.SURFACES[role]['metallic'], 0)
            if role != 'embers':
                c = material.roots['EMISSIVE_COLOR'][0].props['constant']
                self.assertEqual((c.r, c.g, c.b), (0, 0, 0))
            else:
                node = material.roots['EMISSIVE_COLOR'][0]
                self.assertIn('mask*0.45', node.props['code'])
        self.assertEqual(len(u.EditorAssetLibrary.saved), 3)

    def test_shader_generation_uses_frozen_animation_and_tint_recipe(self):
        # Altering a preview constant must regenerate native code, avoiding two
        # independently maintained animation algorithms drifting silently.
        code = M.density_hlsl()
        with patch.dict(M.RECIPE, {'rootFadeStart': .11, 'tipPower': .73}):
            self.assertNotEqual(code, M.density_hlsl())
            self.assertIn('smoothstep(0.11,0.2', M.density_hlsl())
            self.assertIn('0.73', M.density_hlsl())
        with patch.dict(M.RECIPE, {'emissionStrength': 2.4}):
            self.assertIn('Density*2.4', M.emission_hlsl())


if __name__ == '__main__':
    unittest.main()
