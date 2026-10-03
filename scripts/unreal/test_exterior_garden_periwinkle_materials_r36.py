"""Meaningful CPU source/API fixtures; all created 'assets' here are mocks."""
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('own_r36_material_fixture', ROOT/'scripts/unreal/exterior-garden-periwinkle-materials-r36.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Properties:
    def __init__(self, **values):
        self.values = values
    def set_editor_property(self, key, value):
        self.values[key] = m._private().f32(value) if key in ('r','opacity_mask_clip_value') else value
    def get_editor_property(self, key):
        return self.values[key]


class MockNative:
    """Observed public call shapes, with no UE import/save/native geometry."""
    def __init__(self):
        self.assets = {}
        self.import_tasks = []
        self.created_graphs = 0
        self.saved = []
        def surface(group, names):
            return SimpleNamespace(**{n:group+'.'+n for n in names})
        self.MaterialShadingModel = surface('MaterialShadingModel',['MSM_TWO_SIDED_FOLIAGE'])
        self.MaterialUsage = surface('MaterialUsage',['MATUSAGE_INSTANCED_STATIC_MESHES'])
        self.TextureCompressionSettings = surface('TextureCompressionSettings',['TC_DEFAULT','TC_NORMALMAP','TC_MASKS'])
        self.TextureSourceEncoding = surface('TextureSourceEncoding',['TSE_SRGB','TSE_NONE'])
        self.MaterialSamplerType = surface('MaterialSamplerType',['SAMPLERTYPE_COLOR','SAMPLERTYPE_NORMAL','SAMPLERTYPE_MASKS'])
        self.BlendMode = surface('BlendMode',['BLEND_MASKED'])
        self.TextureAddress = surface('TextureAddress',['TA_WRAP'])
        self.TextureMipGenSettings = surface('TextureMipGenSettings',['TMGS_FROM_TEXTURE_GROUP'])
        self.TexturePowerOfTwoSetting = surface('TexturePowerOfTwoSetting',['NONE'])
        self.MaterialProperty = surface('MaterialProperty',['MP_'+n for n in ('BASE_COLOR','NORMAL','ROUGHNESS','METALLIC','SPECULAR','OPACITY_MASK','SUBSURFACE_COLOR')])
        self.Vector4 = lambda x,y,z,w: SimpleNamespace(x=x,y=y,z=z,w=w)
        self.AssetImportTask = type('AssetImportTask',(Properties,),{})
        self.MaterialFactoryNew = type('MaterialFactoryNew',(Properties,),{})
        class Asset(Properties):
            def __init__(self,path,**values):
                super().__init__(**values)
                self.path = path
                self.tags = {}
            def get_path_name(self):
                return self.path
        class Texture2D(Asset):
            def __init__(self,path):
                super().__init__(path,source_color_settings=Properties(encoding_override='TextureSourceEncoding.TSE_NONE'))
            def blueprint_get_size_x(self): return 2048
            def blueprint_get_size_y(self): return 2048
        class Material(Asset):
            def __init__(self,path):
                super().__init__(path)
                self.nodes = []
                self.roots = {}
                self.usage = set()
        self.Texture2D,self.Material = Texture2D,Material
        for name in ('TextureCoordinate','TextureSample','Constant','Multiply'):
            setattr(self,'MaterialExpression'+name,type('MaterialExpression'+name,(Properties,),{}))
        def object_path(path):
            return path if '.' in path.rsplit('/',1)[-1] else path+'.'+path.rsplit('/',1)[-1]
        def save(obj,only_if_dirty):
            self.saved.append(obj.path)
            return True
        self.EditorAssetLibrary = SimpleNamespace(
            does_asset_exist=lambda p:object_path(p) in self.assets,
            load_asset=lambda p:self.assets.get(object_path(p)),
            set_metadata_tag=lambda o,k,v:o.tags.__setitem__(k,v),
            get_metadata_tag=lambda o,k:o.tags.get(k,''),save_loaded_asset=save)
        def imports(tasks):
            for task in tasks:
                self.import_tasks.append(copy.deepcopy(task.values))
                path=task.values['destination_path']+'/'+task.values['destination_name']
                self.assets[object_path(path)] = Texture2D(object_path(path))
        def create(name,path,cls,factory):
            self.created_graphs += 1
            value=cls(object_path(path+'/'+name));self.assets[value.path]=value
            return value
        self.AssetToolsHelpers = SimpleNamespace(get_asset_tools=lambda:SimpleNamespace(import_asset_tasks=imports,create_asset=create))
        def expression(material,cls,x,y):
            n=cls();n.inputs={};material.nodes.append(n)
            return n
        def connect(a,out,b,input_):
            b.inputs[input_]=(a,out)
            return True
        def root(n,out,prop):
            material=next(v for v in self.assets.values() if isinstance(v,Material))
            material.roots[prop.rsplit('MP_',1)[1]]=(n,out)
            return True
        self.MaterialEditingLibrary = SimpleNamespace(create_material_expression=expression,
            connect_material_expressions=connect,connect_material_property=root,
            recompile_material=lambda material:[],set_base_material_usage=lambda o,v,b:o.usage.add(v),
            has_material_usage=lambda o,v:v in o.usage)

    def graph(self,u,material):
        rows=[]
        for node in material.nodes:
            inputs=[]
            if type(node).__name__=='MaterialExpressionTextureSample':
                ports=['UVs','Tex','Apply View MipBias']
            elif type(node).__name__=='MaterialExpressionMultiply':ports=['A','B']
            else:ports=[]
            for port in ports:
                n,out=node.inputs.get(port,(None,None))
                inputs.append([port,n.values['desc'] if n else None,out])
            values={k:v.get_path_name() if k=='texture' else v for k,v in node.values.items() if k!='desc'}
            rows.append({'class':type(node).__name__,'role':node.values['desc'],'values':values,'inputs':inputs})
        roots={k:None for k in ('BASE_COLOR','NORMAL','ROUGHNESS','METALLIC','SPECULAR','OPACITY_MASK','SUBSURFACE_COLOR','OPACITY','AMBIENT_OCCLUSION','WORLD_POSITION_OFFSET')}
        roots.update({k:[v[0].values['desc'],v[1]]for k,v in material.roots.items()})
        return {'nodes':rows,'roots':roots}


class MaterialSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe=json.loads(m.RECIPE.read_text())

    def build(self):
        u=MockNative();obj,report=m.build_materials(u,copy.deepcopy(self.recipe),u.graph)
        return u,obj,report

    def test_original_five_source_pngs_and_role_census(self):
        m.validate_recipe(self.recipe)
        self.assertEqual([m.png_header(m.checked(p))['sourceBits']for p in self.recipe['maps'].values()],[16]*5)
        self.assertEqual(len(m.package_assets(self.recipe)),6)
        self.assertEqual(self.recipe['sourceOriginalAlphaMode'],'BLEND')
        self.assertFalse(self.recipe['sourceOpticalModelExactlyReproduced'])

    def test_role_swaps_missing_opacity_foreign_recipe_rejected(self):
        changed=copy.deepcopy(self.recipe);changed['maps']['opacity'],changed['maps']['roughness']=changed['maps']['roughness'],changed['maps']['opacity']
        cases=[changed]
        for key,value in [('sourceOriginalAlphaMode','MASK'),('subsurfaceCalibration',.24),('prefix','/Game/Foreign'),('nativeAppearanceAccepted',True)]:
            changed=copy.deepcopy(self.recipe);changed[key]=value;cases.append(changed)
        changed=copy.deepcopy(self.recipe);del changed['maps']['opacity'];cases.append(changed)
        for changed in cases:
            with self.subTest(changed=changed.get('subsurfaceCalibration')),self.assertRaises(RuntimeError):m.validate_recipe(changed)

    def test_cpu_mock_full_build_and_saved_readback_contract(self):
        u,obj,report=self.build()
        self.assertIs(m.verify_materials(u,report,self.recipe,u.graph),obj)
        self.assertEqual(len(u.import_tasks),5);self.assertEqual(u.created_graphs,1)
        self.assertEqual(len(report['graph']['nodes']),10)
        self.assertEqual(len(report['newPackageAssets']),6)
        self.assertTrue(all(t['automated'] and not t['replace_existing'] and not t['save']for t in u.import_tasks))
        self.assertFalse(report['nativeImportedPixelsDecoded'])

    def test_alpha_a_diffuse_alpha_and_roughness_g_rejected(self):
        u,obj,r=self.build()
        for root,channel in [('OPACITY_MASK','A'),('ROUGHNESS','G')]:
            bad=copy.deepcopy(r['graph']);bad['roots'][root][1]=channel
            with self.subTest(root=root),self.assertRaises(RuntimeError):m.check_graph(bad,{k:v['asset']for k,v in r['textures'].items()})
        bad=copy.deepcopy(r['graph']);bad['roots']['OPACITY_MASK']=[m.TAG+m.KEY+':albedo','A']
        with self.assertRaises(RuntimeError):m.check_graph(bad,{k:v['asset']for k,v in r['textures'].items()})

    def test_sss_albedo_substitution_and_strength_change_rejected(self):
        u,obj,r=self.build();bad=copy.deepcopy(r['graph']);n=next(n for n in bad['nodes']if n['role'].endswith(':transmission'));n['inputs'][0][1]=m.TAG+m.KEY+':albedo'
        with self.assertRaises(RuntimeError):m.check_graph(bad,{k:v['asset']for k,v in r['textures'].items()})
        bad=copy.deepcopy(r['graph']);n=next(n for n in bad['nodes']if n['role'].endswith(':strength'));n['values']['r']=m._private().f32(.24)
        with self.assertRaises(RuntimeError):m.check_graph(bad,{k:v['asset']for k,v in r['textures'].items()})

    def test_missing_mask_extra_node_uv1_ao_wpo_rejected(self):
        u,obj,r=self.build()
        variants=[]
        bad=copy.deepcopy(r['graph']);bad['nodes']=[n for n in bad['nodes']if not n['role'].endswith(':opacity')];variants.append(bad)
        bad=copy.deepcopy(r['graph']);bad['nodes'].append(copy.deepcopy(bad['nodes'][0]));variants.append(bad)
        bad=copy.deepcopy(r['graph']);next(n for n in bad['nodes']if n['role'].endswith(':uv'))['values']['coordinate_index']=1;variants.append(bad)
        for root in ['AMBIENT_OCCLUSION','WORLD_POSITION_OFFSET']:
            bad=copy.deepcopy(r['graph']);bad['roots'][root]=[m.TAG+m.KEY+':roughness','R'];variants.append(bad)
        for bad in variants:
            with self.assertRaises(RuntimeError):m.check_graph(bad,{k:v['asset']for k,v in r['textures'].items()})

    def test_color_and_data_encoding_and_gl_sign_policies(self):
        u,obj,r=self.build()
        for role,row in r['textures'].items():
            m.check_texture_policy(u,row['snapshot'],role)
            self.assertEqual(row['snapshot']['srgb'],role in ('albedo','translucency'))
            self.assertEqual(row['snapshot']['flip_green_channel'],role=='normalGl')
        for role,key,value in [('normalGl','flip_green_channel',False),('opacity','srgb',True),('roughness','sourceEncoding','TextureSourceEncoding.TSE_SRGB'),('translucency','srgb',False),('opacity','alphaCoverageThresholds',[0.,.5,0.,0.])]:
            bad=copy.deepcopy(r['textures'][role]['snapshot']);bad[key]=value
            with self.subTest(role=role,key=key),self.assertRaises(RuntimeError):m.check_texture_policy(u,bad,role)

    def test_known_enum_prefix_and_ambiguity_missing_reject_before_writes(self):
        u=MockNative();proof=m.preflight_enums(u)
        self.assertIn('MSM_TWO_SIDED_FOLIAGE',proof['MaterialShadingModel.TWOSIDEDFOLIAGE'])
        u.MaterialShadingModel.TWO_SIDED_FOLIAGE='MaterialShadingModel.TWO_SIDED_FOLIAGE'
        with self.assertRaises(RuntimeError):m.preflight_enums(u)
        u=MockNative();del u.MaterialSamplerType.SAMPLERTYPE_NORMAL
        with self.assertRaises(RuntimeError):m.build_materials(u,self.recipe,u.graph)
        self.assertEqual(u.assets,{})
        self.assertEqual(u.import_tasks,[])
        self.assertEqual(u.created_graphs,0)

    def test_saved_policy_and_source_metadata_mutations_reject(self):
        for target in ['material-policy','texture-policy','source-metadata']:
            u,obj,r=self.build()
            if target=='material-policy':obj.set_editor_property('opacity_mask_clip_value',.4)
            elif target=='texture-policy':u.assets[r['textures']['normalGl']['asset']].set_editor_property('flip_green_channel',False)
            else:u.assets[r['textures']['albedo']['asset']].tags['source_sha256']='0'*64
            with self.subTest(target=target),self.assertRaises(RuntimeError):m.verify_materials(u,r,self.recipe,u.graph)

    def test_foreign_map_identity_and_native_acceptance_claim_rejected(self):
        u,obj,r=self.build();bad=copy.deepcopy(r);bad['textures']['opacity']['asset']='/Game/Old.T_Old'
        with self.assertRaises(RuntimeError):m.verify_materials(u,bad,self.recipe,u.graph)
        for key in ['physicalOpticalCalibrationAccepted','nativeAppearanceAccepted','nativeImportedPixelsDecoded','materialPackagesIndependentlyUnloaded']:
            bad=copy.deepcopy(r);bad[key]=True
            with self.subTest(key=key),self.assertRaises(RuntimeError):m.verify_materials(u,bad,self.recipe,u.graph)

    def test_frozen_api_delegate_owner_unchanged(self):
        d=m._private()
        self.assertEqual(d.OWNER,'scripts/unreal/exterior-garden-fern-materials-r25.py')
        self.assertEqual(d.PREFIX,'/Game/Brezi/GardenFern20261002R25')
        self.assertEqual(m.sha(m.DELEGATE),m.DELEGATE_SHA)


if __name__ == '__main__':
    unittest.main(verbosity=2)
