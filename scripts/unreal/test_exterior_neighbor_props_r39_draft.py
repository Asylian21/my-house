"""Bounded source/API-contract fixtures. These do not exercise Unreal."""
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[2]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=load('r39_contract_fixture','scripts/unreal/exterior-neighbor-props-contract-r39-draft.py')
m=load('r39_material_fixture','scripts/unreal/exterior-neighbor-props-materials-r39-draft.py')
n=load('r39_native_fixture','scripts/unreal/exterior-neighbor-props-native-r39-draft.py')

class Vec:
    def __init__(self,values):self.x,self.y,*remaining=values;self.z=remaining[0]if remaining else 0
class Id:
    def __init__(self,id_value):self.id_value=id_value
class Class:
    def __init__(self,path):self.path=path
    def get_path_name(self):return self.path
class Description:
    def __init__(self,part):self.part=part
    def get_triangle_count(self):return self.part['triangles']
    def get_triangle_polygon_group(self,tri):return Id(0)
    def get_triangle_vertex_instance(self,tri,corner):return self.part['indices'][3*tri.id_value+corner]
    def get_vertex_instance_vertex(self,vertex):return vertex
    def get_vertex_position(self,vertex):return Vec(self.part['nativeVerticesCm'][vertex])
    def get_vertex_instance_uv(self,vertex,channel):return Vec(self.part['uv0'][vertex])
class Mesh:
    def __init__(self,part):self.part=part;self.path=c.PREFIX+'/Geometry/'+part['key'].replace(':','_')+'.own'
    def get_path_name(self):return self.path
    def get_class(self):return Class('/Script/Engine.StaticMesh')
    def get_num_lods(self):return 1
    def get_editor_property(self,key):return [object()]if key=='static_materials'else None
    def get_num_triangles(self,lod):return self.part['triangles']
    def get_num_sections(self,lod):return 1
    def get_static_mesh_description(self,lod):return Description(self.part)
class Component:
    def __init__(self,mesh,path):self.mesh=mesh;self.path=path
    def get_editor_property(self,key):return self.mesh if key=='static_mesh'else None
    def get_path_name(self):return self.path
class Actor:
    def __init__(self,path,component,pose):self.path=path;self.component=component;self.pose=pose
    def get_path_name(self):return self.path
    def get_components_by_class(self,cls):return [self.component]if self.component else []
    def get_actor_transform(self):return self.pose

def source_graph(recipe):
    tag=c.TAG+recipe['key']+':';_,textures=m.assets(recipe)
    nodes=[{'role':tag+'uv','class':'MaterialExpressionTextureCoordinate','values':{'coordinate_index':0,'u_tiling':1.,'v_tiling':1.},'inputs':[]}]
    for role in recipe['maps']:
        sampler='SAMPLERTYPE_NORMAL'if role=='normalGL'else'SAMPLERTYPE_COLOR'if role=='albedo'else'SAMPLERTYPE_MASKS'
        nodes.append({'role':tag+role,'class':'MaterialExpressionTextureSample','values':{'texture':textures[role],'sampler_type':'MaterialSamplerType.'+sampler+': 4'},
          'inputs':[['UVs',tag+'uv',''],['Tex',None,None],['Apply View MipBias',None,None]]})
    nodes.append({'role':tag+'specular','class':'MaterialExpressionConstant','values':{'r':recipe['ueSpecular']},'inputs':[]})
    if not recipe['metallicFactor']:nodes.append({'role':tag+'metallic-zero','class':'MaterialExpressionConstant','values':{'r':0.},'inputs':[]})
    roots={'BASE_COLOR':[tag+'albedo','RGB'],'NORMAL':[tag+'normalGL','RGB'],'ROUGHNESS':[tag+'roughness','R'],
      'METALLIC':[tag+'metallic','R']if recipe['metallicFactor']else[tag+'metallic-zero',''],'SPECULAR':[tag+'specular',''],
      'AMBIENT_OCCLUSION':None,'OPACITY':None,'OPACITY_MASK':None,'WORLD_POSITION_OFFSET':None}
    return {'nodes':nodes,'roots':roots},textures

