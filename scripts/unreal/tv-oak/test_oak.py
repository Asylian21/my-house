"""CPU geometry/mapping/provenance gates. No Unreal import, renderer or material emulation."""
import copy
import math
import unittest
from unittest.mock import patch
import oak_reference as ref
import tv_oak


class OakReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=ref.verify_inputs()

    def test_exact_three_boxes_and_excluded_oval(self):
        self.assertEqual(self.contract["selectedIds"],["DOM_01293","DOM_01296","DOM_01300"])
        self.assertEqual(self.contract["preservedWoodObjects"],155)
        self.assertNotIn("DOM_01326",ref.IDS)
        self.assertEqual(sum(len(v) for v in self.contract["boxes"].values()),36)

    def test_source_face_basis_is_orthonormal_and_right_handed(self):
        for triangles in self.contract["boxes"].values():
            for triangle in triangles:
                n=triangle["normalSite"];t,v,n=ref.basis((n[0],-n[1],n[2]))
                self.assertEqual(ref.cross(t,v),n)
                for a,b in ((t,v),(t,n),(v,n)):self.assertEqual(ref.dot(a,b),0)
                for a in (t,v,n):self.assertEqual(ref.dot(a,a),1)

    def test_every_source_edge_preserves_physical_scan_scale(self):
        for triangles in self.contract["boxes"].values():
            for triangle in triangles:
                n=triangle["normalSite"];normal=(n[0],-n[1],n[2])
                points=[(p[0]/10,-p[1]/10,p[2]/10) for p in triangle["positionsMm"]]
                uv=[ref.project(p,normal,self.contract["anchorCm"]) for p in points]
                for i,j in ((0,1),(1,2),(2,0)):
                    distance=math.dist(points[i],points[j]);uv_distance=math.dist(uv[i],uv[j])
                    self.assertAlmostEqual(uv_distance*ref.PERIOD_CM,distance,places=10)

    def test_vertical_front_grain_and_horizontal_depth_grain(self):
        for n in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0)):
            _,v,_=ref.basis(n);self.assertEqual(v,(0,0,-1))
            u0=ref.project((0,0,0),n,(0,0,0));u1=ref.project((0,0,ref.PERIOD_CM),n,(0,0,0))
            self.assertEqual(u1,(u0[0],u0[1]-1))
        for n in ((0,0,1),(0,0,-1)):self.assertEqual(ref.basis(n)[1],(-1,0,0))

    def test_flat_normal_is_exact_source_normal_on_all_faces(self):
        for n in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
            self.assertEqual(ref.projected_normal((0,0,1),n),n)

    def test_opengl_green_faces_image_up_on_each_vertical_face(self):
        # GL +Y is image up. Native flip makes Y negative along projected image-down V.
        for n in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0)):
            bumped=ref.projected_normal((0,.6,.8),n)
            self.assertGreater(bumped[2],0)
            self.assertGreater(ref.dot(bumped,n),0)
            self.assertAlmostEqual(ref.dot(bumped,bumped),1,places=12)

    def test_red_normal_lobe_follows_image_u_without_face_mirror(self):
        for n in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
            t,_,_=ref.basis(n);self.assertGreater(ref.dot(ref.projected_normal((.6,0,.8),n),t),0)

    def test_normal_strength_zero_is_flat(self):
        self.assertEqual(ref.projected_normal((.4,.3,.8),(1,0,0),0),(1,0,0))

    def test_roughness_center_preserves_authored_mean_without_clamp(self):
        rough=lambda value:.74+ref.ROUGH_AMPLITUDE*(value-ref.ROUGH_MEAN)
        self.assertEqual(rough(ref.ROUGH_MEAN),.74)
        self.assertGreater(rough(0),.67);self.assertLess(rough(1),.80)
        self.assertAlmostEqual(rough(0),.6763515003989725)
        self.assertAlmostEqual(rough(1),.7963515003989725)

    def test_palette_preserves_global_linear_mean(self):
        old=(.5160589851937696,.30194568744301303,.13243419959108355)
        scanned=(.3613597193448993,.21257769420432443,.09951454248737411)
        for a,b,gain in zip(old,scanned,ref.PALETTE):self.assertAlmostEqual(a,b*gain,places=14)

    def test_all_six_face_physical_period_is_exact(self):
        for n in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
            t,v,_=ref.basis(n)
            self.assertEqual(ref.project(tuple(x*ref.PERIOD_CM for x in t),n,(0,0,0)),(1,0))
            self.assertEqual(ref.project(tuple(x*ref.PERIOD_CM for x in v),n,(0,0,0)),(0,1))

    def test_non_axis_aligned_and_invalid_faces_fail_closed(self):
        for normal in ((1,1,0),(0,0,0),(float("nan"),0,0)):
            with self.assertRaises(ValueError):ref.basis(normal)

    def test_supplied_source_change_is_rejected(self):
        s=copy.deepcopy(self.contract["scene"])
        next(o for o in s["objects"] if o["id"]=="DOM_01293")["sourceId"]="unrelated"
        with self.assertRaisesRegex(ValueError,"Supplied scene"):ref.verify_inputs(s)

    def test_obj_hash_change_is_rejected_before_projection(self):
        real=ref.sha
        with patch.object(ref,"sha",side_effect=lambda p: "0"*64 if str(p).endswith("dom-mm.obj") else real(p)):
            with self.assertRaisesRegex(ValueError,"Pinned canonical"):ref.verify_inputs()

    def test_invalid_jpeg_does_not_pass_dimensions(self):
        for data in (b"",b"\xff\xd8",b"\xff\xd8\xff\xc0\x00\xff"):
            with self.assertRaises(ValueError):ref.jpeg_size(data)

    def test_production_shader_uses_same_basis_in_uv_and_normal(self):
        # Identity contract against an accidental separate mapping recipe, not a shader execution claim.
        codes=tv_oak.shader_codes();basis=ref.Path(__file__).with_name("oak-basis.hlsl").read_text()
        self.assertTrue(codes["uv"].startswith(basis));self.assertTrue(codes["normal"].startswith(basis))
        self.assertIn("MapNormal",codes["normal"])
        self.assertNotIn("TextureCoordinate",codes["uv"])

    def test_texture_pins_match_observed_native_api(self):
        # Actual UE 5.8 import exposed these short names. Raw C++ GetInputName
        # says Coordinates; MaterialEditingLibrary shortens it to UVs.
        native_inputs=["UVs","Tex","Apply View MipBias"]
        edges=[edge for edge in tv_oak.links() if edge[2] in ("albedo","normalMap","roughMap")]
        self.assertEqual(len(edges),3)
        for origin,output,dest,pin in edges:
            self.assertEqual((origin,output,pin),("uv","",native_inputs[0]))


if __name__=="__main__":unittest.main(verbosity=2)
