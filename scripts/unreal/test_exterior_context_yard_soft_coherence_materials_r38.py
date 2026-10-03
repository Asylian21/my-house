"""Owned R38 mocked reflection/graph/policy checks; no Unreal or pixels."""
import copy
import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('r38_final_material_fixture', HERE/'exterior-context-yard-soft-coherence-materials-r38.py')
m = importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class Props:
    def __init__(self, values=None): self.props = dict(values or {});self.writes = []
    def get_editor_property(self, key): return self.props[key]
    def set_editor_property(self, key, value): self.props[key] = value;self.writes.append(key)


class Node(Props):
    def __init__(self, name, row=None):
        super().__init__();self.name = name;self.edges = {};self.roles = []
        if row:
            self.props = copy.deepcopy(row['values']);self.props['desc'] = row['role']
            self.edges = {name: [source, output] for name, source, output in row['inputs']}
            self.roles = list(self.edges)
    def get_class(self): return SimpleNamespace(get_name=lambda: self.name)
    def set_material_function(self, value): self.props['material_function'] = value.get_path_name();return True


class Asset(Props):
    def __init__(self, path, values=None): super().__init__(values);self.path = path;self.metadata = {}
    def get_path_name(self): return self.path


class Texture(Asset):
    def __init__(self, path):
        super().__init__(path, {k: None for k in m.FIELDS})
        self.props.update(source_color_settings=Props({'encoding_override': None}),
            downscale=Props({'default': 0., 'per_platform': {'Mac': 3.}}),
            alpha_coverage_thresholds=SimpleNamespace(x=1., y=1., z=1., w=1.))
    def blueprint_get_size_x(self): return 2048
    def blueprint_get_size_y(self): return 2048


class Material(Asset):
    def __init__(self, path, graph):
        super().__init__(path, copy.deepcopy(graph['flags']))
        self.nodes = [Node(row['class'], row) for row in graph['nodes']]
        self.roots = copy.deepcopy(graph['roots'])
        for node in self.nodes:
            if node.name == 'MaterialExpressionTextureSample': node.props['sampler_source'] = 'old-shared-sampler'
            if node.name == 'MaterialExpressionWorldPosition': node.props['world_position_shader_offset'] = 'old-world-offset'


def fake_unreal(bundle, compile_errors=None):
    u = SimpleNamespace();enum_rows = {
        'TextureFilter': {'TF_BILINEAR': '<TextureFilter.TF_BILINEAR: 1>'},
        'SamplerSourceMode': {'SSM_FROM_TEXTURE_ASSET': '<SamplerSourceMode.SSM_FROM_TEXTURE_ASSET: 0>'},
        'TextureMipGenSettings': {'TMGS_NO_MIPMAPS': '<TextureMipGenSettings.TMGS_NO_MIPMAPS: 13>'},
        'TextureAddress': {'TA_CLAMP': '<TextureAddress.TA_CLAMP: 1>'},
        'TextureCompressionSettings': {'TC_MASKS': '<TextureCompressionSettings.TC_MASKS: 2>'},
        'TextureSourceEncoding': {'TSE_NONE': '<TextureSourceEncoding.TSE_NONE: 0>'},
        'TexturePowerOfTwoSetting': {'NONE': '<TexturePowerOfTwoSetting.NONE: 0>'},
        'BlendMode': {'BLEND_MASKED': '<BlendMode.BLEND_MASKED: 1>'},
        'CustomMaterialOutputType': {f'CMOT_FLOAT{i}': f'<CustomMaterialOutputType.CMOT_FLOAT{i}: {i-1}>' for i in (1, 2, 3)},
        'MaterialSamplerType': {'SAMPLERTYPE_MASKS': '<MaterialSamplerType.SAMPLERTYPE_MASKS: 4>'},
        'TextureMipValueMode': {'TMVM_NONE': '<TextureMipValueMode.TMVM_NONE: 0>'}}
    for name, values in enum_rows.items(): setattr(u, name, SimpleNamespace(**values))
    u.Material = Material;u.Texture2D = Texture;u.CustomInput = Props;u.AssetImportTask = Props
    u.LinearColor = lambda *v: list(v);u.Vector4 = lambda *v: SimpleNamespace(**dict(zip('xyzw', v)))
    classes = {row['class'] for graph in bundle['nativeGraphs'].values() for row in graph['nodes']}
    for name in classes: setattr(u, name, name)
    u.MaterialProperty = SimpleNamespace(**{f'MP_{key}': key for key in ('BASE_COLOR', 'NORMAL', 'ROUGHNESS', 'OPACITY_MASK')})
    assets = {bundle['originalBackdropAsset']: Material(bundle['originalBackdropAsset'], bundle['originalGraph']),
        bundle['originalSubstrateAsset']: Material(bundle['originalSubstrateAsset'], bundle['graphs']['substrate'])}
    saved = [];created = []
    def canonical(path): return path if '.' in path.rsplit('/', 1)[-1] else path+'.'+path.rsplit('/', 1)[-1]
    def load(path): return assets.get(canonical(path), Asset(path))
    def duplicate(source, path):
        asset = Material(canonical(path), snapshot(u, load(source)));assets[asset.path] = asset;return asset
    def create(material, cls, x, y): node = Node(cls);material.nodes.append(node);created.append(node);return node
    def connect(source, output, destination, input_name):
        name = input_name or 'None';destination.edges[name] = [source.props['desc'], output];return True
    def root(node, output, prop):
        material = next(a for a in assets.values() if isinstance(a, Material) and node in a.nodes)
        material.roots[prop] = [node.props['desc'], output];return True
    def import_tasks(tasks):
        for task in tasks:
            p = task.props['destination_path']+'/'+task.props['destination_name'];asset = Texture(canonical(p));assets[asset.path] = asset
    u.EditorAssetLibrary = SimpleNamespace(load_asset=load, does_asset_exist=lambda p: canonical(p) in assets,
        duplicate_asset=duplicate, save_loaded_asset=lambda asset, dirty: saved.append(asset.path) or True,
        set_metadata_tag=lambda asset, key, value: asset.metadata.__setitem__(key, value),
        get_metadata_tag=lambda asset, key: asset.metadata.get(key, ''))
    u.AssetToolsHelpers = SimpleNamespace(get_asset_tools=lambda: SimpleNamespace(import_asset_tasks=import_tasks))
    u.MaterialEditingLibrary = SimpleNamespace(get_material_expressions=lambda a: a.nodes, create_material_expression=create,
        connect_material_expressions=connect, connect_material_property=root,
        recompile_material=lambda a: list(compile_errors or []), get_material_expression_input_names=lambda n: list(n.edges))
    texture_cdo = Texture('CDO');sample_cdo = Props({k: None for k in ('sampler_source', 'sampler_type', 'mip_value_mode', 'automatic_view_mip_bias')})
    u.get_default_object = lambda cls: texture_cdo if cls == Texture else sample_cdo
    u.test = SimpleNamespace(assets=assets, saved=saved, created=created, texture_cdo=texture_cdo, sample_cdo=sample_cdo)
    return u


