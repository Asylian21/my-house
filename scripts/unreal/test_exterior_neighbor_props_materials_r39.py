"""Owned CPU-only changed-contract fixtures; every created asset is a mock."""
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('own_r39_material_fixture',ROOT/'scripts/unreal/exterior-neighbor-props-materials-r39.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class Properties:
    def __init__(self, **values):
        self.values = values
    def set_editor_property(self, key, value):
        self.values[key] = m.api().f32(value) if key in ('r','opacity_mask_clip_value') else value
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
        self.MaterialShadingModel = surface('MaterialShadingModel',['MSM_DEFAULT_LIT'])
        self.MaterialUsage = surface('MaterialUsage',['MATUSAGE_INSTANCED_STATIC_MESHES'])
        self.TextureCompressionSettings = surface('TextureCompressionSettings',['TC_DEFAULT','TC_NORMALMAP','TC_MASKS'])
        self.TextureSourceEncoding = surface('TextureSourceEncoding',['TSE_SRGB','TSE_NONE'])
        self.MaterialSamplerType = surface('MaterialSamplerType',['SAMPLERTYPE_COLOR','SAMPLERTYPE_NORMAL','SAMPLERTYPE_MASKS'])
        self.BlendMode = surface('BlendMode',['BLEND_OPAQUE'])
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
                super().__init__(path,opacity_mask_clip_value=m.api().f32(.333))
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
            n=cls();n.inputs={};n.material=material;material.nodes.append(n)
            return n
        def connect(a,out,b,input_):
            b.inputs[input_]=(a,out)
            return True
        def root(n,out,prop):
            material=n.material
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


class MaterialContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        proposal=m.c.read(m.c.SOURCE);receipt=m.c.read(m.c.checked(proposal['originalDownloadReceipt']))
        cls.source={'proposal':proposal,'proposalPin':m.c.pin(m.c.SOURCE),'receipt':receipt,
          'recipes':{k:m.c.material_recipe(proposal['models'][k],receipt)for k in m.c.MODEL_IDS}}
        cls.binding={'schema':'fixture-only-authenticated-binding','selectedBaseSha256':'7'*64}
    def packet(self):
        return {'source':copy.deepcopy(self.source),'base':{'fixtureOnly':True},'binding':copy.deepcopy(self.binding)}
    def build(self):
        packet=self.packet();u=MockNative()
        original=m.binding_guard
        def require(b):m.c.require(b==self.binding,'Fixture exact native binding required')
        m.binding_guard=lambda:SimpleNamespace(require_native_binding=require)
        try:objects,report=m.build_materials(u,packet,self.binding,u.graph)
        finally:m.binding_guard=original
        return u,packet,objects,report
    def verify(self,u,packet,report):
        original=m.binding_guard;m.binding_guard=lambda:SimpleNamespace(require_native_binding=lambda b:m.c.require(b==self.binding,'Fixture exact binding required'))
        try:return m.verify_materials(u,packet,self.binding,report,u.graph)
        finally:m.binding_guard=original
    def test_binding_and_packet_fail_before_uobject_access(self):
        u=MockNative();original=m.binding_guard
        m.binding_guard=lambda:SimpleNamespace(require_native_binding=lambda b:m.c.require(b==self.binding,'Unselected native base'))
        try:
            for binding,packet in [({'selectedBaseSha256':'0'*64},self.packet()),(self.binding,{'source':self.source,'base':{}}),
              (self.binding,{**self.packet(),'binding':{'wrong':True}})]:
                with self.subTest(binding=binding),self.assertRaises(RuntimeError):m.build_materials(u,packet,binding,u.graph)
        finally:m.binding_guard=original
        self.assertEqual(u.assets,{});self.assertEqual(u.import_tasks,[]);self.assertEqual(u.created_graphs,0)
    def test_actual_original_three_recipes_eleven_pngs_and_limits(self):
        self.assertEqual(len(m.validate_recipes(self.source)),14)
        self.assertEqual(sum(len(r['maps'])for r in self.source['recipes'].values()),11)
        self.assertEqual([m.png_header(p)['sourceBits']for r in self.source['recipes'].values()for p in r['maps'].values()],[16]*11)
        self.assertFalse(self.source['recipes']['watering_can_metal_01']['sourceOpticalModelExactlyReproduced'])
        self.assertEqual(self.source['recipes']['watering_can_metal_01']['ueSpecular'],0.)
    def test_three_mock_graphs_roundtrip_without_save_or_pixel_claim(self):
        u,packet,objects,r=self.build();self.assertEqual(self.verify(u,packet,r),objects)
        self.assertEqual((u.created_graphs,len(u.import_tasks),len(r['newPackageAssets'])),(3,11,14))
        self.assertTrue(all(len(row['graph']['nodes'])==6 for row in r['materials'].values()))
        self.assertTrue(all(row['instancedStaticMeshUsage'] for row in r['materials'].values()))
        self.assertTrue(all(t['automated'] and not t['replace_existing'] and not t['save']for t in u.import_tasks))
        self.assertEqual(u.saved,[]);self.assertEqual(r['nativeBinding'],self.binding)
        self.assertFalse(r['nativeSourceTexelsDecoded']);self.assertFalse(r['sourceOpticalModelExactlyReproduced'])
    def test_recipe_role_swap_wrong_factor_and_foreign_uv_rejected(self):
        cases=[];bad=copy.deepcopy(self.source);row=bad['recipes']['garden_hose_wall_mounted_01'];row['maps']['normalGL'],row['maps']['roughness']=row['maps']['roughness'],row['maps']['normalGL'];cases.append(bad)
        for model,key,value in [('planter_pot_clay','metallicFactor',1),('watering_can_metal_01','ueSpecular',.5),('garden_hose_wall_mounted_01','uvChannel',1),('planter_pot_clay','ambientOcclusionRoot','roughness')]:
            bad=copy.deepcopy(self.source);bad['recipes'][model][key]=value;cases.append(bad)
        for bad in cases:
            with self.assertRaises(RuntimeError):m.validate_recipes(bad)
    def test_graph_channels_uv0_ao_wpo_and_missing_map_rejected(self):
        u,p,o,r=self.build();key='garden_hose_wall_mounted_01';row=r['materials'][key];recipe=self.source['recipes'][key];paths={k:v['asset']for k,v in row['textures'].items()};variants=[]
        for root,channel in [('ROUGHNESS','G'),('METALLIC','B')]:
            g=copy.deepcopy(row['graph']);g['roots'][root][1]=channel;variants.append(g)
        g=copy.deepcopy(row['graph']);next(n for n in g['nodes']if n['role'].endswith(':uv'))['values']['coordinate_index']=1;variants.append(g)
        for root in ['AMBIENT_OCCLUSION','WORLD_POSITION_OFFSET','OPACITY']:
            g=copy.deepcopy(row['graph']);g['roots'][root]=[m.c.TAG+key+':roughness','R'];variants.append(g)
        g=copy.deepcopy(row['graph']);g['nodes']=[n for n in g['nodes']if not n['role'].endswith(':metallic')];variants.append(g)
        for g in variants:
            with self.assertRaises(RuntimeError):m.validate_graph(g,recipe,paths)
    def test_material_map_policy_and_metadata_mutations_rejected(self):
        for kind in ['material','normal-sign','data-srgb','metadata','hism-usage']:
            u,p,o,r=self.build();key='garden_hose_wall_mounted_01';row=r['materials'][key]
            if kind=='material':o[key].set_editor_property('two_sided',False)
            elif kind=='normal-sign':u.assets[row['textures']['normalGL']['asset']].set_editor_property('flip_green_channel',False)
            elif kind=='data-srgb':u.assets[row['textures']['roughness']['asset']].set_editor_property('srgb',True)
            elif kind=='hism-usage':o[key].usage.clear()
            else:u.assets[row['textures']['albedo']['asset']].tags['source_sha256']='0'*64
            with self.subTest(kind=kind),self.assertRaises(RuntimeError):self.verify(u,p,r)
    def test_source_binding_and_evidence_flags_cannot_be_promoted(self):
        u,p,o,r=self.build();variants=[]
        for k in ['nativeSourceTexelsDecoded','nativeGpuPixelFormatVerified','nativeNormalTangentReadbackAvailable','materialPackagesIndependentlyUnloaded','sourceOpticalModelExactlyReproduced','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted']:
            bad=copy.deepcopy(r);bad[k]=True;variants.append(bad)
        bad=copy.deepcopy(r);bad['nativeBinding']={'wrong':True};variants.append(bad)
        bad=copy.deepcopy(r);bad['sourceRecipeContract']['sha256']='0'*64;variants.append(bad)
        for bad in variants:
            with self.assertRaises(RuntimeError):self.verify(u,p,bad)
    def test_enum_preflight_missing_sampler_rejects_before_write(self):
        u=MockNative();proof=m.preflight_enums(u);self.assertIn('MSM_DEFAULT_LIT',proof['MaterialShadingModel.DEFAULTLIT'])
        del u.MaterialSamplerType.SAMPLERTYPE_NORMAL
        with self.assertRaises(RuntimeError):m._build_kernel(u,self.source,u.graph)
        self.assertEqual(u.assets,{});self.assertEqual(u.import_tasks,[])
    def test_private_frozen_delegate_identity_unmodified(self):
        self.assertEqual(m.c.OWNER,'scripts/unreal/exterior-neighbor-props-contract-r39-draft.py')
        self.assertEqual(m.api().OWNER,'scripts/unreal/exterior-garden-fern-materials-r25.py')
        self.assertEqual(m.c.sha(m.DELEGATE),m.DELEGATE_SHA)
        self.assertEqual(m.c.sha(m.SOURCE_CONTRACT),m.SOURCE_CONTRACT_SHA)

if __name__=='__main__':unittest.main(verbosity=2)
