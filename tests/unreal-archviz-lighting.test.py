import copy
import importlib.util
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("archviz_lighting", ROOT / "scripts/unreal/archviz_lighting.py")
lighting = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lighting)


def scene_fixture():
    scene = {"units": "millimetres", "activeDesign": dict(lighting.EXPECTED_DESIGN),
             "sceneCenterMm": {"x": 1500, "y": -2500}, "objects": [], "interior": {"rooms": []},
             "interiorLighting": {"fixtures": []}}

    def obj(name, bounds, **metadata):
        lo, hi = bounds
        center = scene["sceneCenterMm"]
        result = {"id": f"DOM_{len(scene['objects']):05}", "sourceId": name, "enabled": True, "metadata": metadata,
                  "boundsMm": {"min": [lo[0]-center["x"], lo[1]-center["y"], lo[2]],
                               "max": [hi[0]-center["x"], hi[1]-center["y"], hi[2]]}}
        scene["objects"].append(result)
        return result

    for i in range(1, 14):
        id_ = f"ROOM-1-{i:02}" if i < 13 else "ROOM-DRESSING"
        x, y = i * 10000, 0
        room = {"id": id_, "number": f"1.{i:02}", "name": id_, "clearHeightMm": 2600,
                "ceiling": "VAULTED_TO_RIDGE" if i == 3 else "FLAT", "wetRoom": i in (5, 6, 7, 11),
                "rectsMm": [{"x0": x, "y0": y, "x1": x+4000, "y1": y+3000}]}
        if i == 2:
            room["rectsMm"][0].update(x1=x+11000, y1=y+1100)
        scene["interior"]["rooms"].append(room)
        obj(room["number"] + " " + room["name"] + " · SDK podhľad",
            ([x, y, 2600], [room["rectsMm"][0]["x1"], room["rectsMm"][0]["y1"], 4700 if i == 3 else 2630]))
        for j, name in enumerate(lighting.EMITTERS.get(id_, [])):
            obj(name, ([x+700+j*1500, y+1100, 2490], [x+1200+j*1500, y+1150, 2520]))
    for id_, kind, x, z, flux in [("INT-KITCHEN-TASK-01", "RECT_UNDERCABINET", 30800, 1600, 590),
                                  ("INT-KITCHEN-ISLAND-01", "RECT_PENDANT", 32300, 2200, 1800)]:
        obj(id_, ([x-500, 2000, z], [x+500, 2020, z+20]), interiorLightId=id_)
        source = {"id": id_, "kind": kind, "light": {"positionPlanMm": [x, 2010, z-2],
                  "sourceWidthMm": 1000, "sourceHeightMm": 12, "directionPlan": [0, 0, -1],
                  "widthAxisPlan": [1, 0, 0], "lumens": flux, "temperatureK": 3000, "dayMultiplier": 0}}
        if kind == "RECT_PENDANT":
            source["suspension"] = [
                {"xMm": 31000, "mountWidthMm": 30, "ceilingLeftMm": 3985, "ceilingRightMm": 4015, "ceilingMm": 4000},
                {"xMm": 33000, "mountWidthMm": 30, "ceilingLeftMm": 4015, "ceilingRightMm": 3985, "ceilingMm": 4000}]
        scene["interiorLighting"]["fixtures"].append(source)
    return scene


