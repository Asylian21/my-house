"""CPU source/analytic checks. No Unreal mock is treated as native evidence."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
def load(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
f=load('facade_wood');s=load('shading')


class FacadeTests(unittest.TestCase):
    def test_saved_values_across_node_json_rewrite(self):
        self.assertTrue(f.same_saved_values({'uvError':0.0,'size':(4096,4096)},
                                          {'uvError':0,'size':[4096,4096]}))
        self.assertFalse(f.same_saved_values({'uvError':0.0},{'uvError':1e-12}))
        self.assertFalse(f.same_saved_values({'size':[4096,4096]},{'size':[2048,4096]}))
        with self.assertRaises(ValueError):f.same_saved_values({'value':float('nan')},{'value':0})

    @classmethod
    def setUpClass(cls):
        cls.geometry=f.ROOT/'output/unreal/geometry'
        cls.scene=json.loads((cls.geometry/'scene.json').read_text())
        cls.contract=f.verify_inputs(cls.scene,cls.geometry)
        cls.source=f.read_source(cls.geometry/'dom-mm.obj',cls.contract)

    @staticmethod
    def snapshot(tris):
        return {'rows':[[{'instance':3*i+j,'vertex':3*i+j,'pCm':[p[0]/10,-p[1]/10,p[2]/10],
                          'uv0':list(uv)} for j,(p,uv) in enumerate(tri)] for i,tri in enumerate(tris)],
                'vertexCount':len(tris)*3,'instanceCount':len(tris)*3,'renderTriangles':len(tris),'renderSections':1}

    def test_exact_scope(self):
        self.assertEqual(len(f.SLOTS),12);self.assertEqual(len(set(f.SLOTS.values())),10)
        self.assertNotIn('DOM_01876',f.SLOTS);self.assertNotIn('MAT_0111',f.SLOTS.values())
        self.assertEqual(sum(len(v) for v in self.source.values()),204)

    def test_complete_canonical_triangles(self):
        for id_,tris in self.source.items():
            p=f.source_proof(self.snapshot(tris),tris,id_)
            self.assertLess(p['maximumPositionErrorMm'],1e-8)
            self.assertTrue(p['windingAndMultiplicityVerified'])

    def test_cyclic_winding_accepted(self):
        id_='DOM_00158';tris=self.source[id_];snapshot=self.snapshot(tris)
        snapshot['rows']=[r[1:]+r[:1] for r in snapshot['rows']]
        f.source_proof(snapshot,tris,id_)

    def test_reversed_winding_rejected(self):
        id_='DOM_00158';tris=self.source[id_];snap=self.snapshot(tris)
        snap['rows'][0].reverse()
        with self.assertRaisesRegex(RuntimeError,'absent/ambiguous/reversed'):f.source_proof(snap,tris,id_)

    def test_outside_position_bound(self):
        id_='DOM_00158';tris=self.source[id_];snap=self.snapshot(tris)
        snap['rows'][0][0]['pCm'][0]+=.0003
        with self.assertRaises(RuntimeError):f.source_proof(snap,tris,id_)

    def test_uv0_change_rejected(self):
        id_='DOM_00158';tris=self.source[id_];snap=self.snapshot(tris)
        snap['rows'][0][0]['uv0'][1]+=.00001
        with self.assertRaises(RuntimeError):f.source_proof(snap,tris,id_)

    def test_triangle_multiplicity_rejected(self):
        id_='DOM_00158';tris=self.source[id_];snap=self.snapshot(tris)
        snap['rows'][-1]=copy.deepcopy(snap['rows'][0])
        with self.assertRaises(RuntimeError):f.source_proof(snap,tris,id_)

    def test_foreign_geometry_rejected(self):
        with self.assertRaises(RuntimeError):
            f.source_proof(self.snapshot(self.source['DOM_00157']),self.source['DOM_00158'],'DOM_00158')

    def test_supplied_scene_mutation_rejected(self):
        scene=copy.deepcopy(self.scene);scene['objects'][0]['name']='foreign'
        with self.assertRaisesRegex(RuntimeError,'supplied scene'):f.verify_inputs(scene,self.geometry)

    def test_common_gable_field(self):
        ref=self.contract['reference'];self.assertEqual(ref['anchorCm'],[0,0,0])
        self.assertEqual({f.SLOTS[i] for i in ['DOM_00061','DOM_00062','DOM_00063']},{'MAT_0011'})
        self.assertEqual(ref['grainNativeBySlot']['MAT_0011'],[0,0,1])
        a=s.board_uv(400,735);b=s.board_uv(400,735)
        self.assertEqual(a,b)

    def test_walls_vertical_and_cheek_intent(self):
        for slot,grain in self.contract['reference']['grainNativeBySlot'].items():
            if slot not in ('MAT_0023','MAT_0024'):self.assertEqual(grain,[0,0,1])
        audit=json.loads((f.ROOT/'output/unreal/facade-wood-study/source-audit.json').read_text())
        groups=audit['objects']['DOM_00157']['planarOrientationGroups'][:2]
        self.assertTrue(all(abs(g['vDirectionsNative'][0][1])>.99 for g in groups))

    def test_roof_grain_parallel_source(self):
        ref=self.contract['reference']
        for slot,n in [('MAT_0023',(.5710988547,0,-.8208812936)),('MAT_0024',(-.5710988548,0,-.8208812935))]:
            g=ref['grainNativeBySlot'][slot];N,T,B=s.basis(n,g)
            self.assertGreater(sum(x*y for x,y in zip(T,g)),.999999)
            self.assertLess(abs(sum(x*y for x,y in zip(N,T))),1e-12)
            self.assertAlmostEqual(abs(B[1]),1)

    def test_basis_right_handed_and_end_fallback(self):
        for normal in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),(1e-7,0,1)]:
            n,t,b=s.basis(normal,(0,0,1))
            for v in (n,t,b):self.assertAlmostEqual(sum(x*x for x in v),1)
            for a,c in [(n,t),(n,b),(t,b)]:self.assertAlmostEqual(sum(x*y for x,y in zip(a,c)),0)
            cross=(t[1]*b[2]-t[2]*b[1],t[2]*b[0]-t[0]*b[2],t[0]*b[1]-t[1]*b[0])
            for x,y in zip(cross,n):self.assertAlmostEqual(x,y)

    def test_all_actual_face_bases_finite(self):
        audit=json.loads((f.ROOT/'output/unreal/facade-wood-study/source-audit.json').read_text())
        for id_,obj in audit['objects'].items():
            g=self.contract['reference']['grainNativeBySlot'][f.SLOTS[id_]]
            for face in obj['sourceFaces']:
                n=face['windingNormalSource']; n=(n[0],-n[1],n[2])
                vectors=s.basis(n,g)
                self.assertTrue(all(math.isfinite(v) for vector in vectors for v in vector))

    def test_photo_full_period_and_derivative(self):
        for cross in [-22.3,2.7,37.1]:
            u0=s.board_uv(123.4,cross);u1=s.board_uv(312.4,cross)
            self.assertAlmostEqual(u1[0]-u0[0],1);self.assertEqual(u1[1],u0[1])
            dv=(s.board_uv(123.4,cross+.01)[1]-u0[1])/.01
            self.assertAlmostEqual(dv,1/189)

    def test_bands_avoid_original_seams(self):
        proof=json.loads((f.ROOT/'output/unreal/facade-wood-study/photo-strip-audit.json').read_text())
        self.assertEqual([v['v'][0] for v in proof['selectedBands']],list(s.BANDS))
        for row in proof['selectedBands']:
            self.assertGreater(row['minimumMainSeamGutterPixels'],88)
            self.assertAlmostEqual(row['v'][1]-row['v'][0],5/189,places=8)

    def test_hash_negative_boards_stable_with_all_bands(self):
        values=[s.board_uv(0,i*5+.001) for i in range(-100,101)]
        used={min(range(8),key=lambda j:abs(v[1]-s.BANDS[j])) for v in values}
        self.assertEqual(used,set(range(8)))
        self.assertEqual(values,[s.board_uv(0,i*5+.001) for i in range(-100,101)])
        self.assertTrue(all(0<=u<1 and 0<=v<1 for u,v in values))

    def test_joint_exact_center_and_board_middle(self):
        for x in [-50,0,15,500]:
            self.assertAlmostEqual(s.joint_shade(x,1e-5),.42,places=7)
            self.assertEqual(s.joint_shade(x+2.5,1e-5),1)

    def test_joint_far_field_energy_mean(self):
        expected=1-(1-.42)*(.1953125/5)
        for footprint in [1,2,10,101]:
            for x in [-500.123,-.5,0,19.75]:self.assertAlmostEqual(s.joint_shade(x,footprint),expected,places=10)

    def test_joint_soft_continuous_and_bounded(self):
        a=[s.joint_shade(i*.0005,.1) for i in range(-1000,1000)]
        self.assertTrue(all(.42<=v<=1 for v in a))
        self.assertLess(max(abs(x-y) for x,y in zip(a,a[1:])),.002)

    def test_graph_no_discontinuous_texture_derivatives(self):
        for key in ['gradientX','gradientY']:
            for forbidden in ['floor(','frac(','bands[','phase','MapNormal']:self.assertNotIn(forbidden,s.CODES[key])
            self.assertIn('Q / 189.0',s.CODES[key])
        self.assertEqual(sum(1 for _,_,_,pin in f.graph_links() if pin in ['DDX(UVs)','DDY(UVs)']),6)

    def test_graph_unique_source_to_target_output_queries(self):
        links=f.graph_links();pairs=[(a,c) for a,_,c,_ in links]
        self.assertEqual(len(pairs),len(set(pairs)))
        self.assertEqual(len(links),30)

    def test_raw_roughness_no_geometry_outputs(self):
        self.assertIn(('ROUGHNESS','roughMap','R'),f.OUTPUTS)
        self.assertEqual({x[0] for x in f.OUTPUTS},{'BASE_COLOR','ROUGHNESS','NORMAL','METALLIC','SPECULAR'})
        self.assertIn('* 0.35',s.CODES['normal']);self.assertNotIn('Time',str(s.CODES))

    def test_saved_json_tuple_array_normalization(self):
        native={'textures':{'albedo':{'pixels':(4096,4096)}},'grain':(0,0,1)}
        saved=json.loads(json.dumps(native))
        self.assertEqual(f.digest(native),f.digest(saved))
        saved['grain'][2]=.9
        self.assertNotEqual(f.digest(native),f.digest(saved))


if __name__=='__main__':unittest.main()
