"""Independent pinned-source, native-frame and rejection tests, no editor jobs."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('grove_native_test',HERE/'exterior-canopy-native.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
CANOPY=M.ROOT/'output/unreal/exterior-canopy-masters-20260930-r1d'
ECOLOGY=M.ROOT/'output/unreal/exterior-canopy-ecology-20260930-r3'
CONTEXT=M.ROOT/'output/unreal/exterior-context-20260927-r8/context-plan.json'
MERGED=M.ROOT/'output/unreal/exterior-assets-greenery-20260930-r3/geometry-manifest.json'

def read(path):return json.loads(Path(path).read_text())


class GroveNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context=read(CONTEXT);cls.merged=read(MERGED);cls.canopy=read(CANOPY/'canopy-plan.json')
        cls.canopy_manifest=read(CANOPY/'geometry-manifest.json');cls.ecology=read(ECOLOGY/'canopy-ecology-plan.json')
        cls.ecology_manifest=read(ECOLOGY/'geometry-manifest.json')
        cls.canopy_meshes={r['id']:r for r in cls.canopy_manifest['meshes']}
        cls.canopy_measured=M._measured_library(cls.canopy_meshes)
        cls.ecology_meshes={r['id']:r for r in cls.ecology_manifest['meshes']}
        cls.ecology_measured=M._measured_library(cls.ecology_meshes)

    def canopy_validate(self,plan=None,context=None,manifest=None,merged=None):
        return M.validated_replacements(plan or self.canopy,manifest or self.canopy_manifest,context or self.context,
            merged or self.merged,self.context['sourceSceneSha256'],self.context['sourceObjSha256'])

    def ecology_validate(self,plan=None,context=None,manifest=None,merged=None):
        return M.validated_ecology(plan or self.ecology,manifest or self.ecology_manifest,context or self.context,
            merged or self.merged,self.context['sourceSceneSha256'],self.context['sourceObjSha256'])

    def test_actual_78_poses_all_27_lods_lower50cm_and_non_grove_rows_preserved(self):
        before=M.digest(self.context)
        result=self.canopy_validate()
        self.assertEqual(len(result['placements']),78)
        self.assertEqual(result['audit']['status'],'verified-source-grove-canopy-replacement')
        self.assertEqual(result['audit']['deletedTrees'],0)
        self.assertEqual(M.digest(self.context),before)
        replacement={r['id']:r for r in result['placements']}
        after=[replacement.get(r['id'],r)for r in self.context['regionalVegetationPlacements']]
        self.assertEqual(len(after),len(self.context['regionalVegetationPlacements']))
        self.assertTrue(all(a==b for a,b in zip(after,self.context['regionalVegetationPlacements'])if b['regionId']!=M.REGION))
        self.assertTrue(all(r['sourceMeshId']in M.FAMILIES.values()for r in result['placements']))

    def test_unreviewed_owner_frame_setback_or_mutated_original_context_rejected(self):
        for change in [lambda p:p.update(owner='scripts/unreal/unknown.py'),lambda p:p.update(sourceObjSha256='0'*64),
                       lambda p:p['housePlacement'].update(eastSetbackMm=2999),lambda p:p['activeDesign'].update(variant='A')]:
            plan=deepcopy(self.canopy);change(plan)
            with self.assertRaises(RuntimeError):self.canopy_validate(plan)
        context=deepcopy(self.context);context['regionalVegetationPlacements'][0]['yawDeg']+=1
        with self.assertRaisesRegex(RuntimeError,'original source context'):self.canopy_validate(context=context)

    def test_exact_original_grove_row_keys_roots_order_yaw_scale_and_evidence_rejected(self):
        cases=[lambda p:p['canopyPlacements'][0]['positionCm'].__setitem__(2,0),
            lambda p:p['canopyPlacements'][0].update(yawDeg=0),lambda p:p['canopyPlacements'][0].update(scale=[1,1,1]),
            lambda p:p['canopyPlacements'][0].update(heightCm=999),lambda p:p['canopyPlacements'][0].pop('sourceImageWitness'),
            lambda p:p['canopyPlacements'][0].update(sourceMeshId='regional_upright_b'),
            lambda p:p['canopyPlacements'].reverse(),lambda p:p['canopyPlacements'].pop()]
        with patch.object(M,'_measured_library',return_value=self.canopy_measured):
            for change in cases:
                plan=deepcopy(self.canopy);change(plan)
                with self.assertRaisesRegex(RuntimeError,'preservation|order'):self.canopy_validate(plan)

    def test_merged_master_subset_and_material_or_missing_lod_rejected(self):
        for change in [lambda m:m['meshes'].pop(next(i for i,r in enumerate(m['meshes'])if r['id']in M.CANOPY_IDS)),
                       lambda m:next(r for r in m['meshes']if r['id']in M.CANOPY_IDS)['materialKeys'].append('unsafe'),
                       lambda m:next(r for r in m['meshes']if r['id']in M.CANOPY_IDS)['lods'].pop()]:
            merged=deepcopy(self.merged);change(merged)
            with self.assertRaisesRegex(RuntimeError,'merged master subset'):self.canopy_validate(merged=merged)

    def test_actual_lower50cm_axis_radius_and_forged_metadata_rejected(self):
        decoded=deepcopy(self.canopy_measured[1]);key=next(iter(self.canopy_meshes));node=key+'_LOD2'
        positions=decoded[node]['basal'];p=positions[0];positions[0]=(p[0]+.01,p[1],p[2])
        proof=read(CANOPY/'morphology-audit.json');old=read(M.ROOT/'output/unreal/exterior-regional-assets-20260927-r4/growth-skeletons.json')
        with self.assertRaisesRegex(RuntimeError,'lower50cm'):M._basal_compatibility(self.canopy_meshes,decoded,old,proof)
        proof['meshes'][key]['basalRadiiCm'][0]+=.01
        with self.assertRaisesRegex(RuntimeError,'lower50cm proof'):M._basal_compatibility(self.canopy_meshes,self.canopy_measured[1],old,proof)

    def test_actual_binary_out_of_range_indices_and_degenerate_face_rejected(self):
        source=ECOLOGY/'canopy-ecology.glb';raw=bytearray(source.read_bytes())
        n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);primitive=doc['meshes'][0]['primitives'][0]
        a=doc['accessors'][primitive['indices']];view=doc['bufferViews'][a['bufferView']]
        start=28+n+view.get('byteOffset',0)+a.get('byteOffset',0);fmt={5121:'B',5123:'H',5125:'I'}[a['componentType']]
        with tempfile.TemporaryDirectory(dir=M.ROOT/'output/unreal',prefix='canopy-native-rejection-')as temporary:
            path=Path(temporary)/'unsafe.glb';bad=bytearray(raw);struct.pack_into('<'+fmt,bad,start,65535);path.write_bytes(bad)
            with self.assertRaisesRegex(RuntimeError,'indices escape'):M._glb_nodes(path)
            bad=bytearray(raw);first=struct.unpack_from('<'+fmt,bad,start)[0];struct.pack_into('<'+fmt,bad,start+struct.calcsize(fmt),first);path.write_bytes(bad)
            with self.assertRaisesRegex(RuntimeError,'degenerate triangle'):M._glb_nodes(path)

    def test_measurable_declared_bounds_or_material_claim_cannot_replace_actual_geometry(self):
        meshes=deepcopy(self.ecology_meshes);next(iter(meshes.values()))['lods'][0]['expectedBoundsCm']['max'][2]+=.01
        with self.assertRaisesRegex(RuntimeError,'actual decoded bounds'):M._measured_library(meshes)
        meshes=deepcopy(self.ecology_meshes);next(iter(meshes.values()))['materialKeys'].append('unsafe')
        with self.assertRaisesRegex(RuntimeError,'geometry/material inventory'):M._measured_library(meshes)

    def test_actual_24851_additive_crowns_130_detail_groups_36_basal_and_source_ground(self):
        before=M.digest(self.context);result=self.ecology_validate()
        self.assertEqual(result['audit']['status'],'verified-source-grove-ecology')
        self.assertEqual((len(result['groups']),sum(len(g['instances'])for g in result['groups'])),(166,24851))
        self.assertEqual((sum(g['qualityDetail']for g in result['groups']),sum(not g['qualityDetail']for g in result['groups'])),(130,36))
        self.assertTrue(all(set(r)=={'positionCm','yawDeg','scale'}for g in result['groups']for r in g['instances']))
        self.assertEqual(M.digest(self.context),before)
        self.assertEqual(result['audit']['deletedTrees'],0)

    def test_ecology_self_consistent_bad_quality_transform_ground_or_flares_rejected(self):
        # Simulate a freshly pinned but unsafe plan; retain all actual sources,
        # decoded GLBs and constraints, bypass only the old immutable plan pin.
        pin=read(ECOLOGY/'canopy-ecology-manifest.json')['plan'];original=M.read_pin
        cases=[lambda p:p['groups'][0].update(qualityDetail=True),lambda p:p['groups'][0].update(cullEndCm=90000),
            lambda p:p['groups'][0]['instances'][0].update(scale=[1,1,1.1]),
            lambda p:p['groups'][0]['instances'][0]['renderedGround'].update(measuredElevation=True),
            lambda p:p['groups'][0]['instances'][0].update(existingTreeId='missing'),
            lambda p:p['groups'][0]['instances'][0]['positionCm'].__setitem__(2,0)]
        with patch.object(M,'_measured_library',return_value=self.ecology_measured):
            for change in cases:
                plan=deepcopy(self.ecology);change(plan)
                with patch.object(M,'read_pin',side_effect=lambda p:plan if p==pin else original(p)):
                    with self.assertRaisesRegex(RuntimeError,'policy|transform|ground|identity'):self.ecology_validate(plan)

    def test_circle_union_and_exact_private_source_exclusion_are_independent(self):
        rows=self.ecology['ecologyPlacements'];trees=self.ecology['existingTrees']
        self.assertTrue(M._circle_in_crowns(rows[0]['positionCm'][:2],rows[0]['radiusCm'],trees))
        self.assertFalse(M._circle_in_crowns(rows[0]['positionCm'][:2],10000,trees))
        box={'type':'Polygon','coordinates':[[[0,0],[100,0],[100,100],[0,100],[0,0]]]}
        mask=M._Geo(box)
        with self.assertRaisesRegex(RuntimeError,'actual source exclusion'):mask.outside_clear([50,50],1)
        with self.assertRaisesRegex(RuntimeError,'actual source exclusion'):mask.outside_clear([101,50],2)
        mask.outside_clear([103,50],2)

    def test_pinned_unsafe_ecology_plan_and_changed_existing_census_rejected(self):
        plan=deepcopy(self.ecology);plan['existingTrees'].pop()
        with self.assertRaisesRegex(RuntimeError,'original tree roots'):self.ecology_validate(plan)
        plan=deepcopy(self.ecology);plan['ecologyPlacements'][0]['positionCm'][0]+=.01
        with self.assertRaisesRegex(RuntimeError,'immutable plan proof'):self.ecology_validate(plan)


if __name__=='__main__':unittest.main()
