"""Focused CPU geometry/provenance failure-injection tests; no UE is started."""
import copy
import importlib.util
import json
import math
import struct
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("stove_geometry_test",HERE/"generate.py")
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
editor_spec=importlib.util.spec_from_file_location("stove_editor_test",HERE.parent/"stove_visuals.py")
editor=importlib.util.module_from_spec(editor_spec); editor_spec.loader.exec_module(editor)


class StoveVisualGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory=gen.ROOT/"output/unreal/geometry"
        cls.scene,cls.records,cls.triangles,cls.center=gen.verify_source(cls.directory)
        cls.meshes,cls.transforms,cls.validation=gen.geometry(cls.triangles,cls.center)

    def source_fixture(self,mutate):
        temp=tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup); directory=Path(temp.name)
        scene=copy.deepcopy(self.scene); mutate(scene)
        (directory/"scene.json").write_text(json.dumps(scene)); (directory/"dom-mm.obj").symlink_to(self.directory/"dom-mm.obj")
        return directory

    def test_exact_seven_proxy_scope_and_preserved_glass(self):
        self.assertEqual(set(gen.GUARDS),{"DOM_00522","DOM_00525","DOM_00531","DOM_00532","DOM_00533","DOM_00534","DOM_00535"})
        self.assertEqual(set(gen.PRESERVED),{"DOM_00526"})

    def test_source_id_drift_rejected(self):
        def mutate(scene):
            next(r for r in scene["objects"] if r["id"]=="DOM_00522")["sourceId"]+=" changed"
        with self.assertRaisesRegex(ValueError,"identity changed"): gen.verify_source(self.source_fixture(mutate))

    def test_collision_authority_drift_rejected(self):
        def mutate(scene):
            next(r for r in scene["objects"] if r["id"]=="DOM_00522")["metadata"]["babylonCheckCollisions"]=False
        with self.assertRaisesRegex(ValueError,"collision changed"): gen.verify_source(self.source_fixture(mutate))

    def test_duplicate_source_actor_rejected(self):
        directory=self.source_fixture(lambda scene:scene["objects"].append(copy.deepcopy(self.records["DOM_00522"])))
        with self.assertRaisesRegex(ValueError,"duplicated"): gen.verify_source(directory)

    def test_stale_obj_sha_rejected(self):
        with self.assertRaisesRegex(ValueError,"OBJ SHA"): gen.verify_source(self.source_fixture(lambda scene:scene.update(objSha256="0"*64)))

    def test_flames_are_six_bounded_cards_without_cones(self):
        flame=next(m for m in self.meshes if m.role=="flames")
        self.assertEqual(len(flame.indices)//3,12)
        self.assertLess(self.validation[flame.name]["maximumRadiusMm"],210)
        self.assertEqual({p[2] for p in flame.positions},{520,535,690,720,825})

    def test_all_visible_details_stay_in_source_envelope(self):
        for mesh in self.meshes:
            self.assertLessEqual(self.validation[mesh.name]["maximumRadiusMm"],255.001)
        self.assertLess(self.validation["STOVEV_LOGS"]["maximumRadiusMm"],214)

    def test_protruding_flame_vertex_rejected(self):
        mesh=copy.deepcopy(next(m for m in self.meshes if m.role=="flames")); mesh.positions[0]=(270,0,700)
        with self.assertRaisesRegex(ValueError,"envelope"): gen.validate_vertices([mesh])

    def test_flame_above_chamber_rejected(self):
        mesh=copy.deepcopy(next(m for m in self.meshes if m.role=="flames")); mesh.positions[0]=(150,0,1100)
        with self.assertRaisesRegex(ValueError,"chamber"): gen.validate_vertices([mesh])

    def test_nonfinite_vertex_rejected(self):
        mesh=copy.deepcopy(self.meshes[0]); mesh.positions[0]=(math.nan,0,0)
        with self.assertRaisesRegex(ValueError,"Nonfinite"): gen.validate_vertices([mesh])

    def test_reclosed_stove_window_rejected(self):
        shell=copy.deepcopy(self.meshes[0]); shell.triangle((250,-2,600),(250,2,600),(250,0,800))
        with self.assertRaisesRegex(ValueError,"closes"): gen.validate_vertices([shell])

    def test_glb_roundtrip_and_triangle_winding(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/"stove.glb"; gen.write_glb(self.meshes,self.center,path)
            actual=gen.read_glb_positions(path,self.center)
            self.assertEqual(set(actual),{m.name for m in self.meshes})
            for mesh in self.meshes:
                self.assertEqual(len(actual[mesh.name]),len(mesh.positions))
                error=max(abs(a-b) for p,q in zip(mesh.positions,actual[mesh.name]) for a,b in zip(p,q))
                self.assertLess(error,0.002)
            raw=bytearray(path.read_bytes()); struct.pack_into("<I",raw,4,1); path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,"header"): gen.read_glb_positions(path,self.center)

    def test_log_faces_point_outward(self):
        mesh=next(m for m in self.meshes if m.role=="logs")
        # First side triangle sits at positive X on first log; its authored
        # geometric normal must face outward, not into the combustion chamber.
        self.assertGreater(mesh.normals[0][0],0.8)

    def test_generator_is_deterministic(self):
        meshes,transforms,validation=gen.geometry(self.triangles,self.center)
        self.assertEqual(transforms,self.transforms); self.assertEqual(validation,self.validation)
        for a,b in zip(meshes,self.meshes): self.assertEqual(a.positions,b.positions)

    def test_current_generated_report_passes_editor_input_validation(self):
        # Run this suite with both host Python and UE's bundled Python CLI.
        # The latter reproduces the native math.hypot summary ULP difference.
        report,path=editor.verify_inputs(self.scene,self.directory)
        self.assertEqual(report["status"],"stove-visual-geometry-validated")
        self.assertEqual(path,self.directory.parent/"stove-visuals")

    def test_derived_summary_accepts_binary64_ulp_rounding(self):
        expected=copy.deepcopy(self.validation)
        expected["STOVEV_CHAMBER"]["maximumRadiusMm"]=math.nextafter(expected["STOVEV_CHAMBER"]["maximumRadiusMm"],math.inf)
        difference=editor.validate_summary(self.validation,expected)
        self.assertGreater(difference,0); self.assertLess(difference,1e-12)

    def test_derived_summary_rejects_meaningful_drift(self):
        expected=copy.deepcopy(self.validation); expected["STOVEV_LOGS"]["maximumRadiusMm"]+=1e-8
        with self.assertRaisesRegex(RuntimeError,"differs by"): editor.validate_summary(self.validation,expected)

    def test_derived_summary_count_and_nonfinite_stay_strict(self):
        expected=copy.deepcopy(self.validation); expected["STOVEV_FLAMES"]["triangles"]+=1
        with self.assertRaisesRegex(RuntimeError,"triangle count"): editor.validate_summary(self.validation,expected)
        expected=copy.deepcopy(self.validation); expected["STOVEV_LOGS"]["maximumRadiusMm"]=math.nan
        with self.assertRaisesRegex(RuntimeError,"Nonfinite"): editor.validate_summary(self.validation,expected)


if __name__=="__main__": unittest.main(verbosity=2)
