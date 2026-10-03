"""Five focused CPU-only R43 material contracts; every asset is a fixture."""
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
s = importlib.util.spec_from_file_location('r43_own_material_fixture', ROOT/'scripts/unreal/exterior-context-parcel-boundary-materials-r43.py')
m = importlib.util.module_from_spec(s);s.loader.exec_module(m)


class Properties:
    def __init__(self, **values): self.values = values
    def get_editor_property(self, key): return self.values[key]
    def set_editor_property(self, key, value):
        self.values[key] = m.api().f32(value) if key in ('r', 'opacity_mask_clip_value') else value


class MockNative:
    """Models only proven public call shapes; cannot prove Unreal reflection."""
    def __init__(self):
        self.assets = {};self.tasks = [];self.created = 0;self.saved = []
        def enum(group, names): return SimpleNamespace(**{n: group+'.'+n for n in names})
        groups = {'MaterialShadingModel': ['MSM_DEFAULT_LIT'],
            'TextureCompressionSettings': ['TC_DEFAULT', 'TC_NORMALMAP', 'TC_MASKS'],
            'TextureSourceEncoding': ['TSE_SRGB', 'TSE_NONE'],
            'MaterialSamplerType': ['SAMPLERTYPE_COLOR', 'SAMPLERTYPE_NORMAL', 'SAMPLERTYPE_MASKS'],
            'BlendMode': ['BLEND_OPAQUE'], 'TextureAddress': ['TA_WRAP'], 'TextureFilter': ['TF_DEFAULT'],
            'TextureMipGenSettings': ['TMGS_FROM_TEXTURE_GROUP'], 'TexturePowerOfTwoSetting': ['NONE'],
            'MaterialProperty': ['MP_'+n for n in ('BASE_COLOR', 'NORMAL', 'ROUGHNESS', 'METALLIC', 'SPECULAR')]}
        for group, names in groups.items(): setattr(self, group, enum(group, names))
        self.Vector4 = lambda x,y,z,w: SimpleNamespace(x=x,y=y,z=z,w=w)
        self.LinearColor = lambda r,g,b,a: SimpleNamespace(r=m.api().f32(r),g=m.api().f32(g),b=m.api().f32(b),a=m.api().f32(a))
        self.AssetImportTask = type('AssetImportTask', (Properties,), {})
        self.MaterialFactoryNew = type('MaterialFactoryNew', (Properties,), {})
        class Asset(Properties):
            def __init__(self, path, **values): super().__init__(**values);self.path=path;self.tags={}
            def get_path_name(self): return self.path
        native = self
        class Texture2D(Asset):
            def __init__(self, path):
                super().__init__(path, **m.texture_values(native, 'diffuse'),
                    source_color_settings=Properties(encoding_override='TextureSourceEncoding.TSE_NONE'),
                    downscale=Properties(default=1.,per_platform={}),
                    alpha_coverage_thresholds=native.Vector4(0,0,0,0))
            def blueprint_get_size_x(self): return 2048
            def blueprint_get_size_y(self): return 2048
        class Material(Asset):
            def __init__(self, path):
                super().__init__(path,opacity_mask_clip_value=m.api().f32(.333));self.nodes=[];self.roots={}
        self.Texture2D,self.Material=Texture2D,Material
        for name in ('TextureCoordinate', 'TextureSample', 'Constant', 'Constant3Vector'):
            setattr(self,'MaterialExpression'+name,type('MaterialExpression'+name,(Properties,),{}))
        self.get_default_object=lambda cls:cls('/Fixture/Default')
        def path(p): return p if '.' in p.rsplit('/',1)[-1] else p+'.'+p.rsplit('/',1)[-1]
        self.EditorAssetLibrary=SimpleNamespace(does_asset_exist=lambda p:path(p) in self.assets,
            load_asset=lambda p:self.assets.get(path(p)),set_metadata_tag=lambda o,k,v:o.tags.__setitem__(k,v),
            get_metadata_tag=lambda o,k:o.tags.get(k,''),save_loaded_asset=lambda o,b:self.saved.append(o.path))
        def imports(tasks):
            for t in tasks:
                self.tasks.append(copy.deepcopy(t.values));p=path(t.values['destination_path']+'/'+t.values['destination_name']);self.assets[p]=Texture2D(p)
        def create(name,folder,cls,factory):
            self.created+=1;o=cls(path(folder+'/'+name));self.assets[o.path]=o;return o
        self.AssetToolsHelpers=SimpleNamespace(get_asset_tools=lambda:SimpleNamespace(import_asset_tasks=imports,create_asset=create))
        def expression(material,cls,x,y):
            o=cls();o.inputs={};o.material=material;material.nodes.append(o);return o
        def connect(a,out,b,port): b.inputs[port]=(a,out);return True
        def root(o,out,prop): o.material.roots[prop.rsplit('MP_',1)[1]]=(o,out);return True
        self.MaterialEditingLibrary=SimpleNamespace(create_material_expression=expression,
            connect_material_expressions=connect,connect_material_property=root,recompile_material=lambda o:[])

    def graph(self,u,material):
        nodes=[]
        for node in material.nodes:
            cls=type(node).__name__;ports=['UVs','Tex','Apply View MipBias'] if cls=='MaterialExpressionTextureSample' else []
            inputs=[]
            for port in ports:
                o,out=node.inputs.get(port,(None,None));inputs.append([port,o.values['desc'] if o else None,out])
            values={k:(v.get_path_name() if k=='texture' else [getattr(v,a) for a in 'rgba'] if k=='constant' else v)
                for k,v in node.values.items() if k!='desc'}
            nodes.append({'class':cls,'role':node.values['desc'],'values':values,'inputs':inputs})
        roots={k:None for k in ('BASE_COLOR','NORMAL','ROUGHNESS','METALLIC','SPECULAR','OPACITY_MASK','SUBSURFACE_COLOR','OPACITY','AMBIENT_OCCLUSION','WORLD_POSITION_OFFSET')}
        roots.update({k:[o.values['desc'],out] for k,(o,out) in material.roots.items()});return {'nodes':nodes,'roots':roots}


