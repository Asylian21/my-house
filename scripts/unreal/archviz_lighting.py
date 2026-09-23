"""Source-bound indoor luminaires for the current Unreal architectural tour.

Pure planning is importable without Unreal. The editor adapter adds only tagged
RectLight actors: it never changes source meshes, exposure, sun or sky. Flux is a
visualization lighting proposal, not measured illuminance or vendor photometry.
"""
import hashlib
import json
import math

OWNER = "scripts/unreal/archviz_lighting.py"
OWNER_TAG = "BreziArchvizInteriorLighting"
EXPECTED_DESIGN = {"variant": "C", "heatingLayout": "B", "livingLayout": "B"}
SPACING_MM = 2400
CLEARANCE_MM = 20

# Exact authored emitters, never generated DOM ordinals. Lamps below work-plane
# height are decorative reading lamps and are not room-lighting substitutes.
EMITTERS = {
    "ROOM-1-04": ["OFFICE-FITOUT-2026-08-29 · LIGHT · teplý súvislý difúzor"],
    "ROOM-1-08": ["C-GIRL-108 · LIGHT · teplý opálový difúzor"],
    "ROOM-1-09": ["C-BOY-109 · LIGHT · teplý opálový difúzor"],
    "ROOM-1-10": ["C-BEDROOM-110 · LIGHT · teplý difúzor"],
    "ROOM-1-11": ["C-BATHROOM-111 · LIGHT · zapustené kruhové svietidlo"],
    "ROOM-1-03": [f"LIVING-103-DINING · závesné svietidlo {i} · 2700 K difúzor" for i in (1, 2)],
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def finite(values):
    return all(isinstance(v, (float, int)) and not isinstance(v, bool) and math.isfinite(v) for v in values)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def inside(room, x, y, margin=0):
    return any(r["x0"] + margin <= x <= r["x1"] - margin
               and r["y0"] + margin <= y <= r["y1"] - margin for r in room["rectsMm"])


def ceiling_planes(scene):
    """Use actual exported suspension height/slope samples, not a second roof model."""
    pendant = [f for f in scene["interiorLighting"]["fixtures"] if f["kind"] == "RECT_PENDANT"]
    require(len(pendant) == 1, "One exported kitchen pendant is required for vault slope provenance")
    planes = []
    for support in pendant[0]["suspension"]:
        x, half = support["xMm"], support["mountWidthMm"] / 2
        left, right = support["ceilingLeftMm"], support["ceilingRightMm"]
        require(finite([x, half, left, right]) and half > 0, "Invalid source ceiling slope samples")
        slope = (right - left) / (2 * half)
        intercept = (left + right) / 2 - slope * x
        require(abs(slope * x + intercept - support["ceilingMm"]) <= 1, "Inconsistent source ceiling sample")
        planes.append((slope, intercept))
    require(len(planes) == 2 and planes[0][0] > 0 and planes[1][0] < 0,
            "Vault requires the two source roof slope samples")
    return planes


def ceiling_at(room, x, planes):
    if room["ceiling"] == "FLAT":
        return room["clearHeightMm"]
    require(room["ceiling"] == "VAULTED_TO_RIDGE", "Unknown source ceiling kind")
    return min(a * x + b for a, b in planes)


def room_cells(room):
    """Partition each actual clear rectangle; retain the narrow hall's full length."""
    result = []
    for rect_index, r in enumerate(room["rectsMm"]):
        nx = max(1, math.ceil((r["x1"] - r["x0"]) / SPACING_MM))
        ny = max(1, math.ceil((r["y1"] - r["y0"]) / SPACING_MM))
        for ix in range(nx):
            for iy in range(ny):
                width = (r["x1"] - r["x0"]) / nx
                depth = (r["y1"] - r["y0"]) / ny
                result.append({"x": r["x0"] + (ix + .5) * width, "y": r["y0"] + (iy + .5) * depth,
                               "areaM2": width * depth / 1e6, "widthMm": width, "depthMm": depth,
                               "id": f"r{rect_index + 1}-{ix + 1}-{iy + 1}"})
    return result


def source_bounds(obj, center):
    lo, hi = obj["boundsMm"]["min"], obj["boundsMm"]["max"]
    require(len(lo) == len(hi) == 3 and finite(lo + hi) and all(b > a for a, b in zip(lo, hi)),
            "Invalid source emitter/ceiling bounds")
    return [lo[0] + center["x"], lo[1] + center["y"], lo[2]], [hi[0] + center["x"], hi[1] + center["y"], hi[2]]


def fixture(room, id_, point, width, height, width_axis, anchor, flux=None, kelvin=3000):
    return {"id": id_, "roomId": room["id"], "positionPlanMm": point, "sourceWidthMm": width,
            "sourceHeightMm": height, "widthAxis": width_axis, "lumens": flux,
            "temperatureK": kelvin, "anchor": anchor, "dayMultiplier": 1, "nightMultiplier": 1}


def build_archviz_lighting(scene):
    require(scene.get("activeDesign") == EXPECTED_DESIGN, "Interior lights require current C/B/B")
    require(scene.get("units") == "millimetres", "Source must use millimetres")
    center = scene["sceneCenterMm"]
    require(finite([center["x"], center["y"]]), "Invalid source scene center")
    rooms = scene["interior"]["rooms"]
    require(len(rooms) == 13 and len({r["id"] for r in rooms}) == 13, "Current 13-room source inventory required")
    require({r["id"] for r in rooms} == {f"ROOM-1-{i:02}" for i in range(1, 13)} | {"ROOM-DRESSING"},
            "Unknown active room inventory")
    objects = scene["objects"]
    planes = ceiling_planes(scene)
    fixtures, room_reports = [], []
    for room in rooms:
        require(room["rectsMm"] and finite([room["clearHeightMm"]]) and 2200 <= room["clearHeightMm"] <= 3500,
                "Invalid room ceiling")
        for rect in room["rectsMm"]:
            require(finite(list(rect.values())) and rect["x1"] > rect["x0"] and rect["y1"] > rect["y0"],
                    "Invalid clear room rectangle")
        current = []
        for name in EMITTERS.get(room["id"], []):
            matching = [o for o in objects if o["sourceId"] == name and o["enabled"]]
            require(len(matching) == 1, "Missing or ambiguous authored diffuser: " + name)
            obj = matching[0]
            lo, hi = source_bounds(obj, center)
            x, y = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
            require(inside(room, x, y), "Authored diffuser moved outside its source room: " + name)
            dx, dy = hi[0] - lo[0], hi[1] - lo[1]
            current.append(fixture(room, "AV-" + room["id"] + "-emitter-" + str(len(current) + 1),
                [x, y, lo[2] - 2], max(dx, dy), min(dx, dy), "X" if dx >= dy else "Y",
                {"kind": "EXPORTED_DIFFUSER", "sourceId": name, "objectId": obj["id"], "boundsMm": obj["boundsMm"]},
                kelvin=2700 if "2700 K" in name else 3000))
        if room["id"] == "ROOM-1-03":
            for source in scene["interiorLighting"]["fixtures"]:
                light = source["light"]
                require(light["directionPlan"] == [0, 0, -1] and light["widthAxisPlan"] == [1, 0, 0],
                        "Unexpected source kitchen light orientation")
                matches = [o for o in objects if o.get("metadata", {}).get("interiorLightId") == source["id"] and o["enabled"]]
                require(len(matches) == 1, "Missing or ambiguous source kitchen light body")
                require(inside(room, *light["positionPlanMm"][:2]), "Source kitchen light is outside living room")
                current.append(fixture(room, "AV-" + source["id"], list(light["positionPlanMm"]),
                    light["sourceWidthMm"], light["sourceHeightMm"], "X",
                    {"kind": "EXPORTED_PHOTOMETRIC_FIXTURE", "sourceId": matches[0]["sourceId"],
                     "objectId": matches[0]["id"], "sourceFixtureId": source["id"], "sourceDayMultiplier": light["dayMultiplier"]},
                    flux=light["lumens"], kelvin=light["temperatureK"]))
        ceilings = [o for o in objects if o["enabled"] and o["sourceId"].startswith(room["number"] + " ")
                    and "SDK podhľad" in o["sourceId"]]
        require(ceilings, "Missing exported source ceiling: " + room["id"])
        cells = room_cells(room)
        for cell in cells:
            # Existing task lamps cannot cover circulation more than 1.8 m away.
            if any(math.hypot(f["positionPlanMm"][0] - cell["x"], f["positionPlanMm"][1] - cell["y"]) <= 1800
                   and f["positionPlanMm"][2] > 1800 for f in current):
                continue
            x, y = cell["x"], cell["y"]
            candidates = []
            for obj in ceilings:
                lo, hi = source_bounds(obj, center)
                if lo[0] - 1 <= x <= hi[0] + 1 and lo[1] - 1 <= y <= hi[1] + 1:
                    candidates.append((obj, lo, hi))
            require(candidates, "No native source ceiling above proposed luminaire: " + room["id"])
            obj, lo, hi = min(candidates, key=lambda row: row[2][2] - row[1][2])
            z = (lo[2] if room["ceiling"] == "FLAT" else ceiling_at(room, x, planes) - 40) - CLEARANCE_MM
            require(room["clearHeightMm"] - 100 <= z <= 5000, "Supplement is outside source ceiling envelope")
            width = min(500, cell["widthMm"] * .5)
            height = min(500, cell["depthMm"] * .5)
            current.append(fixture(room, "AV-" + room["id"] + "-ceiling-" + cell["id"], [x, y, z], width, height, "X",
                {"kind": "SOURCE_CEILING_SUPPLEMENT", "sourceId": obj["sourceId"], "objectId": obj["id"],
                 "boundsMm": obj["boundsMm"], "ceilingClearanceMm": CLEARANCE_MM,
                 "visibleLuminaireMeshAuthored": False, "cell": cell}))
        require(current, "Room has no actual light source: " + room["id"])
        area = sum(c["areaM2"] for c in cells)
        # Installed luminous flux per floor area is an explicit design allowance,
        # not an assertion of achieved lux. Shadowing and Metal rendering need QA.
        density = 240 if room["id"] in ("ROOM-1-01", "ROOM-1-02") else 400 if room["wetRoom"] else 350
        fixed = sum(f["lumens"] or 0 for f in current)
        proposed = [f for f in current if f["lumens"] is None]
        remaining = max(0, area * density - fixed)
        # Allocate by floor-cell ownership, so a tiny hall connector never gets
        # the same flux as an entire bedroom. Keep authored kitchen flux exact.
        weights = {f["id"]: 0.0 for f in proposed}
        for cell in cells:
            eligible = proposed or current
            nearest = min(eligible, key=lambda f: math.hypot(f["positionPlanMm"][0] - cell["x"], f["positionPlanMm"][1] - cell["y"]))
            if nearest["id"] in weights:
                weights[nearest["id"]] += cell["areaM2"]
        for f in proposed:
            f["lumens"] = round(remaining * max(weights[f["id"]], .25) / sum(max(v, .25) for v in weights.values()), 3)
        for f in current:
            x, y, z = f["positionPlanMm"]
            require(finite([x, y, z, f["lumens"], f["sourceWidthMm"], f["sourceHeightMm"]]) and 0 < f["lumens"] <= 9000,
                    "Invalid or excessive local luminaire flux")
            f.update(positionCm=[(x - center["x"]) / 10, (center["y"] - y) / 10, z / 10],
                     sourceWidthCm=f["sourceWidthMm"] / 10, sourceHeightCm=f["sourceHeightMm"] / 10,
                     direction=[0, 0, -1], attenuationRadiusCm=min(650, max(350, z / 10 + 120)),
                     castsShadows=True, intensityUnits="LUMENS", inverseExposureBlend=0)
        fixtures.extend(current)
        room_reports.append({"id": room["id"], "name": room["name"], "areaM2": area,
                             "fixtureIds": [f["id"] for f in current], "lumens": sum(f["lumens"] for f in current),
                             "proposedLumensPerM2": density, "achievedIlluminanceMeasured": False})
    require(len(fixtures) <= 48 and len({f["id"] for f in fixtures}) == len(fixtures), "Unbounded or duplicate light plan")
    result = {"schemaVersion": 1, "owner": OWNER, "activeDesign": EXPECTED_DESIGN,
              "sceneObjectSha256": digest({"objects": scene["objects"], "interior": scene["interior"], "interiorLighting": scene["interiorLighting"]}),
              "fixtures": fixtures, "rooms": room_reports,
              "policy": {"dayAndNight": "Indoor luminaires remain on in the occupied architectural tour",
                         "exteriorSunSkyExposureModified": False, "sourceGeometryModified": False,
                         "iesAvailable": False, "vendorPhotometryAvailable": False,
                         "photometry": "Authored lumens where exported; otherwise room-area visualization allowance",
                         "visualQualityVerified": False}}
    result["contractSha256"] = digest(result)
    return result


def _xyz(value):
    return [float(value.x), float(value.y), float(value.z)]


def verify_archviz_lighting(scene, actor_system):
    import unreal
    plan = build_archviz_lighting(scene)
    expected = {f["id"]: f for f in plan["fixtures"]}
    found, readback = set(), []
    for actor in actor_system.get_all_level_actors():
        tags = {str(t) for t in actor.get_editor_property("tags")}
        if OWNER_TAG not in tags:
            continue
        ids = tags & expected.keys()
        require(len(ids) == 1 and not (ids & found), "Unexpected or duplicated owned interior light")
        id_ = next(iter(ids))
        f = expected[id_]
        light = actor.get_component_by_class(unreal.RectLightComponent)
        require(light is not None, "Owned interior fixture has no rect light")
        position, direction = _xyz(actor.get_actor_location()), _xyz(actor.get_actor_forward_vector())
        width_axis = _xyz(actor.get_actor_right_vector())
        expected_width_axis = [1, 0, 0] if f["widthAxis"] == "X" else [0, 1, 0]
        require(max(abs(a-b) for a, b in zip(position, f["positionCm"])) < .01
                and max(abs(a-b) for a, b in zip(direction, f["direction"])) < 1e-5
                and abs(abs(sum(a*b for a, b in zip(width_axis, expected_width_axis)))-1) < 1e-5,
                "Interior light pose/rectangle width-axis drift")
        fields = {"intensity": f["lumens"], "source_width": f["sourceWidthCm"], "source_height": f["sourceHeightCm"],
                  "temperature": f["temperatureK"], "attenuation_radius": f["attenuationRadiusCm"],
                  "inverse_exposure_blend": 0.0, "indirect_lighting_intensity": 1.0, "volumetric_scattering_intensity": 0.0}
        actual = {k: float(light.get_editor_property(k)) for k in fields}
        require(all(abs(actual[k]-v) <= max(.001, abs(v)*1e-6) for k, v in fields.items()), "Interior light property drift")
        require(light.get_editor_property("intensity_units") == unreal.LightUnits.LUMENS
                and light.get_editor_property("mobility") == unreal.ComponentMobility.MOVABLE
                and light.get_editor_property("cast_shadows") and light.get_editor_property("use_temperature")
                and light.get_editor_property("affects_world") and light.get_editor_property("visible")
                and light.get_editor_property("ies_texture") is None, "Interior light visibility/photometry/shadow drift")
        found.add(id_)
        readback.append({"id": id_, "actor": actor.get_path_name(), "positionCm": position,
                         "direction": direction, "widthAxis": width_axis,
                         "properties": actual, "castsShadows": True, "visible": True})
    require(found == expected.keys(), "Incomplete native indoor room lighting")
    return {**plan, "status": "native-properties-verified", "fixtureCount": len(found), "roomCount": len(plan["rooms"]),
            "readback": sorted(readback, key=lambda row: row["id"])}


def apply_archviz_lighting(scene, actor_system):
    import unreal
    plan = build_archviz_lighting(scene)  # Validate every source before any actor mutation.
    require(not any(OWNER_TAG in {str(t) for t in a.get_editor_property("tags")}
                    for a in actor_system.get_all_level_actors()), "Interior lighting already installed; refuse duplicate lights")
    created = []
    try:
        for f in plan["fixtures"]:
            actor = actor_system.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*f["positionCm"]),
                unreal.Rotator(pitch=-90, yaw=-90 if f["widthAxis"] == "X" else 0, roll=0))
            require(actor is not None, "Failed to create interior rect light")
            created.append(actor)
            actor.set_actor_label(f["id"])
            actor.set_folder_path("Brezi/Lighting/Interior")
            actor.set_editor_property("tags", [unreal.Name(OWNER_TAG), unreal.Name(f["id"]), unreal.Name(f["roomId"])])
            light = actor.get_component_by_class(unreal.RectLightComponent)
            light.set_mobility(unreal.ComponentMobility.MOVABLE)
            light.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
            light.set_intensity(f["lumens"])
            light.set_source_width(f["sourceWidthCm"])
            light.set_source_height(f["sourceHeightCm"])
            light.set_attenuation_radius(f["attenuationRadiusCm"])
            for key, value in {"use_temperature": True, "temperature": f["temperatureK"], "cast_shadows": True,
                               "indirect_lighting_intensity": 1.0, "inverse_exposure_blend": 0.0,
                               "volumetric_scattering_intensity": 0.0}.items():
                light.set_editor_property(key, value)
        return verify_archviz_lighting(scene, actor_system)
    except Exception:
        for actor in reversed(created):
            actor_system.destroy_actor(actor)
        raise
