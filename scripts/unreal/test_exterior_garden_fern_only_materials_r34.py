"""CPU ownership/graph fixtures; no R34 material import or native proof."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
FILE = ROOT/'scripts/unreal/exterior-garden-fern-only-materials-r34.py'
spec = importlib.util.spec_from_file_location('r34_material_owner_fixture', FILE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def remap(value, pairs):
    if isinstance(value, str):
        for a, b in pairs:
            value = value.replace(a, b)
        return value
    if isinstance(value, list):
        return [remap(v, pairs) for v in value]
    if isinstance(value, dict):
        return {remap(k, pairs): remap(v, pairs) for k, v in value.items()}
    return value


class Materials(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(m.RECIPE.read_text())
        spec = importlib.util.spec_from_file_location('r34_unchanged_source_fixture', m.DELEGATE)
        cls.original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.original)
        saved = ROOT/'output/unreal/exterior-20261002-r25b/garden-fern-native-report-r2.json'
        if m.sha(saved) != 'dc96a4927a0b0ec0e8abb3740e7a918e65a6ba6a0881ba77bc29275c1445e0b2':
            raise RuntimeError('Actual historical saved fern graph fixture changed')
        cls.report = remap(json.loads(saved.read_text())['materialReport'],
            [(cls.original.PREFIX, m.PREFIX), (cls.original.TAG, m.TAG)])
        cls.report['owner'] = m.OWNER

    def test_private_original_writer_is_unmodified(self):
        d = m._private()
        self.assertIsNot(d, self.original)
        self.assertEqual(d.KEY, self.original.KEY)
        self.assertEqual(d.KEY, 'ph_original_fern_02_b_r25')
        self.assertEqual(self.original.PREFIX, '/Game/Brezi/GardenFern20261002R25')
        self.assertEqual(self.original.OWNER, 'scripts/unreal/exterior-garden-fern-materials-r25.py')
        self.assertEqual(m.sha(m.DELEGATE), m.DELEGATE_SHA)
        self.assertNotIn('_r34_private_original_fern', sys.modules)

    def test_exact_one_fern_recipe_retains_alpha_and_no_occlusion(self):
        recipe = m.validate_recipe(self.recipe)
        self.assertEqual(recipe['sourceAlphaBits'], 16)
        self.assertIsNone(recipe['occlusionRoot'])
        self.assertEqual(self.recipe['sourceVariants'], ['fern_02_a', 'fern_02_c', 'fern_02_d'])

    def test_rehashed_recipe_escape_and_extra_grass_rejected(self):
        for key, value in [('prefix', '/Game/Brezi/Foreign'), ('textureObjectCount', 8),
            ('sourceVariants', ['fern_02_a', 'grass_medium_01_tall_a']),
            ('privateSourceDelegateKeyMustRemainOriginal', 'new_owned_key'), ('nativeR34Applied', True)]:
            changed = copy.deepcopy(self.recipe)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                m.validate_recipe(changed)

    def test_historical_graph_annotation_fixture_and_five_packages(self):
        m._graph(self.report)
        assets = m._package_assets(self.report)
        self.assertEqual(len(assets), 5)
        self.assertEqual(len(set(assets)), 5)
        self.assertTrue(all(a.startswith(m.PREFIX+'/') for a in assets))

    def test_alpha_a_ao_and_uv1_routes_rejected(self):
        r = copy.deepcopy(self.report)
        r['graph']['roots']['OPACITY_MASK'][1] = 'A'
        with self.assertRaises(RuntimeError):
            m._graph(r)
        r = copy.deepcopy(self.report)
        r['graph']['roots']['AMBIENT_OCCLUSION'] = [m.TAG+'ARM', 'R']
        with self.assertRaises(RuntimeError):
            m._graph(r)
        r = copy.deepcopy(self.report)
        n = next(n for n in r['graph']['nodes'] if n['role'] == m.TAG+m.KEY+':uv')
        n['values']['coordinate_index'] = 1
        with self.assertRaises(RuntimeError):
            m._graph(r)

    def test_foreign_old_package_and_missing_alpha_rejected(self):
        r = copy.deepcopy(self.report)
        r['textures']['alpha']['asset'] = self.original.PREFIX+'/Textures/old.old'
        with self.assertRaises(RuntimeError):
            m._package_assets(r)
        r = copy.deepcopy(self.report)
        del r['textures']['alpha']
        with self.assertRaises(RuntimeError):
            m._package_assets(r)


if __name__ == '__main__':
    unittest.main(verbosity=2)
