"""CPU source/receipt fixtures only; no Unreal/native/appearance proof."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('yard_ground_materials_r32', ROOT/'scripts/unreal/exterior-context-yard-ground-materials-r32.py')
m = importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ACTUAL_R28 = ROOT/'output/unreal/exterior-20261002-r28b/context-yard-native-report-r2.json'
ACTUAL_R28_SHA = 'dfbca65515fc08aea52515195ab5ef752fe07cdca622cd41964e99875ced2456'


def fixture(identity, original):
    """R28 actually saved mask/Dither ports; R32 new mix node is source-only."""
    row = json.loads(m.check_file(ACTUAL_R28, ACTUAL_R28_SHA).read_text())
    prototype = [n for n in row['newMaterials'][0]['graph']['nodes'] if n['role'].startswith('BreziYardR28:')]
    assert len(prototype) == 3
    tag = m.TAG+identity+':'
    additions = json.loads(json.dumps(prototype).replace('BreziYardR28:', tag))
    result = copy.deepcopy(original)
    if identity == 'yard_substrate_r32':
        additions += [{'role': tag+'soil-g', 'class': 'MaterialExpressionComponentMask',
            'values': {'r': False, 'g': True, 'b': False, 'a': False}, 'inputs': [['None', tag+'uv1', '']]},
            {'role': tag+'cover-amount', 'class': 'MaterialExpressionCustom',
            'values': {'code': m.COVER_CODE, 'output_type': '<CustomMaterialOutputType.CMOT_FLOAT1: 0>'},
            'inputs': [['SoilFraction', tag+'soil-g', '']]}]
        for node in result['nodes']:
            if node['role'] in m.MIX_ROLES:
                next(link for link in node['inputs'] if link[0] == 'Amount')[1] = tag+'cover-amount'
    result['nodes'] = sorted(result['nodes']+additions, key=lambda n: n['role'])
    result['roots']['OPACITY_MASK'] = [tag+'temporal-dither', 'Result']
    result['flags'].update(blend_mode='<BlendMode.BLEND_MASKED: 1>', opacity_mask_clip_value=.5)
    return result


class GuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proposals, cls.graphs, cls.textures = m.load_contract()
        cls.variants = {k: fixture(k,v) for k,v in cls.graphs.items()}

    def reject_graph(self, identity, mutate):
        row = copy.deepcopy(self.variants[identity]);mutate(row)
        with self.assertRaises(ValueError):m.validate_graph(identity, self.graphs[identity], row)

    def test_actual_old_graphs_and_saved_native_ports_define_the_source_route(self):
        self.assertEqual(len(self.textures), 12)
        for identity, graph in self.variants.items():
            proof = m.validate_graph(identity, self.graphs[identity], graph)
            self.assertEqual(proof['newNodes'], 3 if identity == 'yard_gravel_r32' else 5)
            self.assertEqual(proof['changedOriginalAmountLinks'], 0 if identity == 'yard_gravel_r32' else 3)
            self.assertFalse(proof['sourceUvFeatherNativePixelsVerified'])
        self.assertEqual([len(g['nodes']) for g in self.variants.values()], [68,71])
        self.assertEqual({v['metadata']['source_sha256'] for v in self.textures.values()},
            {v['metadata']['source_sha256'] for v in m.load_contract()[2].values()})

    def test_changed_even_rehashed_recipe_cannot_replace_the_frozen_source(self):
        m.validate_proposals(self.proposals)
        row = copy.deepcopy(self.proposals);row[1]['changes']['soilFractionRange'] = [0,1]
        self.assertNotEqual(m.digest(row), m.digest(self.proposals))
        with self.assertRaises(ValueError):m.validate_proposals(row)
        row = copy.deepcopy(self.proposals);row[0]['baseRecipe']['albedoScale'] = .3
        with self.assertRaises(ValueError):m.validate_proposals(row)

    def test_one_unreplaced_channel_or_wrong_cover_equation_is_rejected(self):
        identity = 'yard_substrate_r32'
        for role in m.MIX_ROLES:
            def mutate(g, role=role):
                n = next(n for n in g['nodes'] if n['role'] == role)
                next(v for v in n['inputs'] if v[0] == 'Amount')[1] = 'BreziExterior:irregular-ground-cover'
            with self.subTest(role=role):self.reject_graph(identity, mutate)
        self.reject_graph(identity, lambda g: next(n for n in g['nodes'] if n['role'].endswith(':cover-amount'))['values'].update(code='return SoilFraction;'))

    def test_original_transfer_functions_sampler_and_metric_scale_remain_exact(self):
        identity = 'yard_substrate_r32'
        roles = ['BreziExterior:natural-ground-color', 'BreziExterior:world-ground-normal', 'BreziExterior:metric-ground-uv']
        for role in roles:
            def mutate(g, role=role):next(n for n in g['nodes'] if n['role'] == role)['values']['code'] += '\n// unauthorized'
            with self.subTest(role=role):self.reject_graph(identity, mutate)
        self.reject_graph(identity, lambda g: next(n for n in g['nodes'] if n['class'] == 'MaterialExpressionTextureSample')['values'].update(sampler_type='<MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR: 6>'))

    def test_coverage_channel_dither_output_and_old_node_retention_are_strict(self):
        identity = 'yard_gravel_r32'
        self.reject_graph(identity, lambda g: next(n for n in g['nodes'] if n['role'].endswith(':coverage-r'))['values'].update(r=False,g=True))
        self.reject_graph(identity, lambda g: g['roots'].update(OPACITY_MASK=[m.TAG+identity+':temporal-dither','']))
        self.reject_graph(identity, lambda g: g['nodes'].pop(0))
        self.reject_graph(identity, lambda g: next(n for n in g['nodes'] if n['role'].endswith(':uv1'))['values'].update(coordinate_index=0))

    def test_shared_native_texture_encoding_normal_flip_alpha_and_provenance_cannot_drift(self):
        m.validate_shared_textures(self.textures, self.textures)
        for field in ['sourceEncoding', 'flip_green_channel', 'alphaCoverageThresholds']:
            actual = copy.deepcopy(self.textures);row = next(iter(actual.values()))
            if field == 'sourceEncoding':row['values'][field] = '<TextureSourceEncoding.TSE_S_RGB: 1>' if row['values'][field].endswith('NONE: 0>') else '<TextureSourceEncoding.TSE_NONE: 0>'
            elif field == 'flip_green_channel':row['values'][field] = not row['values'][field]
            else:row['values'][field] = [.5,0,0,0]
            with self.subTest(field=field), self.assertRaises(ValueError):m.validate_shared_textures(actual, self.textures)
        actual = copy.deepcopy(self.textures);next(iter(actual.values()))['metadata']['source_sha256'] = '0'*64
        with self.assertRaises(ValueError):m.validate_shared_textures(actual, self.textures)

    def test_other_pbr_roots_and_flags_cannot_change(self):
        self.reject_graph('yard_substrate_r32', lambda g: g['roots'].update(NORMAL=g['roots']['BASE_COLOR']))
        self.reject_graph('yard_substrate_r32', lambda g: g['flags'].update(tangent_space_normal=True))
        self.reject_graph('yard_gravel_r32', lambda g: g['roots'].update(WORLD_POSITION_OFFSET=g['roots']['BASE_COLOR']))

    def test_only_two_owned_material_names_and_no_extra_graph_schema(self):
        self.assertEqual(len({m.new_asset(k) for k in m.ROLES}), 2)
        self.assertTrue(all(m.new_asset(k).startswith(m.PREFIX+'/Materials/') for k in m.ROLES))
        with self.assertRaises(ValueError):m.new_asset('context_garden_soil')
        self.reject_graph('yard_gravel_r32', lambda g: g.update(nativeAppearanceAccepted=True))


if __name__ == '__main__':unittest.main(verbosity=2)
