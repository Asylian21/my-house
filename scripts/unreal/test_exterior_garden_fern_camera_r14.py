"""CPU source/staging fixtures; never evidence of a new native capture."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
def module(name, file):
    s = importlib.util.spec_from_file_location(name, ROOT/'scripts/unreal'/file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m

c = module('r14_camera_fixture', 'exterior-garden-fern-camera-r14.py')


class PurposefulCameraFixtures(unittest.TestCase):
    def test_actual_source_ground_and_whole_crowns(self):
        view, audit = c.derive()
        self.assertEqual(view['id'], c.VIEW_ID)
        self.assertEqual(audit['sourceEyeContainingTriangleOrdinals'], [25])
        self.assertEqual(audit['sourceEyeClearanceBoxHits'], [])
        self.assertEqual(audit['sourceWholeCrownSightCorridorHits'], [])
        self.assertTrue(audit['original120cmFullCrownConservativeFraming']['entireBoxInsideSource16by9Frustum'])
        self.assertTrue(audit['saved35cmFernFullCrownConservativeFraming']['entireBoxInsideSource16by9Frustum'])
        self.assertFalse(audit['nativeFovMeasured'])

    def test_camera_append_preserves_all_root_fields_and_rows(self):
        original = (c.BASE.parent/'Project/BreziTwin/Content/Data/viewpoints.json').read_bytes()
        view, _ = c.derive()
        a, b = json.loads(original), json.loads(c.appended_bytes(original, view))
        self.assertEqual({k: v for k, v in a.items() if k != 'views'}, {k: v for k, v in b.items() if k != 'views'})
        self.assertEqual(b['views'][:-1], a['views'])
        self.assertEqual(b['views'][-1], view)

    def test_duplicate_camera_or_reencoded_prefix_is_rejected(self):
        original = (c.BASE.parent/'Project/BreziTwin/Content/Data/viewpoints.json').read_bytes()
        view, _ = c.derive()
        with self.assertRaises(RuntimeError):
            c.appended_bytes(c.appended_bytes(original, view), view)
        with self.assertRaises(RuntimeError):
            c.appended_bytes(json.dumps(json.loads(original)).encode(), view)

    def test_too_close_camera_that_crops_old_crown_is_rejected(self):
        view, _ = c.derive()
        altered = copy.deepcopy(view)
        altered['eyeCm'][1] -= 200
        root = c.read(c.FERN)['savedRootReadback']['actualNativeRootXYZ']
        with self.assertRaises(RuntimeError):
            c.frame_box(altered, c.crown_box(root, 54.49, 0, 120))

    def test_ground_degenerate_triangle_is_not_support(self):
        self.assertFalse(c.triangle_inside([0, 0], [[0, 0, 0], [1, 0, 0], [2, 0, 0]]))
        self.assertTrue(c.triangle_inside([.2, .2], [[0, 0, 0], [1, 0, 0], [0, 1, 0]]))

    def test_source_unsupported_by_saved_pair_is_rejected_before_reader(self):
        s = module('r14_stage_fixture', 'exterior-garden-fern-camera-stage-r14.py')
        with self.assertRaises(RuntimeError):
            s.actual_source(ROOT/'output/unreal/exterior-20261002-r25a')


if __name__ == '__main__':
    unittest.main()
