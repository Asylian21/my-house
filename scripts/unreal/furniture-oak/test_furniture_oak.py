"""Actual canonical source/projection/exception-policy tests; no native mocks."""
import copy
import importlib.util
import math
import tempfile
import unittest
from pathlib import Path
import furniture_reference as ref
import furniture_oak


class FurnitureOakTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=ref.verify_inputs();cls.common=ref.load_tv("oak_reference");cls.writer=ref.load_tv("tv_oak")

    def test_exact_nine_objects_and_all149_other_wood_preserved(self):
        self.assertEqual(self.contract["selectedIds"],["DOM_00613","DOM_00643","DOM_00647","DOM_00650","DOM_01328","DOM_01345","DOM_01354","DOM_01363","DOM_01372"])
        self.assertEqual(sum(map(len,self.contract["boxes"].values())),108)
        self.assertEqual(self.contract["preservedWoodObjects"],149)
        self.assertFalse(ref.IDS&ref.TV_IDS)
        self.assertTrue({"DOM_01337","DOM_01344","DOM_01353","DOM_01362","DOM_01371","DOM_01326"}.isdisjoint(ref.IDS))

    def test_two_materials_share_exactly_one_pinned_texture_triplet(self):
        self.assertEqual(set(self.contract["profiles"]),{"kitchen","dining"})
        a,b=self.contract["groups"].values();self.assertEqual(a["candidate"],b["candidate"])
        self.assertEqual(len(a["candidate"]["maps"]),3)
        self.assertEqual(a["candidate"]["dimensionsMillimetres"],[ref.PERIOD_CM*10]*2)

    def test_all_source_triangle_edges_have_exact_physical_scan_scale(self):
        for name,group in self.contract["groups"].items():
            for id_ in group["selectedIds"]:
                for tri in self.contract["boxes"][id_]:
                    ns=tri["normalSite"];n=(ns[0],-ns[1],ns[2])
                    p=[(v[0]/10,-v[1]/10,v[2]/10) for v in tri["positionsMm"]]
                    uv=[ref.project(v,n,group["anchorCm"],group["grain"]) for v in p]
                    for i,j in ((0,1),(1,2),(2,0)):self.assertAlmostEqual(math.dist(uv[i],uv[j])*ref.PERIOD_CM,math.dist(p[i],p[j]),places=10,msg=name+id_)

    def test_both_tangent_bases_are_right_handed_on_six_cardinal_faces(self):
        for grain in ("verticalZ","longitudinalX"):
            for n in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
                t,v,n=ref.basis(n,grain)
                self.assertEqual(self.common.cross(t,v),n)
                self.assertEqual(self.common.dot(t,v),0)
                for axis in (t,v,n):self.assertEqual(self.common.dot(axis,axis),1)

    def test_kitchen_upright_grain_is_vertical(self):
        for n in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0)):
            self.assertEqual(ref.basis(n,"verticalZ")[1],(0,0,-1))

    def test_tabletop_and_rails_broad_faces_follow_long_x_axis(self):
        for n in ((0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
            self.assertEqual(ref.basis(n,"longitudinalX")[1],(1,0,0))
            self.assertEqual(ref.project((ref.PERIOD_CM,0,0),n,(0,0,0),"longitudinalX"),(0,1))
        for n in ((1,0,0),(-1,0,0)):self.assertEqual(ref.basis(n,"longitudinalX")[1],(0,0,-1))

    def test_flat_normal_and_single_green_flip_follow_identical_frames(self):
        for grain in ("verticalZ","longitudinalX"):
            for n in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
                t,v,n=ref.basis(n,grain)
                self.assertEqual(ref.projected_normal((0,0,1),n,grain),n)
                self.assertGreater(self.common.dot(ref.projected_normal((.6,0,.8),n,grain),t),0)
                self.assertLess(self.common.dot(ref.projected_normal((0,.6,.8),n,grain),v),0)
                self.assertGreater(self.common.dot(ref.projected_normal((0,.6,.8),n,grain),n),0)

    def test_diagonal_or_nonfinite_source_faces_fail_closed(self):
        for n in ((1,1,0),(0,0,0),(float("nan"),0,0)):
            for grain in ("verticalZ","longitudinalX"):
                with self.assertRaises(ValueError):ref.basis(n,grain)

    def test_distinct_means_are_preserved_and_roughness_does_not_clip(self):
        for name,group in self.contract["groups"].items():
            recipe=self.contract["proposal"]["materials"][group["sourceSlot"]]
            means=[.3613597193448993,.21257769420432443,.09951454248737411]
            for source,raw,gain in zip(recipe["targetLinearMean"],means,self.contract["profiles"][name]["palette"]):self.assertAlmostEqual(source,raw*gain,places=14)
            rough=lambda r:group["sourceRoughness"]+ref.ROUGH_AMPLITUDE*(r-ref.ROUGH_MEAN)
            self.assertEqual(rough(ref.ROUGH_MEAN),.55 if name=="kitchen" else .68)
            self.assertGreater(rough(0),0);self.assertLess(rough(1),1)
            self.assertLess(max(abs(x) for x in recipe["saturationMeanLoss"]),1.5e-7)
        self.assertNotEqual(self.contract["profiles"]["kitchen"]["palette"],self.contract["profiles"]["dining"]["palette"])

    def test_default_tv_shader_graph_contract_is_unchanged(self):
        spec=importlib.util.spec_from_file_location("actual_tv_oak",ref.ROOT/"scripts/unreal/tv-oak/tv_oak.py")
        original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
        self.assertEqual(self.writer.shader_codes(),original.shader_codes())
        self.assertEqual(self.writer.links(),original.links());self.assertEqual(self.writer.outputs(),original.outputs())
        self.assertEqual(self.writer.material_profile()["owner"],original.OWNER)
        self.assertEqual(self.writer.material_profile()["materialName"],"M_TVCabinetPhotoOak")

    def test_each_profile_uses_one_identical_basis_for_uv_and_normal(self):
        for profile in self.contract["profiles"].values():
            codes=self.writer.shader_codes(profile)
            self.assertTrue(codes["uv"].startswith(profile["basisCode"]))
            self.assertTrue(codes["normal"].startswith(profile["basisCode"]))
        self.assertNotEqual(self.contract["profiles"]["kitchen"]["basisCode"],self.contract["profiles"]["dining"]["basisCode"])

    def test_profile_name_cannot_escape_owned_asset_namespace(self):
        for change in ({"materialName":"../M_bad"},{"owner":"some-other-owner"},{"palette":[1,float("nan"),1]},{"basisCode":""}):
            profile=dict(self.contract["profiles"]["kitchen"]);profile.update(change)
            with self.assertRaises(RuntimeError):self.writer.material_profile(profile)

    def test_exact_exception_policy_changes_no_geometry_or_other_bindings(self):
        before={i:{"mesh":i,"effectiveMaterial":"old/"+i,"overrides":[],"triangles":12,"collision":"unchanged","uvChannels":1} for i in self.contract["woodIds"]}
        saved=copy.deepcopy(before);bindings={i:"/Game/Brezi/MaterialStudies/FurniturePhotoOak/V_test/M_test" for i in ref.IDS}
        after=ref.expected_components(before,bindings)
        self.assertEqual(before,saved)
        for id_,value in before.items():
            if id_ not in ref.IDS:self.assertEqual(after[id_],value)
            else:self.assertEqual({k:v for k,v in after[id_].items() if k not in ("effectiveMaterial","overrides")},{k:v for k,v in value.items() if k not in ("effectiveMaterial","overrides")})
        for i in ref.TV_IDS:self.assertEqual(after[i],before[i])

    def test_extra_missing_or_foreign_exception_is_rejected(self):
        before={i:{} for i in self.contract["woodIds"]};valid={i:"/Game/Brezi/MaterialStudies/FurniturePhotoOak/V_test/M_test" for i in ref.IDS}
        cases=[{**valid,"DOM_01326":"/Game/Brezi/MaterialStudies/FurniturePhotoOak/V_test/M_test"},{k:v for k,v in valid.items() if k!="DOM_01328"},{**valid,"DOM_01328":"/Game/Foreign"}]
        for bindings in cases:
            with self.assertRaises(ValueError):ref.expected_components(before,bindings)

    def test_supplied_source_record_drift_is_rejected(self):
        scene=copy.deepcopy(self.contract["scene"]);next(o for o in scene["objects"] if o["id"]=="DOM_00613")["sourceId"]="foreign"
        with self.assertRaises(ValueError):ref.verify_inputs(scene)

    def test_selected_box_parser_rejects_outward_geometry_and_foreign_slot(self):
        id_="DOM_01328";triangles=self.contract["boxes"][id_]
        def fixture(bad_vertex=False,bad_slot=False):
            lines=["o "+id_,"usemtl "+("MAT_0039" if bad_slot else ref.SLOTS[id_])];index=0
            for tri in triangles:
                refs=[]
                for p in tri["positionsMm"]:
                    point=list(p)
                    if bad_vertex and index==0:point[0]+=.01
                    lines += ["v "+" ".join(map(str,point)),"vn "+" ".join(map(str,tri["normalSite"]))]
                    index+=1;refs.append(f"{index}/1/{index}")
                lines.append("f "+" ".join(refs))
            return "\n".join(lines)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"selected.obj"
            path.write_text(fixture());self.common.read_boxes(path,self.contract["records"],{id_},{id_:ref.SLOTS[id_]})
            for bad_vertex,bad_slot in ((True,False),(False,True)):
                path.write_text(fixture(bad_vertex,bad_slot))
                with self.assertRaises(ValueError):self.common.read_boxes(path,self.contract["records"],{id_},{id_:ref.SLOTS[id_]})

    def test_output_only_import_and_restore_fail_before_unreal_import(self):
        # Exercise a real nonproduction copy even after the reviewed module has
        # been adopted. The canonical path legitimately proceeds to Unreal.
        with tempfile.TemporaryDirectory(prefix="furniture-guard-",dir=ref.ROOT/"output/unreal") as d:
            path=Path(d)/"furniture_oak.py"
            path.write_bytes(Path(furniture_oak.__file__).read_bytes())
            spec=importlib.util.spec_from_file_location("furniture_guard_copy",path)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            for fn in (module.apply_furniture_oak,module.restore_furniture_oak):
                with self.assertRaisesRegex(RuntimeError,"Output-only"):fn(None,ref.ROOT/"output/unreal/geometry")


if __name__=="__main__":unittest.main(verbosity=2)
