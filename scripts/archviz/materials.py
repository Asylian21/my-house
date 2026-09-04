"""Cycles shaders at metre scale; source geometry and slots remain intact."""

import math
import re
import bpy


def linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def image_node(nodes, path, color=False):
    node = nodes.new("ShaderNodeTexImage")
    node.image = bpy.data.images.load(str(path), check_existing=True)
    node.image.colorspace_settings.name = "sRGB" if color else "Non-Color"
    return node


def make_grass_material(assets):
    """Dry cutout blades; explicit shader avoids artistic library colour groups."""
    material = bpy.data.materials.new("ArchViz | Dry living grass blades")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    diffuse = image_node(
        nodes, assets / "grass_bermuda_01/textures/grass_bermuda_01_diff_1k.jpg", True
    )
    alpha = image_node(
        nodes, assets / "grass_bermuda_01/textures/grass_bermuda_01_alpha_1k.png"
    )
    tint = nodes.new("ShaderNodeMixRGB")
    tint.blend_type = "MULTIPLY"
    tint.inputs[0].default_value = 1
    tint.inputs[2].default_value = (0.70, 0.85, 0.55, 1)
    links.new(diffuse.outputs[0], tint.inputs[1])
    links.new(tint.outputs[0], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Specular IOR Level"].default_value = 0.12
    translucent = nodes.new("ShaderNodeBsdfTranslucent")
    links.new(tint.outputs[0], translucent.inputs[0])
    leaf = nodes.new("ShaderNodeMixShader")
    leaf.inputs[0].default_value = 0.15
    links.new(bsdf.outputs[0], leaf.inputs[1])
    links.new(translucent.outputs[0], leaf.inputs[2])
    cutout = nodes.new("ShaderNodeMixShader")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    links.new(alpha.outputs[0], cutout.inputs[0])
    links.new(transparent.outputs[0], cutout.inputs[1])
    links.new(leaf.outputs[0], cutout.inputs[2])
    links.new(cutout.outputs[0], nodes.get("Material Output").inputs["Surface"])
    return material


def make_hedge_material(assets):
    """A cutout leaf BSDF with conserved energy and separate twig colour."""
    material = bpy.data.materials.new("ArchViz | Living hedge leaves")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    textures = {}
    for key, ext in {
        "diff": "jpg",
        "alpha": "png",
        "mask": "png",
        "rough": "exr",
        "nor_gl": "exr",
    }.items():
        textures[key] = image_node(
            nodes, assets / f"shrub_02/textures/shrub_02_{key}_1k.{ext}", key == "diff"
        )
    tint = nodes.new("ShaderNodeMixRGB")
    tint.blend_type = "MULTIPLY"
    tint.inputs[2].default_value = (0.45, 0.85, 0.30, 1)
    links.new(textures["mask"].outputs["Color"], tint.inputs[0])
    links.new(textures["diff"].outputs["Color"], tint.inputs[1])
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Specular IOR Level"].default_value = 0.30
    links.new(tint.outputs[0], bsdf.inputs["Base Color"])
    rough = nodes.new("ShaderNodeMath")
    rough.operation = "MAXIMUM"
    rough.inputs[1].default_value = 0.55
    links.new(textures["rough"].outputs["Color"], rough.inputs[0])
    links.new(rough.outputs[0], bsdf.inputs["Roughness"])
    normal = nodes.new("ShaderNodeNormalMap")
    normal.inputs["Strength"].default_value = 0.5
    links.new(textures["nor_gl"].outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs[0], bsdf.inputs["Normal"])
    translucency = nodes.new("ShaderNodeBsdfTranslucent")
    links.new(tint.outputs[0], translucency.inputs["Color"])
    mix = nodes.new("ShaderNodeMixShader")
    weight = nodes.new("ShaderNodeMath")
    weight.operation = "MULTIPLY"
    weight.inputs[1].default_value = 0.18
    links.new(textures["mask"].outputs["Color"], weight.inputs[0])
    links.new(weight.outputs[0], mix.inputs[0])
    links.new(bsdf.outputs[0], mix.inputs[1])
    links.new(translucency.outputs[0], mix.inputs[2])
    cutout = nodes.new("ShaderNodeMixShader")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    links.new(textures["alpha"].outputs["Color"], cutout.inputs[0])
    links.new(transparent.outputs[0], cutout.inputs[1])
    links.new(mix.outputs[0], cutout.inputs[2])
    output = nodes.new("ShaderNodeOutputMaterial")
    links.new(cutout.outputs[0], output.inputs["Surface"])
    return material


def make_material(slot, source, assets, lock, root):
    mat = bpy.data.materials.new(slot + " | " + source["name"])
    mat.use_nodes = True
    mat["source_material"] = source["name"]
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    name = source["name"].lower()
    bsdf.inputs["Base Color"].default_value = (*[linear(c) for c in source["color"]], 1)
    bsdf.inputs["Roughness"].default_value = (
        source["roughness"] if source["roughness"] is not None else 0.6
    )
    bsdf.inputs["Metallic"].default_value = source["metallic"] or 0
    asset = None
    if name in (
        "real-wall",
        "real-soffit",
        "real-interior-wall",
        "real-interior-plaster",
        "real-interior-ceiling",
    ):
        asset = "white_plaster_02"
    elif name in ("real-grass", "real-grass-context", "real-terrain", "real-mulch"):
        asset = "leafy_grass"
    elif "gravel" in name or "kačírek" in name:
        asset = "gravel_floor_02"
    elif (
        name in ("real-deck", "real-timber", "real-timber-dark")
        or "larch" in name
        or name.startswith("terr-")
    ):
        asset = "hinoki_planks"
    elif name in ("real-paving", "real-paving-entry", "real-concrete"):
        asset = "concrete_pavement"
    elif name == "real-road":
        # Preserve the project's observed paved road. Asphalt remains a ready slot.
        asset = "concrete_pavement"
    elif name == "archviz-asphalt":
        asset = "asphalt_02"
    if asset:
        spec = lock["assets"][asset]
        mat["asset"] = asset
        mat["tile_size_m"] = spec["tileSizeMetres"]
        geo = nodes.new("ShaderNodeNewGeometry")
        scale = nodes.new("ShaderNodeVectorMath")
        scale.operation = "SCALE"
        scale.inputs[3].default_value = 1 / spec["tileSizeMetres"]
        links.new(geo.outputs["Position"], scale.inputs[0])
        vector = scale.outputs[0]
        cladding_size = re.search(r"larch-.*:([0-9.]+)x([0-9.]+)$", name)
        if cladding_size:
            uv = nodes.new("ShaderNodeTexCoord")
            mapping = nodes.new("ShaderNodeMapping")
            mapping.inputs["Scale"].default_value = (
                float(cladding_size[1]) / spec["tileSizeMetres"],
                float(cladding_size[2]) / spec["tileSizeMetres"],
                1,
            )
            mapping.inputs["Rotation"].default_value.z = math.pi / 2
            links.new(uv.outputs["UV"], mapping.inputs["Vector"])
            vector = mapping.outputs["Vector"]
        textures = {}
        for key in ("diffuse", "roughness", "displacement"):
            tex = image_node(
                nodes, assets / spec["maps"][key]["path"], key == "diffuse"
            )
            tex.projection = "FLAT" if cladding_size else "BOX"
            tex.projection_blend = 0.18
            links.new(vector, tex.inputs["Vector"])
            textures[key] = tex
        links.new(textures["diffuse"].outputs["Color"], bsdf.inputs["Base Color"])
        if asset == "white_plaster_02":
            # Clean mineral render retains fine aggregate, without reading as
            # abandoned concrete. Texture colour is only a subtle variation.
            mix = nodes.new("ShaderNodeMixRGB")
            mix.blend_type = "MIX"
            mix.inputs[0].default_value = 0.15
            mix.inputs[1].default_value = (0.82, 0.80, 0.75, 1)
            links.new(textures["diffuse"].outputs["Color"], mix.inputs[2])
            links.new(mix.outputs[0], bsdf.inputs["Base Color"])
        if asset == "leafy_grass":
            # Scan is woodland ground: retain fine variation while living
            # Bermuda blades and turf tones replace the leaf-litter colour.
            ramp = nodes.new("ShaderNodeValToRGB")
            ramp.color_ramp.elements[0].color = (0.026, 0.055, 0.009, 1)
            ramp.color_ramp.elements[1].color = (0.065, 0.115, 0.023, 1)
            if name == "real-mulch":
                ramp.color_ramp.elements[0].color = (0.018, 0.008, 0.003, 1)
                ramp.color_ramp.elements[1].color = (0.13, 0.065, 0.025, 1)
            links.new(textures["diffuse"].outputs["Color"], ramp.inputs[0])
            links.new(ramp.outputs[0], bsdf.inputs["Base Color"])
        links.new(textures["roughness"].outputs["Color"], bsdf.inputs["Roughness"])
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Distance"].default_value = (
            0.001 if asset == "white_plaster_02" else 0.007
        )
        bump.inputs["Strength"].default_value = 0.45
        if name == "real-mulch":
            bump.inputs["Distance"].default_value = 0.025
            bump.inputs["Strength"].default_value = 0.8
        links.new(textures["displacement"].outputs["Color"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        if asset == "leafy_grass":
            for link in list(bsdf.inputs["Roughness"].links):
                links.remove(link)
            bsdf.inputs["Roughness"].default_value = 1.0
            bsdf.inputs["Specular IOR Level"].default_value = 0.10
    elif (
        source.get("texture", "").startswith("/assets/textures/")
        if source.get("texture")
        else False
    ):
        path = root / "public" / source["texture"].lstrip("/")
        if path.exists() and "glass" not in name and "hedge" not in name:
            tex = image_node(nodes, path, True)
            links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if name in (
        "real-glass-frame",
        "real-glass-frame-wood",
        "real-fence-metal",
        "real-roof-edge",
    ):
        for link in list(bsdf.inputs["Base Color"].links):
            links.remove(link)
        # Screen approximation of powder-coated RAL 7016; coating is dielectric.
        bsdf.inputs["Base Color"].default_value = (
            *[linear(c / 255) for c in (56, 62, 66)],
            1,
        )
        bsdf.inputs["Metallic"].default_value = 0.08
        bsdf.inputs["Roughness"].default_value = 0.34
        bsdf.inputs["Coat Weight"].default_value = 0.25
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 1800
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Distance"].default_value = 0.00008
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        mat["finish"] = "RAL 7016 screen approximation, fine powder coat"
    if name == "real-roof":
        for link in list(bsdf.inputs["Base Color"].links):
            links.remove(link)
        bsdf.inputs["Base Color"].default_value = (0.032, 0.037, 0.043, 1)
        bsdf.inputs["Roughness"].default_value = 0.52
        bsdf.inputs["Metallic"].default_value = 0
        wave = nodes.new("ShaderNodeTexWave")
        wave.bands_direction = "X"
        wave.inputs["Scale"].default_value = 28
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Distance"].default_value = 0.0008
        links.new(wave.outputs["Color"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    if name in (
        "real-glass",
        "real-bathroom-shower-glass",
        "real-interior-fireplace-glass",
    ):
        bsdf.inputs["Base Color"].default_value = (0.96, 0.985, 0.975, 1)
        bsdf.inputs["Metallic"].default_value = 0
        bsdf.inputs["Transmission Weight"].default_value = 1
        bsdf.inputs["Roughness"].default_value = 0.025
        bsdf.inputs["IOR"].default_value = 1.52
    if name == "real-pool-water":
        bsdf.inputs["Base Color"].default_value = (0.98, 0.995, 1, 1)
        bsdf.inputs["Transmission Weight"].default_value = 1
        bsdf.inputs["Roughness"].default_value = 0.035
        bsdf.inputs["IOR"].default_value = 1.333
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 7
        noise.inputs["Detail"].default_value = 3
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Distance"].default_value = 0.003
        bump.inputs["Strength"].default_value = 0.3
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        absorption = nodes.new("ShaderNodeVolumeAbsorption")
        absorption.inputs["Color"].default_value = (0.36, 0.83, 0.89, 1)
        absorption.inputs["Density"].default_value = 0.13
        links.new(absorption.outputs[0], nodes.get("Material Output").inputs["Volume"])
    if "mirror" in name:
        bsdf.inputs["Metallic"].default_value = 1
        bsdf.inputs["Roughness"].default_value = 0.025
        bsdf.inputs["Base Color"].default_value = (0.93, 0.94, 0.95, 1)
    if "curtain" in name:
        bsdf.inputs["Sheen Weight"].default_value = 0.4
        bsdf.inputs["Transmission Weight"].default_value = 0.12
    if any(s in name for s in ("fabric", "boucle", "rug")):
        bsdf.inputs["Sheen Weight"].default_value = 0.35
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 650
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Distance"].default_value = 0.0005
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    if name == "real-solar":
        bsdf.inputs["Base Color"].default_value = (0.006, 0.012, 0.023, 1)
        bsdf.inputs["Roughness"].default_value = 0.23
        bsdf.inputs["Specular IOR Level"].default_value = 0.18
    if "ember" in name or "warm-light" in name or "pool-led" in name:
        temperature = nodes.new("ShaderNodeBlackbody")
        temperature.inputs[0].default_value = 1850 if "ember" in name else 2700
        links.new(temperature.outputs[0], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 9 if "ember" in name else 3
    return mat
