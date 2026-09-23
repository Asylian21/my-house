"""CPU checks for refresh source authority; these are not native acceptance."""
import copy
import hashlib
import json
import runpy
import subprocess
import tempfile
import unittest
from pathlib import Path

MODULE = runpy.run_path(str(Path(__file__).with_name("model-refresh-import.py")))


def source():
    return {"name": "Kitchen 2026 · prírodný dub", "color": [0.79, 0.69, 0.58],
            "roughness": 0.72, "metallic": 0, "alpha": 1,
            "emission": [0, 0, 0], "texture": "/assets/textures/kitchen/living-natural-oak-albedo.jpg"}


def scene_and_records():
    scene = {"activeDesign": {"variant": "C", "heatingLayout": "B", "livingLayout": "B"},
             "layoutId": "C-2026-09-07", "house": {"placement": {"streetSetbackMm": 3000, "eastSetbackMm": 3000}}}
    # IDs are intentionally arbitrary: source semantics must survive reordering.
    records = {id_: {"id": id_, "sourceId": name, "name": name, "enabled": True,
                     "group": group, "boundsMm": {"min": [0, 0, 0], "max": [10, 20, 30]},
                     "materialNames": ["new source finish"]}
               for id_, name, group in [("DOM_09000", "KITCHEN-RUN · new island", "Interior"),
                                        ("DOM_00003", "FRONT-07 current glazing", "Windows")]}
    return scene, records


class SourceAuthorityTests(unittest.TestCase):
    def test_cbb_is_explicit_and_independent_of_ordinal_ids(self):
        scene, records = scene_and_records()
        result = MODULE["validate_current_source"](scene, records)
        self.assertEqual(result["kitchen"][0]["id"], "DOM_09000")
        self.assertEqual(result["windows"][0]["id"], "DOM_00003")

    def test_historical_layout_id_is_insufficient(self):
        scene, records = scene_and_records()
        del scene["activeDesign"]
        with self.assertRaisesRegex(RuntimeError, "explicitly exported"):
            MODULE["validate_current_source"](scene, records)

    def test_archive_design_disabled_object_and_wrong_setback_are_rejected(self):
        for kind in ("archive", "disabled", "setback"):
            with self.subTest(kind=kind):
                scene, records = scene_and_records()
                if kind == "archive":
                    scene["activeDesign"]["livingLayout"] = "A"
                elif kind == "disabled":
                    records["DOM_00003"]["enabled"] = False
                else:
                    scene["house"]["placement"]["eastSetbackMm"] = 3077
                with self.assertRaises(RuntimeError):
                    MODULE["validate_current_source"](scene, records)


