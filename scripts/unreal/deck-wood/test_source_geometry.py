"""CPU source/mocked-public-API tests only; no Unreal import, asset write or native proof."""
import copy
import importlib.util
import math
from pathlib import Path
import struct
from types import SimpleNamespace as S
import unittest

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('deck_source_geometry',HERE/'source_geometry.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
SOURCE=g.read_source(ROOT/'output/unreal/geometry/dom-mm.obj')
f32=lambda x:struct.unpack('<f',struct.pack('<f',x))[0]


def rows(object_id,source=SOURCE):
    out=[]
    for index,t in enumerate(source[object_id]['triangles']):
        out.append([{'id':100+(index*3+j)*2,'p':(f32(p[0]/10),f32(-p[1]/10),f32(p[2]/10)),
                     'uv0':tuple(f32(x) for x in t['nativeUv0'][j])} for j,p in enumerate(t['p'])])
    return out


class Description:
    def __init__(self,data): self.data=data;self.byid={x['id']:x for r in data for x in r}
    def get_triangle_count(self):return len(self.data)
    def is_triangle_valid(self,i):return 0<=i.id_value<len(self.data)
    def get_triangle_vertex_instance(self,i,c):return S(id_value=self.data[i.id_value][c]['id'])
    def is_vertex_instance_valid(self,i):return i.id_value in self.byid
    def get_vertex_instance_vertex(self,i):return i
    def is_vertex_valid(self,i):return i.id_value in self.byid
    def get_vertex_position(self,i):return S(**dict(zip(('x','y','z'),self.byid[i.id_value]['p'])))
    def get_vertex_instance_uv(self,i,channel):
        assert channel==0
        return S(**dict(zip(('x','y'),self.byid[i.id_value]['uv0'])))
    def get_vertex_instance_count(self):return len(self.byid)


def api_plan(object_id,desc):return g.read_and_plan(S(TriangleID=lambda **kw:S(**kw)),S(get_static_mesh_description=lambda lod:desc),object_id,SOURCE)


class DeckGeometry(unittest.TestCase):
    def test_exact_source_counts_and_bindings(self):
        self.assertEqual({i:(r['slot'],len(r['boards']),len(r['triangles'])) for i,r in SOURCE.items()},
                         {i:(slot,n,12*n) for i,(slot,n) in g.TARGETS.items()})
        self.assertEqual(sum(len(r['boards']) for r in SOURCE.values()),265)
        self.assertEqual(sum(len(r['triangles']) for r in SOURCE.values()),3180)
    def test_actual_source_boxes_faces_band_budget(self):
        for i,r in SOURCE.items():
            for b in r['boards']:
                self.assertEqual(len(b['faces']),6)
                for f in b['faces']:
                    self.assertTrue(f['outwardWinding'])
                    if i!=g.HATCH:self.assertLessEqual(f['vExtentMm'],145.00001)
    def test_physical_uv_spans_on_every_face(self):
        for r in SOURCE.values():
            for b in r['boards']:
                for f in b['faces']:
                    t=[t for t in r['triangles'] if t['boardIndex']==b['index'] and t['face']==(f['axis'],f['side'])]
                    for channel,extent,period in [(0,f['uExtentMm'],1440),(1,f['vExtentMm'],1500)]:
                        values=[uv[channel]for q in t for uv in q['uv1']]
                        self.assertAlmostEqual(max(values)-min(values),extent/period,places=12)
    def test_uv1_positive_axes_match_native_uv0(self):
        for r in SOURCE.values():
            for t in r['triangles']:
                for a,b in ((0,1),(1,2),(2,0)):
                    for channel in (0,1):
                        old=t['nativeUv0'][b][channel]-t['nativeUv0'][a][channel]
                        new=t['uv1'][b][channel]-t['uv1'][a][channel]
                        self.assertEqual(old==0,new==0)
                        self.assertGreaterEqual(old*new,0)
    def test_band_and_phase_are_board_constant(self):
        for i,r in SOURCE.items():
            for b in r['boards']:
                self.assertGreaterEqual(b['uPhase'],0);self.assertLess(b['uPhase'],1)
                if i!=g.HATCH:self.assertEqual(b['vPhase'],g.BAND_STARTS[b['bandIndex']])
    def test_hatch_is_full_pattern_and_reports_native_top_axes(self):
        r=SOURCE[g.HATCH];self.assertTrue(r['mapping']['hatchSeparateFullPattern'])
        self.assertIsNone(r['boards'][0]['bandIndex'])
        top=next(f for f in r['boards'][0]['faces']if f['axis']==2 and f['side']==1)
        self.assertEqual(top['uDirectionSource'],(0.,-1.,0.));self.assertEqual(top['vDirectionSource'],(1.,0.,0.))
    def test_source_parse_is_deterministic_and_does_not_write(self):
        path=ROOT/'output/unreal/geometry/dom-mm.obj';before=path.stat()
        self.assertEqual(SOURCE,g.read_source(path));after=path.stat()
        self.assertEqual((before.st_size,before.st_mtime_ns),(after.st_size,after.st_mtime_ns))
    def test_native_mock_full_five_float32_source_coverage(self):
        for i in SOURCE:
            data=rows(i);before=copy.deepcopy(data);plan=api_plan(i,Description(data))
            self.assertEqual(data,before);self.assertEqual(plan['ids'],sorted(x['id']for r in data for x in r))
            self.assertEqual(len(plan['uv1']),len(data)*3)
            self.assertLessEqual(plan['proof']['maximumVertexErrorMm'],.002)
            self.assertFalse(plan['proof']['uvMutationPerformed']);self.assertFalse(plan['proof']['savedReloadVerified'])
    def test_touching_source_vertices_use_whole_triangle_identity(self):
        plan=api_plan('DOM_01713',Description(rows('DOM_01713')))
        self.assertEqual(plan['proof']['maximumSourceVertexCandidatesWithinTolerance'],2)
        self.assertEqual(plan['proof']['matchingPolicy'],'unique-canonical-triangle-cyclic-winding-plus-native-UV0')
    def test_indistinguishable_whole_source_triangles_are_rejected(self):
        source=copy.deepcopy(SOURCE);source[g.HATCH]['triangles'][1]=copy.deepcopy(source[g.HATCH]['triangles'][0])
        data=rows(g.HATCH)
        with self.assertRaisesRegex(RuntimeError,'multiple canonical'):g._plan_native_rows(data,len(data)*3,g.HATCH,source)
    def test_native_triangle_order_and_cyclic_corner_shift(self):
        data=rows('DOM_01708');expected=api_plan('DOM_01708',Description(data))
        reordered=[r[1:]+r[:1]for r in reversed(data)]
        actual=api_plan('DOM_01708',Description(reordered))
        self.assertEqual(expected,actual)
    def test_reversed_native_winding_rejected(self):
        data=rows(g.HATCH);data[0]=list(reversed(data[0]))
        with self.assertRaisesRegex(RuntimeError,'winding'):g._plan_native_rows(data,len(data)*3,g.HATCH,SOURCE)
    def test_duplicate_native_triangle_rejected(self):
        data=rows(g.HATCH);data[0]=copy.deepcopy(data[1])
        with self.assertRaisesRegex(RuntimeError,'multiplicity'):g._plan_native_rows(data,len(data)*3,g.HATCH,SOURCE)
    def test_position_outside_002mm_rejected(self):
        data=rows(g.HATCH);p=data[0][0]['p'];data[0][0]['p']=(p[0]+.001,p[1],p[2])
        with self.assertRaisesRegex(RuntimeError,'no source'):g._plan_native_rows(data,len(data)*3,g.HATCH,SOURCE)
    def test_uv0_unflipped_obj_v_rejected(self):
        data=rows(g.HATCH);data[0][0]['uv0']=(data[0][0]['uv0'][0],1-data[0][0]['uv0'][1])
        with self.assertRaisesRegex(RuntimeError,'UV0 differs'):g._plan_native_rows(data,len(data)*3,g.HATCH,SOURCE)
    def test_native_uv0_changed_rejected(self):
        data=rows(g.HATCH);uv=data[0][0]['uv0'];data[0][0]['uv0']=(uv[0]+.001,uv[1])
        with self.assertRaisesRegex(RuntimeError,'UV0 differs'):g._plan_native_rows(data,len(data)*3,g.HATCH,SOURCE)
    def test_shared_vertex_instance_conflicting_uv1_rejected(self):
        data=rows(g.HATCH);data[0][1]['id']=data[0][0]['id']
        with self.assertRaisesRegex(RuntimeError,'conflicting UV1'):g._plan_native_rows(data,len(data)*3-1,g.HATCH,SOURCE)
    def test_unreferenced_native_instance_rejected(self):
        data=rows(g.HATCH)
        with self.assertRaisesRegex(RuntimeError,'coverage'):g._plan_native_rows(data,len(data)*3+1,g.HATCH,SOURCE)
    def test_native_triangle_id_hole_rejected(self):
        d=Description(rows(g.HATCH));d.is_triangle_valid=lambda i:i.id_value!=1
        with self.assertRaisesRegex(RuntimeError,'holes'):api_plan(g.HATCH,d)
    def test_nonfinite_native_position_rejected(self):
        data=rows(g.HATCH);data[0][0]['p']=(math.nan,0,0)
        with self.assertRaisesRegex(RuntimeError,'Nonfinite'):g._plan_native_rows(data,len(data)*3,g.HATCH,SOURCE)
    def test_foreign_source_id_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'Unregistered'):api_plan('DOM_00001',Description(rows(g.HATCH)))
    def test_broken_box_shell_rejected(self):
        source=copy.deepcopy(SOURCE[g.HATCH]['triangles']);source[0]['p']=list(reversed(source[0]['p']))
        source[0]['nativeUv0']=list(reversed(source[0]['nativeUv0']))
        with self.assertRaisesRegex(RuntimeError,'winding'):g._boards(g.HATCH,source)
    def test_all_reversed_source_shell_rejected(self):
        source=copy.deepcopy(SOURCE[g.HATCH]['triangles'])
        for t in source:t['p'].reverse();t['nativeUv0'].reverse()
        with self.assertRaisesRegex(RuntimeError,'outward'):g._boards(g.HATCH,source)
    def test_source_face_nonaffine_uv_rejected(self):
        source=copy.deepcopy(SOURCE[g.HATCH]['triangles']);source[0]['nativeUv0'][0]=(.4321,.8765)
        with self.assertRaises(RuntimeError):g._boards(g.HATCH,source)
    def test_source_box_wrong_hatch_dimensions_rejected(self):
        source=copy.deepcopy(SOURCE[g.HATCH]['triangles'])
        for t in source:t['p']=[(x*1.1,y,z)for x,y,z in t['p']]
        with self.assertRaisesRegex(RuntimeError,'dimensions'):g._boards(g.HATCH,source)

if __name__=='__main__':unittest.main()