class SourcePlanTests(unittest.TestCase):
    def setUp(self):
        self.scene = scene_fixture()

    def test_every_room_has_actual_shadowed_downward_lights_without_changing_scene(self):
        before = copy.deepcopy(self.scene)
        plan = lighting.build_archviz_lighting(self.scene)
        self.assertEqual(self.scene, before)
        self.assertEqual(len(plan["rooms"]), 13)
        self.assertLessEqual(len(plan["fixtures"]), 48)
        for fixture in plan["fixtures"]:
            room = next(r for r in self.scene["interior"]["rooms"] if r["id"] == fixture["roomId"])
            self.assertTrue(lighting.inside(room, *fixture["positionPlanMm"][:2]))
            self.assertEqual(fixture["direction"], [0, 0, -1])
            self.assertTrue(fixture["castsShadows"])
            self.assertEqual(fixture["intensityUnits"], "LUMENS")
            self.assertEqual(fixture["inverseExposureBlend"], 0)
            self.assertEqual((fixture["dayMultiplier"], fixture["nightMultiplier"]), (1, 1))
            self.assertGreater(fixture["lumens"], 0)
        self.assertFalse(plan["policy"]["exteriorSunSkyExposureModified"])
        self.assertFalse(plan["policy"]["sourceGeometryModified"])
        self.assertFalse(plan["policy"]["visualQualityVerified"])

    def test_long_narrow_hall_has_distributed_coverage_and_conserved_flux(self):
        plan = lighting.build_archviz_lighting(self.scene)
        hall = next(r for r in self.scene["interior"]["rooms"] if r["id"] == "ROOM-1-02")
        lights = [f for f in plan["fixtures"] if f["roomId"] == hall["id"]]
        self.assertGreaterEqual(len(lights), 4)
        for cell in lighting.room_cells(hall):
            self.assertLessEqual(min(math.dist([cell["x"], cell["y"]], f["positionPlanMm"][:2]) for f in lights), 1800)
        report = next(r for r in plan["rooms"] if r["id"] == hall["id"])
        self.assertAlmostEqual(report["lumens"], report["areaM2"]*240, places=2)

    def test_exact_kitchen_lumens_and_diffuser_clearance(self):
        plan = lighting.build_archviz_lighting(self.scene)
        for source in self.scene["interiorLighting"]["fixtures"]:
            f = next(f for f in plan["fixtures"] if f["id"] == "AV-" + source["id"])
            self.assertEqual(f["lumens"], source["light"]["lumens"])
            self.assertEqual(f["positionPlanMm"], source["light"]["positionPlanMm"])
        for f in plan["fixtures"]:
            if f["anchor"]["kind"] == "EXPORTED_DIFFUSER":
                self.assertEqual(f["positionPlanMm"][2], f["anchor"]["boundsMm"]["min"][2]-2)

    def test_scene_offset_and_unreal_y_handedness(self):
        f = lighting.build_archviz_lighting(self.scene)["fixtures"][0]
        x, y, z = f["positionPlanMm"]
        self.assertEqual(f["positionCm"], [(x-1500)/10, (-2500-y)/10, z/10])

    def test_flat_supplements_are_below_actual_ceiling_and_vault_uses_source_slopes(self):
        plan = lighting.build_archviz_lighting(self.scene)
        for f in plan["fixtures"]:
            if f["anchor"]["kind"] == "SOURCE_CEILING_SUPPLEMENT":
                if f["roomId"] != "ROOM-1-03":
                    self.assertEqual(f["positionPlanMm"][2], f["anchor"]["boundsMm"]["min"][2]-20)
        room = self.scene["interior"]["rooms"][2]
        planes = lighting.ceiling_planes(self.scene)
        self.assertEqual(lighting.ceiling_at(room, 32000, planes), 5000)
        self.assertEqual(lighting.ceiling_at(room, 30500, planes), 3500)
        self.assertEqual(lighting.ceiling_at(room, 33500, planes), 3500)

    def test_reordered_dom_objects_do_not_change_photometry_or_positions(self):
        a = lighting.build_archviz_lighting(self.scene)
        self.scene["objects"].reverse()
        for i, obj in enumerate(self.scene["objects"]):
            obj["id"] = f"DOM_{i+70000}"
        b = lighting.build_archviz_lighting(self.scene)
        fields = ["id", "positionCm", "lumens", "sourceWidthCm", "sourceHeightCm"]
        self.assertEqual([{k:f[k] for k in fields} for f in a["fixtures"]], [{k:f[k] for k in fields} for f in b["fixtures"]])

    def test_wrong_design_missing_room_missing_ceiling_ambiguous_diffuser_fail(self):
        mutations = [lambda s: s["activeDesign"].update(livingLayout="A"),
                     lambda s: s["interior"]["rooms"].pop(),
                     lambda s: s["objects"].pop(0),
                     lambda s: s["objects"].append(copy.deepcopy(next(o for o in s["objects"] if "teplý súvislý" in o["sourceId"])))]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                scene = copy.deepcopy(self.scene)
                mutate(scene)
                with self.assertRaises(RuntimeError):
                    lighting.build_archviz_lighting(scene)

    def test_moved_emitter_and_corrupt_slope_fail(self):
        obj = next(o for o in self.scene["objects"] if "teplý súvislý" in o["sourceId"])
        obj["boundsMm"]["min"][0] += 20000
        obj["boundsMm"]["max"][0] += 20000
        with self.assertRaisesRegex(RuntimeError, "outside its source room"):
            lighting.build_archviz_lighting(self.scene)
        scene = scene_fixture()
        scene["interiorLighting"]["fixtures"][1]["suspension"][0]["ceilingMm"] += 50
        with self.assertRaisesRegex(RuntimeError, "Inconsistent source ceiling"):
            lighting.build_archviz_lighting(scene)

    def test_current_captured_source_has_thirteen_room_coverage(self):
        path = ROOT / "output/unreal/walk-game-20260922/geometry/scene.json"
        if not path.exists():
            self.skipTest("Local current-model baseline is unavailable; synthetic contract tests still run")
        plan = lighting.build_archviz_lighting(json.loads(path.read_text()))
        self.assertEqual(len(plan["rooms"]), 13)
        self.assertEqual(len(plan["fixtures"]), 40)
        self.assertTrue(all(len(room["fixtureIds"]) > 0 for room in plan["rooms"]))


if __name__ == "__main__":
    unittest.main()
