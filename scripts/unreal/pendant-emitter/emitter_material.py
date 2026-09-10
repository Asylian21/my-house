"""Native graph helpers for the adopted pendant candidate; no entrypoint."""
import math

OWNER = "scripts/unreal/pendant-emitter/pendant_emitter.py"
NODE_TAG = "BreziPendantNodeRole"
OUTPUTS = {"BASE_COLOR":"base", "ROUGHNESS":"roughness", "METALLIC":"metallic", "SPECULAR":"specular", "EMISSIVE_COLOR":"emission"}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def rgb(value):
    return [float(getattr(value,k)) for k in ("r","g","b")]


def close(actual, expected, label):
    require(len(actual) == len(expected) and all(math.isfinite(a) and abs(a-b) <= max(1e-7,abs(b)*2e-7) for a,b in zip(actual,expected)), "Native pendant constant differs: "+label)


def working_space_proof(u, ref):
    # URendererSettings and its enum lack generated Python wrappers in UE5.8.
    # The typed bridge reads the actual CDO; it does not initialize or infer it.
    result = u.BreziRendererSettingsAudit.read_working_color_space()
    require(result.get_editor_property("valid") is True, "Editor working-space CDO readback unavailable")
    settings_class = str(result.get_editor_property("settings_class"))
    settings_object = str(result.get_editor_property("settings_object"))
    require(settings_class == "/Script/Engine.RendererSettings"
            and settings_object == "/Script/Engine.Default__RendererSettings", "Working-space CDO identity differs")
    choice = result.get_editor_property("choice_value")
    require(type(choice) is int, "Working-space choice is not the native integer")
    coordinates = {}
    for name in ref.CHROMATICITIES:
        value = result.get_editor_property(name)
        coordinates[name] = [float(value.x),float(value.y)]
    ref.verify_working_space(choice, coordinates)
    legacy = result.get_editor_property("legacy_luminance_factors")
    require(type(legacy) is bool, "Working-space legacy luminance readback is not boolean")
    return {"choice":"EWorkingColorSpace::sRGB", "choiceValue":choice, "chromaticities":coordinates,
            "legacyLuminanceFactors":legacy, "method":"typed-editor-RendererSettings-CDO",
            "settingsClass":settings_class, "settingsObject":settings_object,
            "normalizationUsesExplicitRec709Weights":True, "settingsNativeGetters":True,
            "renderThreadWorkingUniformReadback":False}


def source_surface_proof(u, source, contract):
    """Read the original glTF MIC, not the currently overridden component."""
    lib = u.MaterialEditingLibrary
    require(isinstance(source,u.MaterialInstanceConstant), "Expected canonical glTF material instance")
    names = {str(n) for n in lib.get_scalar_parameter_names(source)}
    expected = {"MetallicFactor":0.0,"RoughnessFactor":contract["scene"]["materials"]["MAT_0046"]["roughness"],"SpecularFactor":0.0}
    require(set(expected) <= names, "Source scalar pins missing: expected "+str(sorted(expected))+", actual "+str(sorted(names)))
    values = {k:float(lib.get_material_instance_scalar_parameter_value(source,k)) for k in expected}
    for key,value in values.items():
        close([value],[expected[key]],key)
    vectors = {str(n) for n in lib.get_vector_parameter_names(source)}
    require("BaseColorFactor" in vectors, "Source BaseColorFactor parameter missing: "+str(sorted(vectors)))
    base = lib.get_material_instance_vector_parameter_value(source,"BaseColorFactor")
    close(rgb(base),contract["scene"]["materials"]["MAT_0046"]["color"],"source base")
    close([float(base.a)],[1.0],"source alpha")
    return {"sourceMaterial":source.get_path_name(),"base":rgb(base),"roughness":values["RoughnessFactor"],
            "metallic":values["MetallicFactor"],"specular":values["SpecularFactor"],"sourceParameterGetters":True}


def policy(u):
    return {"material_domain":u.MaterialDomain.MD_SURFACE, "blend_mode":u.BlendMode.BLEND_OPAQUE, "shading_model":u.MaterialShadingModel.MSM_DEFAULT_LIT,
            "two_sided":False, "tangent_space_normal":True, "use_material_attributes":False}


def constants(contract, surface):
    return {"base":surface["base"],"roughness":[surface["roughness"]],"metallic":[surface["metallic"]],
            "specular":[surface["specular"]],"emission":contract["photometry"]["emissionRGB"]}