class SourceMaterialTests(unittest.TestCase):
    def test_current_oak_and_black_stone_follow_source_texture_not_old_slot(self):
        oak = source()
        stone = {**oak, "name": "Kitchen 2026 · čierny kameň", "color": [0.18, 0.19, 0.18],
                 "texture": "/assets/textures/stone-dark-albedo.jpg"}
        for item in (oak, stone):
            recipe = MODULE["material_recipe"](item)
            self.assertEqual(recipe["texture"], "public" + item["texture"])
            self.assertEqual(recipe["color"], item["color"])
            self.assertEqual(recipe["blend"], "opaque")

    def test_source_alpha_and_card_transparency_are_preserved(self):
        glass = {**source(), "name": "new glazing", "texture": None, "alpha": 0.14}
        self.assertEqual(MODULE["material_recipe"](glass)["blend"], "translucent")
        self.assertEqual(MODULE["material_recipe"](glass)["alpha"], 0.14)
        card = {**source(), "name": "plant card", "texture": "/assets/vegetation/ornamental-grass-card.png"}
        self.assertEqual(MODULE["material_recipe"](card)["blend"], "masked")

    def test_invalid_pbr_and_escaped_paths_fail_before_native_mutation(self):
        for updates in ({"alpha": 1.1}, {"roughness": float("nan")}, {"emission": [-1, 0, 0]},
                        {"texture": "/assets/../../private.png"}, {"texture": "https://example.com/a.png"}):
            with self.subTest(updates=updates):
                with self.assertRaises(RuntimeError):
                    MODULE["material_recipe"]({**copy.deepcopy(source()), **updates})

    def test_procedural_texture_is_disclosed_as_scalar_fallback(self):
        item = {**source(), "name": "real-solar", "texture": "photovoltaic-cell-grid"}
        recipe = MODULE["material_recipe"](item)
        self.assertIsNone(recipe["texture"])
        self.assertEqual(recipe["unsupportedProceduralTexture"], "photovoltaic-cell-grid")
        self.assertEqual(recipe["proceduralFallback"]["sourceSrgbHex"], "#121c25")
        self.assertLess(max(recipe["color"]), .03)

    def test_current_procedural_road_uses_explicit_dark_source_color(self):
        recipe = MODULE["material_recipe"]({**source(), "name": "real-road", "texture": "street-grey-block-paver-albedo"})
        self.assertEqual(recipe["proceduralFallback"]["sourceSrgbHex"], "#525755")
        self.assertFalse(recipe["proceduralFallback"]["fullProceduralShaderTransferred"])
        self.assertLess(max(recipe["color"]), .11)

    def test_source_uv_values_are_parsed_instead_of_pinned_to_old_constants(self):
        current = {**source(), "name": "real-grass", "texture": "/assets/textures/lawn-albedo.jpg"}
        self.assertEqual(MODULE["source_uv_transform"](current)["scale"], [12, 10])
        text = 'this.applyTexture(this.realisticMaterials.grass, "lawn-albedo", 9, 7, "lawn-normal", .4);'
        self.assertEqual(MODULE["source_uv_transform"](current, scene_text=text)["scale"], [9, 7])
        with self.assertRaisesRegex(RuntimeError, "ambiguous"):
            MODULE["source_uv_transform"](current, scene_text=text + text)

    def test_oak_metric_scale_matches_installed_babylon_texture_matrix(self):
        mapping = MODULE["source_uv_transform"](source())
        self.assertEqual(mapping["rotationRadians"], 0)
        self.assertEqual(mapping["scale"], [1 / 1.83, 1 / 1.83])
        probes = [[0, 0], [1, 0], [0.25, 0.75], [2.1, -0.8]]
        # Independent Babylon implementation, then glTF V-axis conjugation.
        script = '''import { Texture } from '@babylonjs/core/Materials/Textures/texture.js';
import { Vector3 } from '@babylonjs/core/Maths/math.vector.js';
const t = new Texture(null,null); t.uScale=t.vScale=1/1.83;
console.log(JSON.stringify(PROBES.map(([u,v])=>{const p=Vector3.TransformCoordinates(new Vector3(u,1-v,1),t.getTextureMatrix());return [p.x,1-p.y]})));'''.replace("PROBES", json.dumps(probes))
        actual = json.loads(subprocess.check_output(["node", "--input-type=module", "-e", script], cwd=MODULE["ROOT"], text=True))
        affine = MODULE["native_uv_affine"](mapping)
        for probe, expected in zip(probes, actual):
            for row, target in zip(affine, expected):
                self.assertAlmostEqual(row[0] * probe[0] + row[1] * probe[1] + row[2], target, places=6)

    def test_oak_metric_transform_rejects_stale_or_unreviewed_uv_changes(self):
        text = MODULE["source_text"]("lib/babylon-kitchen.ts")
        changes = [text.replace("1/1.83;", "1/2.0;", 1),
                   text + "\noakTexture.wAng=Math.PI/2;",
                   text + "\noakTexture.uScale=2;",
                   text + "\n(oak.albedoTexture as Texture).wAng=Math.PI/2;"]
        for changed in changes:
            with self.subTest(changed=changed[-80:]), self.assertRaisesRegex(RuntimeError, "reviewed source transform"):
                MODULE["source_uv_transform"](source(), kitchen_text=changed)
        with self.assertRaisesRegex(RuntimeError, "reviewed source transform"):
            MODULE["source_uv_transform"]({**source(), "texture": "/assets/textures/living-natural-oak-albedo.jpg"})


