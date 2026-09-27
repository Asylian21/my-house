"""Furniture native witness/restore boundaries; no Unreal process."""
import copy
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location('furniture_import',Path(__file__).with_name('realism-furniture-import.py'))
M=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class FurnitureTests(unittest.TestCase):
    def fixture(self):
        flags={name:True for name in M.RENDER_FLAGS}
        original={}
        changes=[]
        for id_ in M.SOURCE_IDS:
            original[id_]={'tags':[id_],'components':[{'path':id_+'.source','visible':False,'hiddenInGame':True,'materials':['cloth'],'mesh':'original','collision':'QUERY_ONLY'}]}
            component={'path':'PH_'+id_+'.component','visible':True,'hiddenInGame':False,'renderFlags':flags,'passFlags':{'render_in_main_pass':True,'render_in_depth_pass':True},
                       'mesh':'bevel','materials':['cloth'],'collision':'NO_COLLISION','transform':[1,2,3]}
            original['PH_'+id_]={'tags':['PH_'+id_],'components':[component]}
            changes.append({'sourceId':id_,'visualSourceId':'PH_'+id_,'actor':'PH_'+id_,'component':component['path'],
                'before':{key:component[key] for key in ('visible','hiddenInGame','renderFlags')},
                'after':{'visible':False,'hiddenInGame':True,'renderFlags':{name:False for name in M.RENDER_FLAGS}}})
        material_changes=[]
        for id_ in M.GRAIN_IDS:
            actor='PH_'+id_
            original[actor]={'tags':[actor],'components':[{'path':actor+'.component','mesh':'wood','materials':['oak'],'collision':'NO_COLLISION'}]}
            material_changes.append({'sourceId':id_,'actor':actor,'component':actor+'.component','slot':0,'before':'oak','after':'/Game/Brezi/Realism/Furniture/Materials/Oak.Oak'})
        original['r4-door']={'tags':['BreziDoorId=BATH-105-DRYER-DOOR'],'components':[{'path':'door.component','visible':True,'hiddenInGame':False,'passFlags':{'render_in_main_pass':False,'render_in_depth_pass':False},'collision':'QUERY_ONLY','attachParent':None}]}
        original['r4-overlay']={'tags':['BreziRealismRoomDetails20260926'],'components':[{'path':'overlay.component','attachParent':'door.component','mobility':'MOVABLE'}]}
        return original,changes,material_changes

    def test_only20ph_flags_and11grain_slots_change(self):
        original,changes,materials=self.fixture()
        after=M.expected_witness(original,changes,materials)
        for id_ in M.SOURCE_IDS:
            self.assertEqual(after[id_],original[id_])
            self.assertFalse(after['PH_'+id_]['components'][0]['visible'])
            self.assertEqual(after['PH_'+id_]['components'][0]['passFlags'],original['PH_'+id_]['components'][0]['passFlags'])
        self.assertEqual(after['r4-door'],original['r4-door'])
        self.assertEqual(after['r4-overlay'],original['r4-overlay'])
        M.verify_witness(after,after,[])

    def test_saved_r4_attachments_collision_and_passflags_are_protected(self):
        original,changes,materials=self.fixture()
        expected=M.expected_witness(original,changes,materials)
        for actor,field,value in [('r4-door','collision','NO_COLLISION'),('r4-door','hiddenInGame',True),
            ('r4-door','passFlags',{'render_in_main_pass':True,'render_in_depth_pass':True}),('r4-overlay','attachParent',None)]:
            actual=copy.deepcopy(expected);actual[actor]['components'][0][field]=value
            with self.subTest(actor=actor,field=field),self.assertRaises(RuntimeError):M.verify_witness(expected,actual,[])

    def test_source_hiding_or_extra_grain_slot_rejected(self):
        original,changes,materials=self.fixture()
        with self.assertRaises(RuntimeError):M.expected_witness(original,changes,materials[:-1])
        changes[0]['visualSourceId']=changes[0]['sourceId']
        with self.assertRaises(RuntimeError):M.expected_witness(original,changes,materials)

    def test_oldcontent_immutable_newassets_onlyfurniture(self):
        content=Path('/project/Content');before={str(content/M.MAP_FILE):'map',str(content/'Brezi/Realism/RoomDetails/Door.uasset'):'old'}
        after={**before,str(content/M.MAP_FILE):'new',str(content/'Brezi/Realism/Furniture/Geometry/Sofa.uasset'):'new'}
        M.validate_changes(before,after,content)
        for p in ['Brezi/Realism/RoomDetails/Door.uasset','Brezi/Realism/Other/New.uasset','Brezi/Realism/Furniture/script.py']:
            with self.assertRaises(RuntimeError):M.validate_changes(before,{**after,str(content/p):'changed'},content)

    def test_failed_restore_preserves_evidence_and_refuses_drift_or_livepid(self):
        for state in ('ready','running','drifted'):
            with self.subTest(state=state),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp).resolve();source,output=root/'source',root/'target';content=output/'Project/BreziTwin/Content';donor=source/'Project/BreziTwin/Content'
                for folder in (content,donor):
                    (folder/'Brezi/Maps').mkdir(parents=True);(folder/M.MAP_FILE).write_bytes(b'original')
                before=M.inventory(content);(output/'realism-furniture-checkpoint').mkdir();(output/'realism-furniture-checkpoint/Brezi.umap').write_bytes(b'original')
                (content/M.MAP_FILE).write_bytes(b'failed');new=content/'Brezi/Realism/Furniture/New.uasset';new.parent.mkdir(parents=True);new.write_bytes(b'failedasset')
                M.write(output/'realism-furniture-report.json',{'status':'failed','output':str(output),'sourceOutput':str(source),'nativeProcessId':123,'beforeAssetHashes':before,'failedContentHashes':M.inventory(content)})
                M.write(output/'performance-source.json',{'content':before})
                if state=='drifted':new.write_bytes(b'drifted')
                prior=M.inventory(output);helper=SimpleNamespace(checked_paths=lambda source,output:(Path(source),output))
                with patch.object(M,'module',return_value=helper),patch.object(M.os,'kill',side_effect=None if state=='running' else ProcessLookupError):
                    if state=='ready':
                        M.restore(output);self.assertEqual(M.inventory(content),before);self.assertFalse((output/'realism-furniture-report.json').exists())
                        history=list((output/'realism-furniture-history').iterdir());self.assertEqual((history[0]/'failed-assets/Brezi/Realism/Furniture/New.uasset').read_bytes(),b'failedasset')
                    else:
                        with self.assertRaises(RuntimeError):M.restore(output)
                        self.assertEqual(M.inventory(output),prior)


if __name__=='__main__':unittest.main()
