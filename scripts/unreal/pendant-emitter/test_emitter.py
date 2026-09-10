"""CPU contracts only: these tests do not simulate native UObject success."""
import ast
import copy
import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def load(name, path=None):
    spec = importlib.util.spec_from_file_location(name,path or HERE/(name+".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ref = load("emitter_reference")
graph = load("emitter_material")


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = ref.ROOT/"output/unreal/geometry"
        cls.scene = json.loads((cls.directory/"scene.json").read_text())
        cls.contract = ref.verify_inputs(cls.scene,cls.directory)
        cls.triangles = ref.source_triangles(cls.directory/"dom-mm.obj")
        cls.bounds = cls.contract["record"]["boundsMm"]

    def test_actual_pinned_source_area_and_scope(self):
        self.assertEqual(self.contract["geometry"]["outwardNondegenerateTriangles"],2600)
        self.assertEqual(self.contract["geometry"]["zeroAreaPoleTriangles"],104)
        self.assertAlmostEqual(self.contract["geometry"]["surfaceAreaM2"],ref.AREA_M2,places=12)
        self.assertEqual(len(self.contract["protectedIds"]),31)
        self.assertTrue({"DOM_01306","DOM_01307","DOM_01374","DOM_01373"} <= set(self.contract["protectedIds"]))

    def test_globe_polyhedral_area_is_not_analytic_sphere(self):
        self.assertLess(ref.AREA_M2,4*math.pi*.1**2)
        self.assertAlmostEqual(1-ref.AREA_M2/(4*math.pi*.1**2),.00303874623,places=10)

    def test_caller_identity_drift_rejected(self):
        for key,value in (("sourceId","invented"),("materialSlots",["MAT_0047"]),("triangles",12)):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.scene)
                next(r for r in changed["objects"] if r["id"] == ref.ID)[key] = value
                with self.assertRaisesRegex(ValueError,"Caller scene"):
                    ref.verify_inputs(changed,self.directory)

    def test_disk_pins_reject_before_geometry_parse(self):
        with patch.object(ref,"sha",return_value="0"*64),patch.object(ref,"source_triangles",side_effect=AssertionError("should not parse")):
            with self.assertRaisesRegex(ValueError,"pin drift"):
                ref.verify_inputs(self.scene,self.directory)

    def test_area_is_independent_of_triangle_order(self):
        actual = ref.geometry_metrics(list(reversed(self.triangles)),self.bounds)
        self.assertAlmostEqual(actual["surfaceAreaM2"],ref.AREA_M2,places=12)

    def test_inward_face_rejected(self):
        t = copy.deepcopy(self.triangles)
        index = next(i for i,p in enumerate(t) if len(set(p)) == 3 and p[0][2] != self.bounds["max"][2])
        t[index] = tuple(reversed(t[index]))
        with self.assertRaisesRegex(ValueError,"not outward"):
            ref.geometry_metrics(t,self.bounds)

    def test_open_surface_and_double_surface_rejected(self):
        t = [p for p in self.triangles if len(set(p)) == 3]
        for changed in (t[1:],t+t):
            with self.assertRaisesRegex(ValueError,"not closed|Duplicated"):
                ref.geometry_metrics(changed,self.bounds)

    def test_nonfinite_and_outside_vertices_rejected(self):
        for value in (float("nan"),self.bounds["max"][0]+.01):
            t = copy.deepcopy(self.triangles)
            t[0] = ((value,t[0][0][1],t[0][0][2]),t[0][1],t[0][2])
            with self.assertRaisesRegex(ValueError,"Nonfinite|escaped"):
                ref.geometry_metrics(t,self.bounds)

    def test_flux_reconstruction_and_no_srgb_or_channel_clamp(self):
        p = self.contract["photometry"]
        self.assertAlmostEqual(ref.dot(p["colorNormalizedToY1"],ref.Y_WEIGHTS),1,places=15)
        self.assertAlmostEqual(p["reconstructedFluxLumens"],800,places=10)
        self.assertAlmostEqual(p["luminanceCdPerM2"],2032.6002291329164,places=9)
        self.assertGreater(p["emissionRGB"][0],3900)
        self.assertGreater(p["colorNormalizedToY1"][0],1)

    def test_equal_flux_larger_area_reduces_luminance(self):
        a = ref.photometry(ref.AREA_M2)
        b = ref.photometry(ref.AREA_M2*2)
        self.assertAlmostEqual(b["luminanceCdPerM2"]*2,a["luminanceCdPerM2"],places=10)
        self.assertAlmostEqual(b["reconstructedFluxLumens"],800,places=10)

    def test_invalid_power_area_and_cct(self):
        for a,f,t in ((0,800,2700),(-1,800,2700),(1,-1,2700),(math.nan,800,2700),(1,math.inf,2700),(1,800,999),(1,800,math.nan)):
            with self.assertRaises(ValueError):
                ref.photometry(a,f,t)
        self.assertEqual(ref.photometry(ref.AREA_M2,0)["emissionRGB"],[0,0,0])

    def test_bt709_actual_coordinates_required(self):
        ref.verify_working_space(1,ref.CHROMATICITIES)
        for choice,coords in ((2,ref.CHROMATICITIES),(7,ref.CHROMATICITIES),(1,{k:(0,0) for k in ref.CHROMATICITIES}),(1,{})):
            with self.assertRaises(ValueError):
                ref.verify_working_space(choice,coords)

    def test_only_one_component_material_and_flag_may_change(self):
        before = {ref.ID:{"overrides":[],"emissiveLightSource":False,"meshMaterial":"/Source","effectiveMaterial":"/Source","collision":"none","uvChannels":1},
                  "DOM_01306":{"overrides":[],"effectiveMaterial":"/Source","emissiveLightSource":False}}
        original = copy.deepcopy(before)
        path = "/Game/Brezi/MaterialStudies/PendantEmitter/V_x/M.M"
        after = ref.expected_components(before,path)
        self.assertEqual(before,original)
        self.assertEqual(after["DOM_01306"],before["DOM_01306"])
        self.assertEqual(after[ref.ID]["collision"],"none")
        self.assertEqual(after[ref.ID]["uvChannels"],1)
        self.assertTrue(after[ref.ID]["emissiveLightSource"])
        for changed in ("/Foreign/M.M",None):
            with self.assertRaises(ValueError):
                ref.expected_components(before,changed)

    def test_reversal_preserves_empty_null_existing_overrides_and_true_flag(self):
        before = {ref.ID:{"meshMaterial":"/Source","effectiveMaterial":"/Candidate","overrides":["/Candidate"],"emissiveLightSource":True}}
        for values in ([],[None],["/Previous/Material.Material"]):
            for flag in (True,False):
                prior = {"overrides":values,"emissiveLightSource":flag}
                result = ref.expected_components(before,restored=prior)[ref.ID]
                self.assertEqual(result["overrides"],values)
                self.assertEqual(result["emissiveLightSource"],flag)
                self.assertEqual(result["effectiveMaterial"],values[0] if values and values[0] else "/Source")

    def test_malformed_retained_state_rejected(self):
        for prior in ({},{"overrides":[],"emissiveLightSource":1},{"overrides":["relative"],"emissiveLightSource":False},
                      {"overrides":[None,None],"emissiveLightSource":True},{"overrides":[],"emissiveLightSource":False,"extra":True}):
            with self.assertRaises(ValueError):
                ref.validate_prior(prior)

    def test_native_float_tolerance_is_hdr_relative_not_clamped(self):
        graph.close([3930.23779296875],[3930.23791603587],"HDR float32")
        for actual in ([1],[3929],[math.nan],[math.inf]):
            with self.assertRaises(RuntimeError):
                graph.close(actual,[3930.23791603587],"bad emission")

    def test_output_only_entrypoints_refuse_before_unreal_import(self):
        # Portable even after adoption: use a real nonproduction copy inside output.
        with tempfile.TemporaryDirectory(dir=ref.ROOT/"output/unreal",prefix="pendant-guard-") as directory:
            path = Path(directory)/"pendant_emitter.py"
            path.write_bytes((HERE/"pendant_emitter.py").read_bytes())
            module = load("guarded_pendant",path)
            for function in (module.apply_pendant_emitter,module.restore_pendant_emitter):
                with self.assertRaisesRegex(RuntimeError,"Output-only pendant"):
                    function({},self.directory)

    def test_graph_has_no_shader_time_light_or_geometry_authoring(self):
        tree = ast.parse((HERE/"emitter_material.py").read_text())
        names = {n.attr for n in ast.walk(tree) if isinstance(n,ast.Attribute)}
        forbidden = {"MaterialExpressionCustom","MaterialExpressionTime","MaterialExpressionTextureSample","spawn_actor_from_class","set_static_mesh","set_editor_world","execute_console_command"}
        self.assertFalse(names & forbidden)
        self.assertEqual(set(graph.OUTPUTS),{"BASE_COLOR","ROUGHNESS","METALLIC","SPECULAR","EMISSIVE_COLOR"})


if __name__ == "__main__":
    unittest.main()
