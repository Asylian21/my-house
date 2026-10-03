"""Opt-in graph composition, source gates and saved-condition tamper detection."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value

T = module('transition_existing_material_test_shim', Path(__file__).with_name('test_exterior_materials.py'))
M = T.M
H = module('transition_material_helper', Path(__file__).with_name('exterior-neighborhood-transition-materials.py'))
KEY = H.KEY
OPTIONS = {'vegetation_manifest': ROOT/'output/unreal/exterior-assets-shape-20261001-r1/material-manifest.json',
           'ortho_manifest': ROOT/'output/unreal/exterior-ortho-20260927-r2/orthophoto-manifest.json',
           'field_macro_manifest': ROOT/'output/unreal/exterior-field-macro-20260927-r3/field-macro-manifest.json',
           'projection_manifest': ROOT/'output/unreal/exterior-ortho-projection-20260930-r2/ortho-projection-manifest.json'}


class TransitionMaterialsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # UE5.8 Texture2D has no Python-exposed CompressionNone property.
        # Keep this native limitation active through construction and readback.
        def native_set(texture, name, value):
            if name == 'compression_none':raise RuntimeError('Texture2D property not exposed: compression_none')
            return T.Node.set_editor_property(texture, name, value)
        def native_get(texture, name):
            if name == 'compression_none':raise RuntimeError('Texture2D property not exposed: compression_none')
            return T.Node.get_editor_property(texture, name)
        cls.exposure_guards=[patch.object(T.Texture,'set_editor_property',native_set),
                             patch.object(T.Texture,'get_editor_property',native_get)]
        for guard in cls.exposure_guards:guard.start()
        cls.base_u = T.fake_unreal()
        cls.base_m, cls.base_r = M.build_materials(**OPTIONS, unreal_module=cls.base_u)
        cls.enabled_u = T.fake_unreal()
        cls.enabled_m, cls.enabled_r = M.build_materials(**OPTIONS, unreal_module=cls.enabled_u, transition=H.PLAN)
        cls.prepared = H.prepare_transition(H.PLAN)

    @classmethod
    def tearDownClass(cls):
        for guard in cls.exposure_guards:guard.stop()

    def saved(self):
        u = copy.deepcopy(self.enabled_u)
        return u, copy.deepcopy(self.enabled_r)

    def nodes(self, material):
        return {n.props['desc'].removeprefix(M.TAG): n for n in material.nodes}

    def test_optional_actual_library_adds_one_material_texture_preserves_forty_graphs(self):
        self.assertEqual((len(self.base_m), len(self.base_r['textures'])), (40, 73))
        self.assertEqual((len(self.enabled_m), len(self.enabled_r['textures'])), (41, 74))
        self.assertEqual({k:v for k,v in self.enabled_r['materials'].items() if k != KEY}, self.base_r['materials'])
        self.assertEqual({k:v for k,v in self.enabled_r['textures'].items() if v['role'] != 'ground_condition'}, self.base_r['textures'])
        self.assertEqual(M.verify_materials(self.enabled_r, unreal_module=self.enabled_u)['materials'], 41)
        recipe = self.enabled_r['materials'][KEY]['recipe']; source = self.base_r['materials']['context_meadow']['recipe']
        for field in ('maps','groundCover','tileCm','yawDegrees','macroStrength','fieldMacro','groundOrthophoto','projectionMask'):
            self.assertEqual(recipe[field], source[field])
        self.assertEqual(len(self.enabled_r['materials'][KEY]['graph']['nodes']), 114)
        self.assertEqual(self.enabled_r['neighborhoodTransition']['originalMaterialsUnchanged'], 40)

    def test_new_graph_rewires_only_four_ground_responses_and_retains_ortho_roots(self):
        n=self.nodes(self.enabled_m[KEY]);original=self.nodes(self.enabled_m['context_meadow'])
        for role in ('albedo','normal','roughness'):
            self.assertEqual(n['groundcover-'+role].inputs['Amount'], (n['continuous-ground-cover'], ''))
        self.assertEqual(n['natural-ground-color'].inputs['Tint'], (n['continuous-ground-tint'], ''))
        self.assertEqual(n['natural-ground-color'].inputs['AlbedoScale'], (n['continuous-ground-albedo-response'], ''))
        self.assertEqual(n['world-ground-normal'].inputs['Strength'], (n['continuous-ground-normal-strength'], ''))
        self.assertEqual(n['continuous-ground-tint'].inputs['Meadow'], (n['linear-tint'], ''))
        for role in ('field-macro-basecolor','ground-ortho-protected-field-weight','ground-ortho-camera-distance'):
            self.assertEqual(n[role].props['code'], original[role].props['code'])
        self.assertEqual(n['continuous-condition-world-uv'].inputs['Position'], (n['world-position'], ''))
        self.assertEqual(n['ground_condition-world-condition'].inputs['UVs'], (n['continuous-condition-world-uv'], ''))

    def test_authored_texture_has_distinct_linear_uncompressed_ordinary_mip_identity(self):
        key,entry=next((k,v) for k,v in self.enabled_r['textures'].items() if v['role']=='ground_condition')
        self.assertTrue(key.startswith('ground_condition_'));self.assertNotIn('ortho',key)
        self.assertEqual(entry['sourceLicense'],'LicenseRef-Project-Authored')
        self.assertEqual(entry['sourcePage'], str(ROOT/'scripts/unreal/exterior-neighborhood-transition-study.py'))
        tex=self.enabled_u.EditorAssetLibrary.load_asset(entry['asset'])
        for field,value in {'srgb':False,'compression_settings':'RGBA8',
                            'address_x':'CLAMP','address_y':'CLAMP','lod_bias':0,'mip_gen_settings':'FROM_GROUP',
                            'do_scale_mips_for_alpha_coverage':False,'never_stream':True}.items():
            self.assertEqual(tex.props[field],value)
        self.assertNotIn('compression_none', tex.props)
        condition=self.enabled_r['neighborhoodTransition']['condition']
        self.assertNotIn('compressionNone',condition)
        self.assertFalse(condition['compressionNonePropertyExposed'])
        self.assertEqual(condition['uncompressedFormatBasis'],'TC_VectorDisplacementmap -> NameBGRA8 (UE5.8 native source)')
        with self.assertRaisesRegex(RuntimeError,'not exposed'):tex.set_editor_property('compression_none',True)
        with self.assertRaisesRegex(RuntimeError,'not exposed'):tex.get_editor_property('compression_none')
        self.assertEqual(tex.props['source_color_settings'].props['encoding_override'],'ENC_NONE')
        node=self.nodes(self.enabled_m[KEY])['ground_condition-world-condition']
        self.assertEqual(node.props['sampler_type'],'LINEAR_COLOR')
        self.assertEqual(node.props['mip_value_mode'],'DEFAULT');self.assertFalse(node.props['automatic_view_mip_bias'])
        self.assertEqual(entry['sourceEncodingReadback'],'TSE_NONE')

    def test_saved_condition_flags_source_encoding_role_and_sampler_tamper_rejected(self):
        for field,value in [('srgb',True),('compression_settings','DEFAULT'),('address_x','WRAP'),('mip_gen_settings','NO_MIPMAPS')]:
            with self.subTest(field=field):
                u,r=self.saved();entry=next(v for v in r['textures'].values() if v['role']=='ground_condition')
                u.EditorAssetLibrary.load_asset(entry['asset']).props[field]=value
                with self.assertRaises(RuntimeError):M.verify_materials(r,unreal_module=u)
        u,r=self.saved();entry=next(v for v in r['textures'].values() if v['role']=='ground_condition')
        u.EditorAssetLibrary.load_asset(entry['asset']).props['source_color_settings'].props['encoding_override']='ENC_SRGB'
        with self.assertRaises(RuntimeError):M.verify_materials(r,unreal_module=u)
        u,r=self.saved();entry=next(v for v in r['textures'].values() if v['role']=='ground_condition');entry['role']='ortho_projection'
        with self.assertRaises(RuntimeError):M.verify_materials(r,unreal_module=u)
        u,r=self.saved();m=u.EditorAssetLibrary.load_asset(r['materials'][KEY]['asset'])
        self.nodes(m)['ground_condition-world-condition'].props['automatic_view_mip_bias']=True
        with self.assertRaises(RuntimeError):M.verify_materials(r,unreal_module=u)

    def test_exact_plan_proof_helper_and_native_receipt_pins_rejected_before_writes(self):
        for field in ('PLAN_SHA','PROOF_SHA','NATIVE_SHA','RECEIPT_SHA'):
            with self.subTest(field=field), patch.object(H,field,'0'*64):
                with self.assertRaises(RuntimeError):H.prepare_transition(H.PLAN)
        with tempfile.TemporaryDirectory() as folder:
            duplicate=Path(folder)/'plan.json';duplicate.write_bytes(H.PLAN.read_bytes())
            with self.assertRaises(RuntimeError):H.prepare_transition(duplicate)
        u=T.fake_unreal()
        with self.assertRaises(RuntimeError):M.build_materials(**OPTIONS,unreal_module=u,transition=H.PROOF)
        self.assertEqual(u.EditorAssetLibrary.values,{})

    def test_missing_changed_geographic_recipe_and_existing_alias_rejected(self):
        for field in ('maps','groundCover','fieldMacro','groundOrthophoto','projectionMask'):
            with self.subTest(field=field):
                records=copy.deepcopy(self.base_r['materials']);records['context_meadow']['recipe'].pop(field)
                writer=M.Writer(self.base_u,M.PREFIX)
                writer.texture_report=self.base_r['textures']
                with self.assertRaises(RuntimeError):H.append_transition(writer,self.base_m.copy(),records,self.prepared,
                    {'graph_snapshot':M.graph_snapshot,'digest':M.digest,'OWNER':M.OWNER,'TAG':M.TAG})
        writer=M.Writer(self.base_u,M.PREFIX);writer.texture_report=self.base_r['textures']
        records=copy.deepcopy(self.base_r['materials']);materials=self.base_m.copy();materials[KEY]=materials['context_meadow']
        with self.assertRaises(RuntimeError):H.append_transition(writer,materials,records,self.prepared,
            {'graph_snapshot':M.graph_snapshot,'digest':M.digest,'OWNER':M.OWNER,'TAG':M.TAG})
        with self.assertRaises(RuntimeError):M.Writer(T.fake_unreal(),'/Game/Foreign')

    def test_response_bounds_and_world_condition_continuity_across_actual_parcel_edge(self):
        for c in (-100,0,.15,.3,.5,.85,1,100):
            response=H.response(c)
            self.assertTrue(.3<=response['coverAmount']<=.78)
            self.assertTrue(.74<=response['albedoScale']<=.78)
            self.assertTrue(.65<=response['normalStrength']<=.7)
        with self.assertRaises(RuntimeError):H.response(float('nan'))
        native=H._native();x=5698.608659454598;y=16232.6
        left=H.response(native._condition(x-.01,y));right=H.response(native._condition(x+.01,y))
        self.assertLess(abs(left['coverAmount']-right['coverAmount']),1e-5)
        self.assertLess(max(abs(a-b) for a,b in zip(left['tint'],right['tint'])),1e-5)
        self.assertEqual(self.prepared['conditionValidation']['dimensions'],[1024,1024])
        self.assertTrue(self.prepared['conditionValidation']['all1048576ConditionPixelsVerified'])

    def test_saved_four_response_graph_changes_rejected_and_old_materials_untouched(self):
        for role in ('continuous-ground-cover','continuous-ground-tint','continuous-ground-albedo-response','continuous-ground-normal-strength'):
            with self.subTest(role=role):
                u,r=self.saved();m=u.EditorAssetLibrary.load_asset(r['materials'][KEY]['asset'])
                self.nodes(m)[role].props['code']='return 1;'
                with self.assertRaises(RuntimeError):M.verify_materials(r,unreal_module=u)
        self.assertEqual(M.verify_materials(self.base_r,unreal_module=self.base_u)['materials'],40)


if __name__ == '__main__': unittest.main()
