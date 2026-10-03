"""Adversarial source/GLB/counterfactual R21 checks; no Unreal dependency."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r21_native_cpu',HERE/'exterior-canopy-foreground-native.py')
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
g=native.guard


class ForegroundGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.bundle=g.load_source()

    def mutated(self,key):
        # Only the selected subtree is changed; large frozen original inputs
        # stay shared read-only, keeping this bounded suite inexpensive.
        bundle=dict(self.bundle);bundle[key]=copy.deepcopy(bundle[key]);return bundle

    def fails(self,bundle,text):
        with self.assertRaisesRegex(ValueError,text):g.validate_payload(bundle)

    def test_actual_source_decoded_masks_contact_and_budget(self):
        a=self.bundle['audit'];self.assertEqual((a['surfaceTriangles'],a['newRoots'],a['newGroups']), (1843,512,4));self.assertTrue(a['actualSourceGroundContactsVerified']);self.assertFalse(a['nativeGeometryDecoded'])

    def test_false_source_native_acceptance_rejected(self):
        b=self.mutated('plan');b['plan']['nativeAppearanceAccepted']=True;self.fails(b,'acceptance')

    def test_cbb_setback_change_rejected(self):
        b=self.mutated('plan');b['plan']['housePlacement']['eastSetbackMm']=2999;self.fails(b,'C/B/B')

    def test_existing_camera_retarget_rejected(self):
        b=self.mutated('plan');b['plan']['camera']['targetCm'][0]+=1;self.fails(b,'camera')

    def test_source_group_preservation_hash_rejected(self):
        b=self.mutated('plan');b['plan']['preservedSourceArrays']['groups']='0'*64;self.fails(b,'Protected context array')

    def test_feather_nan_or_other_channel_rejected(self):
        b=self.mutated('geometry');b['geometry']['mesh']['uv1'][0][1]=.01;self.fails(b,'feather UV1')

    def test_metric_uv_drift_rejected(self):
        b=self.mutated('geometry');b['geometry']['mesh']['uv0'][0][0]+=.001;self.fails(b,'Metric UV0')

    def test_source_triangle_winding_reversal_rejected(self):
        b=self.mutated('geometry');v=b['geometry']['mesh']['indices'];v[0],v[1]=v[1],v[0];self.fails(b,'winding')

    def test_microrelief_above_budget_rejected(self):
        b=self.mutated('geometry');b['geometry']['mesh']['verticesCm'][0][2]=-23;self.fails(b,'microrelief')

    def test_root_wrong_native_master_rejected(self):
        b=self.mutated('roots');b['roots']['groups'][0]['nativeMesh']+='_foreign';self.fails(b,'native master')

    def test_root_nonuniform_scale_rejected(self):
        b=self.mutated('roots');b['roots']['groups'][0]['instances'][0]['scale'][2]+=.1;self.fails(b,'serialized transform')

    def test_root_outside_new_domain_rejected(self):
        b=self.mutated('roots');b['roots']['groups'][0]['instances'][0]['positionCm'][0]+=4000;self.fails(b,'footprint')

    def test_root_contact_not_original_floor_rejected(self):
        b=self.mutated('roots');b['roots']['groups'][0]['instances'][0]['positionCm'][2]+=.01;self.fails(b,'Root contact')

    def test_no_new_textures_material_scope_rejected(self):
        b=self.mutated('material');b['material']['newTextureObjects']=1;self.fails(b,'material scope')

    def test_one_ulp_bound_annotation_does_not_fake_attribute_difference(self):
        # Positive test for the precise class that stopped the R20 source guard:
        # source radius annotations may differ one binary64 ULP across libm.
        import math
        b=self.mutated('roots');v=b['roots']['models']['canopy_ecology_grass_0'];v['radiusCm']=math.nextafter(v['radiusCm'],math.inf)
        self.assertEqual(g.validate_payload(b)['newRoots'],512)

    def test_actual_glb_roundtrip_and_uv1_tamper(self):
        mesh=self.bundle['geometry']['mesh']
        with tempfile.TemporaryDirectory()as d:
            path=Path(d)/'source.glb';native.write_glb(path,mesh);self.assertEqual(native.decode_glb(path,mesh)['triangles'],1843)
            payload=bytearray(path.read_bytes());size=struct.unpack_from('<I',payload,12)[0];doc=json.loads(payload[20:20+size]);a=doc['accessors'][doc['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_1']];v=doc['bufferViews'][a['bufferView']];offset=20+size+8+v['byteOffset'];struct.pack_into('<f',payload,offset,.987654);path.write_bytes(payload)
            with self.assertRaisesRegex(ValueError,'UV1'):native.decode_glb(path,mesh)

    def actor_fixture(self):
        before={str(i):{'tick':False,'mesh':'old','instanceHash':'unchanged'}for i in range(5306)};added=['new_'+str(i)for i in range(5)];expected={**copy.deepcopy(before),**{k:{'source':'new-only'}for k in added}}
        return before,expected,copy.deepcopy(expected),added

    def test_actor_counterfactual_preserves_all5306_and_only5_added(self):
        before,expected,after,added=self.actor_fixture();g.validate_actor_delta(before,expected,after,added)
        after['17']['instanceHash']='changed'
        with self.assertRaisesRegex(ValueError,'Original actor'):g.validate_actor_delta(before,expected,after,added)
        before,expected,after,added=self.actor_fixture();after['unexpected']={}
        with self.assertRaisesRegex(ValueError,'Unknown'):g.validate_actor_delta(before,expected,after,added)

    def test_content_exact5_packages_and_map_only(self):
        before={str(i):{'sha256':'old','bytes':1}for i in range(3974)};before['Brezi/Maps/Brezi.umap']={'sha256':'map-before','bytes':1};assets=['Brezi/CanopyForeground20261002R21/'+str(i)+'.uasset'for i in range(5)];after={**copy.deepcopy(before),**{k:{'sha256':'new','bytes':1}for k in assets}};after['Brezi/Maps/Brezi.umap']={'sha256':'map-after','bytes':2};g.validate_content_delta(before,after,assets)
        after['5']['sha256']='changed-old'
        with self.assertRaisesRegex(ValueError,'Original Content'):g.validate_content_delta(before,after,assets)
        after['5']['sha256']='old';after['Brezi/CanopyForeground20261002R21/unplanned-texture.uasset']={}
        with self.assertRaisesRegex(ValueError,'Unknown'):g.validate_content_delta(before,after,assets)

    def graph_fixture(self):
        original=self.bundle['inputs']['nativeR16']['materials']['materials']['context_meadow']['graph'];variant=copy.deepcopy(original);tag=g.NODE_TAG
        variant['nodes']+= [
            {'role':tag+'uv1','class':'MaterialExpressionTextureCoordinate','values':{'coordinate_index':1,'u_tiling':1.,'v_tiling':1.},'inputs':[]},
            {'role':tag+'coverage-r','class':'MaterialExpressionComponentMask','values':{'r':True,'g':False,'b':False,'a':False},'inputs':[['None',tag+'uv1','']]},
            {'role':tag+'temporal-dither','class':'MaterialExpressionMaterialFunctionCall','values':{'material_function':'/Engine/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA.DitherTemporalAA'},'inputs':[['Alpha Threshold',tag+'coverage-r',''],['Random',None,None]]}]
        variant['nodes'].sort(key=lambda v:v['role']);variant['roots']['OPACITY_MASK']=[tag+'temporal-dither','Result'];variant['flags']['blend_mode']='<BlendMode.BLEND_MASKED: 1>';variant['flags']['opacity_mask_clip_value']=.5
        return original,variant

    def test_graph_only104_exact_nodes_plus3_uv1_dither(self):
        original,variant=self.graph_fixture();g.validate_graph_copy(original,variant)
        variant['roots']['ROUGHNESS']=variant['roots']['OPACITY_MASK']
        with self.assertRaisesRegex(ValueError,'PBR roots'):g.validate_graph_copy(original,variant)
        original,variant=self.graph_fixture();next(v for v in variant['nodes']if v['role']==g.NODE_TAG+'uv1')['values']['coordinate_index']=0
        with self.assertRaisesRegex(ValueError,'UV1'):g.validate_graph_copy(original,variant)

    def test_real_saved_r16_dither_and_mask_pin_schema(self):
        graph=self.bundle['inputs']['nativeR16']['materials']['materials']['canopy_floor_litter']['graph'];nodes={v['role']:v for v in graph['nodes']}
        mask=nodes['BreziExterior:soil-exposure-coverage-u'];dither=nodes['BreziExterior:soil-exposure-native-temporal-dither']
        self.assertEqual(mask['inputs'][0][0],'None');self.assertEqual(graph['roots']['OPACITY_MASK'][1],'Result');self.assertEqual([v[0]for v in dither['inputs']],['Alpha Threshold','Random'])

    def test_actual_clone_membership_and_hardlink_claim_rejected(self):
        # The root-produced, authentic fresh candidate receipt is read only.
        # Native repeats hashes and actual inode checks before any map load.
        project=g.ROOT/'output/unreal/exterior-20261002-r21a/Project/BreziTwin';base_project=g.ROOT/'output/unreal/exterior-20261001-r16a/Project/BreziTwin'
        clone=g.read(project.parents[1]/'foreground-project-clone.json');base_rows={};protected={'files':{},'fileCount':132}
        for row in clone['files']:
            relative=str(Path(row['destination']).relative_to(project))
            if relative.startswith('Content/'):base_rows[relative[len('Content/'):]]={k:row[k]for k in ('sha256','bytes')}
            else:protected['files'][relative]=row
        g.validate_clone(clone,base_rows,protected,base_project,project)
        altered=copy.deepcopy(clone);altered['files'][0]['independentInodes']=False
        with self.assertRaisesRegex(ValueError,'ownership'):g.validate_clone(altered,base_rows,protected,base_project,project)


if __name__=='__main__':unittest.main()
