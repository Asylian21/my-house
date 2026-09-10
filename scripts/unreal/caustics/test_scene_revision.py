"""CPU-only corrupted-lineage fixtures. No fixture represents native acceptance."""
from pathlib import Path
import copy, json, tempfile, unittest
from unittest.mock import patch
import scene_revision as r

class RevisionTests(unittest.TestCase):
    def test_header_preserves_separate_current_and_receiver_origins(self):
        a={k:'a'*64 for k in ('sceneSha256','objSha256','receiverOriginSceneSha256','receiverOriginObjSha256','bindingSha256','mapSha256','waterBindingSha256','transportSha256','deliverySha256')}
        a.update({k:'b'*40 for k in ('bindingSha1','transportSha1','deliverySha1')})
        a['receiverOriginSceneSha256']='c'*64
        text=r.header(a,'d'*64,'')
        self.assertIn('CurrentSceneSha256 = TEXT("'+'a'*64+'")',text)
        self.assertIn('ReceiverOriginSceneSha256 = TEXT("'+'c'*64+'")',text)
        self.assertIn('LegacyEditorPairSha256 = TEXT("")',text)
        with self.assertRaises(ValueError):r.header(a,'untrusted";code','')

    def fixture(self,root,hidden=False):
        project=root/'project';(project/'Content/Brezi/Maps').mkdir(parents=True);(project/'Content/Data').mkdir()
        (project/r.PRIVATE).mkdir(parents=True)
        mapfile=project/'Content/Brezi/Maps/Brezi.umap';mapfile.write_bytes(b'synthetic map for unit tests only')
        walk=project/'Content/Data/walking.json';walk.write_bytes(b'{}')
        binding=root/'binding.json';binding.write_bytes(b'{}')
        a={k:'a'*64 for k in ('sceneSha256','objSha256','receiverOriginSceneSha256','receiverOriginObjSha256','waterBindingSha256','transportSha256','deliverySha256')}
        a.update({k:'b'*40 for k in ('transportSha1','deliverySha1')})
        a.update(schemaVersion=1,status='pre-build-source-scene-revision',bindingSha256=r.sha(binding),bindingSha1=r.sha(binding,'sha1'),mapSha256=r.sha(mapfile),walkingSha256=r.sha(walk))
        if hidden:
            hidden_path=project/'Content/Data/hidden-collision.json';hidden_path.write_bytes(b'fixture hidden collision')
            source_path=root/'hidden-source.json';source_path.write_bytes(b'fixture source')
            a.update(hiddenCollisionSha256=r.sha(hidden_path),hiddenCollisionSourceFileHashes={str(source_path.relative_to(root)):r.sha(source_path)},hiddenCollisionAssetHashes={})
        authority=root/'authority.json';authority.write_bytes(r.encode(a));ah=r.sha(authority)
        header=project/r.PRIVATE/'BreziSceneRevision.h';header.write_text(r.header(a,ah,''))
        proofs={}
        for i,phase in enumerate((0,.125)):
            proof=root/f'proof-{i}.json';value={'status':'opaque-scene-transport-and-composite-readback-validated',
                'fixtureOnly':True,'sceneBindingSha256':a['bindingSha256'],'waterBindingSha256':a['waterBindingSha256'],
                'transportContractSha256':a['transportSha256'],'scene':{'matchedReceivers':45,'matchedWater':1},
                'inputHashes':{str(p):r.sha(p) for p in (authority,mapfile,walk,header)},'requestedMaterialTimeSeconds':phase,'nativePid':900000+i}
            if hidden:value['inputHashes'][str(hidden_path)]=r.sha(hidden_path)
            proof.write_bytes(r.encode(value));proofs[str(proof)]=r.sha(proof)
        pair=root/'pair.json';pair.write_bytes(r.encode({'status':'two-phase-opaque-transport-readbacks-validated','fixtureOnly':True,
            'proofs':proofs,'requestedMaterialPhasesSeconds':[0,.125],'nativePids':[900000,900001]}))
        return project,authority,ah,binding,pair

    def test_rejects_stale_map_missing_precapture_authority_and_duplicate_phase(self):
        for case in ('map','authority-pin','phase','header','pair-sha'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as d:
                root=Path(d).resolve();project,authority,ah,binding,pair=self.fixture(root)
                args=[authority,ah,binding,pair,r.sha(pair),project]
                r.check_pair(*args) # Fixture self-consistency only, no GPU execution.
                if case=='map':(project/'Content/Brezi/Maps/Brezi.umap').write_bytes(b'changed')
                elif case=='header':(project/r.PRIVATE/'BreziSceneRevision.h').write_text('changed')
                elif case=='pair-sha':args[4]='0'*64
                else:
                    p=root/'proof-1.json';v=r.read(p)
                    if case=='authority-pin':v['inputHashes'].pop(str(authority))
                    else:v['requestedMaterialTimeSeconds']=0
                    p.write_bytes(r.encode(v));v=r.read(pair);v['proofs'][str(p)]=r.sha(p);pair.write_bytes(r.encode(v));args[4]=r.sha(pair)
                with self.assertRaises(ValueError):r.check_pair(*args)

    def test_hidden_authority_requires_current_file_and_precapture_pin(self):
        for case in ('unchanged','manifest','capture-pin','source'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as d:
                root=Path(d).resolve();project,authority,ah,binding,pair=self.fixture(root,hidden=True)
                args=[authority,ah,binding,pair,r.sha(pair),project]
                with patch.object(r,'ROOT',root):
                    r.check_pair(*args) # Synthetic integrity fixture, not native acceptance.
                    if case=='unchanged':continue
                    if case=='manifest':(project/'Content/Data/hidden-collision.json').write_bytes(b'stale')
                    elif case=='source':(root/'hidden-source.json').write_bytes(b'changed hull')
                    else:
                        proof=root/'proof-1.json';v=r.read(proof);v['inputHashes'].pop(str(project/'Content/Data/hidden-collision.json'))
                        proof.write_bytes(r.encode(v));v=r.read(pair);v['proofs'][str(proof)]=r.sha(proof);pair.write_bytes(r.encode(v));args[4]=r.sha(pair)
                    with self.assertRaises(ValueError):r.check_pair(*args)


class HiddenSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        context=r.ROOT/'output/unreal/deck-gap-study/native-context.json'
        binding=r.ROOT/'output/unreal/deck-gap-study/scene-revision/export-01/binding.json'
        if not context.is_file() or not binding.is_file():raise unittest.SkipTest('Reviewed local deck migration inputs unavailable')
        c=r.read(context);cls.project=Path(c['project']);cls.binding=r.read(binding)
        cls.hidden=Path(c['source'])/'hidden-collision.json'

    def test_actual_export_and_58_preserved_native_assets(self):
        result=r.verify_hidden_collision(self.project,self.binding,self.hidden)
        self.assertEqual(result['sha256'],r.sha(self.hidden));self.assertEqual(len(result['assetFileHashes']),58)
        self.assertEqual(result['proof']['colliders'],57);self.assertEqual(result['proof']['triangles'],684)
        self.assertFalse(result['proof']['nativeCollisionQueriesReexecuted'])

    def test_old_hidden_export_is_rejected_for_new_source(self):
        with self.assertRaisesRegex(ValueError,'another scene/OBJ'):
            r.verify_hidden_collision(self.project,self.binding,r.ROOT/'output/unreal/geometry/hidden-collision.json')

    def test_saved_hidden_asset_corruption_rejected(self):
        value=r.verify_hidden_collision(self.project,self.binding,self.hidden)
        target=self.project/next(iter(value['assetFileHashes']));real=r.sha
        def changed(path,kind='sha256'):
            return '0'*64 if Path(path)==target else real(path,kind)
        with patch.object(r,'sha',changed),self.assertRaisesRegex(ValueError,'Saved hidden collision asset changed'):
            r.verify_hidden_collision(self.project,self.binding,self.hidden)

    def test_modified_installed_manifest_is_rejected(self):
        target=self.project/'Content/Data/hidden-collision.json';real=r.sha
        def changed(path,kind='sha256'):
            return '0'*64 if Path(path)==target else real(path,kind)
        with patch.object(r,'sha',changed),self.assertRaisesRegex(ValueError,'unreviewed origin'):
            r.verify_hidden_collision(self.project,self.binding,self.hidden)

    def test_hidden_record_policy_change_is_rejected(self):
        real=r.read
        def changed(path):
            value=real(path)
            if Path(path)==r.ROOT/'output/unreal/geometry/hidden-collision.json':value['objects'][0]['nativeRole']='floor'
            return value
        with patch.object(r,'read',changed),self.assertRaisesRegex(ValueError,'records, geometry or policy changed'):
            r.verify_hidden_collision(self.project,self.binding,self.hidden)

    def test_capture_geometry_change_is_rejected(self):
        real=r.read
        def changed(path):
            value=real(path)
            if Path(path)==self.hidden.parent/'hidden-collision-source.json':value['colliders'][0]['positions'][0]+=1
            return value
        with patch.object(r,'read',changed),self.assertRaisesRegex(ValueError,'capture geometry or metadata changed'):
            r.verify_hidden_collision(self.project,self.binding,self.hidden)

    def test_historical_geometry_proof_cannot_be_relabelled(self):
        real=r.read
        def changed(path):
            value=real(path)
            if Path(path)==r.ROOT/'output/unreal/import-report.json':value['hiddenCollision']['verification']['nativeTrianglesMeasured']=False
            return value
        with patch.object(r,'read',changed),self.assertRaisesRegex(ValueError,'saved geometry proof absent'):
            r.verify_hidden_collision(self.project,self.binding,self.hidden)

if __name__=='__main__':unittest.main()
