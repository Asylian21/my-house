"""Bounded CPU recipe/schema guards; these fixtures do not import R30 assets."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
FILE = ROOT/'scripts/unreal/exterior-garden-composition-materials-r30.py'
spec = importlib.util.spec_from_file_location('r30_material_fixture_owner', FILE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def replace(value, pairs):
    if isinstance(value, str):
        for old, new in pairs:
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [replace(v, pairs) for v in value]
    if isinstance(value, dict):
        return {replace(k, pairs): replace(v, pairs) for k, v in value.items()}
    return value


class Materials(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(m.RECIPE.read_text())
        cls.original = {}
        for role in ('fern', 'grass'):
            file = m.DELEGATES[role][0]
            spec = importlib.util.spec_from_file_location('unchanged_'+role+'_fixture', file)
            delegate = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(delegate)
            cls.original[role] = delegate
        cls.reports = {}
        paths = {
            'fern': ('output/unreal/exterior-20261002-r25b/garden-fern-native-report-r2.json',
                'dc96a4927a0b0ec0e8abb3740e7a918e65a6ba6a0881ba77bc29275c1445e0b2'),
            'grass': ('output/unreal/exterior-20261002-r20d/curved-grass-native-report-r4.json',
                '63ff19a28e571ff4a63d0a9e13726c90a01fcc82b691b81dd2b6a35ac01eb4eb')}
        for role, (relative, digest) in paths.items():
            file = ROOT/relative
            if m.sha(file) != digest:
                raise RuntimeError('Actual saved historical graph fixture changed')
            row = json.loads(file.read_text())['materialReport']
            old, private = cls.original[role], m._private(role)
            cls.reports[role] = replace(row, [(old.PREFIX, private.PREFIX), (old.TAG, private.TAG)])
            cls.reports[role]['owner'] = m.OWNER

    def test_original_recipes_and_private_ownership(self):
        validated = m.validate_recipe(self.recipe)
        self.assertIsNone(validated['fern']['occlusionRoot'])
        self.assertEqual(validated['fern']['sourceAlphaBits'], 16)
        self.assertEqual(validated['grass']['providerSourceAlphaMode'], 'BLEND')
        for role, old in self.original.items():
            private = m._private(role)
            self.assertIsNot(private, old)
            self.assertEqual(old.PREFIX, '/Game/Brezi/GardenFern20261002R25' if role == 'fern'
                else '/Game/Brezi/CurvedGrass20261001R20')
            self.assertNotEqual(old.OWNER, private.OWNER)
            self.assertEqual(private.KEY, old.KEY)
            self.assertEqual(m.sha(m.DELEGATES[role][0]), m.DELEGATES[role][1])

    def test_modified_recipe_rejected_without_rehashed_escape(self):
        for path, value in [(('prefix',), '/Game/Brezi/Foreign'),
            (('grassRecipe', 'explicitOpacitySource'), 'albedo.A'),
            (('grassRecipe', 'ueOnlySubsurfaceScale'), .24),
            (('fernDelegate', 'sha256'), '0'*64), (('sourcePixelsEdited',), True)]:
            changed = copy.deepcopy(self.recipe)
            at = changed
            for key in path[:-1]:
                at = at[key]
            at[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(RuntimeError):
                m.validate_recipe(changed)

    def test_real_saved_graph_schema_with_owned_tags(self):
        # Only graph/path annotation remapping: no new native material proof.
        for role, report in self.reports.items():
            m._graph(role, report)
        assets = m._package_assets(self.reports)
        self.assertEqual(len(assets), 10)
        self.assertEqual(len(set(assets)), 10)
        self.assertTrue(all(p.startswith(m.PREFIX+'/') for p in assets))

    def test_wrong_alpha_sampler_and_ao_routes_rejected(self):
        for role in ('fern', 'grass'):
            changed = copy.deepcopy(self.reports[role])
            changed['graph']['roots']['OPACITY_MASK'][1] = 'A'
            with self.subTest(role=role), self.assertRaises(RuntimeError):
                m._graph(role, changed)
        changed = copy.deepcopy(self.reports['fern'])
        changed['graph']['roots']['AMBIENT_OCCLUSION'] = [m._private('fern').TAG+'ARM', 'R']
        with self.assertRaises(RuntimeError):
            m._graph('fern', changed)
        changed = copy.deepcopy(self.reports['grass'])
        node = next(n for n in changed['graph']['nodes'] if n['role'] == m._private('grass').TAG+'normal')
        node['values']['sampler_type'] = '<MaterialSamplerType.SAMPLERTYPE_MASKS: 3>'
        with self.assertRaises(RuntimeError):
            m._graph('grass', changed)

    def test_native_texture_policy_fixture_color_normal_alpha(self):
        rows = self.reports['grass']['textures']
        u = SimpleNamespace(
            TextureCompressionSettings=type('Compression', (), {
                'TC_DEFAULT': rows['albedo']['snapshot']['compression_settings'],
                'TC_NORMALMAP': rows['normal']['snapshot']['compression_settings'],
                'TC_MASKS': rows['alpha']['snapshot']['compression_settings']}),
            TextureSourceEncoding=type('Encoding', (), {
                'TSE_SRGB': rows['albedo']['snapshot']['sourceEncoding'],
                'TSE_NONE': rows['normal']['snapshot']['sourceEncoding']}),
            TextureAddress=SimpleNamespace(TA_WRAP=rows['alpha']['snapshot']['address_x']),
            TextureMipGenSettings=SimpleNamespace(TMGS_FROM_TEXTURE_GROUP=rows['alpha']['snapshot']['mip_gen_settings']),
            TexturePowerOfTwoSetting=SimpleNamespace(NONE=rows['alpha']['snapshot']['power_of_two_mode']))
        for role, row in rows.items():
            m._grass_texture_policy(u, row['snapshot'], role)
        for role, key, value in [('alpha', 'srgb', True), ('normal', 'flip_green_channel', False),
            ('alpha', 'alphaCoverageThresholds', [0., .5, 0., 0.]),
            ('arm', 'compression_settings', rows['albedo']['snapshot']['compression_settings'])]:
            changed = copy.deepcopy(rows[role]['snapshot'])
            changed[key] = value
            with self.subTest(role=role, key=key), self.assertRaises(RuntimeError):
                m._grass_texture_policy(u, changed, role)

    def test_foreign_package_and_role_population_rejected(self):
        changed = copy.deepcopy(self.reports)
        changed['grass']['textures']['alpha']['asset'] = self.original['grass'].PREFIX+'/Textures/old.old'
        with self.assertRaises(RuntimeError):
            m._package_assets(changed)
        changed = copy.deepcopy(self.reports)
        del changed['fern']['textures']['normalGL']
        with self.assertRaises(RuntimeError):
            m._package_assets(changed)


if __name__ == '__main__':
    unittest.main(verbosity=2)
