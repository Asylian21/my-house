"""Actual stdlib integration, morphology mutations and immutable-source guards."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('taper_native',ROOT/'scripts/unreal/exterior-lawn-tapered-native.py')
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)


class TaperIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=json.loads((n.OUTPUT/'lawn-natural-plan.json').read_text());cls.library=json.loads((n.OUTPUT/'geometry-manifest.json').read_text())
        cls.meshes={m['id']:m for m in cls.library['meshes']};cls.decoded=n._glb_geometry(n.OUTPUT/'lawn-natural.glb',True)
        cls.records=json.loads((n.OUTPUT/'lawn-natural-prototypes.json').read_text())
        source,_=n.selected_source();cls.old=json.loads((Path(source['priorPlan']['path']).parent/'lawn-natural-prototypes.json').read_text())
        cls.before={path:n.sha(path)for path in cls.plan['inputFiles']}

    @classmethod
    def tearDownClass(cls):
        if {p:n.sha(p)for p in cls.before}!=cls.before:raise AssertionError('Frozen/source input mutated during tests')

    def validate(self,plan=None,library=None):
        return n.validated_groups(plan or self.plan,library or self.library,self.plan['sourceSceneSha256'],self.plan['sourceObjSha256'])

    def morphology(self,decoded):n._tapered_morphology(self.meshes,decoded,self.records,self.old)

    def test_01_actual_groups_crowns_legacy_and_no_lod_loss(self):
        groups=self.validate();self.assertEqual(len(groups),40);self.assertEqual(sum(len(g['instances'])for g in groups),102011)
        for old,new in zip(self.plan['groups'],groups):
            self.assertEqual(new['instances'],[{k:r[k]for k in ('positionCm','yawDeg','scale')}for r in old['instances']])
        self.assertEqual(self.plan['audit']['allInstancesTriangleBudgetByLod'],[18571200]*3)

    def test_02_reject_upright_owner_spoof(self):
        plan=deepcopy(self.plan);plan['owner']='scripts/unreal/exterior-lawn-upright.py'
        with self.assertRaisesRegex(RuntimeError,'adapter owner'):self.validate(plan)

    def test_03_reject_repinned_placement_and_policy(self):
        for change in ('transform','domain','collision','survey'):
            plan=deepcopy(self.plan)
            if change=='transform':plan['groups'][0]['instances'][0]['positionCm'][0]+=10000
            if change=='domain':plan['managedLawnKeepPolygonsCm'][0][0][0]-=100
            if change=='collision':plan['renderingPolicy']['collision']='query-and-physics'
            if change=='survey':plan['sourceTriangleCount']=999
            with self.subTest(change=change),self.assertRaisesRegex(RuntimeError,'original policy/rows'):self.validate(plan)

    def test_04_reject_unsafe_self_repinned_glb(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'output/unreal')as directory:
            directory=Path(directory);glb=directory/'foreign.glb';raw=bytearray((n.OUTPUT/'lawn-natural.glb').read_bytes());raw[-64]^=1;glb.write_bytes(raw)
            library=deepcopy(self.library)
            for m in library['meshes']:m.update(glbPath=str(glb),glbSha256=n.sha(glb))
            path=directory/'geometry-manifest.json';path.write_text(json.dumps(library));plan=deepcopy(self.plan);plan['geometryManifest']={'path':str(path),'sha256':n.sha(path)}
            bundle=json.loads((n.OUTPUT/'lawn-natural-manifest.json').read_text());bundle['geometryManifest']=plan['geometryManifest']
            (directory/'lawn-natural-manifest.json').write_text(json.dumps(bundle))
            with self.assertRaisesRegex(RuntimeError,'selected GLB byte identity'):self.validate(plan,library)

    def test_05_reject_unsafe_self_repinned_anatomy(self):
        plan=deepcopy(self.plan);plan['geometryProof']['sha256']='0'*64
        with self.assertRaisesRegex(RuntimeError,'anatomy pin|bundle/proof ownership'):self.validate(plan)

    def test_06_actual_frames_are_not_unit_vector_claims(self):
        decoded=deepcopy(self.decoded);key=next(iter(self.meshes))
        for lod in range(3):decoded[key+'_LOD'+str(lod)]['normals'][0]=(0.,0.,1.)
        with self.assertRaisesRegex(RuntimeError,'normals/tangents'):self.morphology(decoded)

    def test_07_reject_uv_tangent_handedness(self):
        decoded=deepcopy(self.decoded);key=next(iter(self.meshes))
        for lod in range(3):
            d=decoded[key+'_LOD'+str(lod)];t=d['tangents'][0];d['tangents'][0]=(*t[:3],-t[3])
        with self.assertRaisesRegex(RuntimeError,'normals/tangents'):self.morphology(decoded)

    def test_08_reject_loss_of_far_leaf_identity(self):
        decoded=deepcopy(self.decoded);name=next(k for k in decoded if k.endswith('_LOD2'));decoded[name]['colors'][0]=(1.,1.,1.,1.)
        with self.assertRaisesRegex(RuntimeError,'identity lost'):self.morphology(decoded)

    def test_09_reject_disconnected_leaf_and_flat_tip_uv(self):
        key=next(iter(self.meshes))
        for kind in ('topology','tip'):
            decoded=deepcopy(self.decoded)
            for lod in range(3):
                d=decoded[key+'_LOD'+str(lod)]
                if kind=='topology':values=list(d['indices']);values[0]=5;d['indices']=tuple(values)
                else:d['uv0'][4]=(0.,.78)
            with self.subTest(kind=kind),self.assertRaises(RuntimeError):self.morphology(decoded)

    def test_10_actual_opaque_alpha_and_mean_color(self):
        key=next(iter(self.meshes))
        for kind in ('alpha','color'):
            decoded=deepcopy(self.decoded)
            for lod in range(3):
                d=decoded[key+'_LOD'+str(lod)];c=d['colors'][0];d['colors'][0]=(*c[:3],.5)if kind=='alpha'else(.1,.1,.1,1.)
            with self.subTest(kind=kind),self.assertRaisesRegex(RuntimeError,'opaque color|mean color'):self.morphology(decoded)

    def test_11_receipts_actual_values_and_pending_acceptance(self):
        audit=self.plan['audit'];self.assertEqual(audit['physicalCoverage']['status'],n.COVER_STATUS);self.assertEqual(audit['boundaryCoverage']['status'],n.BOUNDARY_STATUS)
        self.assertTrue(all(.75<=l['projectedCoverage']<.80 and l['tenCmBinCoverageP10']>=.55 for w in audit['physicalCoverage']['windows']for l in w['lods']))
        self.assertEqual([w['boundaryId']for w in audit['boundaryCoverage']['windows']],['deck','mulch'])
        self.assertTrue(all(audit[k]is False for k in ('nativeVerified','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','integrationAuthorized')))
        decoded=self.decoded;managed=n.base_module()._managed_domain(self.plan)
        for field in ('physicalCoverage','boundaryCoverage'):
            plan=deepcopy(self.plan);plan['audit'][field]['windows'][0]['lods'][0]['projectedCoverage']=.99
            with self.subTest(field=field),self.assertRaisesRegex(RuntimeError,'receipt differs|policy differs|bundle plan pin differs'):n._coverage_claims(plan,self.meshes,decoded,managed)

    def test_12_adapter_views_and_recipe_are_exact(self):
        source,_=n.selected_source();directory=Path(source['priorPlan']['path']).parent
        old=json.loads((directory/'lawn-qa-views.json').read_text());views=json.loads((n.OUTPUT/'lawn-qa-views.json').read_text())
        self.assertEqual(views['views'],old['views']);self.assertEqual(views['owner'],n.ADAPTER);self.assertEqual(views['plan']['sha256'],n.sha(n.OUTPUT/'lawn-natural-plan.json'))
        self.assertEqual((n.OUTPUT/'material-manifest.json').read_bytes(),(n.STUDY/'material-manifest.json').read_bytes())
        self.assertEqual(n.sha(n.BASE),n.BASE_SHA)


if __name__=='__main__':unittest.main(verbosity=2)
