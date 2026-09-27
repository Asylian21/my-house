"""One-binding map witness and exact owned-package failure restoration."""
import copy
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location('calibration_import',Path(__file__).with_name('realism-stove-calibration-import.py'))
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)

class CalibrationImportTests(unittest.TestCase):
    def fixture(self):
        old='/Game/Brezi/Realism/Stove/Materials/M_Stove_Flames.M_Stove_Flames'
        change={'actor':'flame','component':'flame.component','slot':0,'before':old,'after':M.PREFIX+'/Materials/M_Stove_Flames_512.M_Stove_Flames_512'}
        actors={name:{'components':[{'path':name+'.component','mesh':'old','materials':[old if name=='flame' else name],
            'collision':'QUERY_ONLY','attachParent':'door','passFlags':{'render_in_main_pass':False},'transform':[1,2,3],
            'intensity':2800,'visible':True,'hiddenInGame':False}]} for name in ('flame','glass','light','r4-door','r4-overlay','r5-oak')}
        return actors,change

    def test_exact_one_binding_delta_preserves_every_other_actor_property(self):
        original,change=self.fixture();expected=M.expected_witness(original,[change])
        self.assertEqual(expected['flame']['components'][0]['materials'],[change['after']])
        expected['flame']['components'][0]['materials']=[change['before']]
        self.assertEqual(expected,original)
        for changes in ([],[change,change],[{**change,'slot':1}],[{**change,'after':'foreign'}]):
            with self.assertRaises(RuntimeError):M.expected_witness(original,changes)

    def test_geometry_door_pass_flags_glass_and_lights_fail_closed(self):
        original,change=self.fixture();expected=M.expected_witness(original,[change])
        for actor,field,value in [('flame','mesh','other'),('r4-door','passFlags',{}),('r4-overlay','attachParent',None),
            ('r5-oak','materials',['other']),('glass','visible',False),('light','intensity',3000),('flame','transform',[0,0,0])]:
            changed=copy.deepcopy(expected);changed[actor]['components'][0][field]=value
            with self.subTest(actor=actor,field=field),self.assertRaises(RuntimeError):M.verify_witness(expected,changed)
        with self.assertRaises(RuntimeError):M.verify_witness(expected,{**expected,'newactor':{}})

    def test_only_one_new_material_and_map_byte_change_allowed(self):
        content=Path('/project/Content');old=str(content/'old.uasset');map_=str(content/M.MAP_FILE)
        clone=str(content/'Brezi/Realism/StoveCalibration/Materials/M_Stove_Flames_512.uasset')
        before={map_:'map',old:'old'};after={**before,map_:'new',clone:'clone'}
        M.validate_changes(before,after,content,complete=True)
        for changed in ({**after,old:'changed'},{**after,str(content/'extra.uasset'):'extra'},before):
            with self.assertRaises(RuntimeError):M.validate_changes(before,changed,content,complete=True)

    def test_restore_requires_dead_process_and_exact_failed_bytes_and_preserves_history(self):
        for state in ('ready','running','drifted'):
            with self.subTest(state=state),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp).resolve();source,output=root/'source',root/'target';content=output/'Project/BreziTwin/Content';donor=source/'Project/BreziTwin/Content'
                for folder in (content,donor):
                    (folder/'Brezi/Maps').mkdir(parents=True);(folder/M.MAP_FILE).write_bytes(b'original')
                before=M.inventory(content);checkpoint=output/'realism-stove-calibration-checkpoint';checkpoint.mkdir();(checkpoint/'Brezi.umap').write_bytes(b'original')
                (content/M.MAP_FILE).write_bytes(b'failed');clone=content/'Brezi/Realism/StoveCalibration/Materials/M_Stove_Flames_512.uasset';clone.parent.mkdir(parents=True);clone.write_bytes(b'clone')
                M.write(output/'realism-stove-calibration-report.json',{'status':'failed','output':str(output),'sourceOutput':str(source),'nativeProcessId':123,'beforeAssetHashes':before,'failedContentHashes':M.inventory(content)})
                M.write(output/'performance-source.json',{'content':before})
                if state=='drifted':clone.write_bytes(b'drift')
                prior=M.inventory(output);helper=SimpleNamespace(checked_paths=lambda source,output:(Path(source),output))
                with patch.object(M,'module',return_value=helper),patch.object(M.os,'kill',side_effect=None if state=='running' else ProcessLookupError):
                    if state=='ready':
                        M.restore(output);self.assertEqual(M.inventory(content),before);self.assertFalse((output/'realism-stove-calibration-report.json').exists())
                        history=list((output/'realism-stove-calibration-history').iterdir());self.assertEqual(len(history),1)
                        self.assertEqual((history[0]/'failed-assets/Brezi/Realism/StoveCalibration/Materials/M_Stove_Flames_512.uasset').read_bytes(),b'clone')
                    else:
                        with self.assertRaises(RuntimeError):M.restore(output)
                        self.assertEqual(M.inventory(output),prior)

if __name__=='__main__':unittest.main()
