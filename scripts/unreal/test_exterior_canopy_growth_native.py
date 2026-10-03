"""Unmocked stdlib native-input proofs and self-repinned growth rejections."""
from contextlib import contextmanager
from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('new_growth_native_test',HERE/'exterior-canopy-native.py')
N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
OUT=N.GROWTH_STUDY

def read(path):return json.loads(Path(path).read_text())
def write(path,value):Path(path).write_text(json.dumps(value,indent=2)+'\n')


class GrowthNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=read(OUT/'canopy-plan.json');cls.geometry=read(OUT/'geometry-manifest.json')
        cls.context=read(cls.plan['sourceContext']['path'])
        cls.merged=read(N.ROOT/'output/unreal/exterior-assets-greenery-20260930-r3/geometry-manifest.json')
        cls.merged['meshes'].extend(deepcopy(cls.geometry['meshes']))
        cls.before={str(p):N.sha(p)for p in [HERE/'exterior-canopy-growth.py',OUT/'canopy-plan.json',
            OUT/'geometry-manifest.json',OUT/'growth-skeletons.json',OUT/'morphology-audit.json']}

    @classmethod
    def tearDownClass(cls):
        for path,value in cls.before.items():
            if N.sha(path)!=value:raise AssertionError('Frozen growth source mutated: '+path)

    def validate(self,plan=None,geometry=None,context=None,merged=None):
        return N.validated_replacements(self.plan if plan is None else plan,self.geometry if geometry is None else geometry,
            self.context if context is None else context,self.merged if merged is None else merged,
            self.context['sourceSceneSha256'],self.context['sourceObjSha256'])

    @contextmanager
    def repinned(self):
        # Fresh output wrappers may point at unchanged authoring data. The tests
        # modify only temporary candidate bytes and repin them like an attacker.
        with tempfile.TemporaryDirectory(dir=N.ROOT/'output/unreal',prefix='growth-native-negative-')as directory:
            directory=Path(directory);plan=deepcopy(self.plan);geometry=deepcopy(self.geometry)
            for name in('growth-skeletons.json','morphology-audit.json','material-manifest.json'):
                (directory/name).write_bytes((OUT/name).read_bytes())
            old=plan['geometryManifest']['path'];plan['inputFiles'].pop(old)
            plan['inputFiles'].pop(str(OUT/'growth-skeletons.json'))
            plan['inputFiles'][str(directory/'growth-skeletons.json')]=N.sha(directory/'growth-skeletons.json')
            def seal():
                write(directory/'geometry-manifest.json',geometry)
                pin={'path':str(directory/'geometry-manifest.json'),'sha256':N.sha(directory/'geometry-manifest.json')}
                plan['geometryManifest']=pin;plan['inputFiles'][pin['path']]=pin['sha256']
                merged=deepcopy(self.merged);lookup={r['id']:r for r in geometry['meshes']}
                merged['meshes']=[deepcopy(lookup.get(r['id'],r))for r in merged['meshes']]
                return merged
            yield directory,plan,geometry,seal

    def test_unmocked_actual27lods_connectivity_tissue_lower50cm_and78roots(self):
        before=N.digest(self.context);result=self.validate();audit=result['audit']
        self.assertEqual(audit['status'],'verified-source-grove-canopy-growth')
        self.assertEqual((audit['masters'],audit['lods'],len(result['placements'])),(9,27,78))
        self.assertEqual(audit['allInstancesTriangleBudgetByLod'],[9397168,6061840,2349912])
        self.assertTrue(audit['actualConnectedHierarchyAndTerminalLeafGeometryVerified'])
        self.assertTrue(audit['actualNestedLeafIdentitiesVerified'])
        self.assertTrue(audit['actualAreaNormalsAndUvTangentsVerified'])
        self.assertEqual(audit['nonGroveRegionalRowsPreserved'],1022)
        self.assertFalse(audit['collisionActorsChanged']);self.assertFalse(audit['farCostAccepted'])
        self.assertFalse(audit['nativeAppearanceAccepted']);self.assertEqual(N.digest(self.context),before)
        for new,old in zip(result['placements'],self.plan['originalCanopyPlacements']):
            self.assertEqual({k:v for k,v in new.items()if k not in('meshId','sourceMeshId')},
                             {k:v for k,v in old.items()if k!='meshId'})

    def test_unreviewed_owner_setback_census_policy_and_root_metadata_rejected(self):
        cases=[lambda p:p.update(owner='scripts/unreal/unknown-growth.py'),
            lambda p:p.update(sourceSceneSha256='0'*64),lambda p:p['housePlacement'].update(eastSetbackMm=2999),
            lambda p:p.update(activeDesign={'variant':'A','heatingLayout':'B','livingLayout':'B'}),
            lambda p:p['policy'].update(collisionActorsChanged=True),lambda p:p['policy'].update(speciesAgeAndExactRootNotSurveyed=False),
            lambda p:p.update(scannedBotanicalCensus=True),lambda p:p['originalCanopyPlacements'].pop()]
        for change in cases:
            plan=deepcopy(self.plan);change(plan)
            with self.subTest(change=change),self.assertRaises(RuntimeError):self.validate(plan)

    def test_exact_placement_order_yaw_scale_and_variant_cannot_be_reauthorized(self):
        cases=[lambda p:p['canopyPlacements'][0]['positionCm'].__setitem__(2,p['canopyPlacements'][0]['positionCm'][2]+1),
            lambda p:p['canopyPlacements'][0].update(yawDeg=p['canopyPlacements'][0]['yawDeg']+1),
            lambda p:p['canopyPlacements'][0]['scale'].__setitem__(0,p['canopyPlacements'][0]['scale'][0]+.01),
            lambda p:p['canopyPlacements'][0].update(heightCm=999),lambda p:p['canopyPlacements'][0].pop('sourceImageWitness'),
            lambda p:p['canopyPlacements'][0].update(sourceMeshId='unknown'),
            lambda p:p['canopyPlacements'][0].update(meshId=p['canopyPlacements'][0]['meshId'][:-1]+('b'if p['canopyPlacements'][0]['meshId'][-1]=='a'else'a')),
            lambda p:p['canopyPlacements'].reverse(),lambda p:p['canopyPlacements'].pop()]
        for change in cases:
            plan=deepcopy(self.plan);change(plan)
            with self.subTest(change=change),self.assertRaisesRegex(RuntimeError,'preservation|policy'):self.validate(plan)
        source=deepcopy(self.context);source['regionalVegetationPlacements'][0]['yawDeg']+=1
        with self.assertRaisesRegex(RuntimeError,'original source context'):self.validate(context=source)
        with self.repinned()as(directory,plan,geometry,seal):
            altered=deepcopy(self.context);altered['regionalVegetationPlacements'][0]['scale']=[1,1,1]
            write(directory/'context.json',altered)
            pin={'path':str(directory/'context.json'),'sha256':N.sha(directory/'context.json')}
            plan['sourceContext']=pin;geometry['inputFiles'][pin['path']]=pin['sha256']
            merged=seal()
            with self.assertRaisesRegex(RuntimeError,'immutable source dependencies'):self.validate(plan,geometry,altered,merged)

    def test_self_repinned_height_radius_master_material_and_collision_claim_rejected(self):
        changes=[lambda g:g['meshes'][0].update(heightCm=999),lambda g:g['meshes'][0].update(radialEnvelopeCm=999),
            lambda g:g['meshes'][0]['lods'][0]['expectedBoundsCm']['max'].__setitem__(0,999),
            lambda g:g['meshes'][0].update(sourceFamily='regional_upright_b'),
            lambda g:g['meshes'][0].update(collision=True),lambda g:g['meshes'][0].update(composition='Scanned botanical census')]
        for change in changes:
            with self.repinned()as(_,plan,geometry,seal):
                change(geometry);merged=seal()
                with self.subTest(change=change),self.assertRaisesRegex(RuntimeError,'immutable height/radius/material/master'):self.validate(plan,geometry,merged=merged)
        with self.repinned()as(_,plan,geometry,seal):
            geometry['status']='PASS_NATIVE_PHOTOREAL';merged=seal()
            with self.assertRaisesRegex(RuntimeError,'immutable authoring status'):self.validate(plan,geometry,merged=merged)

    def test_self_repinned_growth_skeleton_and_nested_leaf_membership_rejected(self):
        for kind in('connectivity','growth','nested'):
            with self.repinned()as(directory,plan,geometry,seal):
                filename='morphology-audit.json'if kind=='nested'else'growth-skeletons.json'
                value=read(directory/filename)
                if kind=='nested':next(iter(value['meshes'].values()))['lodLeafIds']['2'].pop()
                else:
                    morph=next(iter(value.values()))
                    if kind=='connectivity':morph['branches'][1]['points'][0][0]+=.01
                    else:morph['growth']['leafClusterEllipsoids']=True
                write(directory/filename,value)
                if kind!='nested':plan['inputFiles'][str(directory/filename)]=N.sha(directory/filename)
                merged=seal()
                with self.subTest(kind=kind),self.assertRaisesRegex(RuntimeError,'immutable connected skeleton|immutable morphology'):self.validate(plan,geometry,merged=merged)

    def test_self_repinned_photographic_recipe_change_rejected(self):
        with self.repinned()as(directory,plan,geometry,seal):
            recipes=read(directory/'material-manifest.json');recipes['regional_green_leaf']['tint']=[0,1,1]
            write(directory/'material-manifest.json',recipes);merged=seal()
            with self.assertRaisesRegex(RuntimeError,'recipe'):self.validate(plan,geometry,merged=merged)

    def _changed_binary(self,directory,geometry,attribute):
        row=geometry['meshes'][0];raw=bytearray(Path(row['glbPath']).read_bytes());size=struct.unpack_from('<I',raw,12)[0]
        doc=json.loads(raw[20:20+size]);primitive=doc['meshes'][0]['primitives'][1]
        accessor=doc['accessors'][primitive['attributes'][attribute]];view=doc['bufferViews'][accessor['bufferView']]
        width={'VEC2':2,'VEC3':3,'VEC4':4}[accessor['type']]
        offset=28+size+view.get('byteOffset',0)+accessor.get('byteOffset',0)+300*width*4
        original=struct.unpack_from('<f',raw,offset)[0]
        struct.pack_into('<f',raw,offset,original+.0001 if attribute=='POSITION'else original+1.)
        path=directory/'repinned.glb';path.write_bytes(raw);row['glbPath']=str(path);row['glbSha256']=N.sha(path)

    def test_actual_repinned_interior_leaf_vertex_cannot_hide_behind_same_bounds(self):
        with self.repinned()as(directory,plan,geometry,seal):
            self._changed_binary(directory,geometry,'POSITION');merged=seal()
            with self.assertRaisesRegex(RuntimeError,'actual leaf tissue'):self.validate(plan,geometry,merged=merged)

    def test_actual_repinned_nonunit_normal_cannot_hide_behind_source_metadata(self):
        with self.repinned()as(directory,plan,geometry,seal):
            self._changed_binary(directory,geometry,'NORMAL');merged=seal()
            with self.assertRaisesRegex(RuntimeError,'normal/tangent'):self.validate(plan,geometry,merged=merged)

    def test_actual_unit_orthogonal_frame_must_match_connected_surface(self):
        with self.repinned()as(directory,plan,geometry,seal):
            row=geometry['meshes'][0];raw=bytearray(Path(row['glbPath']).read_bytes());size=struct.unpack_from('<I',raw,12)[0]
            doc=json.loads(raw[20:20+size]);attrs=doc['meshes'][0]['primitives'][1]['attributes']
            # Rotate both unit vectors by the same small rigid angle. Length,
            # orthogonality and face orientation remain valid; only the actual
            # area normal/UV basis reconstruction can reject this false frame.
            for attribute in('NORMAL','TANGENT'):
                a=doc['accessors'][attrs[attribute]];view=doc['bufferViews'][a['bufferView']]
                width=3 if attribute=='NORMAL'else 4
                offset=28+size+view['byteOffset']+300*width*4
                x,y,z=struct.unpack_from('<3f',raw,offset);angle=.005
                struct.pack_into('<3f',raw,offset,x,y*math.cos(angle)-z*math.sin(angle),y*math.sin(angle)+z*math.cos(angle))
            path=directory/'false-unit-frame.glb';path.write_bytes(raw);row['glbPath']=str(path);row['glbSha256']=N.sha(path)
            merged=seal()
            with self.assertRaisesRegex(RuntimeError,'actual area normal/UV tangent'):self.validate(plan,geometry,merged=merged)

    def test_unmeasured_skin_morph_animation_scene_and_accessor_modifiers_rejected(self):
        cases=[lambda d:d['nodes'][0].update(skin=0),lambda d:d.update(skins=[{'joints':[0]}]),
            lambda d:d.update(animations=[]),lambda d:d['scenes'][0]['nodes'].pop(),
            lambda d:d['meshes'][0]['primitives'][0].update(targets=[{'POSITION':0}]),
            lambda d:d['accessors'][0].update(normalized=True),lambda d:d['buffers'][0].update(uri='external.bin')]
        for change in cases:
            with self.repinned()as(directory,plan,geometry,seal):
                row=geometry['meshes'][0];raw=Path(row['glbPath']).read_bytes();size=struct.unpack_from('<I',raw,12)[0]
                doc=json.loads(raw[20:20+size]);change(doc);binary=raw[28+size:]
                body=json.dumps(doc,separators=(',',':')).encode();body+=b' '*((-len(body))%4)
                path=directory/'unmeasured.glb';path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(body)+len(binary))+
                    struct.pack('<II',len(body),0x4e4f534a)+body+struct.pack('<II',len(binary),0x004e4942)+binary)
                row['glbPath']=str(path);row['glbSha256']=N.sha(path);merged=seal()
                with self.subTest(change=change),self.assertRaisesRegex(RuntimeError,'unmeasured'):self.validate(plan,geometry,merged=merged)

    def test_merged_master_inventory_and_bad_actual_indices_rejected(self):
        merged=deepcopy(self.merged);merged['meshes'].pop()
        with self.assertRaisesRegex(RuntimeError,'merged master subset'):self.validate(merged=merged)
        with tempfile.TemporaryDirectory(dir=N.ROOT/'output/unreal',prefix='growth-indices-')as directory:
            row=self.geometry['meshes'][0];raw=bytearray(Path(row['glbPath']).read_bytes());size=struct.unpack_from('<I',raw,12)[0]
            doc=json.loads(raw[20:20+size]);a=doc['accessors'][doc['meshes'][0]['primitives'][0]['indices']]
            view=doc['bufferViews'][a['bufferView']];offset=28+size+view.get('byteOffset',0)+a.get('byteOffset',0)
            struct.pack_into('<I',raw,offset,2**32-1);path=Path(directory)/'invalid.glb';path.write_bytes(raw)
            with self.assertRaisesRegex(RuntimeError,'indices escape'):N._glb_nodes(path,detailed=True)


if __name__=='__main__':unittest.main()
