"""Small adversarial checks against the actual published R24 descriptor/recipe."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('r24_tree_source', ROOT/'scripts/unreal/exterior-original-tree-study.py')
study = importlib.util.module_from_spec(spec); spec.loader.exec_module(study)


class OriginalTreeSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = study.OUTPUT
        cls.original = study.read(study.REFERENCE/'tree_small_02/tree_small_02_2k.gltf')
        cls.candidate = study.read(cls.directory/'candidate-original-tree.gltf')
        cls.plan = study.read(cls.directory/'original-tree-source-plan.json')
        cls.selection = study.read(cls.directory/'single-tree-selection.json')
        cls.scale = cls.selection['newActorProposal']['sourceNodeUniformScale']
        cls.bottom = -cls.candidate['nodes'][0]['translation'][1]/cls.scale

    def validate(self, value):
        study.validate_document(value, self.original, self.directory, self.scale, self.bottom)

    def test_actual_candidate_keeps_the_complete_original(self):
        self.validate(self.candidate)
        self.assertEqual(self.candidate['meshes'], self.original['meshes'])
        self.assertEqual(self.candidate['accessors'], self.original['accessors'])
        self.assertEqual(self.candidate['materials'], self.original['materials'])
        self.assertEqual(self.plan['budget']['sourceTriangles'], 2062487)
        self.assertFalse(self.plan['pendingNativeBase']['selectionComplete'])
        self.assertIsNone(self.plan['pendingNativeBase']['selectedNativeReport'])

    def test_reordered_indices_are_rejected(self):
        value = deepcopy(self.candidate)
        value['meshes'][0]['primitives'][0]['indices'] = value['meshes'][0]['primitives'][1]['indices']
        with self.assertRaisesRegex(ValueError, 'published attributes'): self.validate(value)

    def test_changed_uv_accessor_is_rejected(self):
        value = deepcopy(self.candidate)
        value['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_1'] = value['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_0']
        with self.assertRaisesRegex(ValueError, 'published attributes'): self.validate(value)

    def test_branch_uv0_substitution_and_khr_loss_are_rejected(self):
        for mode in ('uv', 'transform'):
            value = deepcopy(self.candidate); row = value['materials'][0]['normalTexture']
            if mode == 'uv': row['texCoord'] = 0
            else: del row['extensions']
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'KHR material mapping'): self.validate(value)

    def test_nonuniform_fit_and_extra_root_are_rejected(self):
        value = deepcopy(self.candidate); value['nodes'][0]['scale'][0] *= .99
        with self.assertRaisesRegex(ValueError, 'node scope'): self.validate(value)
        value = deepcopy(self.candidate); value['nodes'].append(deepcopy(value['nodes'][0]))
        with self.assertRaisesRegex(ValueError, 'node scope'): self.validate(value)

    def test_original_photo_alpha_conversion_is_explicit(self):
        rows = study.source_materials(self.original, self.plan['originalProviderFiles'])
        self.assertEqual(rows[0]['uvSet'], 1)
        self.assertEqual(rows[0]['KHRTextureTransform'], {'offset':[0, .40000009536743164], 'scale':[3, .5999999046325684]})
        leaf = rows[1]
        self.assertEqual(leaf['providerMaterial']['alphaMode'], 'BLEND')
        self.assertEqual(leaf['nativeProposal']['blendMode'], 'MASKED')
        self.assertEqual(Path(leaf['alphaSource']['path']).name, 'tree_small_02_leaves_alpha_2k.png')
        self.assertFalse(leaf['nativeShaderMatchesOriginalGlTFExactly'])
        self.assertFalse(leaf['nativeProposal']['nativeGraphBuilt'])

    def test_source_metallic_or_extra_ao_route_is_rejected(self):
        value = deepcopy(self.original); value['materials'][0]['pbrMetallicRoughness']['metallicFactor'] = 1
        with self.assertRaisesRegex(ValueError, 'defaults'): study.source_materials(value, self.plan['originalProviderFiles'])
        value = deepcopy(self.original); value['materials'][0]['occlusionTexture'] = {'index':2}
        with self.assertRaisesRegex(ValueError, 'defaults'): study.source_materials(value, self.plan['originalProviderFiles'])

    def test_single_retirement_and_full_triangle_mask_limits(self):
        self.assertEqual(self.selection['retiredOriginalIndex'], 0)
        self.assertEqual(self.selection['remainingNativeMembers'], 3)
        self.assertEqual(self.selection['retainedSourceRootIds'], ['village_nearest_grove_11','village_nearest_grove_27','village_nearest_grove_30'])
        proof = study.read(self.directory/'whole-tree-mask-review.json')
        self.assertEqual(proof['decodedTransformedVertices'], 1777278)
        self.assertEqual(proof['triangles'], 2062487)
        self.assertEqual(len(proof['exclusions']), 6)
        self.assertGreater(proof['wholeTreeGroveBoundaryClearanceLowerBoundCm'], 600)
        for row in proof['exclusions'].values():
            self.assertTrue(row['allVerticesAndTriangleEdgesProvenOutside'])
            self.assertGreater(row['completeTriangleClearanceLowerBoundCm'], 75)


if __name__ == '__main__': unittest.main()