class BoundaryMaterials(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source={'planPin':m.pin(m.SOURCE),'plan':json.loads(m.SOURCE.read_text())}
        cls.binding={'schema':'fixture-only-R43-authenticated-native-binding','nativeSelectedSha256':'6'*64}
    def packet(self): return {'source':copy.deepcopy(self.source),'base':{'fixtureOnly':True},'binding':copy.deepcopy(self.binding)}
    def bound(self,call):
        old=m.binding_guard;m.binding_guard=lambda:SimpleNamespace(require_native_binding=lambda b:m.require(b==self.binding,'Fixture exact selected binding required'))
        try:return call()
        finally:m.binding_guard=old
    def build(self):
        u=MockNative();p=self.packet();objects,report=self.bound(lambda:m.build_materials(u,p,self.binding,u.graph));return u,p,objects,report
    def verify(self,u,p,r): return self.bound(lambda:m.verify_materials(u,p,self.binding,r,u.graph))

    def test_binding_and_source_mutations_reject_before_asset_access(self):
        variants=[]
        p=self.packet();p['binding']={'wrong':True};variants.append(p)
        p=self.packet();p['source']['plan']['materials']['wood']['maps']['normal'],p['source']['plan']['materials']['wood']['maps']['roughness']=p['source']['plan']['materials']['wood']['maps']['roughness'],p['source']['plan']['materials']['wood']['maps']['normal'];variants.append(p)
        p=self.packet();p['source']['plan']['materials']['metal']['roughness']=.5;variants.append(p)
        for p in variants:
            u=MockNative()
            with self.subTest(),self.assertRaises(ValueError):self.bound(lambda:m.build_materials(u,p,self.binding,u.graph))
            self.assertEqual((u.assets,u.tasks,u.created),({},[],0))

    def test_original_six_jpg_sources_metric_uv_and_metal_constant(self):
        recipes,packages=m.validate_recipes(self.source);self.assertEqual(len(packages),9)
        headers=[m.jpg_header(row) for role in ('wood','gravel') for row in recipes[role]['maps'].values()]
        self.assertEqual(len(headers),6);self.assertTrue(all(h['pixels']==[2048,2048] and h['sourceBits']==8 for h in headers))
        self.assertEqual([recipes[r]['metricTileCm'] for r in ('wood','gravel')],[150,200])
        self.assertEqual(recipes['metal']['baseColorLinear'],[.055,.062,.067])

    def test_three_mock_graphs_roundtrip_no_saves_no_optical_claim(self):
        u,p,objects,r=self.build();self.assertEqual(self.verify(u,p,r),objects)
        self.assertEqual((u.created,len(u.tasks),len(r['newPackageAssets'])),(3,6,9))
        self.assertEqual([len(r['materials'][role]['graph']['nodes']) for role in m.ROLES],[6,4,6])
        self.assertTrue(all(not row['policy']['two_sided'] for row in r['materials'].values()))
        self.assertTrue(all(t['automated'] and not t['replace_existing'] and not t['save'] for t in u.tasks));self.assertEqual(u.saved,[])
        self.assertTrue(all(r[k] is False for k in m.LIMITS))

    def test_graph_uv_channel_and_undeclared_pbr_routes_reject(self):
        u,p,objects,r=self.build();row=r['materials']['wood'];recipe=p['source']['plan']['materials']['wood'];paths=m.assets('wood')[1]
        variants=[]
        for target,value in [('ROUGHNESS',['BreziParcelBoundaryR43:wood:roughness','G']),('AMBIENT_OCCLUSION',['BreziParcelBoundaryR43:wood:roughness','R']),('WORLD_POSITION_OFFSET',['BreziParcelBoundaryR43:wood:normal','RGB'])]:
            g=copy.deepcopy(row['graph']);g['roots'][target]=value;variants.append(g)
        g=copy.deepcopy(row['graph']);next(n for n in g['nodes'] if n['role'].endswith(':uv'))['values']['coordinate_index']=1;variants.append(g)
        g=copy.deepcopy(row['graph']);next(n for n in g['nodes'] if n['role'].endswith(':normal'))['values']['texture']=paths['diffuse'];variants.append(g)
        for g in variants:
            with self.subTest(),self.assertRaises(ValueError):m.validate_graph(g,'wood',recipe,paths)

    def test_saved_texture_policy_binding_and_limits_reject(self):
        u,p,objects,r=self.build();texture=u.assets[m.assets('wood')[1]['normal']]
        texture.values['flip_green_channel']=False
        with self.assertRaises(ValueError):self.verify(u,p,r)
        texture.values['flip_green_channel']=True
        for key,value in [('nativeBinding',{'wrong':True}),('nativeGpuPixelFormatVerified',True)]:
            bad=copy.deepcopy(r);bad[key]=value
            with self.subTest(),self.assertRaises(ValueError):self.verify(u,p,bad)
        self.assertEqual(self.verify(u,p,r),objects)


if __name__=='__main__':unittest.main()
