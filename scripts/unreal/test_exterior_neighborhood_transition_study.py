"""Meaningful actual-source/envelope rejection tests for the future proposal."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('transition_validation', ROOT / 'scripts/unreal/exterior-neighborhood-transition-validation.py')
validation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validation)


class TransitionSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = validation.read(validation.PLAN)
        cls.domains = validation.source_domains()

    def test_actual_decoded_geometry_and_original_sources(self):
        result = validation.validate(self.plan, self.domains)
        self.assertEqual((result['sourceMeshes'], result['instances'], result['groups']), (65, 7000, 158))
        self.assertEqual(result['allLodTriangles'], [6351095, 3487981, 1584502])
        self.assertTrue(result['actualDecodedAllLodCrownsOutsideSoilAndInsideAllowedGround'])
        self.assertTrue(result['actualHighestRenderedSourceTriangleGroundZVerified'])
        self.assertFalse(result['nativeVisualAccepted'])

    def test_ground_contact_forgery_is_rejected(self):
        value = copy.deepcopy(self.plan)
        value['transitionPlacements'][0]['positionCm'][2] += 1.
        value['transitionPlacements'][0]['sourceGroundZCm'] += 1.
        with self.assertRaisesRegex(RuntimeError, 'actual source triangles'):
            validation.validate(value, self.domains)

    def test_private_site_root_is_rejected_even_with_forged_domain_claim(self):
        value = copy.deepcopy(self.plan)
        point = np.asarray(self.domains[0]['protectedTrianglesCm'][0]).mean(axis=0)
        value['transitionPlacements'][0]['positionCm'][:2] = point.tolist()
        with self.assertRaises(RuntimeError):
            validation.validate(value, self.domains)

    def test_field_or_material_scope_forgery_is_rejected(self):
        value = copy.deepcopy(self.plan)
        value['materialBindingProposal'][0]['sourceMeshId'] = 'context_surface_6015_surface_54'
        with self.assertRaisesRegex(RuntimeError, 'target source mesh set'):
            validation.validate(value, self.domains)

    def test_correct_hash_parcel_flat_mask_is_rejected(self):
        value = copy.deepcopy(self.plan)
        pixels = np.asarray(Image.open(value['conditionTexture']['path'])).copy()
        pixels[:, :, 0] = 128
        with tempfile.TemporaryDirectory(prefix='brezi-transition-mask-test-') as temporary:
            path = Path(temporary) / 'forged-field.png'
            Image.fromarray(pixels).save(path)
            value['conditionTexture']['path'] = str(path)
            value['conditionTexture']['sha256'] = validation.sha(path)
            with self.assertRaisesRegex(RuntimeError, 'parcel-dependent or altered pixels'):
                validation.validate(value, self.domains)


if __name__ == '__main__':
    unittest.main()
