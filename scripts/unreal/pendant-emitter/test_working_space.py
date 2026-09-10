"""CPU validation of the bridge result contract, not native C++ execution."""
import copy
import importlib.util
import math
from pathlib import Path
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE/(name+".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ref = load("emitter_reference")
graph = load("emitter_material")


class WorkingSpaceTests(unittest.TestCase):
    def setUp(self):
        self.values = {"valid":True, "choice_value":1, "legacy_luminance_factors":False,
                       "settings_class":"/Script/Engine.RendererSettings",
                       "settings_object":"/Script/Engine.Default__RendererSettings"}
        self.values.update({k:SimpleNamespace(x=v[0],y=v[1]) for k,v in ref.CHROMATICITIES.items()})
        self.reads = []

    def proof(self):
        def get(name):
            self.reads.append(name)
            return self.values[name]
        u = SimpleNamespace(BreziRendererSettingsAudit=SimpleNamespace(
            read_working_color_space=lambda:SimpleNamespace(get_editor_property=get)))
        return graph.working_space_proof(u,ref)

    def test_exact_native_value_contract_without_renderer_enum_wrapper(self):
        result = self.proof()
        self.assertEqual(result["choiceValue"],1)
        self.assertEqual(result["chromaticities"],{k:list(v) for k,v in ref.CHROMATICITIES.items()})
        self.assertEqual(result["method"],"typed-editor-RendererSettings-CDO")
        self.assertTrue(result["settingsNativeGetters"])
        self.assertFalse(result["renderThreadWorkingUniformReadback"])
        self.assertEqual(set(self.reads),set(self.values))

    def test_invalid_editor_readback_stops_before_default_zero_fields(self):
        for invalid in (False,None,0,1):
            self.values["valid"] = invalid
            self.reads.clear()
            with self.assertRaisesRegex(RuntimeError,"unavailable"):
                self.proof()
            self.assertEqual(self.reads,["valid"])

    def test_foreign_cdo_or_class_rejected(self):
        for name in ("settings_class","settings_object"):
            old=self.values[name]
            for invalid in ("",old+"_2","/Script/Engine.Default__DeveloperSettings"):
                self.values[name]=invalid
                with self.assertRaisesRegex(RuntimeError,"identity differs"):
                    self.proof()
            self.values[name]=old

    def test_bool_float_or_text_is_not_native_enum_integer(self):
        for value in (True,1.0,"1",None):
            self.values["choice_value"]=value
            with self.assertRaisesRegex(RuntimeError,"native integer"):
                self.proof()

    def test_non_bt709_native_enum_rejected_without_coordinate_inference(self):
        for value in (0,2,3,7,255):
            self.values["choice_value"]=value
            with self.assertRaises(ValueError):
                self.proof()

    def test_zero_or_shifted_or_nonfinite_native_coordinates_rejected(self):
        for value in (0,.641,math.nan,math.inf):
            self.values["red"]=SimpleNamespace(x=value,y=.33)
            with self.assertRaises(ValueError):
                self.proof()

    def test_missing_coordinate_fails_without_fabricated_default(self):
        del self.values["white"]
        with self.assertRaises(KeyError):
            self.proof()

    def test_nonboolean_legacy_readback_rejected(self):
        for value in (0,1,"False",None):
            self.values["legacy_luminance_factors"]=value
            with self.assertRaisesRegex(RuntimeError,"not boolean"):
                self.proof()

    def test_legacy_setting_recorded_but_explicit_weights_preserved(self):
        original=copy.deepcopy(ref.CHROMATICITIES)
        self.values["legacy_luminance_factors"]=True
        result=self.proof()
        self.assertTrue(result["legacyLuminanceFactors"])
        self.assertTrue(result["normalizationUsesExplicitRec709Weights"])
        self.assertEqual(ref.CHROMATICITIES,original)
        self.assertEqual(ref.Y_WEIGHTS,(.2126,.7152,.0722))


if __name__ == "__main__":
    unittest.main()
