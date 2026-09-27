"""Offline geometry/basis checks for the proposed grain correction; no UE process."""
import copy
import importlib.util
from pathlib import Path
import unittest

SPEC=importlib.util.spec_from_file_location('grain_study',Path(__file__).with_name('realism-grain-study.py'))
M=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class GrainStudyTests(unittest.TestCase):
    def test_exact_semantic_scope_is_eleven_members_two_axes(self):
        self.assertEqual(set(M.COHORT),{1457,1458,1459,1460,1461,1474,1483,1492,1501,1510,1519})
        self.assertEqual(sum(axis=='Y' for _,axis in M.COHORT.values()),9)
        self.assertTrue(all(number not in M.COHORT for number in range(1462,1466)))

    def test_current_projection_provably_crosses_horizontal_rail_grain(self):
        for normal in [(1,0,0),(0,1,0)]:
            _,v=M.basis(normal)
            self.assertEqual(v,(0,0,-1))
            self.assertEqual(M.dot(v,(1,0,0)),0)
            self.assertEqual(M.dot(v,(0,1,0)),0)
        self.assertEqual(M.basis((0,0,1))[1],(-1,0,0))  # tabletop runs along Y

    def test_proposed_side_face_grain_follows_member_long_axis(self):
        for axis,l in [('X',(1,0,0)),('Y',(0,1,0))]:
            for n in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
                t,v=M.basis(n,axis)
                if M.dot(n,l)==0:
                    self.assertEqual(abs(M.dot(v,l)),1)

    def test_basis_preserves_axis_scale_and_handedness_for_normal_map(self):
        cross=lambda a,b:(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
        for axis in ('X','Y'):
            for n in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
                t,v=M.basis(n,axis)
                self.assertEqual(M.dot(t,t),1);self.assertEqual(M.dot(v,v),1)
                self.assertEqual(M.dot(t,v),0);self.assertEqual(cross(t,v),n)

    def test_proposal_has_no_unreal_import_or_native_writer(self):
        text=Path(M.__file__).read_text()
        self.assertNotIn('import unreal',text)
        self.assertNotIn('set_material(',text)
        self.assertNotIn('save_loaded_asset(',text)


if __name__=='__main__':
    unittest.main()
