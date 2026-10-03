"""Independent upright-turf native contract tests; actual GLB morphology/frames and repinned rejection cases. No editor or source writes.

Fixtures write only temporary, repinned candidate bundles. Frozen studies,
original assets and the native integration helper are never changed.
"""
from contextlib import contextmanager
from copy import deepcopy
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('fine_lawn_native_integration',HERE/'exterior-lawn-native.py')
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
OUTPUT=Path(os.environ.get('BREZI_LAWN_UPRIGHT',ROOT/'output/unreal/exterior-lawn-upright-20260930-r4-study'))


def read(path):return json.loads(Path(path).read_text())
def pin(path):return {'path':str(Path(path).resolve()),'sha256':native.sha(path)}
def write(path,value):Path(path).write_text(json.dumps(value,allow_nan=False,separators=(',',':'))+'\n')


class UprightNativeContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=read(OUTPUT/'lawn-natural-plan.json');cls.manifest=read(OUTPUT/'geometry-manifest.json')
        cls.bundle=read(OUTPUT/'lawn-natural-manifest.json')
        cls.coverage=read(cls.plan['coverageReceipt']['path']);cls.boundary=read(cls.plan['boundaryCoverageReceipt']['path'])
        cls.decoded=native._glb_geometry(cls.manifest['meshes'][0]['glbPath'],include_frames=True)

    def validate(self,plan=None,manifest=None):
        return native.validated_groups(self.plan if plan is None else plan,self.manifest if manifest is None else manifest,
            self.plan['sourceSceneSha256'],self.plan['sourceObjSha256'])

    @contextmanager
    def candidate(self,mutate,late_mutate=None):
        """Repin a complete altered bundle so rejection reaches the real guard."""
        with tempfile.TemporaryDirectory(dir=ROOT/'output/unreal',prefix='upright-native-negative-')as temporary:
            directory=Path(temporary)
            c=SimpleNamespace(plan=deepcopy(self.plan),manifest=deepcopy(self.manifest),bundle=deepcopy(self.bundle),
                coverage=deepcopy(self.coverage),boundary=deepcopy(self.boundary),directory=directory)
            # A malicious receipt may keep a matching hash and all embedded
            # copies; the criteria must still reject its unsafe content.
            mutate(c)
            for key,name,body in(('coverageReceipt','lawn-coverage-receipt.json',c.coverage),
                                  ('boundaryCoverageReceipt','lawn-boundary-receipt.json',c.boundary)):
                path=directory/name;write(path,body)
                for record in(c.plan,c.manifest,c.bundle):record[key]=pin(path)
            c.plan['audit']['physicalCoverage']=deepcopy(c.coverage)
            c.plan['audit']['boundaryCoverage']=deepcopy(c.boundary)
            path=directory/'geometry-manifest.json';write(path,c.manifest)
            c.plan['geometryManifest']=c.bundle['geometryManifest']=pin(path)
            if late_mutate is not None:late_mutate(c)
            c.bundle['audit']=deepcopy(c.plan['audit'])
            path=directory/'lawn-natural-plan.json';write(path,c.plan);c.bundle['plan']=pin(path)
            write(directory/'lawn-natural-manifest.json',c.bundle)
            yield c

    def test_actual_fine_all_lods_and_complete_managed_native_groups(self):
        groups=self.validate();p=self.plan
        self.assertEqual(p['owner'],'scripts/unreal/exterior-lawn-upright.py')
        self.assertEqual(p['audit']['status'],'MEASURED_UPRIGHT_MANAGED_LAWN_STUDY_NOT_NATIVE_ACCEPTED')
        self.assertEqual(len(self.manifest['meshes']),20);self.assertEqual(len(self.decoded),60)
        self.assertEqual({g['meshId']for g in groups},native.FAMILY)
        self.assertEqual(len(groups),p['audit']['groups']);self.assertEqual(sum(len(g['instances'])for g in groups),p['audit']['instances'])
        self.assertEqual(p['audit']['instances'],102011);self.assertEqual(len(groups),40)
        self.assertEqual(p['audit']['lowLeaningLeavesPerPatch'],{'interior':16,'boundary':12})
        self.assertLessEqual(p['audit']['nearTriangleBudget'],20000000)
        expected=[{'id':g['id'],'meshId':g['meshId'],'role':'grass','cullEndCm':4000,'qualityDetail':True,
            'instances':[{k:r[k]for k in('positionCm','yawDeg','scale')}for r in g['instances']]}for g in p['groups']]
        self.assertEqual(groups,expected)
        self.assertTrue(all(m['lodScreenSizes']==[1.,.025,.007]for m in self.manifest['meshes']))
        for mesh in self.manifest['meshes']:
            leaves=48 if mesh['edgeMaster']else 64
            for lod in mesh['lods']:
                decoded=self.decoded[lod['nodeName']]
                self.assertEqual(lod['blades'],leaves);self.assertEqual(decoded['triangles'],lod['triangles'])
                self.assertEqual(len(decoded['positions']),lod['vertices'])
        self.assertIs(p['replacementPolicy']['sourceGroundAndCollisionUnchanged'],True)
        self.assertIs(p['replacementPolicy']['unmanagedRuralGroundcoverPreserved'],True)

    def test_boundary_receipt_exact_pins_frames_all_lods_and_physical_cover(self):
        receipt=self.boundary;pin_row=self.plan['boundaryCoverageReceipt']
        self.assertEqual(pin_row,self.manifest['boundaryCoverageReceipt']);self.assertEqual(pin_row,self.bundle['boundaryCoverageReceipt'])
        self.assertEqual(pin_row['sha256'],native.sha(pin_row['path']));self.assertEqual(receipt,self.plan['audit']['boundaryCoverage'])
        self.assertEqual(receipt['status'],'MEASURED_UPRIGHT_STUDY_BOUNDARY_COVERAGE_NOT_NATIVE_ACCEPTED')
        self.assertEqual(receipt['criteria'],{'minimumPhysicalCoverByBoundaryBand':{'1to10mm':.12,'10to30mm':.40,'30to100mm':.50},'outsideSourceDomainPermittedCm':0})
        self.assertEqual({w['boundaryId']for w in receipt['windows']},{'deck','mulch'})
        for window in receipt['windows']:
            axis,inward=window['axisUnitXY'],window['inwardUnitXY']
            self.assertAlmostEqual(math.hypot(*axis),1,places=12);self.assertAlmostEqual(math.hypot(*inward),1,places=12)
            self.assertAlmostEqual(sum(a*b for a,b in zip(axis,inward)),0,places=12)
            self.assertEqual(window['widthCm'],40);self.assertEqual(window['pixelSizeMm'],.25)
            self.assertEqual(window['resolutionXY'],[1600,math.ceil(window['lengthCm']/.025)])
            self.assertEqual([r['lod']for r in window['lods']],[0,1,2]);self.assertGreater(window['intersectingInstances'],0)
            for lod in window['lods']:
                self.assertEqual([b['distanceFromBoundaryMm']for b in lod['boundaryBands']],[[1.,10.],[10.,30.],[30.,100.]])
                self.assertGreater(lod['projectedCoverage'],0);self.assertLessEqual(lod['projectedCoverage'],1)
                for band,minimum in zip(lod['boundaryBands'],(.12,.40,.50)):
                    self.assertGreater(band['physicalCoverFraction'],minimum);self.assertLessEqual(band['physicalCoverFraction'],1)

    def test_wrong_owner_frame_source_ground_lod_and_native_policy_rejected(self):
        mutations=[lambda p:p.update(owner='scripts/unreal/unknown.py'),lambda p:p.update(sourceObjSha256='0'*64),
            lambda p:p['activeDesign'].update(variant='A'),lambda p:p['housePlacement'].update(streetSetbackMm=2999),
            lambda p:p.update(sourceLawnId='DOM_00002'),lambda p:p.update(lodScreenSizes=[1.,.15,.04]),
            lambda p:p['renderingPolicy'].update(windDisplacementCm=.01),
            lambda p:p['replacementPolicy'].update(unmanagedRuralGroundcoverPreserved=False)]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                plan=deepcopy(self.plan);mutate(plan)
                with self.assertRaises(RuntimeError):self.validate(plan)

    def test_actual_manifest_mesh_count_geometry_and_lod_claim_changes_rejected(self):
        cases=[lambda c:c.manifest['meshes'].pop(),
            lambda c:c.manifest['meshes'][0]['lods'][0].update(triangles=c.manifest['meshes'][0]['lods'][0]['triangles']+1),
            lambda c:c.manifest['meshes'][0]['lods'][2].update(vertices=c.manifest['meshes'][0]['lods'][2]['vertices']+1),
            lambda c:c.manifest['meshes'][0]['lods'][1].update(blades=63),
            lambda c:c.manifest['meshes'][0]['lods'][1]['expectedBoundsCm']['max'].__setitem__(0,20),
            lambda c:c.manifest['meshes'][0].update(lodScreenSizes=[1.,.15,.04])]
        for mutate in cases:
            with self.subTest(mutate=mutate),self.candidate(mutate)as c:
                with self.assertRaisesRegex(RuntimeError,'mesh family|decoded|mesh/LOD|topology|inventory'):self.validate(c.plan,c.manifest)

    def test_measured_area_density_triangle_budget_and_interior_phase_claims_rejected(self):
        cases=[lambda c:c.plan['audit'].update(exactAllowedDomainM2=c.plan['audit']['exactAllowedDomainM2']+.1),
            lambda c:c.plan['audit'].update(bladesPerM2EveryLod=c.plan['audit']['bladesPerM2EveryLod']+1),
            lambda c:c.plan['audit'].update(nearTriangleBudget=c.plan['audit']['nearTriangleBudget']+1),
            lambda c:c.plan['audit'].update(interiorSixtyMmLatticePhaseAmplitudeXY=[.2,.2])]
        for mutate in cases:
            with self.subTest(mutate=mutate),self.candidate(mutate)as c:
                with self.assertRaisesRegex(RuntimeError,'area|density|budget|phase'):self.validate(c.plan,c.manifest)

    def test_actual_binary_out_of_range_and_nonfinite_geometry_rejected(self):
        source=bytearray(Path(self.manifest['meshes'][0]['glbPath']).read_bytes())
        size,_=struct.unpack_from('<II',source,12);doc=json.loads(source[20:20+size]);binary=28+size
        primitive=doc['meshes'][doc['nodes'][0]['mesh']]['primitives'][0]
        for role,value in(('indices',0xffffffff),('POSITION',float('nan'))):
            payload=bytearray(source);a=doc['accessors'][primitive['indices']if role=='indices'else primitive['attributes']['POSITION']]
            view=doc['bufferViews'][a['bufferView']];offset=binary+view.get('byteOffset',0)+a.get('byteOffset',0)
            fmt={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']]
            if role=='indices':value=(1<<(8*struct.calcsize(fmt)))-1
            struct.pack_into('<'+fmt,payload,offset,value)
            with self.subTest(role=role),tempfile.TemporaryDirectory(dir=ROOT/'output/unreal')as temporary:
                path=Path(temporary)/'unsafe.glb';path.write_bytes(payload)
                with self.assertRaisesRegex(RuntimeError,'indices|non-finite'):native._glb_geometry(path)

    def test_whole_crown_source_domain_and_native_group_membership_rejected(self):
        cases=[lambda p:p['groups'][0]['instances'][0].update(scale=[1.,1.,1.01]),
            lambda p:p['groups'][0]['instances'][0].update(positionCm=[9000.,9000.,-6.5]),
            lambda p:p['groups'][0]['instances'][0].update(positionCm=[*p['groups'][0]['instances'][0]['positionCm'][:2],-6.4]),
            lambda p:p['groups'][0]['instances'][0].update(radiusCm=p['groups'][0]['instances'][0]['radiusCm']+1),
            lambda p:p['groups'][0].update(id='EX_lawn_natural_unreviewed'),
            lambda p:p['groups'][0].update(qualityDetail=False),
            lambda p:p.update(managedLawnKeepPolygonsCm=[[[-10000,-10000],[10000,-10000],[10000,10000],[-10000,10000]]])]
        for mutate in cases:
            with self.subTest(mutate=mutate):
                plan=deepcopy(self.plan);mutate(plan)
                with self.assertRaises(RuntimeError):self.validate(plan)

    def test_self_consistently_repinned_unsafe_boundary_cover_and_frame_rejected(self):
        cases=[lambda c:c.boundary['criteria'].update(outsideSourceDomainPermittedCm=1),
            lambda c:c.boundary['windows'][0]['lods'][0]['boundaryBands'][1].update(physicalCoverFraction=.39),
            lambda c:c.boundary['windows'][0].update(originCm=[0.,0.]),
            lambda c:c.boundary['windows'][0].update(inwardUnitXY=[0.,0.]),
            lambda c:c.boundary['windows'][0].update(pixelSizeMm=1),
            lambda c:c.boundary['windows'].pop()]
        for mutate in cases:
            with self.subTest(mutate=mutate),self.candidate(mutate)as c:
                with self.assertRaisesRegex(RuntimeError,'[Bb]oundary'):self.validate(c.plan,c.manifest)

    def test_boundary_pin_drift_or_omission_rejected(self):
        for action in('missing','hash','embedded'):
            def mutate(c):
                if action=='missing':c.plan.pop('boundaryCoverageReceipt')
                elif action=='hash':c.plan['boundaryCoverageReceipt']['sha256']='0'*64
                else:c.plan['audit']['boundaryCoverage']['windows'][0]['lods'][0]['boundaryBands'][0]['physicalCoverFraction']=0
            with self.subTest(action=action),self.candidate(lambda c:None,mutate)as c:
                with self.assertRaisesRegex(RuntimeError,'[Bb]oundary'):self.validate(c.plan,c.manifest)

    def test_decoded_actual_pointed_anatomy_normals_and_low_share_proof(self):
        meshes={m['id']:m for m in self.manifest['meshes']}
        native._upright_morphology(self.plan,meshes,self.decoded)
        bundle=read(OUTPUT/'lawn-natural-manifest.json');proof=read(bundle['geometryProof']['path'])
        for record in proof:
            self.assertEqual(sum(b['low']for b in record['bladeRanges']),12 if record['edgeMaster']else 16)
            self.assertTrue(all(b['pointedTip']and not b['clipped']and b['triangleCount']==3 for b in record['bladeRanges']))
        for action in('normal','tangent','tip','uniform-frame','lod-shape'):
            decoded=deepcopy(self.decoded);name=next(iter(decoded));row=decoded[name]
            if action=='normal':row['normals'][0]=(0.,0.,0.)
            elif action=='tangent':row['tangents'][0]=(0.,0.,0.,1.)
            elif action=='tip':row['uv0'][4]=(1.,1.)
            elif action=='uniform-frame':row['normals']=[(0.,0.,1.)]*len(row['positions'])
            else:decoded[name.rsplit('_LOD',1)[0]+'_LOD2']['positions'][0]=(0.,0.,0.)
            with self.subTest(action=action),self.assertRaisesRegex(RuntimeError,'frame|LOD|geometry|tip|normal'):
                native._upright_morphology(self.plan,meshes,decoded)

    def test_repinned_morphology_metadata_leaf_loss_width_reach_and_full_donor_proof_rejected(self):
        records=read(self.bundle['geometryProof']['path'])
        for action in('low-share','clipped','width','reach','leaf-loss','positions','legacy'):
            with tempfile.TemporaryDirectory(dir=ROOT/'output/unreal',prefix='upright-proof-negative-')as temporary:
                folder=Path(temporary);plan=deepcopy(self.plan);bundle=deepcopy(self.bundle);changed=deepcopy(records)
                if action=='legacy':plan['audit']['legacyLawnProof']['retainedInstances']=40436
                elif action=='leaf-loss':changed[0]['bladeRanges'].pop()
                elif action=='positions':changed[0]['positionsCm'][0][2]=0.5
                else:
                    blade=changed[0]['bladeRanges'][0]
                    if action=='low-share':blade['low']=False
                    elif action=='clipped':blade['clipped']=True
                    elif action=='width':blade['widthCm']=0.6
                    else:blade['reachCm']=4.
                path=folder/'lawn-natural-prototypes.json';write(path,changed);bundle['geometryProof']=pin(path)
                write(folder/'lawn-natural-manifest.json',bundle)
                plan['geometryManifest']['path']=str(folder/'geometry-manifest.json')
                with self.subTest(action=action),self.assertRaisesRegex(RuntimeError,'proof|inventory|width|reach|anatomy|trim|geometry'):
                    native._upright_morphology(plan,{m['id']:m for m in self.manifest['meshes']},self.decoded)

    def test_new_study_coverage_cannot_relax_or_force_acceptance(self):
        for mutate in(lambda c:c.coverage['criteria'].update(minimumTopViewCoverage=.70),
                      lambda c:c.coverage['windows'][0]['lods'][0].update(projectedCoverage=.74),
                      lambda c:c.coverage['windows'][0]['lods'][0].update(studyTargetsMet=False),
                      lambda c:c.plan['audit'].update(nativeAppearanceAccepted=True),
                      lambda c:c.plan['audit'].update(instances=102010)):
            with self.subTest(mutate=mutate),self.candidate(mutate)as c:
                with self.assertRaisesRegex(RuntimeError,'coverage|acceptance|population'):self.validate(c.plan,c.manifest)


    def test_actual_legacy_98344_source_and_ordered_40437_trim_proof(self):
        report=read(ROOT/'output/unreal/realism-20260926-r5/photoreal-import-report.json')
        rural=read(ROOT/'output/unreal/realism-20260926-r5/rural-import-report.json')
        source=read(ROOT/'output/unreal/rural-context-20260923-r4/geometry/rural-context-geometry.json')
        geometry,trimmed,pin_row,proof=native._trimmed_legacy_placement(report,rural,source)
        self.assertEqual(native.sha(pin_row['path']),pin_row['sha256'])
        self.assertEqual([len(trimmed[k]['instances'])for k in native.LEGACY_GROUPS],[10118,10153,10147,10019])
        self.assertEqual(proof['retainedInstances'],40437);self.assertEqual(proof['removedByHistoricalRuralImport'],57907)
        inspection=read(ROOT/'output/unreal/lawn-native-inspection-20260930-r1.json')
        self.assertIs(inspection['contentUnchanged'],True);self.assertEqual(inspection['nativeLawnInstanceCount'],40437)
        rows={row['actor']:row for row in inspection['taggedLawnActors']}
        for key in native.LEGACY_GROUPS:
            values=rows[geometry['groups'][key]['actor']]['orderedInstanceTransforms']
            self.assertEqual(native.digest(native._rural_values(values)),proof['groups'][key]['transformsSha256'])


if __name__=='__main__':unittest.main()
