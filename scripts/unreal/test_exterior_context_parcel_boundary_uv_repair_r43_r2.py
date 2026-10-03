"""One targeted actual-geometry grain/exclusion repair contract, no replay."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('r43_uv', Path(__file__).with_name('exterior-context-parcel-boundary-uv-repair-r43-r2.py'))
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)


class WoodOrientationContract(unittest.TestCase):
    def test_actual_member_photo_V_axis_and_complete_masks_only(self):
        plan, before, after, masks, proof = g.load_source()
        self.assertTrue(all(r['solidIntersectionCm2'] == r['connectorIntersectionCm2'] == 0 for r in proof.values()))
        post = next(r for r in after['objects'] if r['material'] == 'wood' and ':post:' in r['id'])
        found = False
        for i, (a, na) in enumerate(zip(post['verticesCm'], post['normals'])):
            if na[2] != 0: continue
            for j, (b, nb) in enumerate(zip(post['verticesCm'], post['normals'])):
                if na == nb and a[:2] == b[:2] and a[2] != b[2]:
                    self.assertEqual(post['uv0'][i][0], post['uv0'][j][0])
                    self.assertNotEqual(post['uv0'][i][1], post['uv0'][j][1]); found = True; break
            if found: break
        self.assertTrue(found, 'Actual vertical long-member side must run along texture V')
        wrong = copy.deepcopy(after); wrong['objects'][0]['verticesCm'][0][0] += 1
        with self.assertRaises(ValueError): g.validate_delta(before, wrong)
        blocked = copy.deepcopy(masks); blocked['roads'] = after['connector']['sourceDomainCm']
        with self.assertRaises(ValueError): g.validate_full_exclusions(after, blocked)


if __name__ == '__main__': unittest.main(verbosity=2)
