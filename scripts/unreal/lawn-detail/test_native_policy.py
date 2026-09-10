"""Portable source/proof checks; these do not execute Unreal or author assets."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
NATIVE=HERE
sys.path.insert(0,str(NATIVE))
import native_assets as a
import native_layer as layer
ROOT=layer.ROOT
PROTOTYPES=ROOT/'output/unreal/vegetation-prototypes'
REPORT=json.loads((PROTOTYPES/'prototypes.json').read_text())
ROWS={p['id']:p for p in REPORT['prototypes'] if p['id'] in a.IDS}


class NativePolicy(unittest.TestCase):
    def test_actual_four_glbs(self):
        self.assertEqual(set(ROWS),set(a.IDS))
        for id_,row in ROWS.items():
            with self.subTest(id=id_):
                source=a.source_mesh(PROTOTYPES/row['file'],row)
                self.assertEqual(source['triangles'],row['triangles'])
                self.assertEqual(source['vertices'],row['exportedVertices'])
                self.assertEqual(a.compare_faces(source['faces'],source['faces'])['maximumUV0Error'],0)

    def test_real_face_winding_and_uv_changes_refused(self):
        row=ROWS[a.IDS[0]];source=a.source_mesh(PROTOTYPES/row['file'],row)['faces']
        for kind in ('winding','uv','position','missing','duplicate'):
            changed=copy.deepcopy(source)
            if kind=='winding':changed[0]=list(reversed(changed[0]))
            if kind=='uv':changed[0][0][1][0]+=.001
            if kind=='position':changed[0][0][0][0]+=.01
            if kind=='missing':changed.pop()
            if kind=='duplicate':changed[0]=copy.deepcopy(changed[1])
            with self.subTest(kind=kind),self.assertRaises(RuntimeError):a.compare_faces(changed,source)

    def test_cyclic_source_winding_allowed(self):
        row=ROWS[a.IDS[1]];source=a.source_mesh(PROTOTYPES/row['file'],row)['faces']
        actual=[r[1:]+r[:1] for r in reversed(source)]
        self.assertTrue(a.compare_faces(actual,source)['triangleMultiplicityAndWindingVerified'])

    def test_source_hash_refused(self):
        row=copy.deepcopy(ROWS[a.IDS[0]]);row['sha256']='0'*64
        with self.assertRaises(RuntimeError):a.source_mesh(PROTOTYPES/row['file'],row)

    def test_transform_order_count_finite_and_error(self):
        row={'p':[0.,1.,2.],'q':[0.,0.,0.,1.],'s':[1.,1.,1.]}
        self.assertEqual(layer.close_transforms([row],[row]),{'p':0.,'q':0.,'s':0.})
        for key,delta in [('p',.003),('q',.01),('s',.001),('p',float('nan'))]:
            changed=copy.deepcopy(row);changed[key][0]+=delta
            with self.subTest(key=key,delta=delta),self.assertRaises(RuntimeError):layer.close_transforms([changed],[row])
        with self.assertRaises(RuntimeError):layer.close_transforms([row],[])
        other=copy.deepcopy(row);other['p'][0]=10
        with self.assertRaises(RuntimeError):layer.close_transforms([row,other],[other,row])

    def test_quaternion_sign_is_equivalent(self):
        one={'p':[0.,0.,0.],'q':[0.,0.,0.,1.],'s':[1.,1.,1.]};two=copy.deepcopy(one);two['q']=[0.,0.,0.,-1.]
        self.assertEqual(layer.close_transforms([one],[two])['q'],0)

    def test_json_value_roundtrip_keeps_numeric_changes_visible(self):
        self.assertEqual(a.values({'x':(0.,1.)}),{'x':[0,1]})
        self.assertNotEqual(a.values({'x':(0.,1.0001)}),{'x':[0,1]})
        with self.assertRaises(ValueError):a.values({'x':float('nan')})

    def test_actual_placement_binding(self):
        path=ROOT/'scripts/unreal/lawn-detail/placement.py'
        spec=importlib.util.spec_from_file_location('actual_lawn_placement',path);p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
        geometry=ROOT/'output/unreal/geometry';scene=json.loads((geometry/'scene.json').read_text())
        contract=p.verify_inputs(scene,geometry);plan=contract['plan']
        self.assertEqual(tuple(p.IDS),a.IDS)
        self.assertEqual(plan['instanceCount'],sum(len(g['instances']) for g in plan['groups']))
        self.assertEqual({g['id'] for g in plan['groups']},{'LAWN_'+i for i in a.IDS})
        self.assertEqual((plan['cullStartCm'],plan['cullEndCm']),(600,1200))


if __name__=='__main__':unittest.main(verbosity=2)