class R39Draft(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.b=c.load_source()
    def test_01_actual_whole_model_counts_and_original_attributes(self):
        parts=self.b['parts'];self.assertEqual([p['triangles']for p in parts[c.MODEL_IDS[0]]],[344,11340])
        self.assertEqual(sum(p['triangles']for rows in parts.values()for p in rows),26601)
        self.assertEqual(sum(p['vertices']for rows in parts.values()for p in rows),16841)
        self.assertTrue(all(p['sourceAttributeNames']==['NORMAL','POSITION','TEXCOORD_0']and not p['sourceTangentPresent']for rows in parts.values()for p in rows))
        self.assertIsNone(self.b['selectedNativeBase']);self.assertEqual(len(self.b['proposal']['placements']),6)
    def test_02_hose_coil_pose_and_whole_source_envelope_are_preserved(self):
        hose=self.b['parts'][c.MODEL_IDS[0]];coil=hose[1]
        self.assertEqual(coil['sourceNodeTranslationMeters'],[-.013036099262535572,-.05608365684747696,.06431593745946884])
        self.assertEqual(coil['proposedNativeNodeTranslationCm'],[-1.3036099672317505,6.431593894958496,-5.608365535736084])
        self.assertFalse(coil['nodeTranslationRouteActuallyMeasured'])
        self.assertEqual(hose[0]['proposedNativeNodeTranslationCm'],[0.,0.,0.])
        self.assertGreater(self.b['proposal']['models'][c.MODEL_IDS[0]]['dimensionsCm'][2],50)
    def test_03_complete_four_part_corners_and_sections_use_original_indices(self):
        proofs=[]
        for rows in self.b['parts'].values():
            for part in rows:proofs.append(n.full_part_identity(SimpleNamespace(TriangleID=Id),Mesh(part),part))
        self.assertEqual(sum(p['triangles']for p in proofs),26601)
        self.assertTrue(all(p['sourceIdentityFromCountAlone']is False and p['sourceIdentityFromNameOrLabel']is False for p in proofs))
    def test_04_reversed_winding_uv_and_position_do_not_establish_identity(self):
        part=self.b['parts'][c.MODEL_IDS[1]][0];expected=n.expected_corners(part)
        rotated=[n.cyclic(list(face[1:]+face[:1]))for face in expected];self.assertEqual(n.validate_corner_rows(part,rotated),c.digest(expected))
        for kind in ['winding','uv','position']:
            actual=copy.deepcopy(expected);face=list(actual[0])
            if kind=='winding':face=[face[0],face[2],face[1]]
            else:
                corner=list(face[0]);corner[3 if kind=='uv'else 0]+=.125;face[0]=tuple(corner)
            actual[0]=n.cyclic(face)
            with self.assertRaises(RuntimeError,msg=kind):n.validate_corner_rows(part,actual)
    def test_05_original_map_roles_png_encoding_and_optical_limits(self):
        self.assertEqual(len(m.validate_recipes(self.b)),14)
        headers=[m.png_header(row)for recipe in self.b['recipes'].values()for row in recipe['maps'].values()]
        self.assertEqual(len(headers),11);self.assertTrue(all(h['pixels']==[2048,2048]and h['sourceBits']==16 and not h['nativeGpuPixelFormatVerified']for h in headers))
        pot=self.b['recipes'][c.MODEL_IDS[1]];can=self.b['recipes'][c.MODEL_IDS[2]]
        self.assertEqual(pot['metallicFactor'],0);self.assertNotIn('metallic',pot['maps']);self.assertEqual(can['ueSpecular'],0)
        self.assertFalse(can['wateringCanGrazingEnergyPreserved']);self.assertFalse(can['wateringCanIorExactlyReproduced']);self.assertIn('metallic',can['maps'])
    def test_06_three_pbr_graphs_reject_ao_uv1_can_ior_only_shine(self):
        for recipe in self.b['recipes'].values():
            graph,textures=source_graph(recipe);m.validate_graph(graph,recipe,textures)
            tampered=copy.deepcopy(graph);tampered['roots']['AMBIENT_OCCLUSION']=tampered['roots']['ROUGHNESS']
            with self.assertRaises(RuntimeError):m.validate_graph(tampered,recipe,textures)
            tampered=copy.deepcopy(graph);tampered['nodes'][0]['values']['coordinate_index']=1
            with self.assertRaises(RuntimeError):m.validate_graph(tampered,recipe,textures)
        recipe=self.b['recipes'][c.MODEL_IDS[2]];graph,textures=source_graph(recipe);graph['nodes'][-1]['values']['r']=.42
        with self.assertRaises(RuntimeError):m.validate_graph(graph,recipe,textures)
    def test_07_receipt_recipe_mutation_cannot_change_source_interpretation(self):
        b=copy.deepcopy(self.b);b['recipes'][c.MODEL_IDS[2]]['ueSpecular']=.42
        with self.assertRaises(RuntimeError):m.validate_recipes(b)
        b=copy.deepcopy(self.b);b['recipes'][c.MODEL_IDS[1]]['maps']['metallic']=b['recipes'][c.MODEL_IDS[1]]['maps']['roughness']
        with self.assertRaises(RuntimeError):m.validate_recipes(b)
    def test_08_hose_binding_keeps_both_parts_and_rejects_lost_coil_pose(self):
        parts=self.b['parts'][c.MODEL_IDS[0]];actors=[];inventory=[]
        for i,part in enumerate(parts):
            path='own_actor_'+str(i);component=Component(Mesh(part),path+'.component');pose=[part['proposedNativeNodeTranslationCm'],[0.,0.,0.,1.],[1.,1.,1.]]
            actors.append(Actor(path,component,pose));inventory.append({'actor':path,'class':'/Script/Engine.StaticMeshActor','label':'arbitrary_'+str(i),
              'transform':pose,'parent':None,'primitiveComponents':[component.get_path_name()],'components':[]})
        found,bindings,containers=n.bind_imported_parts(SimpleNamespace(StaticMeshComponent=Component,TriangleID=Id),parts,actors,{'objects':inventory})
        self.assertEqual(set(found),{p['key']for p in parts});self.assertEqual(len(bindings),2);self.assertEqual(containers,[])
        lost=copy.deepcopy(inventory);lost[1]['transform'][0]=[0.,0.,0.]
        with self.assertRaises(RuntimeError):n.bind_imported_parts(SimpleNamespace(StaticMeshComponent=Component,TriangleID=Id),parts,actors,{'objects':lost})
    def test_09_outside_owned_namespace_never_becomes_a_source_master(self):
        part=self.b['parts'][c.MODEL_IDS[1]][0];mesh=Mesh(part);mesh.path='/Game/Brezi/Existing.asset'
        with self.assertRaises(RuntimeError):n.full_part_identity(SimpleNamespace(TriangleID=Id),mesh,part)
    def test_10_all_public_mutation_entries_reject_before_uobject_access(self):
        class NoUObject:
            def __getattr__(self,name):raise AssertionError('UObject accessed: '+name)
        u=NoUObject();binding={'selectedNativeBase':'invented'}
        for call in [lambda:m.build_materials(u,self.b,binding,None),lambda:m.verify_materials(u,self.b,binding,{},None),
          lambda:n.import_geometry(u,self.b,binding,{},None,None),lambda:n.apply_scene(u,binding=binding),lambda:n.main()]:
            with self.assertRaisesRegex(RuntimeError,'unbound'):call()

if __name__=='__main__':unittest.main(verbosity=2)