def snapshot(u, material):
    rows = []
    templates = {row['role']: row for graph in TEST_BUNDLE['nativeGraphs'].values() for row in graph['nodes']}
    for node in material.nodes:
        role = node.props['desc'];template = templates[role];values = {}
        for key in template['values']:
            value = node.props[key];values[key] = value.get_path_name() if isinstance(value, Asset) else copy.deepcopy(value)
        inputs = [[name, *node.edges.get(name, [None, None])] for name, _, _ in template['inputs']]
        rows.append({'class': node.name, 'role': role, 'values': values, 'inputs': inputs})
    return {'nodes': sorted(rows, key=lambda row: row['role']), 'roots': copy.deepcopy(material.roots), 'flags': copy.deepcopy(material.props)}


TEST_BUNDLE = None


class Materials(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global TEST_BUNDLE
        TEST_BUNDLE = m.g.load_contract();cls.bundle = TEST_BUNDLE

    def build(self, compile_errors=None):
        u = fake_unreal(self.bundle, compile_errors)
        shared = lambda unused: {'historicalSharedTextures': 'unchanged-mocked-native-policy'}
        materials, report = m.build_materials(u, self.bundle, self.bundle['binding'], snapshot, shared)
        return u, materials, report, shared

    def test_actual_final_guard_api_and_reject_before_unreal_access(self):
        for name in ('PNG_SHA', 'SOURCE_SHA', 'MASK_ASSET', 'ASSETS', 'TAG', 'PREFIX', 'require_native_binding', 'validate_policy', 'validate_native_graphs'):
            self.assertTrue(hasattr(m.g, name), name)
        class NoAccess:
            def __getattr__(self, key): raise AssertionError('Unbound call reached UObject API '+key)
        for binding in (None, {}, dict(self.bundle['binding'], selectedNativeProcessId=1)):
            with self.assertRaises(ValueError): m.build_materials(NoAccess(), self.bundle, binding, None, None)

    def test_exact_enum_and_missing_bilinear_reject(self):
        u = fake_unreal(self.bundle);self.assertEqual(len(m.preflight_enums(u)), 13)
        u.TextureFilter = SimpleNamespace(TF_TRILINEAR=1)
        with self.assertRaises(ValueError): m.preflight_enums(u)
        with self.assertRaises(ValueError): m.exact_enum(SimpleNamespace(TF_BILINEAR=1, TFBILINEAR=2), 'TF_BILINEAR')

    def test_reflection_preflight_only_reads_class_defaults(self):
        u = fake_unreal(self.bundle);row = m.preflight_reflection(u)
        self.assertTrue(row['requiredPropertiesReadableBeforeImport']);self.assertFalse(row['setterAvailabilityActuallyMeasured'])
        self.assertEqual(u.test.texture_cdo.writes, []);self.assertEqual(u.test.sample_cdo.writes, [])
        self.assertEqual(u.test.saved, []);self.assertEqual(u.test.created, [])

    def test_mask_import_configures_all_policy_and_source_metadata(self):
        u = fake_unreal(self.bundle);enums = m.preflight_enums(u)
        texture, row = m._import_mask_blueprint(u, self.bundle, enums)
        self.assertEqual(row['metadata']['BreziSourceSha256'], m.g.PNG_SHA)
        self.assertEqual(row['metadata']['BreziGeneratedBy'], m.OWNER)
        self.assertEqual(row['values'], m.expected_texture_values(enums));self.assertEqual(row['downscale'], {'default': 1., 'perPlatform': {}})
        self.assertEqual(u.test.saved, [m.g.MASK_ASSET]);self.assertEqual(texture.props['filter'], enums['filter'])

    def test_native_mask_policy_tampering_rejects(self):
        u = fake_unreal(self.bundle);enums = m.preflight_enums(u)
        _, row = m._import_mask_blueprint(u, self.bundle, enums)
        for key, value in [('filter', 'trilinear'), ('srgb', True), ('compression_none', False), ('max_texture_size', 1024)]:
            bad = copy.deepcopy(row);bad['values'][key] = value
            with self.assertRaises(ValueError): m.validate_mask_snapshot(bad, enums)
        bad = copy.deepcopy(row);bad['alphaCoverageThresholds'][0] = .5
        with self.assertRaises(ValueError): m.validate_mask_snapshot(bad, enums)

    def test_full_build_declared_nodes_roots_flags_compile_array_and_old_graphs(self):
        u, materials, report, shared = self.build()
        self.assertEqual(set(materials), {'backdrop', 'substrate'})
        for key, material in materials.items():
            self.assertEqual(snapshot(u, material), self.bundle['nativeGraphs'][key])
            self.assertEqual(report['materials'][key]['compileErrors'], [])
            mask = next(n for n in material.nodes if n.props['desc'] == m.g.TAG+'fixed-world-yard-mask')
            self.assertEqual(mask.props['sampler_source'], m.preflight_enums(u)['sampler'])
            self.assertEqual(mask.props['mip_value_mode'], '<TextureMipValueMode.TMVM_NONE: 0>')
        self.assertEqual(len(u.test.created), 27)
        self.assertEqual(report['newPackageAssets'], sorted([*m.g.ASSETS.values(), m.g.MASK_ASSET]))
        self.assertFalse(report['nativeTexelsDecoded']);self.assertFalse(report['nativeGpuPixelFormatVerified'])
        self.assertFalse(report['materialPackagesIndependentlyUnloaded']);self.assertFalse(report['nativeAppearanceAccepted'])
        for path, original in report['originalGraphWitness'].items(): self.assertEqual(snapshot(u, u.test.assets[path]), original)

    def test_compile_error_array_rejects_before_new_material_save(self):
        u = fake_unreal(self.bundle, ['Missing DDX'])
        with self.assertRaisesRegex(ValueError, 'graph/compile'):
            m.build_materials(u, self.bundle, self.bundle['binding'], snapshot, lambda _: {'shared': 'same'})
        self.assertEqual(u.test.saved, [m.g.MASK_ASSET])

    def test_saved_verifier_checks_own_graph_and_all_old_aux_routes(self):
        u, materials, report, shared = self.build()
        self.assertEqual(m.verify_materials(u, self.bundle, self.bundle['binding'], report, snapshot, shared), materials)
        original = u.test.assets[self.bundle['originalBackdropAsset']]
        node = next(n for n in original.nodes if n.name == 'MaterialExpressionTextureSample')
        node.props['sampler_source'] = 'changed-old-sampler'
        with self.assertRaisesRegex(ValueError, 'Original graphs/shared texture'):
            m.verify_materials(u, self.bundle, self.bundle['binding'], report, snapshot, shared)

    def test_saved_verifier_rejects_inherited_uv1_and_policy_mutations(self):
        u, materials, report, shared = self.build()
        uv = next(n for n in materials['substrate'].nodes if n.name == 'MaterialExpressionTextureCoordinate')
        uv.props['coordinate_index'] = 0
        with self.assertRaisesRegex(ValueError, 'Saved graph'):
            m.verify_materials(u, self.bundle, self.bundle['binding'], report, snapshot, shared)
        u, _, report, shared = self.build();u.test.assets[m.g.MASK_ASSET].props['filter'] = 'default-group'
        with self.assertRaisesRegex(ValueError, 'policy differs'):
            m.verify_materials(u, self.bundle, self.bundle['binding'], report, snapshot, shared)

    def test_saved_verifier_rejects_old_owner_and_extra_package(self):
        u, _, report, shared = self.build()
        for key, value in [('owner', 'scripts/unreal/exterior-context-yard-soft-coherence-materials-r38-draft.py'),
            ('newPackageAssets', report['newPackageAssets']+['/Game/foreign.foreign'])]:
            bad = copy.deepcopy(report);bad[key] = value
            with self.assertRaisesRegex(ValueError, 'Closed own material report'):
                m.verify_materials(u, self.bundle, self.bundle['binding'], bad, snapshot, shared)


if __name__ == '__main__': unittest.main()