def material_proof(u, material, contract, surface, recipe_sha):
    lib, assets = u.MaterialEditingLibrary, u.EditorAssetLibrary
    require(isinstance(material,u.Material) and assets.get_metadata_tag(material,"BreziGeneratedBy") == OWNER
            and assets.get_metadata_tag(material,"BreziPendantRecipeSha256") == recipe_sha, "Pendant material ownership/recipe differs")
    for key,value in policy(u).items():
        require(material.get_editor_property(key) == value, "Pendant material policy differs: "+key)
    require(lib.has_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE), "Pendant lost saved Nanite material usage")
    expressions = list(lib.get_material_expressions(material))
    nodes = {str(assets.get_metadata_tag(n,NODE_TAG)):n for n in expressions}
    expected = constants(contract,surface)
    require(len(nodes) == len(expressions) == 5 and set(nodes) == set(expected), "Pendant graph is not the exact five constant nodes")
    values = {}
    for role,expected_value in expected.items():
        node = nodes[role]
        cls = u.MaterialExpressionConstant3Vector if len(expected_value) == 3 else u.MaterialExpressionConstant
        require(isinstance(node,cls), "Pendant contains a nonconstant graph node: "+role)
        require(not list(lib.get_material_expression_input_names(node)), "Unexpected pendant constant input")
        actual = rgb(node.get_editor_property("constant")) if len(expected_value) == 3 else [float(node.get_editor_property("r"))]
        close(actual,expected_value,role)
        values[role] = actual
    connections = []
    for name,role in OUTPUTS.items():
        prop = getattr(u.MaterialProperty,"MP_"+name)
        require(lib.get_material_property_input_node(material,prop) == nodes[role], "Pendant output source differs: "+name)
        available = [str(n) for n in lib.get_material_expression_output_names(nodes[role])]
        channel = lib.get_material_property_input_node_output_name(material,prop)
        require(bool(available) and channel == available[0], "Pendant output channel differs: "+name)
        connections.append({"property":name,"sourceRole":role,"outputName":channel,"nativeInputNodeVerified":True})
    for name in ("WORLD_POSITION_OFFSET","OPACITY","OPACITY_MASK","NORMAL","AMBIENT_OCCLUSION","REFRACTION","SUBSURFACE_COLOR"):
        require(lib.get_material_property_input_node(material,getattr(u.MaterialProperty,"MP_"+name)) is None, "Unexpected pendant output: "+name)
    require(u.BreziRendererSettingsAudit.has_no_pixel_depth_offset_connection(material) is True,
            "Pendant pixel depth offset is connected or native readback unavailable")
    reconstructed = math.pi*contract["geometry"]["surfaceAreaM2"]*sum(v*w for v,w in zip(values["emission"],contract["photometry"]["luminanceWeightsRGB"]))
    require(abs(reconstructed-800) < .0002, "Saved float32 pendant emission does not reconstruct authored 800 lm")
    return {"asset":material.get_path_name(),"graphNodeCount":5,"connections":connections,"nativeConstants":values,
            "recipeSha256":recipe_sha,"authoredIntrinsicFluxReconstructedFromNativeConstants":reconstructed,
            "opaque":True,"defaultLit":True,"twoSided":False,"naniteUsage":True,"worldPositionOffsetConnected":False,"pixelDepthOffsetConnected":False,
            "pointLightsAdded":0,"timeDependent":False,"nativeGraphGetters":True,"renderedVerified":False}


def create_material(u, prefix, contract, surface, recipe_sha):
    lib, assets = u.MaterialEditingLibrary, u.EditorAssetLibrary
    path = prefix+"/M_Pendant800lm"
    if assets.does_asset_exist(path):
        material = assets.load_asset(path)
        material_proof(u,material,contract,surface,recipe_sha)
        return material
    material = u.AssetToolsHelpers.get_asset_tools().create_asset("M_Pendant800lm",prefix,u.Material,u.MaterialFactoryNew())
    require(material is not None, "Pendant material creation failed")
    assets.set_metadata_tag(material,"BreziGeneratedBy",OWNER)
    assets.set_metadata_tag(material,"BreziPendantRecipeSha256",recipe_sha)
    for key,value in policy(u).items():
        material.set_editor_property(key,value)
    lib.set_base_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE,True)
    nodes = {}
    for role,value in constants(contract,surface).items():
        cls = u.MaterialExpressionConstant3Vector if len(value) == 3 else u.MaterialExpressionConstant
        node = lib.create_material_expression(material,cls)
        require(node is not None,"Pendant node creation failed: "+role)
        node.set_editor_property("constant" if len(value) == 3 else "r",u.LinearColor(*value,1.0) if len(value) == 3 else value[0])
        assets.set_metadata_tag(node,NODE_TAG,role)
        nodes[role] = node
    for name,role in OUTPUTS.items():
        output_names = [str(n) for n in lib.get_material_expression_output_names(nodes[role])]
        require(len(output_names) >= 1,"Pendant constant has no reflected output: "+role)
        require(lib.connect_material_property(nodes[role],output_names[0],getattr(u.MaterialProperty,"MP_"+name)),
                "Pendant output connection failed: "+role+"."+output_names[0]+" -> "+name+"; available="+str(output_names))
    errors = list(lib.recompile_material(material))
    require(not errors,"Pendant shader compilation errors: "+str(errors))
    material_proof(u,material,contract,surface,recipe_sha)
    require(assets.save_loaded_asset(material,only_if_is_dirty=False),"Pendant material save failed")
    return material
