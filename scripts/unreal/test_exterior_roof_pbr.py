"""CPU source/receipt fixtures only; no native/GPU/material compilation proof."""
import copy
import importlib.util
from pathlib import Path
import sys
import types
import unittest
ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
def load(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=load('r23_test_guard','exterior-roof-pbr-guards.py');m=load('r23_test_materials','exterior-roof-pbr-materials.py')
class RoofSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.bundle=g.load_source()
    def test_actual_frozen_source_controls_and_explicit_metric_limit(self):
        b=self.bundle;self.assertEqual(len(b['baseSaved']),5338);self.assertEqual(len(b['targets']),4)
        self.assertEqual(b['audit']['sourceRoofTriangles'],332);self.assertEqual(b['audit']['existingMaterialGraphs'],51);self.assertEqual(b['audit']['existingTextureObjects'],77)
        self.assertGreater(b['sourceMeasurement']['maximumRelativeMetricEdgeError'],1e-5);self.assertFalse(b['audit']['nativeGeometryReadbackAvailable']);self.assertFalse(b['audit']['nativeAppearanceAccepted'])
    def test_exact_four_component_counterfactual_preserves_every_other_field(self):
        b=self.bundle;after,changes=g.expected_witness(b['baseSaved'],b['targets']);self.assertEqual(len(after),5338);self.assertEqual(len(changes),4)
        touched={r['actor']for r in b['targets']}
        for path,row in b['baseSaved'].items():
            if path not in touched:self.assertEqual(after[path],row)
        changed=copy.deepcopy(b['targets']);changed[0]['slot']=1
        with self.assertRaises(RuntimeError):g.expected_witness(b['baseSaved'],changed)
        changed=copy.deepcopy(b['baseSaved']);changed[b['targets'][0]['actor']]['components'][0]['navigation']=True
        with self.assertRaises(RuntimeError):g.expected_witness(changed,b['targets'])
    def test_rehashed_recipe_fixture_cannot_change_physical_period_or_source_acceptance(self):
        for change in ({'proposedUVMultiplier':[1.,1.]},{'nativeAppearanceAccepted':True},{'sourcePixelsEdited':True},{'newNativeMeshObjectsProposed':1}):
            recipe=copy.deepcopy(self.bundle['recipe']);recipe.update(change)
            with self.assertRaises(RuntimeError):g.validate_recipe(recipe)
    def test_exact_four_asset_packages_reject_geometry_extra_and_old_texture_change(self):
        before={str(i)+'.uasset':dict(sha256='a'*64,bytes=1)for i in range(4026)};before['Brezi/Maps/Brezi.umap']=dict(sha256='b'*64,bytes=1)
        after=copy.deepcopy(before);after['Brezi/Maps/Brezi.umap']=dict(sha256='c'*64,bytes=2)
        textures=[g.PREFIX+'/Textures/T_'+role+'.T_'+role for role in ('albedo','normal','roughness')]
        for asset in [g.MATERIAL,*textures]:after[asset.split('.')[0].removeprefix('/Game/')+'.uasset']=dict(sha256='d'*64,bytes=1)
        self.assertEqual(g.validate_content_delta(before,after,textures)['newUassetPackages'],4)
        malformed=copy.deepcopy(after);malformed['Brezi/RoofPbr20261002R23/Geometry/Extra.uasset']=dict(sha256='d'*64,bytes=1)
        with self.assertRaises(RuntimeError):g.validate_content_delta(before,malformed,textures)
        malformed=copy.deepcopy(after);malformed['0.uasset']['sha256']='e'*64
        with self.assertRaises(RuntimeError):g.validate_content_delta(before,malformed,textures)
    def test_six_node_map_fixture_rejects_tint_normal_strength_opacity_and_uv_drift(self):
        textures={r:'/Game/T_'+r+'.T_'+r for r in ('albedo','normal','roughness')}
        roots={k:None for k in ['BASE_COLOR','NORMAL','ROUGHNESS','METALLIC','SPECULAR','OPACITY','OPACITY_MASK','WORLD_POSITION_OFFSET']}
        roots.update(BASE_COLOR=[m.TAG+'albedo','RGB'],NORMAL=[m.TAG+'normal','RGB'],ROUGHNESS=[m.TAG+'roughness','R'],METALLIC=[m.TAG+'metallic-zero',''],SPECULAR=[m.TAG+'dielectric-specular',''])
        nodes=[dict(role=m.TAG+'metric-uv0',**{'class':'MaterialExpressionTextureCoordinate'},values=dict(coordinate_index=0,u_tiling=.5,v_tiling=.5),inputs=[])]
        for role,asset in textures.items():nodes.append(dict(role=m.TAG+role,**{'class':'MaterialExpressionTextureSample'},values=dict(texture=asset,sampler_type='<MaterialSamplerType.SAMPLERTYPE_'+('NORMAL'if role=='normal'else'MASKS'if role=='roughness'else'COLOR')+': 0>'),inputs=[['UVs',m.TAG+'metric-uv0',''],['Tex',None,None],['Apply View MipBias',None,None]]))
        for role,value in [('metallic-zero',0.),('dielectric-specular',.5)]:nodes.append(dict(role=m.TAG+role,**{'class':'MaterialExpressionConstant'},values={'r':value},inputs=[]))
        graph=dict(roots=roots,nodes=nodes,flags=dict(blend_mode='<BlendMode.BLEND_OPAQUE: 0>',shading_model='<MaterialShadingModel.MSM_DEFAULT_LIT: 1>',two_sided=False,tangent_space_normal=True,use_material_attributes=False));m.verify_graph(graph,textures)
        malformed=copy.deepcopy(graph);malformed['roots']['WORLD_POSITION_OFFSET']=[m.TAG+'albedo','RGB']
        with self.assertRaises(RuntimeError):m.verify_graph(malformed,textures)
        malformed=copy.deepcopy(graph);malformed['nodes'][0]['values']['u_tiling']=1.
        with self.assertRaises(RuntimeError):m.verify_graph(malformed,textures)
    def test_native_enum_prefix_fixture_is_exact_and_rejects_ambiguous_symbols(self):
        u=types.SimpleNamespace(MaterialShadingModel=types.SimpleNamespace(MSM_DEFAULT_LIT=1),MaterialUsage=types.SimpleNamespace(MATUSAGE_INSTANCED_STATIC_MESHES=2))
        self.assertEqual(m.native_enum(u,'MaterialShadingModel','DEFAULTLIT'),1);self.assertEqual(m.native_enum(u,'MaterialUsage','INSTANCEDSTATICMESHES'),2)
        u.MaterialShadingModel.ALIAS_MSM_DEFAULT_LIT=3;self.assertEqual(m.native_enum(u,'MaterialShadingModel','DEFAULTLIT'),1)
        u.MaterialShadingModel.DEFAULT_LIT=4
        with self.assertRaises(RuntimeError):m.native_enum(u,'MaterialShadingModel','DEFAULTLIT')
if __name__=='__main__':unittest.main(verbosity=2)
