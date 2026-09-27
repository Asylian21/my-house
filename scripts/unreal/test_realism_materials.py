"""Scope and color-transfer contracts for the owned realism finish stage."""
import copy
import importlib.util
import json
import math
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('realism_materials', Path(__file__).with_name('realism-materials.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class RealismMaterialTests(unittest.TestCase):
    def source(self, name='real-interior-black-glass', swatch='#0c0e10', **changes):
        value = {'name': name, 'color': M.hex_channels(swatch), 'roughness': .08,
                 'metallic': .1, 'alpha': 1, 'emission': [0, 0, 0], 'texture': None}
        return {**value, **changes}

    def test_black_srgb_is_not_mistaken_for_linear_reflectance(self):
        result = M.recipe(self.source())
        self.assertAlmostEqual(result['decodedLinear'][0], .003676507324047436, places=12)
        self.assertAlmostEqual(result['decodedLinear'][2], .005181516702338386, places=12)
        self.assertLess(result['decodedLinear'][0], result['originalLinearInterpretation'][0] / 10)
        self.assertEqual(result['metallic'], 0)

    def test_color_transfer_preserves_endpoint_and_breakpoint_continuity(self):
        self.assertEqual(M.decode_srgb(0), 0)
        self.assertEqual(M.decode_srgb(1), 1)
        self.assertLess(abs(M.decode_srgb(.04045)-M.decode_srgb(.04045001)), 1e-7)
        for invalid in (-.001, 1.1, float('nan'), float('inf')):
            with self.assertRaises(RuntimeError):
                M.decode_srgb(invalid)

    def test_already_linear_or_textured_source_is_never_double_decoded(self):
        source = self.source()
        source['color'] = [M.decode_srgb(v) for v in source['color']]
        with self.assertRaisesRegex(RuntimeError, 'no longer an unconverted constant'):
            M.recipe(source)
        with self.assertRaises(RuntimeError):
            M.recipe(self.source(texture='/assets/new-graphite.jpg'))
        self.assertIsNone(M.recipe(self.source('Kitchen 2026 · spotrebiče grafit')))
        self.assertIsNone(M.recipe(self.source('real-glass-frame')))

    def test_transmission_emission_and_unrelated_materials_are_protected(self):
        self.assertIsNone(M.recipe(self.source(alpha=.5)))
        self.assertIsNone(M.recipe(self.source(emission=[.1, 0, 0])))
        self.assertIsNone(M.recipe(self.source('real-pool-led')))
        self.assertIsNone(M.recipe(self.source('real-interior-steel')))
        self.assertIsNone(M.recipe(self.source('arbitrary white material')))

    def test_only_audited_artificial_ceiling_luminance_is_removed(self):
        source = self.source('real-interior-ceiling', '#f6f5f1', emission=M.hex_channels('#9a9995'))
        result = M.recipe(source)
        self.assertTrue(result['removeArtificialEmission'])
        self.assertEqual(result['paletteLinear'], [M.decode_srgb(v) for v in source['color']])
        self.assertIsNone(M.recipe({**source, 'name': 'Kitchen 2026 · pracovné svetlo'}))
        with self.assertRaisesRegex(RuntimeError, 'ceiling swatch/emission changed'):
            M.recipe({**source, 'emission': [2, 2, 2]})

    def test_source_dictionary_is_never_mutated(self):
        source = self.source()
        original = copy.deepcopy(source)
        M.recipe(source)
        self.assertEqual(source, original)

    def test_linen_uses_only_color_correction_and_retains_existing_optics(self):
        result = M.recipe(self.source('real-fabric', '#e6e2d8', roughness=.95, metallic=0))
        self.assertEqual(result['kind'], 'existing-linen')
        self.assertNotIn('roughness', result)
        self.assertNotIn('metallic', result)
        self.assertNotIn('normalStrength', result)
        self.assertTrue(all(0 < value < 1 for value in result['correctionRatio']))

    def test_scan_recipes_share_measured_scale_without_changing_design(self):
        oak = M.recipe(self.source('Kitchen 2026 · prírodný dub'))
        plaster = M.recipe(self.source('real-wall'))
        inputs = json.loads((M.ROOT/'scripts/unreal/archviz-material-inputs.json').read_text())
        for result in (oak, plaster):
            self.assertAlmostEqual(result['physicalPeriodCm'], inputs['assets'][result['asset']]['periodCm'])
        self.assertLess(plaster['contrast'], .02)
        self.assertLess(plaster['normalStrength'], .1)
        self.assertLess(oak['contrast'], 1)
        self.assertNotEqual(oak['paletteLinear'], [0, 0, 0])

    def test_every_provenance_known_swatch_has_exact_decode(self):
        for name, (swatch, _, _) in M.SRGB_SOURCES.items():
            result = M.recipe(self.source(name, swatch))
            reconstructed = [a*b for a, b in zip(result['originalLinearInterpretation'], result['correctionRatio'])]
            self.assertTrue(all(math.isclose(a, b, abs_tol=1e-12) for a, b in zip(reconstructed, result['decodedLinear'])))

    def test_current_baseline_supports_required_scope_and_beveled_materials(self):
        path = M.ROOT/'output/unreal/performance-shipping-20260924-r4/geometry/scene.json'
        if not path.exists():
            self.skipTest('The optional accepted R4 scene fixture is not present')
        scene = json.loads(path.read_text())
        names = [source['name'] for source in scene['materials'].values()]
        self.assertEqual(len(names), len(set(names)))
        recipes = {source['name']: M.recipe(source) for source in scene['materials'].values()}
        self.assertTrue(M.OAK | M.PLASTER | set(M.SRGB_SOURCES) <= {name for name, r in recipes.items() if r})
        self.assertIsNone(recipes['real-glass'])
        self.assertIsNone(recipes['real-bathroom-shower-glass'])
        self.assertIsNone(recipes['real-interior-fireplace-glass'])


if __name__ == '__main__':
    unittest.main()
