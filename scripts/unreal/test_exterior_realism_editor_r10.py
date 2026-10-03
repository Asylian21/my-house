"""Saved actual R22c source checker and counterfactual rejection fixtures."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('r10_saved_editor_fixture',ROOT/'scripts/unreal/exterior-realism-integration-editor-check-r10.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
r=c.n.read(c.n.repair.CANDIDATE/c.n.REPORT);plan,b=c.g.validate_plan();supplement=c.n.repair.validate_supplement()


class SavedComposition(unittest.TestCase):
    def test_actual_saved_whole_counterfactual_and_terminal_process(self):
        summary=c.validate_saved(r,plan,b,supplement)
        self.assertEqual((summary['savedActors'],summary['fullSceneHismInstances'],summary['recordedExteriorHismInstances']),(5346,676944,632538))
        c.g.actual_terminal(c.n.repair.CANDIDATE/c.n.REPORT,c.n.repair.CANDIDATE/'realism-integration-native-r3-process.json',c.HELPER,'realism-integration-native-r3')

    def test_old_owner_and_false_saved_or_accepted_flags_rejected(self):
        for field,value in [('owner','scripts/unreal/exterior-realism-integration-native-r22.py'),('savedMapUnloadedReloaded',False),('nativeAppearanceAccepted',True),('performanceAccepted',True)]:
            changed=copy.deepcopy(r);changed[field]=value
            with self.subTest(field=field),self.assertRaises(RuntimeError):c.validate_saved(changed,plan,b,supplement)

    def test_extra_or_colliding_added_actor_identity_rejected(self):
        changed=copy.deepcopy(r);changed['addedActorIdentityMap']['unapproved']='unapproved'
        with self.assertRaises(RuntimeError):c.validate_saved(changed,plan,b,supplement)
        changed=copy.deepcopy(r);changed['addedActorIdentityMap'][next(iter(changed['addedActorIdentityMap']))]=next(iter(b['before']))
        with self.assertRaises(RuntimeError):c.validate_saved(changed,plan,b,supplement)

    def test_64_grass_membership_cull_overlap_cannot_be_widened(self):
        changed=copy.deepcopy(r);changed['componentCullOverrides'][0]['afterCullCm']=[18000,100000]
        with self.assertRaises(RuntimeError):c.validate_saved(changed,plan,b,supplement)
        changed=copy.deepcopy(r);changed['originalMemberChanges'][0]['retainedInstances']-=1
        with self.assertRaises(RuntimeError):c.validate_saved(changed,plan,b,supplement)

    def test_roof_override_and_full_scene_census_cannot_change(self):
        changed=copy.deepcopy(r);changed['roofComponentOverrides'][0]['slot']=1
        with self.assertRaises(RuntimeError):c.validate_saved(changed,plan,b,supplement)
        changed=copy.deepcopy(r);changed['actualFullSceneHismInstances']=632538
        with self.assertRaises(RuntimeError):c.validate_saved(changed,plan,b,supplement)

    def test_exact64_native_matrix_and_material_set_claims_rejected(self):
        changed=copy.deepcopy(r);changed['newGrassRootReadback'][0]['actualStoredDoubleMatrix'][0][0]+=1e-10
        with self.assertRaises(RuntimeError):c.validate_saved(changed,plan,b,supplement)
        changed=copy.deepcopy(r);changed['scopedMaterialGraphs']=55
        with self.assertRaises(RuntimeError):c.validate_saved(changed,plan,b,supplement)


if __name__=='__main__':unittest.main(verbosity=2)