class MaterialRefreshProtectionTests(unittest.TestCase):
    def test_interactive_door_contract_cannot_drift_during_material_refresh(self):
        for location in ("geometry", "staged"):
            with self.subTest(location=location), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                receipt, geometry, content = self.fixture(root)
                payload = b'{"doors":"verified"}'
                receipt["doors"] = {"contractSha256": hashlib.sha256(payload).hexdigest()}
                paths = {"geometry": geometry / "doors.json", "staged": content / "Data/doors.json"}
                for path in paths.values():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(payload)
                MODULE["verify_material_refresh_receipt"](receipt, geometry, content, root)
                paths[location].write_bytes(b'{"doors":"changed"}')
                with self.assertRaisesRegex(RuntimeError, "Materials refresh input drift"):
                    MODULE["verify_material_refresh_receipt"](receipt, geometry, content, root)

    def fixture(self, root):
        geometry = root / "geometry"
        content = root / "Project/Content"
        receipt = {"status": "model-refresh-import-validated", "hiddenCollision": {}, "pipelineFiles": {},
                   "finalAssetHashes": {}, "materials": {"textures": []}}
        def write(path, value=b"verified"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
            return hashlib.sha256(value).hexdigest()
        for field, name in [("sourceManifestSha256", "scene.json"), ("sourceGlbSha256", "brezi-twin.glb"),
                            ("walkingSha256", "walking.json"), ("viewpointsSha256", "viewpoints.json")]:
            receipt[field] = write(geometry / name)
        receipt["hiddenCollision"] = {"sourceContractSha256": write(geometry / "hidden-collision.json"),
                                      "sourceGlbSha256": write(geometry / "brezi-collision-only.glb")}
        receipt["mapFileSha256"] = write(content / "Brezi/Maps/Brezi.umap")
        for name in ["Project/Content/Brezi/Geometry/source.uasset", "Project/Content/Brezi/ModelRefresh/Materials/M_MAT_1.uasset"]:
            receipt["finalAssetHashes"][name] = write(root / name)
        for name in [MODULE["OWNER"], "scripts/unreal/import_scene.py"]:
            receipt["pipelineFiles"][name] = write(root / name)
        texture = "public/assets/albedo.jpg"
        receipt["materials"]["textures"].append({"source": texture, "sha256": write(root / texture)})
        return receipt, geometry, content

    def test_only_importer_pipeline_change_is_allowed_before_material_refresh(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt, geometry, content = self.fixture(root)
            (root / MODULE["OWNER"]).write_bytes(b"new recipe")
            result = MODULE["verify_material_refresh_receipt"](receipt, geometry, content, repository=root)
            self.assertEqual(result["allowedChangedPipelineFile"], MODULE["OWNER"])
            (root / "scripts/unreal/import_scene.py").write_bytes(b"unapproved")
            with self.assertRaisesRegex(RuntimeError, "input drift"):
                MODULE["verify_material_refresh_receipt"](receipt, geometry, content, repository=root)

    def test_source_map_asset_and_texture_drift_each_abort_refresh(self):
        paths = ["geometry/scene.json", "Project/Content/Brezi/Maps/Brezi.umap",
                 "Project/Content/Brezi/Geometry/source.uasset", "public/assets/albedo.jpg"]
        for changed in paths:
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                receipt, geometry, content = self.fixture(root)
                (root / changed).write_bytes(b"changed")
                with self.assertRaisesRegex(RuntimeError, "input drift"):
                    MODULE["verify_material_refresh_receipt"](receipt, geometry, content, repository=root)

    def test_asset_receipt_cannot_target_another_project(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt, geometry, content = self.fixture(root)
            receipt["finalAssetHashes"]["Other/Content/Brezi/Mesh.uasset"] = "ignored"
            with self.assertRaisesRegex(RuntimeError, "outside"):
                MODULE["verify_material_refresh_receipt"](receipt, geometry, content, repository=root)


if __name__ == "__main__":
    unittest.main()
