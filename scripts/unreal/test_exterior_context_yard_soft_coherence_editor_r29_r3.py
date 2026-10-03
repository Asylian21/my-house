"""Changed-contract fixtures only; no Unreal or historical source generation."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('r29r3_checker_fixture', Path(__file__).with_name('exterior-context-yard-soft-coherence-editor-check-r29-r3.py'))
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class ClosedConsumer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = c.read(c.REPORT)
        cls.plan, cls.pf, cls.base, cls.source = (c.side(cls.r[k]) for k in ('selectedPlan', 'sourcePreflight', 'baseNativeReport', 'sourceStudy'))
        cls.cache = {}
        cls.original_side = staticmethod(c.side)

    def side(self, row):
        key = row['path']
        if key not in self.cache:
            self.cache[key] = self.original_side(row)
        return self.cache[key]

    def test_authored_pf_without_repair_evidence_is_valid(self):
        self.assertNotIn('repairEvidence', self.pf)
        c.header(self.r, self.plan, self.pf)

    def test_unknown_native_owner_rejected(self):
        r = copy.deepcopy(self.r)
        r['owner'] = 'scripts/unreal/other-owner.py'
        with self.assertRaisesRegex(ValueError, 'actual saved'):
            c.header(r, self.plan, self.pf)

    def test_saved_scene_change_outside_two_slots_rejected(self):
        changed = copy.deepcopy(self.side(self.r['savedActorWitness']))
        changed[c.g.ACTOR197]['label'] += '-changed'
        def route(row):
            return changed if row == self.r['savedActorWitness'] else self.side(row)
        with patch.object(c, 'side', route), self.assertRaisesRegex(ValueError, 'Reloaded full counterfactual'):
            c.counterfactual(self.r, self.plan, self.base)

    def test_extra_target_field_rejected(self):
        plan = copy.deepcopy(self.plan)
        plan['targets']['backdrop']['materialSlot'] = 1
        with patch.object(c, 'side', self.side), self.assertRaisesRegex(ValueError, 'Exact source target'):
            c.counterfactual(self.r, plan, self.base)

    def test_saved_raw_matrix_digest_tamper_rejected(self):
        changed = copy.deepcopy(self.side(self.r['rawInstanceControlsSaved']))
        next(iter(changed.values()))['rawMatrixBinary64Sha256'] = '0'*64
        def route(row):
            return changed if row == self.r['rawInstanceControlsSaved'] else self.side(row)
        with patch.object(c, 'side', route), self.assertRaisesRegex(ValueError, 'raw native matrix'):
            c.raw_controls(self.r, self.side(self.r['savedActorWitness']))

    def material_mutation(self, change, pattern):
        r = copy.deepcopy(self.r)
        built = copy.deepcopy(self.side(r['newMaterialReport']))
        change(built)
        r['newMaterials'] = built
        def route(row):
            return built if row == r['newMaterialReport'] else self.side(row)
        with patch.object(c, 'side', route), self.assertRaisesRegex(ValueError, pattern):
            c.materials(r, self.plan, self.base, self.source)

    def test_grayscale_enum_number_tamper_rejected(self):
        self.material_mutation(lambda b: b['maskTexture']['values'].__setitem__('compression_settings', '<TextureCompressionSettings.TC_GRAYSCALE: 99>'), 'actually reflected')

    def test_old_world_position_aux_tamper_rejected(self):
        self.material_mutation(lambda b: b['materials']['substrate']['aux']['worldPositionShaderOffsets'].__setitem__('BreziExterior:world-position', '<WorldPositionIncludedOffsets.WPT_EXCLUDE_ALL_SHADER_OFFSETS: 1>'), 'auxiliary route')

    def test_owned_graph_wrong_sampler_rejected(self):
        def change(b):
            graph = b['materials']['backdrop']['graph']
            node = next(n for n in graph['nodes'] if n['role'] == c.g.TAG+'fixed-world-yard-mask')
            node['values']['sampler_type'] = '<MaterialSamplerType.SAMPLERTYPE_MASKS: 4>'
            b['materials']['backdrop']['graphSha256'] = c.digest(graph)
        self.material_mutation(change, 'full graph')

    def test_gpu_format_acceptance_rejected(self):
        self.material_mutation(lambda b: b.__setitem__('nativeGpuPixelFormatVerified', True), 'pixel/GPU/appearance')


if __name__ == '__main__':
    unittest.main()
