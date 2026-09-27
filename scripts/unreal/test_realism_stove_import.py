"""Stove native witness/restore boundaries; no Unreal process."""
import copy
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location('stove_import',Path(__file__).with_name('realism-stove-import.py'))
M=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class StoveTests(unittest.TestCase):
    def fixture(self):
        flags={name:True for name in M.RENDER_FLAGS}
        original={};changes=[]
        for id_ in M.SOURCE_IDS:
            component={'path':id_+'.component','visible':True,'hiddenInGame':False,'renderFlags':flags,
                'passFlags':{'render_in_main_pass':True,'render_in_depth_pass':True},'mesh':'source','materials':['unchanged'],
                'collision':'QUERY_ONLY' if id_=='DOM_00553' else 'NO_COLLISION','transform':[1,2,3]}
            original[id_]={'tags':[id_],'components':[component]}
            changes.append({'sourceId':id_,'actor':id_,'component':component['path'],
                'before':{key:component[key] for key in ('visible','hiddenInGame','renderFlags')},
                'after':{'visible':False,'hiddenInGame':True,'renderFlags':{name:False for name in M.RENDER_FLAGS}}})
        original['r4-door']={'tags':['BreziDoorId=BATH-105-DRYER-DOOR'],'components':[{'path':'door.component','visible':True,'hiddenInGame':False,'passFlags':{'render_in_main_pass':False,'render_in_depth_pass':False},'collision':'QUERY_ONLY','attachParent':None}]}
        original['r4-overlay']={'tags':['BreziRealismRoomDetails20260926'],'components':[{'path':'overlay.component','attachParent':'door.component','mobility':'MOVABLE'}]}
        original['r5-oak']={'tags':['PH_DOM_01457'],'components':[{'path':'oak.component','materials':['Furniture/Materials/OakY'],'mesh':'original'}]}
        original['stove-glass']={'tags':['DOM_00557'],'components':[{'path':'glass.component','materials':['original-glass'],'mesh':'original'}]}
        original['stove-light']={'tags':[],'components':[{'path':'light.component','intensity':2800}]}
        return original,changes

    def test_only_seven_original_renderflags_change(self):
        original,changes=self.fixture();after=M.expected_witness(original,changes)
        for id_ in M.SOURCE_IDS:
            self.assertFalse(after[id_]['components'][0]['visible'])
            for field in ('mesh','transform','materials','collision','passFlags'):
                self.assertEqual(after[id_]['components'][0][field],original[id_]['components'][0][field])
        for id_ in ('r4-door','r4-overlay','r5-oak','stove-glass','stove-light'):
            self.assertEqual(after[id_],original[id_])
        M.verify_witness(after,after,[])

    def test_doors_glass_lights_oak_and_source_collision_are_protected(self):
        original,changes=self.fixture();expected=M.expected_witness(original,changes)
        for actor,field,value in [('r4-door','collision','NO_COLLISION'),('r4-overlay','attachParent',None),
            ('r5-oak','materials',['changed']),('stove-glass','materials',['changed']),('stove-light','intensity',1),('DOM_00553','collision','NO_COLLISION')]:
            actual=copy.deepcopy(expected);actual[actor]['components'][0][field]=value
            with self.subTest(actor=actor,field=field),self.assertRaises(RuntimeError):M.verify_witness(expected,actual,[])
        with self.assertRaises(RuntimeError):M.expected_witness(original,changes[:-1])

    def test_probe_log_requires_original_prefix_and_exact_reviewed_suffix(self):
        rows,pins,proof=M.probe_inputs()
        self.assertEqual(len(rows),2);self.assertEqual(proof['appendedBytes'],855)
        source=Path(proof['path']).read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'native.log';path.write_bytes(source)
            self.assertEqual(M.log_prefix_proof(path,proof['originalSha256'])['originalBytes'],21227)
            for data in (b'x'+source,source+b'Error: unknown problem',source[:21227]+b'unreviewed tail'):
                path.write_bytes(data)
                with self.assertRaises(RuntimeError):M.log_prefix_proof(path,proof['originalSha256'])

    def test_manifest_preserves_current_source_semantics_glass_and_unit_conversion(self):
        manifest=M.read(M.ROOT/'output/unreal/realism-fire-study-20260926-r4/geometry-report.json')
        scene=M.read(M.ROOT/'output/unreal/realism-20260926-r5/geometry/scene.json')
        M.validate_manifest(manifest,scene)
        for kind in ('source','glass','role','units'):
            changed=copy.deepcopy(manifest)
            if kind=='source':changed['sourceRecords']['DOM_00553']['metadata']['babylonCheckCollisions']=False
            elif kind=='glass':changed['hiddenSourceIds'][0]='DOM_00557'
            elif kind=='role':changed['objects'][0]['sourceIds']=['DOM_00557']
            else:changed['objects'][0]['expectedWorldBoundsCm']['min'][0]+=1
            with self.subTest(kind=kind),self.assertRaises(RuntimeError):M.validate_manifest(changed,scene)

    def test_oldcontent_immutable_newassets_onlystove(self):
        content=Path('/project/Content');before={str(content/M.MAP_FILE):'map',str(content/'Brezi/Realism/RoomDetails/Door.uasset'):'old'}
        after={**before,str(content/M.MAP_FILE):'new',str(content/'Brezi/Realism/Stove/Geometry/Sofa.uasset'):'new'}
        M.validate_changes(before,after,content)
        for p in ['Brezi/Realism/RoomDetails/Door.uasset','Brezi/Realism/Other/New.uasset','Brezi/Realism/Stove/script.py']:
            with self.assertRaises(RuntimeError):M.validate_changes(before,{**after,str(content/p):'changed'},content)

    def test_failed_restore_preserves_evidence_and_refuses_drift_or_livepid(self):
        for state in ('ready','running','drifted'):
            with self.subTest(state=state),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp).resolve();source,output=root/'source',root/'target';content=output/'Project/BreziTwin/Content';donor=source/'Project/BreziTwin/Content'
                for folder in (content,donor):
                    (folder/'Brezi/Maps').mkdir(parents=True);(folder/M.MAP_FILE).write_bytes(b'original')
                before=M.inventory(content);(output/'realism-stove-checkpoint').mkdir();(output/'realism-stove-checkpoint/Brezi.umap').write_bytes(b'original')
                (content/M.MAP_FILE).write_bytes(b'failed');new=content/'Brezi/Realism/Stove/New.uasset';new.parent.mkdir(parents=True);new.write_bytes(b'failedasset')
                M.write(output/'realism-stove-report.json',{'status':'failed','output':str(output),'sourceOutput':str(source),'nativeProcessId':123,'beforeAssetHashes':before,'failedContentHashes':M.inventory(content)})
                M.write(output/'performance-source.json',{'content':before})
                if state=='drifted':new.write_bytes(b'drifted')
                prior=M.inventory(output);helper=SimpleNamespace(checked_paths=lambda source,output:(Path(source),output))
                with patch.object(M,'module',return_value=helper),patch.object(M.os,'kill',side_effect=None if state=='running' else ProcessLookupError):
                    if state=='ready':
                        M.restore(output);self.assertEqual(M.inventory(content),before);self.assertFalse((output/'realism-stove-report.json').exists())
                        history=list((output/'realism-stove-history').iterdir());self.assertEqual((history[0]/'failed-assets/Brezi/Realism/Stove/New.uasset').read_bytes(),b'failedasset')
                    else:
                        with self.assertRaises(RuntimeError):M.restore(output)
                        self.assertEqual(M.inventory(output),prior)


if __name__=='__main__':unittest.main()
