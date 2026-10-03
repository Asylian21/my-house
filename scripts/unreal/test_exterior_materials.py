"""Material import contracts and saved-graph tamper detection without Unreal."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import struct
import tempfile
import types
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location('exterior_materials', Path(__file__).with_name('exterior-materials.py'))
M = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)


class Node:
    def __init__(self):
        self.props = {'mip_value_mode': 'DEFAULT', 'coordinate_index': 0, 'u_tiling': 1., 'v_tiling': 1., 'automatic_view_mip_bias': True}
        self.inputs = {}

    def set_editor_property(self, key, value): self.props[key] = value
    def get_editor_property(self, key): return self.props[key]
    def get_class(self): return types.SimpleNamespace(get_name=lambda: self.__class__.__name__)


class Material(Node):
    def __init__(self, path):
        super().__init__(); self.path, self.nodes, self.roots, self.metadata, self.usage = path, [], {}, {}, set()

    def get_path_name(self): return self.path


class Texture(Material):
    def __init__(self,path):
        super().__init__(path);color=Node();color.props['encoding_override']='ENC_NONE'
        self.props['source_color_settings']=color
    def blueprint_get_size_x(self): return getattr(self,'dimensions',(2048,2048))[0]
    def blueprint_get_size_y(self): return getattr(self,'dimensions',(2048,2048))[1]


class MaterialFunction(Material):
    pass


class MaterialFunctionCall(Node):
    def set_material_function(self, function):
        self.props['material_function'] = function
        return isinstance(function, MaterialFunction)


class Library:
    def create_material_expression(self, material, cls, *args):
        node = cls(); node.material = material; material.nodes.append(node); return node

    def connect_material_expressions(self, source, channel, target, pin):
        # Native UE 5.8 outputs: UV has only unnamed float2; vertex RGB and
        # component mask output are unnamed too, not synthetic 'RGB'/'R'.
        name = source.__class__.__name__
        if name in ('MaterialExpressionTextureCoordinate', 'MaterialExpressionComponentMask') and channel: return False
        if name == 'MaterialExpressionVertexColor' and channel not in ('', 'R', 'G', 'B', 'A'): return False
        if target.__class__.__name__ == 'MaterialExpressionComponentMask' and pin: return False
        if target.__class__.__name__ == 'MaterialExpressionTextureSample':
            # UE 5.8 MaterialEditingLibrary.cpp uses GetShortenPinName from
            # MaterialGraphNode.cpp, not TextureSample::GetInputName verbatim.
            # The mip input also exists only for its selected MipValueMode.
            pins = {'UVs', 'Tex', 'Apply View MipBias'}
            pins.update({'DEFAULT': (), 'MIP_LEVEL': ('Level',), 'MIP_BIAS': ('Bias',),
                         'DERIVATIVE': ('DDX(UVs)', 'DDY(UVs)')}[target.props['mip_value_mode']])
            if pin and pin not in pins: return False
            if not pin: pin = 'UVs'
        target.inputs[pin] = (source, channel); return True

    def connect_material_property(self, node, channel, prop):
        if isinstance(node, MaterialFunctionCall) and not channel: channel='Result'
        node.material.roots[prop] = (node, channel); return True

    def get_material_expressions(self, m): return m.nodes
    def get_inputs_for_material_expression(self, m, node):
        return [node.inputs.get('' if pin == 'None' else pin, (None,''))[0] for pin in self.get_material_expression_input_names(node)]
    def get_material_expression_input_names(self, node):
        if node.__class__.__name__ == 'MaterialExpressionComponentMask': return ['None']
        return ['Alpha Threshold','Random'] if isinstance(node, MaterialFunctionCall) and 'material_function' in node.props else list(node.inputs)
    def get_input_node_output_name_for_material_expression(self, node, other): return next(v[1] for v in node.inputs.values() if v[0] is other)
    def get_material_property_input_node(self, m, prop): return m.roots.get(prop, (None, ''))[0]
    def get_material_property_input_node_output_name(self, m, prop): return m.roots[prop][1]
    def set_base_material_usage(self, m, usage, enabled): m.usage.add(usage); return True
    def has_material_usage(self, m, usage): return usage in m.usage
    def recompile_material(self, m): return []


class Assets:
    def __init__(self): self.values, self.saved, self.imports = {}, [], []
    def does_asset_exist(self, path): return path in self.values
    def create_asset(self, name, prefix, cls, *args):
        path = prefix+'/'+name; obj = cls(path); self.values[path] = obj; return obj
    def load_asset(self, path): return self.values.get(path)
    def get_metadata_tag(self, obj, key): return obj.metadata.get(key, '')
    def set_metadata_tag(self, obj, key, value): obj.metadata[key] = value
    def save_loaded_asset(self, obj, **kwargs): self.saved.append(obj); return True
    def import_asset_tasks(self, tasks):
        for task in tasks:
            self.imports.append(copy.deepcopy(task.props))
            tex = self.create_asset(task.props['destination_name'], task.props['destination_path'], Texture)
            with Path(task.props['filename']).open('rb') as stream: header = stream.read(24)
            if header[:8] == b'\x89PNG\r\n\x1a\n': tex.dimensions = struct.unpack('>II',header[16:24])


def fake_unreal():
    u = types.SimpleNamespace(MaterialEditingLibrary=Library(), EditorAssetLibrary=Assets())
    for name in ('Constant', 'Constant3Vector', 'Custom', 'TextureSample', 'TextureCoordinate', 'WorldPosition', 'CameraPositionWS', 'PerInstanceRandom', 'VertexNormalWS', 'VertexColor', 'Multiply', 'ComponentMask'):
        setattr(u, 'MaterialExpression'+name, type('MaterialExpression'+name, (Node,), {}))
    u.MaterialExpressionMaterialFunctionCall = type('MaterialExpressionMaterialFunctionCall', (MaterialFunctionCall,), {})
    u.engine_function = MaterialFunction(M.DITHER_FUNCTION)
    u.load_object = lambda outer, path: u.engine_function if path == M.DITHER_FUNCTION else u.EditorAssetLibrary.load_asset(path)
    u.CustomInput = u.AssetImportTask = Node
    u.Material, u.MaterialFactoryNew, u.Texture2D = Material, object, Texture
    u.AssetToolsHelpers = types.SimpleNamespace(get_asset_tools=lambda: u.EditorAssetLibrary)
    u.LinearColor = lambda r, g, b, a: types.SimpleNamespace(r=r, g=g, b=b, a=a)
    u.Vector4 = lambda x, y, z, w: types.SimpleNamespace(x=x, y=y, z=z, w=w)
    def enum(**values): return types.SimpleNamespace(**values)
    u.BlendMode = enum(BLEND_MASKED='MASKED', BLEND_OPAQUE='OPAQUE')
    u.MaterialShadingModel = enum(MSM_TWOSIDED_FOLIAGE='FOLIAGE', MSM_DEFAULT_LIT='DEFAULT_LIT')
    u.MaterialSamplerType = enum(SAMPLERTYPE_COLOR='COLOR', SAMPLERTYPE_NORMAL='NORMAL', SAMPLERTYPE_MASKS='MASKS', SAMPLERTYPE_LINEAR_GRAYSCALE='LINEAR_GRAYSCALE', SAMPLERTYPE_LINEAR_COLOR='LINEAR_COLOR')
    u.CustomMaterialOutputType = enum(**{'CMOT_FLOAT'+str(i): 'FLOAT'+str(i) for i in range(1, 5)})
    u.MaterialProperty = enum(**{'MP_'+name: name for name in M.ROOTS})
    u.MaterialUsage = enum(MATUSAGE_NANITE='NANITE', MATUSAGE_INSTANCED_STATIC_MESHES='INSTANCED')
    u.TextureCompressionSettings = enum(TC_NORMALMAP='NORMALMAP', TC_DEFAULT='DEFAULT', TC_MASKS='MASKS', TC_GRAYSCALE='GRAYSCALE', TC_VECTOR_DISPLACEMENTMAP='RGBA8')
    u.TextureAddress = enum(TA_WRAP='WRAP', TA_CLAMP='CLAMP')
    u.TextureMipGenSettings = enum(TMGS_FROM_TEXTURE_GROUP='FROM_GROUP', TMGS_NO_MIPMAPS='NO_MIPMAPS')
    u.TexturePowerOfTwoSetting = enum(NONE='NONE',STRETCH_TO_POWER_OF_TWO='STRETCH')
    u.TextureMipValueMode = enum(TMVM_DERIVATIVE='DERIVATIVE', TMVM_MIP_LEVEL='MIP_LEVEL')
    u.TextureSourceEncoding = enum(TSE_NONE='ENC_NONE',TSE_S_RGB='ENC_SRGB')
    return u


def plant_fixture(convention='DirectX', kind='foliage'):
    # Reuse hash-pinned local image bytes as a harmless fixture. This tests the
    # importer interpretation contract, not the botanical appearance of pixels.
    source = M._ground_source('leafy_grass')
    source['maps']['alpha'] = copy.deepcopy(source['maps']['roughness'])
    if kind != 'foliage': source['maps'].pop('alpha')
    source.update(kind=kind, normalConvention=convention)
    return {'test_plant': source}


ORTHO = M.ROOT/'output/unreal/exterior-ortho-20260926-r1/orthophoto-manifest.json'
ORTHO_EARLIER = M.ROOT/'output/unreal/exterior-ortho-20260927-r2/orthophoto-manifest.json'
SEASONAL = M.ROOT/'output/unreal/exterior-seasonal-fields-20260927-r2/seasonal-fields-manifest.json'
FIELD_MACRO = M.ROOT/'output/unreal/exterior-field-macro-20260927-r3/field-macro-manifest.json'
PROJECTION = M.ROOT/'output/unreal/exterior-ortho-projection-20260930-r2/ortho-projection-manifest.json'
ASSETS_R7 = M.ROOT/'output/unreal/exterior-assets-20260927-r7/material-manifest.json'
ASSETS_R5 = M.ROOT/'output/unreal/exterior-assets-20260926-r5/material-manifest.json'
ASSETS_R3 = M.ROOT/'output/unreal/exterior-assets-20260930-r3/material-manifest.json'
ASSETS_GREENERY_R5 = M.ROOT/'output/unreal/exterior-assets-greenery-20260930-r5/material-manifest.json'
CONTEXT_SRGB_BY_SHA = {
    '5b2aa6ce68bf82c1ae3b3433eeefc2a4ec6aae441740b6fbc42db16a2e2597b0':
        ('context_arable', 'context_garden_soil', 'context_soil_exposure'),
    '7b235e32340475f582baea7f5deb1b452f118c5ae61a68dca4001b0f7fbf97d3': ('ph_nettle_plant',),
    '78a6bc3b6465277379cc7db062316ca34fd9f6334b112b0c279a1033d68c77e7': ('ph_tree_small_02_trunk',),
    'fc386b9d205ba38fc7cda66a2499680e6443a7b3fc91496a3d5890e4f98f71a4': ('ph_shrub_04',),
    '2bd96cd167ea4a79a68a98b5de3b33be426c1d272024cde39bca9e8b98a4a33d': ('ph_periwinkle_plant',),
}


class ExteriorMaterialsTests(unittest.TestCase):
    def test_soil_exposure_uses_native_temporal_uv_coverage_and_saved_settings(self):
        u=fake_unreal();materials,report=M.build_materials(unreal_module=u)
        material=materials['context_soil_exposure'];recipe=report['materials']['context_soil_exposure']['recipe']
        nodes={n.props['desc'].removeprefix(M.TAG):n for n in material.nodes}
        self.assertTrue(recipe['featherUV']);self.assertNotIn('groundCover',recipe)
        self.assertEqual(recipe['sourceUrl'],'https://polyhaven.com/a/farm_soil')
        self.assertEqual(recipe['tint'],[.65,.53,.40]);self.assertEqual(recipe['albedoScale'],.30)
        self.assertEqual(material.props['blend_mode'],'MASKED')
        self.assertEqual(material.props['shading_model'],'DEFAULT_LIT')
        self.assertFalse(material.props['two_sided']);self.assertFalse(material.props['tangent_space_normal'])
        self.assertEqual(material.props['opacity_mask_clip_value'],.333)
        uv=nodes['soil-exposure-coverage-uv0'];mask=nodes['soil-exposure-coverage-u'];dither=nodes['soil-exposure-native-temporal-dither']
        self.assertEqual([uv.props[k] for k in ('coordinate_index','u_tiling','v_tiling')],[0,1.,1.])
        self.assertEqual(dither.props['material_function'].get_path_name(),M.DITHER_FUNCTION)
        self.assertEqual([mask.props[k] for k in ('r','g','b','a')],[True,False,False,False])
        self.assertEqual(mask.inputs,{'':(uv,'')})
        broken=nodes['soil-exposure-spatial-camera-coverage']
        self.assertEqual(dither.inputs,{'Alpha Threshold':(broken,'')})
        self.assertEqual(broken.props['code'],M.SOIL_EXPOSURE_COVERAGE)
        self.assertEqual(broken.inputs['EdgeCoverage'],(mask,''))
        self.assertIs(broken.inputs['Position'][0],nodes['world-position'])
        self.assertEqual(broken.inputs['Camera'][0].get_class().get_name(),'MaterialExpressionCameraPositionWS')
        self.assertEqual([getattr(broken.inputs['FadeRange'][0].props['constant'],k) for k in ('r','g')],[4000.,10000.])
        self.assertEqual(material.roots['OPACITY_MASK'],(dither,'Result'))
        self.assertEqual(material.roots['NORMAL'],(nodes['world-ground-normal'],''))
        self.assertIs(nodes['metric-ground-uv'].inputs['Position'][0],nodes['world-position'])
        function=report['engineMaterialFunctions'][0]
        self.assertEqual(function['asset'],M.DITHER_FUNCTION)
        self.assertEqual(report['inputFiles'][function['source']],M.sha(function['source']))
        self.assertEqual(next(n for n in report['materials']['context_soil_exposure']['graph']['nodes']
                              if n['class']=='MaterialExpressionMaterialFunctionCall')['values']['material_function'],M.DITHER_FUNCTION)
        saved_nodes={n['role'].removeprefix(M.TAG):n for n in report['materials']['context_soil_exposure']['graph']['nodes']}
        self.assertEqual(saved_nodes['soil-exposure-coverage-u']['inputs'],
                         [['None',M.TAG+'soil-exposure-coverage-uv0','']])
        self.assertEqual(saved_nodes['soil-exposure-native-temporal-dither']['inputs'],
                         [['Alpha Threshold',M.TAG+'soil-exposure-spatial-camera-coverage',''],['Random',None,None]])
        self.assertEqual(report['materials']['context_soil_exposure']['graph']['roots']['OPACITY_MASK'],
                         [M.TAG+'soil-exposure-native-temporal-dither','Result'])
        M.verify_materials(report,u)
        material.props['opacity_mask_clip_value']=.8
        with self.assertRaisesRegex(RuntimeError,'graph differs'):M.verify_materials(report,u)

    def test_soil_spatial_coverage_has_irregular_interior_and_camera_fade(self):
        values=[]
        for x in range(-500,501,17):
            position=(float(x),x*.67,0.)
            camera=position
            value=M.soil_exposure_coverage(position,camera,1.)
            values.append(value)
            self.assertGreaterEqual(value,.06);self.assertLessEqual(value,.94)
            self.assertEqual(M.soil_exposure_coverage(position,camera,0.),0.)
            self.assertAlmostEqual(M.soil_exposure_coverage(position,(position[0],position[1],4000.),1.),value)
            self.assertAlmostEqual(M.soil_exposure_coverage(position,(position[0],position[1],7000.),1.),value*.5)
            self.assertEqual(M.soil_exposure_coverage(position,(position[0],position[1],10000.),1.),0.)
            self.assertLess(abs(M.soil_exposure_coverage((position[0]+.001,position[1],0.),camera,1.)-value),.001)
        self.assertGreater(max(values)-min(values),.4)

    def test_camera_ground_blend_uses_pixel_distance_exact_coverage_and_site_exclusion(self):
        ortho=M.prepare_orthophoto(ORTHO_EARLIER);layers=ortho['layers'];coverage={'far16km':1.,'detail2km':1.}
        def weights(position,camera,uv=(.5,.5),permission=(1.,1.,0.,1.),source_coverage=coverage):
            return M.ground_orthophoto_weights(position,camera,layers,source_coverage,uv,permission)
        for x in (0.,40000.):
            position=(x,0.,0.)
            for distance,amount in ((0.,0.),(5000.,0.),(10000.,.5),(15000.,1.),(50000.,1.)):
                result=weights(position,(x,0.,distance))
                self.assertAlmostEqual(result['detail']+result['far'],amount)
                self.assertAlmostEqual(result['fallback'],1-amount)
            self.assertEqual(weights(position,(x,0.,50000.),permission=(0.,1.,0.,1.))['fallback'],1.)
            self.assertEqual(weights(position,(x,0.,50000.),permission=(1.,.989,0.,1.))['fallback'],1.)
            self.assertEqual(weights(position,(x,0.,50000.),permission=(.5,1.,0.,1.))['fallback'],.5)
            self.assertEqual(weights(position,(x,0.,50000.),uv=(-.00001,.5))['fallback'],1.)
            self.assertEqual(weights(position,(x,0.,50000.),source_coverage={'far16km':.98,'detail2km':.98})['fallback'],1.)
        self.assertEqual(weights((1e7,1e7,0),(1e7,1e7,50000))['fallback'],1.)

    def test_camera_ground_aerial_graph_is_scoped_world_affine_and_pbr_preserving(self):
        u=fake_unreal();materials,report=M.build_materials(ASSETS_R3,unreal_module=u,ortho_manifest=ORTHO_EARLIER,
                                                        field_macro_manifest=FIELD_MACRO,projection_manifest=PROJECTION)
        self.assertEqual(M.verify_materials(report,u),{'status':'verified-saved-exterior-materials','materials':34,'textures':70})
        self.assertEqual({k for k,v in report['materials'].items() if 'groundOrthophoto' in v['recipe']},M.PROJECTION_KEYS)
        self.assertEqual(report['orthoProjection']['manifestSha256'],M.sha(PROJECTION))
        self.assertIn(str(M.ROOT/'scripts/unreal/exterior-ortho-projection-mask.py'),report['pipelineFiles'])
        for key in M.PROJECTION_KEYS:
            material=materials[key];nodes={n.props['desc'].removeprefix(M.TAG):n for n in material.nodes}
            recipe=report['materials'][key]['recipe'];ortho=recipe['groundOrthophoto'];projection=recipe['projectionMask']
            self.assertEqual(ortho['cameraDistanceBlendCm'],[5000.,15000.]);self.assertNotIn('seasonalFields',ortho)
            distance=nodes['ground-ortho-camera-distance'];weight=nodes['ground-ortho-protected-field-weight']
            self.assertEqual(distance.props['code'],M.ORTHO_CAMERA)
            self.assertIs(distance.inputs['Position'][0],nodes['world-position'])
            self.assertEqual(distance.inputs['Camera'][0].get_class().get_name(),'MaterialExpressionCameraPositionWS')
            self.assertEqual(weight.inputs['ProjectionUV'],(nodes['ground-ortho-projection-world-uv'],''))
            self.assertEqual(weight.inputs['Permission'],(nodes['ortho_projection-permission'],'R'))
            self.assertEqual(weight.inputs['Coverage'],(nodes['ortho_projection-coverage-mip0'],'G'))
            self.assertEqual(nodes['ortho_projection-permission'].props['mip_value_mode'],'DEFAULT')
            self.assertEqual(nodes['ortho_projection-coverage-mip0'].props['mip_value_mode'],'MIP_LEVEL')
            self.assertEqual(nodes['ortho_projection-coverage-mip0'].inputs['Level'][0].props['r'],0.)
            for axis,row in zip(('RowU','RowV'),projection['worldCmToUvRows']):
                value=nodes['ground-projection-'+axis].props['constant']
                self.assertEqual([value.r,value.g,value.b],row)
            self.assertEqual(weight.props['code'],M.GROUND_ORTHO_WEIGHT)
            fallback='field-macro-basecolor' if key in M.FIELD_MACRO_KEYS else 'natural-ground-color'
            self.assertIs(nodes['licensed-ortho-basecolor'].inputs['Fallback'][0],nodes[fallback])
            self.assertIs(nodes['licensed-ortho-basecolor'].inputs['DistanceBlend'][0],weight)
            self.assertEqual(material.roots['NORMAL'],(nodes['world-ground-normal'],''))
            self.assertEqual(material.roots['ROUGHNESS'],(nodes['ground-roughness'],''))
            for layer in ortho['layers']:
                label='ortho-'+layer['id'];mapping=nodes[label+'-affine-uv'];sample=nodes['albedo-'+label]
                coverage=nodes['albedo-'+label+'-coverage-mip0']
                self.assertIs(mapping.inputs['Position'][0],nodes['world-position'])
                self.assertEqual(nodes[label+'-coverage-and-extent'].inputs['Coverage'],(coverage,'A'))
                self.assertEqual(coverage.props['mip_value_mode'],'MIP_LEVEL')
                self.assertEqual(coverage.inputs['Level'][0].props['r'],0.)
                self.assertFalse(coverage.props['automatic_view_mip_bias'])
                self.assertIs(coverage.props['texture'],sample.props['texture'])
                self.assertIs(nodes[label+'-coverage-and-extent'].inputs['UV'][0],sample.inputs['UVs'][0])
            self.assertLessEqual(len(report['materials'][key]['graph']['nodes']),110)
        baseline=M.prepare_manifest(ASSETS_R3)['materials']
        for key in ('context_garden_soil','context_soil_exposure','context_mulch'):
            self.assertEqual(report['materials'][key]['recipe'],baseline[key])
        value=nodes['ground-ortho-distance-blend-cm'].props['constant'];value.r=1.
        with self.assertRaisesRegex(RuntimeError,'graph differs'):M.verify_materials(report,u)
        raw=plant_fixture(kind='bark');raw['test_plant']['groundOrthophoto']={}
        with self.assertRaisesRegex(RuntimeError,'validated optional manifest'):M.prepare_manifest(raw)

    def test_ground_rgb_projection_requires_its_own_validated_mask_not_scalar_macro(self):
        u=fake_unreal();materials,report=M.build_materials(ASSETS_R3,unreal_module=u,ortho_manifest=ORTHO_EARLIER,
                                                        field_macro_manifest=FIELD_MACRO)
        self.assertNotIn('groundOrthophoto',report)
        for key in M.FIELD_MACRO_KEYS:
            self.assertEqual(materials[key].roots['BASE_COLOR'][0].props['desc'],M.TAG+'field-macro-basecolor')
        self.assertNotIn('fieldMacro',report['materials']['context_track']['recipe'])
        u=fake_unreal()
        with self.assertRaisesRegex(RuntimeError,'requires licensed orthophoto'):
            M.build_materials(ASSETS_R3,unreal_module=u,projection_manifest=PROJECTION)
        self.assertEqual(u.EditorAssetLibrary.imports,[])

    def test_soil_feather_scope_and_function_fail_before_native_writes(self):
        raw=plant_fixture(kind='bark');raw['test_plant']['featherUV']=True
        with self.assertRaisesRegex(RuntimeError,'feathered ground'):M.prepare_manifest(raw)
        u=fake_unreal();u.engine_function=None
        with self.assertRaisesRegex(RuntimeError,'native temporal soil'):M.build_materials(unreal_module=u)
        self.assertEqual(u.EditorAssetLibrary.imports,[]);self.assertEqual(u.EditorAssetLibrary.saved,[])
        self.assertEqual(M.context_recipes()['context_arable']['albedoScale'],.35)
        self.assertEqual(M.context_recipes()['context_garden_soil']['albedoScale'],.65)

    def test_authored_garden_foliage_is_opaque_vertex_tinted_and_bounded(self):
        raw=json.loads(ASSETS_R7.read_text())
        raw.update({key:{'kind':'authored-foliage','maps':{},'twoSided':True,
                  'linearColor':[.052,.094,.031],'roughness':.78,'specular':.12,'subsurfaceScale':.045}
             for key in M.AUTHORED_FOLIAGE_KEYS})
        photo=plant_fixture(kind='bark')['test_plant'];photo['twoSided']=True;raw['garden_blade_photo']=photo
        u=fake_unreal();materials,report=M.build_materials(raw,unreal_module=u)
        for key in M.AUTHORED_FOLIAGE_KEYS:
            material=materials[key];nodes={n.props['desc'].removeprefix(M.TAG):n for n in material.nodes}
            self.assertEqual(material.props['blend_mode'],'OPAQUE');self.assertEqual(material.props['shading_model'],'FOLIAGE')
            self.assertTrue(material.props['two_sided']);self.assertTrue(material.props['tangent_space_normal'])
            self.assertNotIn('OPACITY_MASK',material.roots)
            self.assertEqual(nodes['authored-plant-color'].inputs['A'],(nodes['authored-plant-vertex-color'],''))
            self.assertEqual(nodes['authored-plant-color'].inputs['B'],(nodes['authored-plant-linear-color'],''))
            saved_color=next(n for n in report['materials'][key]['graph']['nodes'] if n['role']==M.TAG+'authored-plant-color')
            self.assertEqual(saved_color['inputs'][0],['A',M.TAG+'authored-plant-vertex-color',''])
            self.assertEqual(material.roots['BASE_COLOR'],(nodes['authored-plant-color'],''))
            self.assertEqual(material.roots['SUBSURFACE_COLOR'],(nodes['authored-plant-transmission'],''))
            self.assertEqual(nodes['authored-plant-transmission-scale'].props['r'],.045)
            self.assertFalse(any(n.get_class().get_name()=='MaterialExpressionTextureSample' for n in material.nodes))
        self.assertEqual(materials['garden_blade_photo'].props['blend_mode'],'OPAQUE')
        self.assertTrue(materials['garden_blade_photo'].props['two_sided'])
        self.assertFalse(materials['context_garden_soil'].props['two_sided'])
        self.assertEqual(len(report['materials']),37)
        M.verify_materials(report,u)
        materials['garden_blade_photo'].props['two_sided']=False
        with self.assertRaisesRegex(RuntimeError,'graph differs'):M.verify_materials(report,u)
        for key in ('garden_blade_green', 'garden_petal_rose', 'lawn_natural_blade', 'canopy_understory_stem'):
            for bad in ({'subsurfaceScale':.5},{'linearColor':[2.,0.,0.]},{'twoSided':False},{'maps':{'albedo':{}}}):
                candidate=copy.deepcopy(raw);candidate[key].update(bad)
                with self.assertRaises(RuntimeError):M.prepare_manifest(candidate)
        candidate={'foreign_plant':raw['garden_blade_green']}
        with self.assertRaisesRegex(RuntimeError,'authored foliage'):M.prepare_manifest(candidate)

    def test_grove_ecology_reuses_photo_maps_and_adds_only_bounded_stems(self):
        base=M.ROOT/'output/unreal/exterior-assets-greenery-20260930-r2/material-manifest.json'
        ecology=M.ROOT/'output/unreal/exterior-canopy-ecology-20260930-r3/material-manifest.json'
        raw=json.loads(base.read_text());extra=json.loads(ecology.read_text())
        for key,recipe in extra.items():
            if key in raw:self.assertEqual(raw[key],recipe)
        raw.update(extra)
        prepared=M.prepare_manifest(raw)['materials']
        self.assertEqual(len(prepared),39)
        for key,source in [('canopy_litter_oak','regional_oak_leaf'),('canopy_litter_green','regional_green_leaf')]:
            self.assertEqual(prepared[key]['maps'],prepared[source]['maps'])
            self.assertEqual(prepared[key]['license'],'CC0-1.0')
            self.assertEqual(prepared[key]['normalConvention'],prepared[source]['normalConvention'])
            self.assertLessEqual(prepared[key]['subsurfaceScale'],.025)
            self.assertNotIn('windCm',prepared[key])
        stem=prepared['canopy_understory_stem']
        self.assertEqual(stem['maps'],{})
        self.assertEqual(stem['linearColor'],[.046,.074,.022])
        self.assertTrue(stem['twoSided'])
        self.assertEqual(stem['subsurfaceScale'],.06)
        overflow=copy.deepcopy(raw);overflow['foreign_extra_bark']=copy.deepcopy(raw['ph_tree_small_02_branches'])
        with self.assertRaisesRegex(RuntimeError,'material budget'):M.prepare_manifest(overflow)

    def test_grove_litter_keeps_registered_photo_maps_and_full_interior_coverage(self):
        raw=json.loads((M.ROOT/'output/unreal/exterior-assets-greenery-20260930-r3/material-manifest.json').read_text())
        addition=json.loads((M.ROOT/'output/unreal/exterior-grove-substrate-20260930-r3/material-manifest.json').read_text())
        raw.update(addition);u=fake_unreal();materials,report=M.build_materials(raw,unreal_module=u,
            ortho_manifest=ORTHO_EARLIER,field_macro_manifest=FIELD_MACRO,projection_manifest=PROJECTION)
        self.assertEqual(len(report['materials']),40);self.assertEqual(len(report['textures']),73)
        floor=materials['canopy_floor_litter'];recipe=report['materials']['canopy_floor_litter']['recipe']
        self.assertEqual(recipe['maps'],addition['canopy_floor_litter']['maps'])
        self.assertEqual(recipe['tileCm'],150);self.assertFalse(recipe['stochasticGround'])
        self.assertEqual(recipe['distanceFadeCm'],[12000,18000]);self.assertFalse(floor.props['tangent_space_normal'])
        self.assertEqual(floor.props['blend_mode'],'MASKED')
        nodes={n.props['desc'].removeprefix(M.TAG):n for n in floor.nodes}
        coverage=nodes['soil-exposure-spatial-camera-coverage']
        self.assertEqual(coverage.props['code'],M.GROVE_LITTER_COVERAGE)
        self.assertNotIn('broken',coverage.props['code']);self.assertNotIn('density',coverage.props['code'])
        self.assertFalse(any('-phase-' in name or name.endswith('-weights')for name in nodes))
        self.assertTrue(any('-registered' in name for name in nodes))
        M.verify_materials(report,u)
        floor_record=next(v for v in report['textures'].values() if v['sourceSha256']==M.FLOOR_ALBEDO_SHA and v['role']=='albedo')
        self.assertEqual(floor_record['sourceEncodingOverride'],'sRGB')
        self.assertEqual(floor_record['sourceEncodingReadback'],'TSE_S_RGB')
        self.assertIn('_srcsrgb',floor_record['asset'])
        self.assertEqual(report['inputFiles'][str(M.FLOOR_ENCODING_PROOF)],M.FLOOR_ENCODING_PROOF_SHA)
        proven_albedos = set(CONTEXT_SRGB_BY_SHA) | {M.FLOOR_ALBEDO_SHA}
        corrected = [v for v in report['textures'].values()
                     if v['role']=='albedo' and v['sourceSha256'] in proven_albedos]
        self.assertEqual(len(corrected),6)
        self.assertEqual({v['sourceSha256'] for v in corrected},proven_albedos)
        self.assertTrue(all(v['sourceEncodingOverride']=='sRGB' and v['sourceEncodingReadback']=='TSE_S_RGB'
            for v in corrected))
        untouched = [v for v in report['textures'].values() if v not in corrected]
        self.assertEqual(len(untouched),67)
        self.assertTrue(all(v['sourceEncodingOverride']=='None' and v['sourceEncodingReadback']=='TSE_NONE'
            for v in untouched))
        for change in ({'tileCm':300.},{'distanceFadeCm':[4000.,10000.]},
                       {'stochasticGround':True},{'sourceUrl':'https://polyhaven.com/a/forest_leaves_02'}):
            broken=copy.deepcopy(raw);broken['canopy_floor_litter'].update(change)
            with self.assertRaises(RuntimeError):M.prepare_manifest(broken)
        foreign=copy.deepcopy(raw);foreign['extra_bark']=copy.deepcopy(raw['ph_tree_small_02_branches'])
        with self.assertRaisesRegex(RuntimeError,'material budget'):M.prepare_manifest(foreign)

    def test_floor_source_encoding_saved_native_enum_tamper_is_rejected(self):
        raw=json.loads((M.ROOT/'output/unreal/exterior-grove-substrate-20260930-r3/material-manifest.json').read_text())
        u=fake_unreal();_,report=M.build_materials(raw,unreal_module=u)
        entry=next(v for v in report['textures'].values() if v['sourceSha256']==M.FLOOR_ALBEDO_SHA)
        tex=u.EditorAssetLibrary.load_asset(entry['asset']);tex.props['source_color_settings'].props['encoding_override']='ENC_NONE'
        with self.assertRaisesRegex(RuntimeError,'source encoding interpretation'):M.verify_materials(report,u)

    def test_floor_source_encoding_same_pixels_different_interpretation_cannot_alias(self):
        raw=json.loads((M.ROOT/'output/unreal/exterior-grove-substrate-20260930-r3/material-manifest.json').read_text())
        recipe=M.prepare_manifest(raw)['materials']['canopy_floor_litter'];u=fake_unreal();writer=M.Writer(u,M.PREFIX)
        corrected=writer.texture('albedo',recipe);original=copy.deepcopy(recipe)
        original.pop('sourceEncodingOverride');original.pop('sourceEncodingProof')
        unchanged=writer.texture('albedo',original)
        self.assertIsNot(corrected,unchanged);self.assertEqual(len(writer.texture_report),2)
        self.assertEqual(corrected.props['source_color_settings'].props['encoding_override'],'ENC_SRGB')
        self.assertEqual(unchanged.props['source_color_settings'].props['encoding_override'],'ENC_NONE')
        self.assertEqual(corrected.metadata['source_sha256'],unchanged.metadata['source_sha256'])

    def test_floor_source_encoding_foreign_recipe_or_source_override_rejected(self):
        raw=json.loads((M.ROOT/'output/unreal/exterior-grove-substrate-20260930-r3/material-manifest.json').read_text())
        floor=raw['canopy_floor_litter'];bad=copy.deepcopy(raw)
        bad['canopy_floor_litter']['sourceEncodingOverride']='None'
        with self.assertRaisesRegex(RuntimeError,'source encoding recipe'):M.prepare_manifest(bad)
        foreign=plant_fixture();foreign['sourceEncodingOverride']='sRGB'
        foreign['sourceEncodingProof']={'path':str(M.FLOOR_ENCODING_PROOF),'sha256':M.FLOOR_ENCODING_PROOF_SHA}
        with self.assertRaisesRegex(RuntimeError,'source encoding recipe'):M.prepare_manifest({'foreign_leaf':foreign})
        fake=copy.deepcopy(floor);fake['maps']['albedo']=copy.deepcopy(M._ground_source('sparse_grass')['maps']['albedo'])
        fake['sourceEncodingOverride']='sRGB'
        with self.assertRaisesRegex(RuntimeError,'Unproven'):M.texture_source_encoding('albedo',fake)

    def test_floor_source_encoding_native_proof_drift_rejected(self):
        with patch.object(M,'FLOOR_ENCODING_PROOF_SHA','0'*64):
            with self.assertRaisesRegex(RuntimeError,'native proof drift'):M.floor_encoding_inputs()

    def test_floor_source_encoding_receipt_forgery_rejected(self):
        raw=json.loads((M.ROOT/'output/unreal/exterior-grove-substrate-20260930-r3/material-manifest.json').read_text())
        u=fake_unreal();_,report=M.build_materials(raw,unreal_module=u)
        entry=next(v for v in report['textures'].values() if v['sourceSha256']==M.FLOOR_ALBEDO_SHA)
        entry['sourceEncodingReadback']='TSE_NONE'
        with self.assertRaisesRegex(RuntimeError,'source encoding interpretation'):M.verify_materials(report,u)

    def test_context_source_encoding_current_40_materials_73_textures_has_exact_six_rgb_overrides(self):
        self.assertEqual(set(M.CONTEXT_ENCODING_SOURCES),set(CONTEXT_SRGB_BY_SHA))
        u=fake_unreal();_,report=M.build_materials(ASSETS_GREENERY_R5,unreal_module=u,
            ortho_manifest=ORTHO_EARLIER,field_macro_manifest=FIELD_MACRO,projection_manifest=PROJECTION)
        self.assertEqual(len(report['materials']),40);self.assertEqual(len(report['textures']),73)
        actual_recipes={key for key,row in report['materials'].items()
                        if row['recipe'].get('sourceEncodingOverride')=='sRGB'}
        expected_recipes={key for keys in CONTEXT_SRGB_BY_SHA.values() for key in keys}|{'canopy_floor_litter'}
        self.assertEqual(actual_recipes,expected_recipes)
        corrected=[row for row in report['textures'].values()if row['sourceEncodingOverride']=='sRGB']
        self.assertEqual({row['sourceSha256'] for row in corrected},set(CONTEXT_SRGB_BY_SHA)|{M.FLOOR_ALBEDO_SHA})
        self.assertEqual(len(corrected),6)
        for row in report['textures'].values():
            tex=u.EditorAssetLibrary.load_asset(row['asset'])
            encoded=row in corrected
            self.assertEqual(row['sourceEncodingReadback'],'TSE_S_RGB' if encoded else 'TSE_NONE')
            self.assertEqual(tex.props['source_color_settings'].props['encoding_override'],'ENC_SRGB' if encoded else 'ENC_NONE')
            self.assertEqual('_srcsrgb' in row['asset'],encoded)
            if encoded:self.assertEqual(row['role'],'albedo')
        self.assertEqual(report['inputFiles'][str(M.CONTEXT_ENCODING_PROOF)],M.CONTEXT_ENCODING_PROOF_SHA)
        M.verify_materials(report,u)

    def test_context_source_encoding_each_saved_enum_and_receipt_tamper_is_rejected(self):
        u=fake_unreal();_,report=M.build_materials(ASSETS_GREENERY_R5,unreal_module=u)
        for source_sha in CONTEXT_SRGB_BY_SHA:
            entry=next(row for row in report['textures'].values()if row['sourceSha256']==source_sha and row['role']=='albedo')
            tex=u.EditorAssetLibrary.load_asset(entry['asset'])
            with self.subTest(source=source_sha,mutation='saved-native-enum'):
                tex.props['source_color_settings'].props['encoding_override']='ENC_NONE'
                with self.assertRaisesRegex(RuntimeError,'source encoding interpretation'):M.verify_materials(report,u)
                tex.props['source_color_settings'].props['encoding_override']='ENC_SRGB'
            with self.subTest(source=source_sha,mutation='forged-readback'):
                entry['sourceEncodingReadback']='TSE_NONE'
                with self.assertRaisesRegex(RuntimeError,'source encoding interpretation'):M.verify_materials(report,u)
                entry['sourceEncodingReadback']='TSE_S_RGB'
            with self.subTest(source=source_sha,mutation='forged-role'):
                entry['role']='normal'
                with self.assertRaisesRegex(RuntimeError,'source encoding scope'):M.verify_materials(report,u)
                entry['role']='albedo'
        M.verify_materials(report,u)

    def test_context_source_encoding_exact_recipe_scope_proof_hash_and_data_roles(self):
        recipes=M.prepare_manifest(ASSETS_GREENERY_R5)['materials']
        for source_sha,keys in CONTEXT_SRGB_BY_SHA.items():
            recipe=recipes[keys[0]]
            self.assertEqual(recipe['maps']['albedo']['sha256'],source_sha)
            for mutation in ('foreign-key','foreign-provider','wrong-kind','forged-proof'):
                with self.subTest(source=source_sha,mutation=mutation):
                    bad=copy.deepcopy(recipe);key=keys[0]
                    if mutation=='foreign-key':key='foreign_measured_albedo'
                    elif mutation=='foreign-provider':bad['sourceUrl']='https://polyhaven.com/a/foreign_texture'
                    elif mutation=='wrong-kind':bad['kind']='bark' if recipe['kind']!='bark' else 'ground'
                    else:bad['sourceEncodingProof']['sha256']='0'*64
                    if key in M.CONTEXT_KEYS:
                        with patch.object(M,'context_recipes',return_value={key:bad}):
                            with self.assertRaisesRegex(RuntimeError,'source encoding'):M.prepare_manifest()
                    else:
                        with self.assertRaisesRegex(RuntimeError,'source encoding'):M.prepare_manifest({key:bad})
            u=fake_unreal();writer=M.Writer(u,M.PREFIX)
            for role in set(recipe['maps'])-{'albedo'}:
                with self.subTest(source=source_sha,role=role):
                    self.assertEqual(M.texture_source_encoding(role,recipe),'None')
                    tex=writer.texture(role,recipe)
                    self.assertEqual(tex.props['source_color_settings'].props['encoding_override'],'ENC_NONE')
                    self.assertFalse(tex.props['srgb'])
        with patch.object(M,'CONTEXT_ENCODING_PROOF_SHA','0'*64):
            u=fake_unreal()
            with self.assertRaisesRegex(RuntimeError,'native proof drift'):M.build_materials(ASSETS_GREENERY_R5,unreal_module=u)
            self.assertEqual(u.EditorAssetLibrary.values,{})

    def test_context_source_encoding_causal_proof_and_unchanged_alpha_are_required(self):
        original=json.loads(M.CONTEXT_ENCODING_PROOF.read_text())
        for mutation in ('wrong-control','bad-corrected-rgb','missing-stable-region','changed-alpha','changed-filter','converted-source'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory()as directory:
                directory=Path(directory)
                proof=copy.deepcopy(original);row=proof['textures']['nettle']
                if mutation=='wrong-control':proof['gpuLinearControl']['actual'][0]=.5
                elif mutation=='bad-corrected-rgb':row['sourceOnlyStableComparison']['explicitSourceSRGBMaxAbsLinearRgbError']=.02
                elif mutation=='missing-stable-region':row['sourceOnlyStableComparison']['count']=11
                elif mutation=='changed-alpha':row['allSamplesAlphaComparison']['originalVsExplicitMaxAbsAlphaDifference']=.001
                elif mutation=='changed-filter':row['duplicate']['after']['properties']['filter']='DIFFERENT_FILTER'
                else:proof['providerPixelsConvertedOrEdited']=True
                path=directory/'native-report.json';path.write_text(json.dumps(proof))
                for name in ('prepared.json','native-process.json'):
                    (directory/name).write_bytes((M.CONTEXT_ENCODING_PROOF.parent/name).read_bytes())
                expected_error={'wrong-control':'native measurement','bad-corrected-rgb':'causal RGB/unchanged alpha',
                    'missing-stable-region':'causal RGB/unchanged alpha','changed-alpha':'causal RGB/unchanged alpha',
                    'changed-filter':'changed more than','converted-source':'native measurement'}[mutation]
                with patch.object(M,'CONTEXT_ENCODING_PROOF',path),patch.object(M,'CONTEXT_ENCODING_PROOF_SHA',M.sha(path)):
                    with self.assertRaisesRegex(RuntimeError,expected_error):M.context_encoding_inputs()

    def test_context_source_encoding_shared_farm_pixels_dedup_only_with_same_interpretation(self):
        recipes=M.prepare_manifest(ASSETS_GREENERY_R5)['materials'];u=fake_unreal();writer=M.Writer(u,M.PREFIX)
        farm=[writer.texture('albedo',recipes[key])for key in ('context_arable','context_garden_soil','context_soil_exposure')]
        self.assertIs(farm[0],farm[1]);self.assertIs(farm[0],farm[2])
        bare=copy.deepcopy(recipes['context_arable']);bare.pop('sourceEncodingOverride');bare.pop('sourceEncodingProof')
        shared_pixels=writer.texture('albedo',bare)
        self.assertIsNot(shared_pixels,farm[0])
        self.assertEqual(shared_pixels.metadata['source_sha256'],farm[0].metadata['source_sha256'])
        self.assertEqual(shared_pixels.props['source_color_settings'].props['encoding_override'],'ENC_NONE')
        self.assertEqual(farm[0].props['source_color_settings'].props['encoding_override'],'ENC_SRGB')
        cover=recipes['context_arable']['groundCover']
        self.assertEqual(M.texture_source_encoding('albedo',cover),'None')
        cover_texture=writer.texture('albedo',cover)
        self.assertIsNot(cover_texture,farm[0]);self.assertIsNot(cover_texture,shared_pixels)
        self.assertEqual(cover_texture.props['source_color_settings'].props['encoding_override'],'ENC_NONE')
        self.assertEqual(len(writer.texture_report),3)

    def test_texture_sample_connection_uses_native_shortened_mode_specific_pins(self):
        u=fake_unreal();lib=u.MaterialEditingLibrary;source=u.MaterialExpressionConstant()
        for mode,accepted in (('DEFAULT',()),('MIP_LEVEL',('Level',)),('MIP_BIAS',('Bias',)),
                              ('DERIVATIVE',('DDX(UVs)','DDY(UVs)'))):
            sample=u.MaterialExpressionTextureSample();sample.props['mip_value_mode']=mode
            for pin in ('UVs','Tex','Apply View MipBias',*accepted):
                self.assertTrue(lib.connect_material_expressions(source,'',sample,pin))
            for pin in {'Coordinates','TextureObject','MipLevel','MipBias','MipValue','Level','Bias','DDX(UVs)','DDY(UVs)'}-set(accepted):
                self.assertFalse(lib.connect_material_expressions(source,'',sample,pin), (mode,pin))
                self.assertNotIn(pin,sample.inputs)

    def test_ground_texture_receipts_and_metric_period(self):
        manifest = M.prepare_manifest()
        self.assertEqual(set(manifest['materials']), M.CONTEXT_KEYS)
        for recipe in manifest['materials'].values():
            if recipe['kind'] == 'ground':
                self.assertEqual(recipe['tileCm'], 200)
                self.assertEqual(recipe['normalConvention'], 'OpenGL')
                self.assertEqual(set(recipe['maps']), {'albedo', 'normal', 'roughness'})

    def test_hash_and_provenance_fail_before_native_mutation(self):
        raw = plant_fixture(); raw['test_plant']['maps']['normal']['sha256'] = '0'*64
        with self.assertRaisesRegex(RuntimeError, 'hash/path'): M.prepare_manifest(raw)
        raw = plant_fixture(); raw['test_plant']['license'] = 'unknown'
        with self.assertRaisesRegex(RuntimeError, 'provenance'): M.prepare_manifest(raw)
        raw = plant_fixture(); raw['test_plant']['normalConvention'] = None
        with self.assertRaisesRegex(RuntimeError, 'convention'): M.prepare_manifest(raw)

    def test_atlas_alpha_required_and_wind_refused_without_root_weights(self):
        raw = plant_fixture(); del raw['test_plant']['maps']['alpha']
        with self.assertRaisesRegex(RuntimeError, 'texture roles'): M.prepare_manifest(raw)
        raw = plant_fixture(); raw['test_plant']['windCm'] = 1
        with self.assertRaisesRegex(RuntimeError, 'root weights'): M.prepare_manifest(raw)

    def test_derived_atlas_seals_original_colour_alpha_and_generator(self):
        source = M.ROOT/'output/unreal/exterior-alpha-20260926-r4/derived-material-manifest.json'
        key = 'ph_grass_medium_01'
        raw = {key: json.loads(source.read_text())[key]}; recipe = raw[key]
        generator = M.ROOT/'scripts/unreal/exterior-alpha-dilate.py'
        proof = recipe['albedoDerivation']; original = copy.deepcopy(proof)
        u = fake_unreal(); _, report = M.build_materials(raw, unreal_module=u)
        self.assertEqual(report['pipelineFiles'][str(generator)], M.sha(generator))
        for field in ('sourceAlbedo', 'sourceAlpha', 'sourceGenerator'):
            spec = proof[field]
            self.assertEqual(report['inputFiles'][spec['path']], spec['sha256'])
        M.verify_materials(report, u)
        self.assertIn(str(source.with_name('derivation-report.json')), report['inputFiles'])
        self.assertIn(str(M.ROOT/'output/unreal/exterior-assets-20260926-r3/material-manifest.json'), report['inputFiles'])
        proof['sourceAlbedo']['sha256'] = '0'*64
        with self.assertRaisesRegex(RuntimeError, 'derivation source drift'): M.prepare_manifest(raw)
        proof['sourceAlbedo'] = original['sourceAlbedo']
        proof['sourceAlpha']['sha256'] = '0'*64
        with self.assertRaisesRegex(RuntimeError, 'alpha witness differs'): M.prepare_manifest(raw)

    def test_ground_mapping_rotates_normal_basis_with_uv(self):
        for degrees in (-150, -90, -45, 0, 45, 90, 179):
            angle = math.radians(degrees)
            u_axis = (math.cos(angle)*200, math.sin(angle)*200)
            v_axis = (-math.sin(angle)*200, math.cos(angle)*200)
            self.assertAlmostEqual(M.ground_uv(u_axis, 200, degrees)[0], 1)
            self.assertAlmostEqual(M.ground_uv(u_axis, 200, degrees)[1], 0)
            self.assertAlmostEqual(M.ground_uv(v_axis, 200, degrees)[1], 1)
            normal = M.ground_normal((.4, .2, .9), .65, degrees)
            self.assertAlmostEqual(sum(v*v for v in normal), 1)
            self.assertGreater(normal[2], 0)
            local_xy = M.ground_uv(normal[:2], 1, degrees)
            self.assertAlmostEqual(local_xy[0]/local_xy[1], 2)

    def test_foliage_mask_and_color_spaces_survive_reload_contract(self):
        u = fake_unreal(); materials, report = M.build_materials(plant_fixture(), unreal_module=u)
        self.assertEqual(M.verify_materials(report, u)['materials'], len(M.CONTEXT_KEYS)+1)
        foliage = materials['test_plant']
        self.assertEqual(foliage.props['blend_mode'], 'MASKED')
        self.assertEqual(foliage.props['shading_model'], 'FOLIAGE')
        self.assertTrue(foliage.props['two_sided'])
        self.assertIn('OPACITY_MASK', foliage.roots)
        self.assertIn('SUBSURFACE_COLOR', foliage.roots)
        self.assertNotIn('WORLD_POSITION_OFFSET', foliage.roots)
        self.assertNotIn('EMISSIVE_COLOR', foliage.roots)
        for record in report['textures'].values():
            texture = u.EditorAssetLibrary.load_asset(record['asset'])
            self.assertEqual(texture.props['srgb'], record['role'] == 'albedo')
            self.assertEqual(texture.props['flip_green_channel'], record['role'] == 'normal' and record['normalConvention'] == 'OpenGL')
            self.assertEqual(texture.props['do_scale_mips_for_alpha_coverage'], record['role'] == 'alpha')
            self.assertEqual(texture.props['alpha_coverage_thresholds'].x, .333 if record['role'] == 'alpha' else 0)
        self.assertLessEqual(len(report['textures']), 19)
        self.assertTrue(all(not record['replace_existing'] for record in u.EditorAssetLibrary.imports))

    def test_bark_opaque_and_neither_model_changes_originals(self):
        u = fake_unreal(); original = Material('/Game/Original/Leaf'); original.props['sentinel'] = 'original'
        u.EditorAssetLibrary.values[original.path] = original
        materials, report = M.build_materials(plant_fixture(kind='bark'), unreal_module=u)
        self.assertEqual(materials['test_plant'].props['blend_mode'], 'OPAQUE')
        self.assertNotIn('OPACITY_MASK', materials['test_plant'].roots)
        self.assertEqual(original.props['sentinel'], 'original')
        self.assertNotIn(original, u.EditorAssetLibrary.saved)
        self.assertEqual(M.verify_materials(report, u)['materials'], len(M.CONTEXT_KEYS)+1)
        with self.assertRaisesRegex(RuntimeError, 'overwrite'): M.build_materials(plant_fixture(kind='bark'), unreal_module=u)

    def test_saved_graph_and_texture_tampering_are_detected(self):
        u = fake_unreal(); materials, report = M.build_materials(plant_fixture(), unreal_module=u)
        node = next(n for n in materials['test_plant'].nodes if n.props['desc'] == M.TAG+'scan-color')
        code = node.props['code']; node.props['code'] = 'return float3(1,0,0);'
        with self.assertRaisesRegex(RuntimeError, 'graph differs'): M.verify_materials(report, u)
        node.props['code'] = code
        record = next(v for v in report['textures'].values() if v['role'] == 'normal')
        texture = u.EditorAssetLibrary.load_asset(record['asset']); texture.props['srgb'] = True
        with self.assertRaisesRegex(RuntimeError, 'interpretation'): M.verify_materials(report, u)

    def test_namespace_and_context_scope_are_bounded(self):
        with self.assertRaisesRegex(RuntimeError, 'namespace'): M.Writer(fake_unreal(), '/Game/Original')
        with self.assertRaisesRegex(RuntimeError, 'override'): M.prepare_manifest(context_overrides={'context_crop': {'sunPitch': 10}})
        with self.assertRaisesRegex(RuntimeError, 'replace context'): M.prepare_manifest({'context_crop': {'kind': 'foliage'}})
        result = M.prepare_manifest(context_overrides={'context_crop': {'yawDegrees': 72}})
        self.assertEqual(result['materials']['context_crop']['yawDegrees'], 72)

    def test_stochastic_triangle_blend_is_continuous_on_edges_and_not_periodic(self):
        # Lower/upper triangle must agree at shared edge; weight of the absent
        # vertex vanishes cubically. Offset identities are global grid vertices.
        for x in (.1, .3, .6, .9):
            q = (x, 1-x)
            def to_uv(q):
                y=q[1]*1.7/1.154700538
                return (q[0]*1.7+y*.577350269, y)
            a = M.ground_triangle(to_uv((q[0], q[1]-1e-7)))
            b = M.ground_triangle(to_uv((q[0], q[1]+1e-7)))
            self.assertAlmostEqual(sum(a.values()), 1)
            self.assertLess(sum(abs(a.get(k, 0)-b.get(k, 0)) for k in set(a)|set(b)), 2e-6)
        self.assertNotEqual(set(M.ground_triangle((.2, .3))), set(M.ground_triangle((2.2, .3))))

    def test_sloped_ground_and_dem_keep_geometry_normals(self):
        vertex=(.3, -.4, math.sqrt(.75))
        for degrees in (0, 72, -38):
            actual=M.ground_normal((0, 0, 1), 1, degrees, vertex)
            for a,b in zip(actual, vertex): self.assertAlmostEqual(a,b)
        u=fake_unreal(); mats, report=M.build_materials(unreal_module=u)
        terrain=mats['context_distant_terrain']
        self.assertEqual(terrain.roots['NORMAL'][0].get_class().get_name(), 'MaterialExpressionVertexNormalWS')
        self.assertFalse(terrain.props['tangent_space_normal'])
        ground=mats['context_meadow']
        samples=[n for n in ground.nodes if n.get_class().get_name()=='MaterialExpressionTextureSample']
        self.assertEqual(len(samples),18)
        for node in samples:
            self.assertEqual(node.props['mip_value_mode'],'DERIVATIVE')
            self.assertEqual(set(node.inputs), {'UVs','DDX(UVs)','DDY(UVs)'})
        self.assertEqual(report['materials']['context_track']['recipe']['albedoScale'], .28)
        self.assertTrue(any('Grass004' in p for p in report['inputFiles']))
        self.assertTrue(any('wood_chips_diff_4k' in p for p in report['inputFiles']))
        mulch=report['materials']['context_mulch']['recipe']
        self.assertEqual(mulch['tileCm'],200);self.assertEqual(mulch['albedoScale'],.62)
        self.assertEqual(mulch['tint'],[.94,.98,1.])
        self.assertEqual(mulch['maps'],M._ground_source('wood_chips')['maps'])
        for key in ('context_meadow','context_fallow','context_crop','context_arable'):
            recipe=report['materials'][key]['recipe']
            self.assertLessEqual(recipe['macroStrength'],.05)
            self.assertLessEqual(recipe['coverRange'][1]-recipe['coverRange'][0],.081)

    def test_provider_response_and_leaf_only_transmission_are_bounded_and_verified(self):
        raw=plant_fixture(); recipe=raw['test_plant']
        recipe.update(albedoScale=.5,specular=.0734767,subsurfaceScale=.2,normalStrength=1.5)
        recipe['maps']['mask']=copy.deepcopy(recipe['maps']['alpha'])
        u=fake_unreal(); mats, report=M.build_materials(raw,unreal_module=u)
        mat=mats['test_plant']; nodes={n.props['desc'].removeprefix(M.TAG):n for n in mat.nodes}
        self.assertEqual(nodes['provider-albedo-value'].props['r'],.5)
        self.assertEqual(nodes['surface-specular'].props['r'],.0734767)
        self.assertIs(nodes['leaf-transmission'].inputs['Mask'][0],nodes['mask'])
        self.assertEqual(nodes['leaf-transmission-scale'].props['r'],.2)
        alpha=next(v for v in report['textures'].values() if v['role']=='alpha')
        u.EditorAssetLibrary.load_asset(alpha['asset']).props['alpha_coverage_thresholds'].x=.5
        with self.assertRaisesRegex(RuntimeError,'alpha mip coverage'):M.verify_materials(report,u)
        recipe['subsurfaceScale']=.8
        with self.assertRaisesRegex(RuntimeError,'Unbounded'):M.prepare_manifest(raw)

    def test_distant_village_finishes_use_geometry_normals_and_no_extra_texture_budget(self):
        u=fake_unreal(); materials, report=M.build_materials(unreal_module=u)
        for key in ('context_village_wall','context_village_roof','context_village_darkroof'):
            mat=materials[key]
            self.assertEqual(mat.props['blend_mode'],'OPAQUE')
            self.assertTrue(mat.props['tangent_space_normal'])
            self.assertTrue(all(n.get_class().get_name()!='MaterialExpressionTextureSample' for n in mat.nodes))
            self.assertEqual(mat.roots['METALLIC'][0].props['r'],0)
            code=mat.roots['BASE_COLOR'][0].props['code']
            self.assertIn('.95+.10*',code)
            self.assertIn('Position.xy/1200.0',code)
        self.assertEqual(report['materials']['context_village_wall']['recipe']['linearColor'],[.25,.245,.225])
        self.assertEqual(report['materials']['context_village_roof']['recipe']['linearColor'],[.14,.052,.027])

    def test_leaf_artist_calibration_preserves_petals_neutrals_and_linear_luminance(self):
        for original in ((.35,.03,.13),(.03,.025,.035),(.12,.12,.12),(.17,.10,.035),(0.,0.,0.)):
            self.assertEqual(M.calibrated_leaf(original,original),original)
        green=(.115832,.161016,.010321)
        result=M.calibrated_leaf(green,green)
        luma=lambda color:sum(a*b for a,b in zip(color,(.2126,.7152,.0722)))
        self.assertAlmostEqual(luma(result)/luma(green),.78)
        self.assertAlmostEqual((max(result)-min(result))/(max(green)-min(green)),.78*.88)
        # The approved artist response may darken the leaf but must not mutate
        # source atlases, UVs, alpha or the documented provider value.
        old=json.loads((ASSETS_R5.parent.parent/'exterior-assets-20260926-r4/material-manifest.json').read_text())
        new=json.loads(ASSETS_R5.read_text()); calibration=new['ph_periwinkle_plant'].pop('leafCalibration')
        self.assertEqual(new,old)
        self.assertFalse(calibration['providerBugFix'])
        self.assertEqual(old['ph_periwinkle_plant']['albedoScale'],.8)
        for filename in ('geometry-manifest.json','asset-manifest.json'):
            self.assertEqual((ASSETS_R5.parent/filename).read_bytes(),(ASSETS_R5.parent.parent/'exterior-assets-20260926-r4'/filename).read_bytes())

    def test_leaf_calibration_roots_and_original_response_are_sealed(self):
        raw={'ph_periwinkle_plant':json.loads(ASSETS_R5.read_text())['ph_periwinkle_plant']}
        u=fake_unreal(); materials,report=M.build_materials(raw,unreal_module=u)
        mat=materials['ph_periwinkle_plant']; nodes={n.props['desc'].removeprefix(M.TAG):n for n in mat.nodes}
        self.assertIs(mat.roots['BASE_COLOR'][0],nodes['artist-green-leaf-calibration'])
        self.assertIs(nodes['leaf-transmission'].inputs['Color'][0],nodes['artist-green-leaf-calibration'])
        self.assertEqual(mat.roots['OPACITY_MASK'],(nodes['alpha'],'R'))
        self.assertEqual(nodes['model-uv'].props['u_tiling'],1)
        self.assertEqual(nodes['provider-albedo-value'].props['r'],.8)
        self.assertEqual(nodes['leaf-transmission-scale'].props['r'],.08)
        self.assertEqual(nodes['artist-leaf-brightness'].props['r'],.60)
        self.assertEqual(raw['ph_periwinkle_plant']['leafCalibration']['brightness'],.78)
        self.assertIn(raw['ph_periwinkle_plant']['leafCalibration']['sourceMaterialManifest']['path'],report['inputFiles'])
        M.verify_materials(report,u)
        raw['ph_periwinkle_plant']['albedoScale']=.5
        with self.assertRaisesRegex(RuntimeError,'changed provider'):M.prepare_manifest(raw)

    def test_r7_leaf_darkening_is_narrowly_allowed_and_keeps_source_petals_and_provider(self):
        recipe=json.loads(ASSETS_R5.read_text())['ph_periwinkle_plant']
        raw={'ph_periwinkle_plant':copy.deepcopy(recipe)}
        raw['ph_periwinkle_plant']['leafCalibration']['brightness']=.60
        M.prepare_manifest(raw)
        for color in ((.35,.03,.13),(.03,.025,.035),(.12,.12,.12)):
            self.assertEqual(M.calibrated_leaf(color,color,.60,.88),color)
        green=(.115832,.161016,.010321)
        result=M.calibrated_leaf(green,green,.60,.88)
        self.assertAlmostEqual(sum(v*w for v,w in zip(result,(.2126,.7152,.0722)))/sum(v*w for v,w in zip(green,(.2126,.7152,.0722))),.60)
        self.assertEqual(raw['ph_periwinkle_plant']['maps'],recipe['maps'])
        self.assertEqual(raw['ph_periwinkle_plant']['albedoScale'],.8)
        raw['ph_periwinkle_plant']['leafCalibration']['brightness']=.59
        with self.assertRaises(RuntimeError):M.prepare_manifest(raw)

    def test_orthophoto_affine_and_missing_coverage_do_not_extend_or_blacken_ground(self):
        ortho=M.prepare_orthophoto(ORTHO); layers=ortho['layers']; by_id={v['id']:v for v in layers}
        self.assertEqual(M.orthophoto_uv((0,0),by_id['far16km']),(.4251281678729938,.561337685960636))
        for actual,expected in zip(M.orthophoto_uv((0,0),by_id['detail2km']),(.5,.5)):self.assertAlmostEqual(actual,expected)
        coverage={'far16km':1.,'detail2km':1.}
        self.assertEqual(M.orthophoto_weights((30000,0),layers,coverage),{'detail':0.,'far':0.,'fallback':1.})
        self.assertEqual(M.orthophoto_weights((60000,0),layers,coverage),{'detail':.5,'far':0.,'fallback':.5})
        self.assertEqual(M.orthophoto_weights((90000,0),layers,coverage),{'detail':1.,'far':0.,'fallback':0.})
        self.assertEqual(M.orthophoto_weights((90000,0),layers,{'far16km':0,'detail2km':.98999})['fallback'],1.)
        self.assertEqual(M.orthophoto_weights((90000,0),layers,{'far16km':0,'detail2km':.99})['detail'],1.)
        self.assertEqual(M.orthophoto_weights((1e7,1e7),layers,coverage)['fallback'],1.)

    def test_orthophoto_detail_edge_crossfade_is_metric_and_continuous(self):
        layers=json.loads(ORTHO.read_text())['layers']; detail=next(v for v in layers if v['id']=='detail2km')
        a,b,c=detail['worldCmToUvRows'][0];d,e,f=detail['worldCmToUvRows'][1];det=a*e-b*d
        def world(u,v):return ((e*(u-c)-b*(v-f))/det,(-d*(u-c)+a*(v-f))/det)
        coverage={'far16km':1.,'detail2km':1.}
        half=M.orthophoto_weights(world(.975,.5),layers,coverage)
        self.assertAlmostEqual(half['detail'],.5);self.assertAlmostEqual(half['far'],.5)
        for uv in ((1,.5),(1.001,.5),(-.001,.5)):
            weights=M.orthophoto_weights(world(*uv),layers,coverage)
            self.assertEqual(weights['detail'],0);self.assertEqual(weights['far'],1)
        just_inside=M.orthophoto_weights(world(1-1e-7,.5),layers,coverage)
        self.assertLess(just_inside['detail'],1e-9)

    def test_earlier_ortho_revision_preserves_images_uv_height_and_near_scene(self):
        old=json.loads(ORTHO.read_text());new=json.loads(ORTHO_EARLIER.read_text())
        self.assertEqual(old['layers'],new['layers'])
        self.assertEqual(old['worldFrame'],new['worldFrame'])
        self.assertEqual(old['worldOriginNationalMetres'],new['worldOriginNationalMetres'])
        self.assertEqual(old['materialProposal']['distanceBlendCm'],[30000,90000])
        self.assertEqual(new['materialProposal']['terrainHeightBlendUnchangedCm'],[30000,90000])
        self.assertEqual(new['derivedFrom']['sha256'],M.sha(ORTHO))
        self.assertFalse(new['derivedFrom']['sourcePixelsChanged'])
        ortho=M.prepare_orthophoto(ORTHO_EARLIER);coverage={'far16km':1.,'detail2km':1.}
        self.assertEqual(ortho['distanceBlendCm'],[18000,36000])
        for distance,photo in ((0,0.),(17999,0.),(18000,0.),(22500,.15625),(27000,.5),(31500,.84375),(36000,1.),(60000,1.)):
            actual=M.orthophoto_weights((distance,0),ortho['layers'],coverage,ortho['distanceBlendCm'])
            self.assertAlmostEqual(actual['detail'],photo)
            self.assertAlmostEqual(actual['fallback'],1-photo)
            self.assertEqual(actual['far'],0)
        self.assertEqual(M.orthophoto_weights((27000,0),ortho['layers'],{'far16km':0,'detail2km':.98},ortho['distanceBlendCm'])['fallback'],1.)
        with self.assertRaisesRegex(RuntimeError,'Unreviewed orthophoto distance blend'):
            M.orthophoto_weights((27000,0),ortho['layers'],coverage,(0,36000))

    def test_terrain_rgb_matches_ground_camera_blend_and_preserves_radial_pbr_response(self):
        u=fake_unreal();materials,report=M.build_materials(ASSETS_R5,unreal_module=u,ortho_manifest=ORTHO_EARLIER)
        self.assertEqual(report['orthophoto']['distanceBlendCm'],[18000,36000])
        terrain=materials['context_distant_terrain'];nodes={n.props['desc'].removeprefix(M.TAG):n for n in terrain.nodes}
        radial=nodes['ortho-radial-distance'];value=nodes['ortho-distance-blend-cm'].props['constant']
        self.assertEqual((value.r,value.g,value.b),(18000,36000,0))
        self.assertEqual(radial.props['code'],M.ORTHO_RADIAL)
        self.assertIs(radial.inputs['BlendRange'][0],nodes['ortho-distance-blend-cm'])
        camera_blend=nodes['terrain-ortho-camera-distance']
        self.assertEqual(camera_blend.props['code'],M.ORTHO_CAMERA)
        self.assertIs(camera_blend.inputs['Position'][0],nodes['world-position'])
        self.assertEqual(camera_blend.inputs['Camera'][0].get_class().get_name(),'MaterialExpressionCameraPositionWS')
        camera_range=nodes['terrain-ortho-camera-blend-cm'].props['constant']
        self.assertEqual([camera_range.r,camera_range.g,camera_range.b],[5000.,15000.,0.])
        self.assertIs(nodes['licensed-ortho-basecolor'].inputs['DistanceBlend'][0],camera_blend)
        self.assertNotIn(radial,[v[0]for v in camera_blend.inputs.values()])
        policy=report['materials']['context_distant_terrain']['recipe']['terrainOrthophotoCameraBlend']
        self.assertEqual(policy['cameraDistanceBlendCm'],list(M.GROUND_ORTHO_BLEND_CM))
        self.assertEqual(policy['sourceManifestRadialBlendCm'],[18000,36000])
        self.assertEqual(report['terrainOrthophotoCameraBlend'],{'materialKeys':['context_distant_terrain'],**policy})
        self.assertTrue(policy['providerPixelsAndAffineUnchanged']);self.assertFalse(policy['actorBindingsChanged'])
        self.assertEqual(report['inputFiles'][str(ORTHO_EARLIER)],M.sha(ORTHO_EARLIER))
        self.assertLessEqual(len(report['materials']['context_distant_terrain']['graph']['nodes']),80)
        self.assertIs(nodes['near-terrain-pbr-weight'].inputs['DistanceBlend'][0],radial)
        self.assertIs(nodes['near-terrain-normal-strength'].inputs['Near'][0],nodes['near-terrain-pbr-weight'])
        self.assertIs(nodes['ortho-terrain-slope-normal'].inputs['VertexNormal'][0],nodes['surveyed-vertex-normal'])
        self.assertEqual(M.verify_materials(report,u)['textures'],60)
        value.r=17000
        with self.assertRaisesRegex(RuntimeError,'graph differs'):M.verify_materials(report,u)

    def test_seasonal_mask_zero_mip_uncompressed_sampler_and_original_coverage_are_sealed(self):
        u=fake_unreal();mats,report=M.build_materials(ASSETS_R5,unreal_module=u,ortho_manifest=ORTHO_EARLIER,seasonal_fields_manifest=SEASONAL)
        self.assertEqual(M.verify_materials(report,u)['textures'],62)
        arable=copy.deepcopy(report['materials']['context_arable']['recipe']);baseline=M.prepare_manifest()['materials']['context_arable']
        self.assertEqual(arable.pop('coverRange'),[.52,.60]);self.assertEqual(baseline.pop('coverRange'),[.04,.10])
        self.assertIn('R7 opt-in seasonal',arable.pop('artDirection'));baseline.pop('artDirection')
        self.assertEqual(arable,baseline)
        self.assertEqual(report['seasonalFields']['nearArableStage']['material'],'context_arable')
        self.assertEqual([k for k,v in report['materials'].items() if 'seasonalFields' in v['recipe'].get('orthophoto',{})],['context_distant_terrain'])
        nodes={n.props['desc'].removeprefix(M.TAG):n for n in mats['context_distant_terrain'].nodes}
        for layer in ('far16km','detail2km'):
            label='ortho-'+layer;mask=nodes['season_mask-'+label];photo=nodes['albedo-'+label]
            self.assertEqual(mask.props['mip_value_mode'],'MIP_LEVEL')
            self.assertFalse(mask.props['automatic_view_mip_bias'])
            self.assertEqual(mask.inputs['Level'][0].props['r'],0)
            self.assertEqual(mask.props['sampler_type'],'LINEAR_GRAYSCALE')
            self.assertIs(mask.inputs['UVs'][0],photo.inputs['UVs'][0])
            self.assertEqual(nodes[label+'-coverage-and-extent'].inputs['Coverage'],(nodes['albedo-'+label+'-coverage-mip0'],'A'))
            self.assertEqual(nodes[label+'-seasonal-field-color'].inputs,{'Source':(photo,'RGB'),'Mask':(mask,'R')})
            self.assertEqual(nodes[label+'-seasonal-field-color'].props['code'],M.SEASONAL_FIELD_COLOR)
            tex=mask.props['texture'];self.assertFalse(tex.props['srgb'])
            self.assertEqual(tex.props['compression_settings'],'GRAYSCALE')
            self.assertEqual(tex.props['mip_gen_settings'],'NO_MIPMAPS');self.assertTrue(tex.props['never_stream'])
            self.assertEqual(tex.props['address_x'],'CLAMP')
        self.assertEqual(nodes['licensed-ortho-basecolor'].inputs['Far'],(nodes['ortho-far16km-seasonal-field-color'],''))
        self.assertEqual(nodes['licensed-ortho-basecolor'].inputs['Detail'],(nodes['ortho-detail2km-seasonal-field-color'],''))
        self.assertLessEqual(max(len(r['graph']['nodes']) for r in report['materials'].values()),80)
        mask.props['automatic_view_mip_bias']=True
        with self.assertRaisesRegex(RuntimeError,'graph differs'):M.verify_materials(report,u)
        mask.props['automatic_view_mip_bias']=False;tex.props['never_stream']=False
        with self.assertRaisesRegex(RuntimeError,'interpretation'):M.verify_materials(report,u)

    def test_seasonal_wrong_source_mapping_shader_and_unreviewed_candidate_fail_before_writes(self):
        with self.assertRaisesRegex(RuntimeError,'require licensed orthophoto'):
            M.build_materials(unreal_module=fake_unreal(),seasonal_fields_manifest=SEASONAL)
        with self.assertRaisesRegex(RuntimeError,'source orthophoto differs'):
            M.build_materials(unreal_module=fake_unreal(),ortho_manifest=ORTHO,seasonal_fields_manifest=SEASONAL)
        source=json.loads(SEASONAL.read_text())
        with tempfile.TemporaryDirectory(dir=M.ROOT/'output/unreal',prefix='seasonal-contract-') as temporary:
            path=Path(temporary)/'manifest.json'
            for field in ('mapping','shader','review','format'):
                data=copy.deepcopy(source)
                if field=='mapping':data['layers'][0]['worldCmToUvRows'][0][2]+=.00001
                elif field=='shader':data['shader']['sha256']='0'*64
                elif field=='review':data['status']='CPU_PROTOTYPE_REJECTED'
                else:data['layers'][0]['samplerMipPolicy']='automatic'
                path.write_text(json.dumps(data));u=fake_unreal()
                with self.assertRaises(RuntimeError):M.build_materials(unreal_module=u,ortho_manifest=ORTHO_EARLIER,seasonal_fields_manifest=path)
                self.assertEqual(u.EditorAssetLibrary.imports,[])

    def test_field_macro_scalar_exact_neutral_gate_and_limits(self):
        for factor in (0,.1,128/255,.8,1):
            for uv in ((-.00001,.5),(1.00001,.5),(.5,-.00001),(.5,1.00001)):
                self.assertEqual(M.field_macro_multiplier(factor,(0,1,1,1),uv),1.)
            for containment in ((0,.9899,1,1),(0,1,.9899,1),(0,1,1,0)):
                self.assertEqual(M.field_macro_multiplier(factor,containment,(.5,.5)),1.)
        self.assertEqual(M.field_macro_multiplier(128/255,(0,1,1,1),(.5,.5)),1.)
        self.assertEqual(M.field_macro_multiplier(0,(0,1,1,1),(.5,.5)),.75)
        self.assertEqual(M.field_macro_multiplier(1,(0,1,1,1),(.5,.5)),1.10)
        self.assertEqual(M.field_macro_multiplier(0,(0,1,1,.5),(.5,.5)),.875)

    def test_full_r7_budget_scoped_field_macro_channels_and_resident_rgba_readback(self):
        u=fake_unreal();mats,report=M.build_materials(ASSETS_R7,unreal_module=u,ortho_manifest=ORTHO_EARLIER,
                                                   seasonal_fields_manifest=SEASONAL,field_macro_manifest=FIELD_MACRO)
        self.assertEqual(M.verify_materials(report,u),{'status':'verified-saved-exterior-materials','materials':30,'textures':71})
        self.assertLessEqual(max(len(v['graph']['nodes']) for v in report['materials'].values()),110)
        self.assertEqual({k for k,v in report['materials'].items() if 'fieldMacro' in v['recipe']},M.FIELD_MACRO_KEYS)
        self.assertEqual(report['fieldMacro']['factorRange'],[.75,1.10])
        for key in M.FIELD_MACRO_KEYS:
            mat=mats[key];nodes={n.props['desc'].removeprefix(M.TAG):n for n in mat.nodes}
            color=nodes['field-macro-basecolor'];factor=nodes['field_macro-factor'];domain=nodes['field_macro-containment']
            self.assertEqual(mat.roots['BASE_COLOR'],(color,''))
            self.assertNotIn('licensed-ortho-basecolor',nodes)
            self.assertIs(color.inputs['Source'][0],nodes['natural-ground-color'])
            self.assertEqual(color.inputs['FactorChannel'],(factor,'R'))
            for name,channel in [('Domain','G'),('Coverage','B'),('Weight','A')]:
                masked=nodes['field-macro-'+name.lower()+'-channel']
                self.assertEqual(color.inputs[name],(masked,''))
                self.assertEqual(masked.inputs[''],(domain,'RGBA'))
                self.assertEqual([masked.props[p] for p in ('r','g','b','a')],[False,channel=='G',channel=='B',channel=='A'])
            self.assertEqual(color.props['code'],M.FIELD_MACRO_COLOR)
            self.assertEqual(domain.props['mip_value_mode'],'MIP_LEVEL');self.assertEqual(domain.inputs['Level'][0].props['r'],0.)
            self.assertEqual(factor.props['mip_value_mode'],'DEFAULT')
            self.assertIs(factor.props['texture'],domain.props['texture'])
            for sample in (factor,domain):
                self.assertEqual(sample.props['sampler_type'],'LINEAR_COLOR');self.assertFalse(sample.props['automatic_view_mip_bias'])
            tex=factor.props['texture'];self.assertEqual(tex.props['compression_settings'],'RGBA8');self.assertFalse(tex.props['srgb'])
            self.assertTrue(tex.props['never_stream']);self.assertEqual(tex.props['mip_gen_settings'],'FROM_GROUP')
            self.assertEqual(mat.roots['NORMAL'],(nodes['world-ground-normal'],''))
            self.assertEqual(mat.roots['ROUGHNESS'],(nodes['ground-roughness'],''))
        leaf_nodes={n.props['desc'].removeprefix(M.TAG):n for n in mats['ph_periwinkle_plant'].nodes}
        self.assertEqual(leaf_nodes['artist-leaf-brightness'].props['r'],.60)
        tex.props['compression_settings']='MASKS'
        with self.assertRaisesRegex(RuntimeError,'interpretation'):M.verify_materials(report,u)

    def test_field_macro_wrong_frame_scope_factor_and_sampling_fail_before_native_writes(self):
        source=json.loads(FIELD_MACRO.read_text())
        with tempfile.TemporaryDirectory(dir=M.ROOT/'output/unreal',prefix='macro-contract-') as temporary:
            path=Path(temporary)/'manifest.json'
            for field in ('frame','scope','factor','sampling','texture'):
                data=copy.deepcopy(source)
                if field=='frame':data['worldCmToUvRows'][0][0]*=.01
                elif field=='scope':data['allowedMaterialKeys'].append('context_track')
                elif field=='factor':data['factorRange']=[.65,1.15]
                elif field=='sampling':data['nativeTexturePolicy']['containmentSamplerMip']=1
                else:data['texture']['sha256']='0'*64
                path.write_text(json.dumps(data));u=fake_unreal()
                with self.assertRaises(RuntimeError):M.build_materials(unreal_module=u,field_macro_manifest=path)
                self.assertEqual(u.EditorAssetLibrary.imports,[])

    def test_orthophoto_invalid_mapping_license_and_pixels_fail_before_native_writes(self):
        source=json.loads(ORTHO.read_text())
        with tempfile.TemporaryDirectory(dir=M.ROOT/'output/unreal',prefix='ortho-contract-') as temporary:
            path=Path(temporary)/'manifest.json'
            for field in ('license','affine','image'):
                data=copy.deepcopy(source)
                if field=='license':data['license']['attribution']='unknown'
                elif field=='affine':data['layers'][0]['worldCmToUvRows'][0][0]*=.01
                else:data['layers'][0]['rgbaSha256']='0'*64
                path.write_text(json.dumps(data));u=fake_unreal()
                with self.assertRaises(RuntimeError):M.build_materials(unreal_module=u,ortho_manifest=path)
                self.assertEqual(u.EditorAssetLibrary.imports,[])
                self.assertEqual(u.EditorAssetLibrary.values,{})

    def test_r5_native_contract_budget_clamp_coverage_and_small_affine_tamper(self):
        u=fake_unreal();materials,report=M.build_materials(ASSETS_R5,unreal_module=u,ortho_manifest=ORTHO)
        self.assertEqual(M.verify_materials(report,u),{'status':'verified-saved-exterior-materials','materials':28,'textures':60})
        self.assertLessEqual(max(len(v['graph']['nodes']) for v in report['materials'].values()),80)
        self.assertEqual(report['inputFiles'][str(ORTHO)],M.sha(ORTHO))
        source=json.loads(ORTHO.read_text())
        self.assertTrue(all(report['inputFiles'][k]==v for k,v in source['inputFiles'].items()))
        self.assertEqual([k for k,v in report['materials'].items() if 'orthophoto' in v['recipe']],['context_distant_terrain'])
        terrain=materials['context_distant_terrain'];nodes={n.props['desc'].removeprefix(M.TAG):n for n in terrain.nodes}
        self.assertIs(terrain.roots['NORMAL'][0],nodes['ortho-terrain-slope-normal'])
        self.assertIs(nodes['ortho-terrain-slope-normal'].inputs['VertexNormal'][0],nodes['surveyed-vertex-normal'])
        self.assertNotIn('EMISSIVE_COLOR',terrain.roots)
        self.assertNotIn('OPACITY_MASK',terrain.roots)
        for label in ('far16km','detail2km'):
            sample=nodes['albedo-ortho-'+label];gate=nodes['ortho-'+label+'-coverage-and-extent']
            coverage=nodes['albedo-ortho-'+label+'-coverage-mip0']
            self.assertEqual(gate.inputs['Coverage'],(coverage,'A'))
            self.assertEqual(coverage.props['mip_value_mode'],'MIP_LEVEL')
            self.assertEqual(coverage.inputs['Level'][0].props['r'],0.)
            self.assertIs(coverage.props['texture'],sample.props['texture'])
            self.assertIs(gate.inputs['UV'][0],sample.inputs['UVs'][0])
            self.assertIn('all(UV<=1.0)',gate.props['code'])
            tex=sample.props['texture'];self.assertEqual(tex.props['address_x'],'CLAMP')
            self.assertTrue(tex.props['srgb']);self.assertFalse(tex.props['do_scale_mips_for_alpha_coverage'])
            self.assertEqual(tex.blueprint_get_size_x(),4096)
        affine=nodes['ortho-far16km-RowU'].props['constant'];affine.r+=1e-10
        with self.assertRaisesRegex(RuntimeError,'graph differs'):M.verify_materials(report,u)

    def test_npot_native_stretch_preserves_source_and_uv_and_is_read_back(self):
        raw=plant_fixture();raw['test_plant']['powerOfTwoMode']='stretch'
        source=raw['test_plant']['maps']['albedo'];before=M.sha(source['path'])
        u=fake_unreal();materials,report=M.build_materials(raw,unreal_module=u)
        records=[v for v in report['textures'].values() if v['powerOfTwoMode']=='stretch']
        self.assertEqual(len(records),4)
        self.assertTrue(all(u.EditorAssetLibrary.load_asset(v['asset']).props['power_of_two_mode']=='STRETCH' for v in records))
        uv=next(n for n in materials['test_plant'].nodes if n.props['desc']==M.TAG+'model-uv')
        self.assertEqual((uv.props['u_tiling'],uv.props['v_tiling']),(1,1))
        self.assertEqual(M.sha(source['path']),before)
        M.verify_materials(report,u)
        u.EditorAssetLibrary.load_asset(records[0]['asset']).props['power_of_two_mode']='NONE'
        with self.assertRaisesRegex(RuntimeError,'interpretation'):M.verify_materials(report,u)
        raw['test_plant']['powerOfTwoMode']='pad'
        with self.assertRaisesRegex(RuntimeError,'resize mode'):M.prepare_manifest(raw)


if __name__ == '__main__': unittest.main()
