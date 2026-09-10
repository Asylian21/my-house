"""Three pinned cabinet component material overrides for the native import.

Called by import_scene.py after canonical material authoring, stove visuals and
a successful saved-map reload. Native execution and visual acceptance are
recorded separately; importing this module alone does not launch the engine.
"""
import hashlib
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p/"lib/twin-site.ts").is_file())
OWNER = "scripts/unreal/tv-oak/tv_oak.py"
PREFIX = "/Game/Brezi/MaterialStudies/TVPhotoOak"
REVISION = "NATIVE-TV-CABINET-PHOTO-OAK-20260908-1"
ORIGINAL = "BreziTVOakOriginalOverrides"
REVISION_TAG = "BreziTVOakRevision"
EXPECTED_ROLES = {"position", "normalWS", "anchor", "period", "uv", "albedo", "normalMap", "roughMap",
                  "palette", "albedoMultiply", "albedoBound", "baseRoughness", "roughAmplitude", "roughMean", "roughness",
                  "normalStrength", "normal", "metallic", "specular"}


def reference():
    spec = importlib.util.spec_from_file_location("brezi_tv_oak_reference", Path(__file__).with_name("oak_reference.py"))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def material_profile(profile=None):
    """Explicit profile for the same graph; omitted profile preserves TV defaults."""
    if profile is None:
        profile={"owner":OWNER,"materialName":"M_TVCabinetPhotoOak","palette":reference().PALETTE,
                 "basisCode":Path(__file__).with_name("oak-basis.hlsl").read_text()}
    require(set(profile)=={"owner","materialName","palette","basisCode"},"Oak profile fields differ")
    require(isinstance(profile["owner"],str) and profile["owner"].startswith("scripts/unreal/") and profile["owner"].endswith(".py"),"Oak profile owner differs")
    name=profile["materialName"]
    require(isinstance(name,str) and name.startswith("M_") and all(c.isalnum() or c=="_" for c in name),"Oak material name is unsafe")
    require(len(profile["palette"])==3 and all(math.isfinite(v) and v>0 for v in profile["palette"]),"Oak palette is invalid")
    require(isinstance(profile["basisCode"],str) and bool(profile["basisCode"].strip()),"Oak projection basis is missing")
    return dict(profile)


def shader_codes(profile=None):
    basis = material_profile(profile)["basisCode"]
    return {
        "uv": basis + "\nfloat3 P = Position - AnchorCm;\nreturn float2(dot(P,T),dot(P,V)) / PeriodCm;\n",
        "normal": basis + "\n// Normal sample is decoded BC5 after OpenGL-to-DirectX green flip.\nreturn normalize(T*MapNormal.x*Strength + V*MapNormal.y*Strength + N*max(MapNormal.z,0.001));\n",
        "roughness": "// Center the photographed variation on the authored scalar finish; not vendor calibration.\nreturn BaseRoughness + Amplitude*(MapR-RoughMean);\n",
    }


def links():
    return [("position","","uv","Position"), ("normalWS","","uv","NormalWS"), ("anchor","","uv","AnchorCm"), ("period","","uv","PeriodCm"),
            # MaterialEditingLibrary uses MaterialGraphNode's shortened names:
            # internal TextureSample Coordinates is exposed as UVs (UE 5.8).
            *(("uv","",role,"UVs") for role in ("albedo","normalMap","roughMap")),
            ("albedo","RGB","albedoMultiply","A"), ("palette","","albedoMultiply","B"), ("albedoMultiply","","albedoBound",""),
            ("roughMap","R","roughness","MapR"), ("baseRoughness","","roughness","BaseRoughness"),
            ("roughAmplitude","","roughness","Amplitude"), ("roughMean","","roughness","RoughMean"),
            ("normalMap","RGB","normal","MapNormal"), ("normalWS","","normal","NormalWS"), ("normalStrength","","normal","Strength")]


def outputs():
    return {"BASE_COLOR":"albedoBound", "ROUGHNESS":"roughness", "NORMAL":"normal", "METALLIC":"metallic", "SPECULAR":"specular"}


def texture_proof(u, texture, role, expected, owner=OWNER):
    require(isinstance(texture,u.Texture2D), "Photographed map is not Texture2D")
    compression = {"normalMap":u.TextureCompressionSettings.TC_NORMALMAP, "roughMap":u.TextureCompressionSettings.TC_MASKS,
                   "albedo":u.TextureCompressionSettings.TC_DEFAULT}[role]
    require(u.EditorAssetLibrary.get_metadata_tag(texture,"BreziGeneratedBy") == owner
            and u.EditorAssetLibrary.get_metadata_tag(texture,"source_sha256") == expected, "Photo texture ownership/source hash differs")
    require(bool(texture.get_editor_property("srgb")) is (role=="albedo")
            and texture.get_editor_property("compression_settings") == compression
            and bool(texture.get_editor_property("flip_green_channel")) is (role=="normalMap")
            and texture.get_editor_property("address_x") == u.TextureAddress.TA_WRAP
            and texture.get_editor_property("address_y") == u.TextureAddress.TA_WRAP
            and texture.get_editor_property("mip_gen_settings") == u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP
            and texture.get_editor_property("lod_bias") == 0
            and texture.get_editor_property("max_texture_size") == 0, "Photo texture color/normal/wrap/mip settings differ")
    size = (texture.blueprint_get_size_x(),texture.blueprint_get_size_y())
    require(size == (4096,4096), "Native photo texture size differs from 4K source")
    return {"asset":texture.get_path_name(),"sourceSha256":expected,"pixels":size,
            "srgb":bool(texture.get_editor_property("srgb")),"greenFlipped":bool(texture.get_editor_property("flip_green_channel")),
            "compression":str(compression),"mipGen":str(texture.get_editor_property("mip_gen_settings")),
            "wrapXY":True,"sourceDimensionReadback":True,"residentMipReadback":False}


def material_proof(u, material, contract, profile=None):
    profile=material_profile(profile)
    ref = reference(); lib = u.MaterialEditingLibrary; assets = u.EditorAssetLibrary
    require(isinstance(material,u.Material) and assets.get_metadata_tag(material,"BreziGeneratedBy") == profile["owner"], "Photo material ownership/type differs")
    for key, value in {"blend_mode":u.BlendMode.BLEND_OPAQUE,"shading_model":u.MaterialShadingModel.MSM_DEFAULT_LIT,
                       "two_sided":False,"tangent_space_normal":False,"use_material_attributes":False}.items():
        require(material.get_editor_property(key) == value, "Photographed oak material policy differs: "+key)
    require(lib.has_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE), "Oak material lacks persisted Nanite usage")
    expressions = list(lib.get_material_expressions(material))
    nodes = {str(assets.get_metadata_tag(n,"BreziOakNodeRole")):n for n in expressions}
    require(len(nodes)==len(expressions)==len(EXPECTED_ROLES) and nodes.keys()==EXPECTED_ROLES, "Photo material graph role/topology differs")
    codes = shader_codes(profile)
    for role, code in codes.items():
        require(isinstance(nodes[role],u.MaterialExpressionCustom) and nodes[role].get_editor_property("code")==code, "Photo projection/normal/roughness shader changed: "+role)
    require(isinstance(nodes["position"],u.MaterialExpressionWorldPosition) and isinstance(nodes["normalWS"],u.MaterialExpressionVertexNormalWS), "Photo projection lost world-space inputs")
    require(not any(isinstance(n,u.MaterialExpressionTextureCoordinate) for n in expressions), "Source UV dependency was introduced")
    expected_classes={"albedoMultiply":u.MaterialExpressionMultiply,"albedoBound":u.MaterialExpressionSaturate}
    for role, cls in expected_classes.items(): require(isinstance(nodes[role],cls), "Albedo palette graph differs")
    scalars = {"period":ref.PERIOD_CM,"baseRoughness":contract["sourceRoughness"],"roughAmplitude":ref.ROUGH_AMPLITUDE,
               "roughMean":ref.ROUGH_MEAN,"normalStrength":ref.NORMAL_STRENGTH,"metallic":0,"specular":.5}
    for role, expected in scalars.items():
        require(isinstance(nodes[role],u.MaterialExpressionConstant) and abs(float(nodes[role].get_editor_property("r"))-expected)<1e-5, "Oak scalar getter differs: "+role)
    for role, expected in {"palette":profile["palette"],"anchor":contract["anchorCm"]}.items():
        require(isinstance(nodes[role],u.MaterialExpressionConstant3Vector), "Oak vector role differs")
        color = nodes[role].get_editor_property("constant")
        require(all(abs(float(getattr(color,k))-value)<.0001 for k,value in zip(("r","g","b"),expected)), "Oak palette/anchor getter differs")
    for origin, output, dest, pin in links():
        names = [str(v) for v in lib.get_material_expression_input_names(nodes[dest])]
        sources = list(lib.get_inputs_for_material_expression(material,nodes[dest]))
        require(len(names)==len(sources) and bool(sources), "Oak native graph input getter differs")
        index = 0 if pin=="" else names.index(pin) if pin in names else -1
        require(index>=0 and sources[index]==nodes[origin], "Oak graph link differs: "+origin+" -> "+dest+"."+pin)
        actual_output=lib.get_input_node_output_name_for_material_expression(nodes[dest],nodes[origin])
        # Reflected bool+out-string APIs normally return str/None in UE Python.
        # Retain compatibility with the explicit successful tuple representation.
        if isinstance(actual_output,tuple) and len(actual_output)==2 and actual_output[0] is True:actual_output=actual_output[1]
        available=list(lib.get_material_expression_output_names(nodes[origin]))
        expected_output=output if output else available[0] if available else None
        require(isinstance(actual_output,str) and actual_output==expected_output,"Oak graph output channel differs: "+origin+" -> "+dest)
    for prop, role in outputs().items():
        require(lib.get_material_property_input_node(material,getattr(u.MaterialProperty,"MP_"+prop))==nodes[role], "Oak native material output differs: "+prop)
    for prop in ("WORLD_POSITION_OFFSET","OPACITY","OPACITY_MASK","EMISSIVE_COLOR"):
        require(lib.get_material_property_input_node(material,getattr(u.MaterialProperty,"MP_"+prop)) is None, "Unexpected oak geometry/optical output: "+prop)
    texture_results = {}
    for role, source_role, sampler in (("albedo","Diffuse",u.MaterialSamplerType.SAMPLERTYPE_COLOR),
        ("normalMap","nor_gl",u.MaterialSamplerType.SAMPLERTYPE_NORMAL),("roughMap","Rough",u.MaterialSamplerType.SAMPLERTYPE_MASKS)):
        node = nodes[role]
        require(isinstance(node,u.MaterialExpressionTextureSample) and node.get_editor_property("sampler_type")==sampler, "Oak sampler role differs")
        texture_results[role] = texture_proof(u,node.get_editor_property("texture"),role,ref.MAP_HASHES[source_role],profile["owner"])
    return {"asset":material.get_path_name(),"graphNodes":len(nodes),"blend":str(material.get_editor_property("blend_mode")),
            "worldSpaceNormal":True,"sourceUVDependency":False,"naniteUsage":True,"textures":texture_results,
            "shaderSha256":{k:hashlib.sha256(v.encode()).hexdigest() for k,v in codes.items()},
            "nativeScalarGetters":{k:float(nodes[k].get_editor_property("r")) for k in scalars},
            "nativeVectorGetters":{role:[float(getattr(nodes[role].get_editor_property("constant"),axis)) for axis in ("r","g","b")] for role in ("palette","anchor")},
            "profileOwner":profile["owner"],"materialName":profile["materialName"],
            "renderedVerified":False,"residentMipsVerified":False}


class Writer:
    def __init__(self,u,prefix,contract,profile=None):
        self.u,self.prefix,self.contract = u,prefix,contract
        self.profile=material_profile(profile)
        self.assets,self.lib = u.EditorAssetLibrary,u.MaterialEditingLibrary
        self.paths = set(); self.nodes = {}

    def existing(self,path):
        asset = self.assets.load_asset(path) if self.assets.does_asset_exist(path) else None
        if asset: require(self.assets.get_metadata_tag(asset,"BreziGeneratedBy")==self.profile["owner"], "Refusing unowned oak-study asset: "+path)
        return asset

    def save(self,asset):
        require(asset.get_path_name().startswith(self.prefix+"/"), "Oak asset escaped its owned namespace")
        self.assets.set_metadata_tag(asset,"BreziGeneratedBy",self.profile["owner"])
        require(self.assets.save_loaded_asset(asset,only_if_is_dirty=False), "Oak asset save failed")
        self.paths.add(asset.get_path_name())

    def texture(self,role,source_role):
        spec = self.contract["candidate"]["maps"][source_role]; path=self.prefix+"/Textures/T_"+role
        texture = self.existing(path)
        if texture:
            texture_proof(self.u,texture,role,spec["sha256"],self.profile["owner"]);self.paths.add(texture.get_path_name());return texture
        task = self.u.AssetImportTask()
        for key,value in {"filename":str(ROOT/spec["path"]),"destination_path":self.prefix+"/Textures","destination_name":"T_"+role,
                          "automated":True,"save":False,"replace_existing":False,"factory":self.u.TextureFactory()}.items(): task.set_editor_property(key,value)
        self.u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]); result=task.get_objects()
        require(len(result)==1 and isinstance(result[0],self.u.Texture2D),"Expected one photographed oak texture")
        texture=result[0]
        self.assets.set_metadata_tag(texture,"source_sha256",spec["sha256"])
        compression = {"normalMap":self.u.TextureCompressionSettings.TC_NORMALMAP,"roughMap":self.u.TextureCompressionSettings.TC_MASKS}.get(role,self.u.TextureCompressionSettings.TC_DEFAULT)
        for key,value in {"srgb":role=="albedo","compression_settings":compression,"flip_green_channel":role=="normalMap",
            "address_x":self.u.TextureAddress.TA_WRAP,"address_y":self.u.TextureAddress.TA_WRAP,
            "mip_gen_settings":self.u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP,"lod_bias":0,"max_texture_size":0}.items(): texture.set_editor_property(key,value)
        self.save(texture);texture_proof(self.u,texture,role,spec["sha256"],self.profile["owner"]);return texture

    def node(self,material,role,cls,**properties):
        n=self.lib.create_material_expression(material,cls)
        require(n is not None,"Oak graph node creation failed: "+role)
        for key,value in properties.items(): n.set_editor_property(key,value)
        self.assets.set_metadata_tag(n,"BreziOakNodeRole",role);self.nodes[role]=n;return n

    def custom(self,material,role,code,names,output_type):
        inputs=[]
        for name in names:
            i=self.u.CustomInput();i.set_editor_property("input_name",name);inputs.append(i)
        return self.node(material,role,self.u.MaterialExpressionCustom,code=code,inputs=inputs,output_type=output_type)

    def material(self):
        u=self.u;ref=reference();name=self.profile["materialName"];path=self.prefix+"/Materials/"+name
        material=self.existing(path)
        if material:
            material_proof(u,material,self.contract,self.profile);self.paths.add(material.get_path_name())
            for n in self.lib.get_material_expressions(material):
                if isinstance(n,u.MaterialExpressionTextureSample):self.paths.add(n.get_editor_property("texture").get_path_name())
            return material
        material=u.AssetToolsHelpers.get_asset_tools().create_asset(name,self.prefix+"/Materials",u.Material,u.MaterialFactoryNew())
        require(material is not None,"Oak material creation failed")
        self.assets.set_metadata_tag(material,"BreziGeneratedBy",self.profile["owner"])
        for key,value in {"blend_mode":u.BlendMode.BLEND_OPAQUE,"shading_model":u.MaterialShadingModel.MSM_DEFAULT_LIT,
                          "two_sided":False,"tangent_space_normal":False,"use_material_attributes":False}.items():material.set_editor_property(key,value)
        self.lib.set_base_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE,True)
        self.node(material,"position",u.MaterialExpressionWorldPosition)
        self.node(material,"normalWS",u.MaterialExpressionVertexNormalWS)
        for role,value in {"anchor":self.contract["anchorCm"],"palette":self.profile["palette"]}.items():
            self.node(material,role,u.MaterialExpressionConstant3Vector,constant=u.LinearColor(*value,1))
        for role,value in {"period":ref.PERIOD_CM,"baseRoughness":self.contract["sourceRoughness"],"roughAmplitude":ref.ROUGH_AMPLITUDE,
                           "roughMean":ref.ROUGH_MEAN,"normalStrength":ref.NORMAL_STRENGTH,"metallic":0,"specular":.5}.items():
            self.node(material,role,u.MaterialExpressionConstant,r=value)
        codes=shader_codes(self.profile)
        self.custom(material,"uv",codes["uv"],["Position","NormalWS","AnchorCm","PeriodCm"],u.CustomMaterialOutputType.CMOT_FLOAT2)
        self.custom(material,"normal",codes["normal"],["MapNormal","NormalWS","Strength"],u.CustomMaterialOutputType.CMOT_FLOAT3)
        self.custom(material,"roughness",codes["roughness"],["MapR","BaseRoughness","Amplitude","RoughMean"],u.CustomMaterialOutputType.CMOT_FLOAT1)
        for role,source_role,sampler in (("albedo","Diffuse",u.MaterialSamplerType.SAMPLERTYPE_COLOR),
            ("normalMap","nor_gl",u.MaterialSamplerType.SAMPLERTYPE_NORMAL),("roughMap","Rough",u.MaterialSamplerType.SAMPLERTYPE_MASKS)):
            self.node(material,role,u.MaterialExpressionTextureSample,texture=self.texture(role,source_role),sampler_type=sampler)
        self.node(material,"albedoMultiply",u.MaterialExpressionMultiply);self.node(material,"albedoBound",u.MaterialExpressionSaturate)
        # Inspect every reflected pin before connecting any graph edge. Custom
        # inputs keep their authored names; Saturate's Input is NAME_None/first.
        for origin,output,dest,pin in links():
            inputs=[str(v) for v in self.lib.get_material_expression_input_names(self.nodes[dest])]
            available=[str(v) for v in self.lib.get_material_expression_output_names(self.nodes[origin])]
            require(bool(inputs) and (pin=="" or pin in inputs) and bool(available) and (output=="" or output in available),
                    f"Oak graph pin preflight failed: {origin}.{output} -> {dest}.{pin}; inputs={inputs}; outputs={available}")
        for origin,output,dest,pin in links():
            require(self.lib.connect_material_expressions(self.nodes[origin],output,self.nodes[dest],pin),
                    f"Oak graph connection failed: {origin}.{output} -> {dest}.{pin}; inputs="+str(list(self.lib.get_material_expression_input_names(self.nodes[dest]))))
        for prop,role in outputs().items():require(self.lib.connect_material_property(self.nodes[role],"",getattr(u.MaterialProperty,"MP_"+prop)),"Oak output connection failed: "+prop)
        errors=list(self.lib.recompile_material(material));require(not errors,"Oak native material compile failed: "+str(errors))
        material_proof(u,material,self.contract,self.profile);self.save(material);return material


def components(u,ids):
    found={};selected=set(ids)
    for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        matches=list(selected.intersection(str(t) for t in actor.get_editor_property("tags")))
        if not matches:continue
        require(len(matches)==1 and matches[0] not in found,"Ambiguous canonical wood actor")
        cs=actor.get_components_by_class(u.StaticMeshComponent);require(len(cs)==1,"Expected one canonical wood mesh component")
        found[matches[0]]=(actor,cs[0])
    require(found.keys()==set(ids),"Canonical wood coverage differs")
    return found


def overrides(component):
    return [m.get_path_name() if m else None for m in component.get_editor_property("override_materials")]


def set_overrides(u,component,paths):
    values=[]
    for path in paths:
        m=u.load_object(None,path) if path else None
        require(not path or m is not None,"Cannot restore prior native override: "+str(path));values.append(m)
    component.set_editor_property("override_materials",values)
    require(overrides(component)==paths,"Material override restoration differs")


def snapshot(u,found):
    from materials import _asset_hashes
    data={};paths=[]
    for id_,(actor,c) in found.items():
        mesh=c.get_editor_property("static_mesh");require(mesh is not None,"Missing canonical wood mesh")
        require(c.get_num_materials()==1 and mesh.get_num_sections(0)==1,"Wood mesh unexpectedly has several sections/materials")
        paths.append(mesh.get_path_name()); effective=c.get_material(0);require(effective is not None,"Missing wood material")
        paths.append(effective.get_path_name());transform=c.get_world_transform()
        data[id_]={"mesh":mesh.get_path_name(),"meshMaterial":mesh.get_material(0).get_path_name(),"effectiveMaterial":effective.get_path_name(),"overrides":overrides(c),
            "translation":[float(getattr(transform.translation,k)) for k in ("x","y","z")],"rotation":[float(getattr(transform.rotation,k)) for k in ("x","y","z","w")],
            "scale":[float(getattr(transform.scale3d,k)) for k in ("x","y","z")],"triangles":mesh.get_num_triangles(0),"uvChannels":mesh.get_num_tex_coords(0),
            "collision":str(c.get_collision_enabled()),"profile":str(c.get_collision_profile_name()),"pawnResponse":str(c.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN)),
            "actorTags":[str(t) for t in actor.get_editor_property("tags")],"componentTags":[str(t) for t in c.get_editor_property("component_tags")],
            "visible":bool(c.get_editor_property("visible")),"hiddenInGame":bool(c.get_editor_property("hidden_in_game"))}
    return {"components":data,"assetHashes":_asset_hashes(paths)}


def guard_native_targets(u,found,contract,ids=None,expected_slots=None):
    from materials import _resolve_slot
    ref=reference();selected=ref.IDS if ids is None else frozenset(ids)
    slots_by_id={i:"MAT_0078" for i in selected} if expected_slots is None else expected_slots
    require(set(slots_by_id)==set(selected),"Native oak source slot scope differs")
    for id_ in selected:
        actor,c=found[id_];mesh=c.get_editor_property("static_mesh");record=contract["records"][id_]
        require(mesh.get_num_triangles(0)==12 and mesh.get_num_tex_coords(0)>=1,"Native cabinet topology/UV differs")
        slots=mesh.get_editor_property("static_materials")
        require(len(slots)==1 and _resolve_slot(slots[0],record,contract["scene"]["materials"])==slots_by_id[id_],"Native cabinet source slot differs")
        origin,extent,_=u.SystemLibrary.get_component_bounds(c)
        actual_min=[float(getattr(origin,k)-getattr(extent,k)) for k in ("x","y","z")]
        actual_max=[float(getattr(origin,k)+getattr(extent,k)) for k in ("x","y","z")]
        lo,hi=record["boundsMm"]["min"],record["boundsMm"]["max"]
        expected_min=(lo[0]/10,-hi[1]/10,lo[2]/10);expected_max=(hi[0]/10,-lo[1]/10,hi[2]/10)
        require(all(abs(a-b)<.002 for a,b in zip(actual_min+actual_max,expected_min+expected_max)),"Native cabinet world bounds differ from source")
        require(all(abs(float(getattr(c.get_world_transform().scale3d,k))-1)<1e-6 for k in ("x","y","z")),"Unexpected cabinet instance scale")


def apply_tv_oak(scene,geometry_dir):
    import unreal as u
    from materials import _asset_hashes
    ref=reference();contract=ref.verify_inputs(scene,geometry_dir)
    files=[Path(__file__),Path(__file__).with_name("oak_reference.py"),Path(__file__).with_name("oak-basis.hlsl")]
    files += [ref.STUDY/name for name in ref.FILES]
    files += [ROOT/spec["path"] for spec in contract["candidate"]["maps"].values()]
    hashes={str(path.relative_to(ROOT)):sha(path) for path in files}
    version=ref.digest(hashes)[:16];writer=Writer(u,PREFIX+"/V_"+version,contract)
    report_path=Path(geometry_dir).parent/"tv-oak-report.json"
    report={"schemaVersion":1,"status":"pending","revision":REVISION,"nativeApplied":False,"renderedVerified":False,"photorealismVerified":False,
        "activationStarted":False,"rollbackRequired":False,"rollbackAttempted":False,"rollbackVerified":False,
        "selectedIds":sorted(ref.IDS),"sourceManifestSha256":ref.SCENE_SHA,"sourceObjSha256":ref.OBJ_SHA,"sourceRecordHashes":ref.RECORD_HASHES,
        "woodObjects":158,"preservedWoodObjects":155,"excludedOvalCoffeeTable":"DOM_01326","pipelineFiles":hashes,
        "periodCm":ref.PERIOD_CM,"anchorCm":contract["anchorCm"],"paletteLinearMultiplier":ref.PALETTE,
        "roughness":{"authoredMean":.74,"mapMean":ref.ROUGH_MEAN,"amplitude":ref.ROUGH_AMPLITUDE,"unclampedRange":[.74-.12*ref.ROUGH_MEAN,.74+.12*(1-ref.ROUGH_MEAN)]},
        "normal":{"strength":ref.NORMAL_STRENGTH,"meaning":"Authored appearance control; not calibrated physical finish"},
        "limitations":["Photographed illustrative CC0 veneer, not the selected real product.","Full-texture means are preserved; a cabinet crops a different region and need not share that average.",
            "Five red albedo texels saturate; global linear red mean changes by 1.9924e-8.","Horizontal panel grain follows depth; per-face veneer seams are an authored construction approximation.",
            "Native graph getters and saved reload do not establish cooked Metal normal orientation, resident mip level, day/night appearance or a quality improvement."]}
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem);assets=u.EditorAssetLibrary
    before=None;previous_metadata={};map_path=None;mutated=False

    def write(status):
        report.update(status=status,generatedAt=datetime.now(timezone.utc).isoformat())
        temp=report_path.with_suffix(".tmp");temp.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n");temp.replace(report_path)

    def reload_map():
        require(levels.save_current_level(),"Oak study map save failed")
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False),"Oak study map unload failed")
        require(levels.load_level(map_path),"Oak study map reload failed")

    try:
        write("pending")
        world=u.EditorLevelLibrary.get_editor_world();map_path=world.get_path_name().split(".")[0]
        require(map_path=="/Game/Brezi/Maps/Brezi" and assets.get_metadata_tag(world,"BreziGeneratedBy")=="scripts/unreal/import_scene.py","Expected the owned saved Brezi map")
        found=components(u,contract["woodIds"]);guard_native_targets(u,found,contract);before=snapshot(u,found)
        previous_metadata={id_:{k:assets.get_metadata_tag(found[id_][0],k) for k in (ORIGINAL,REVISION_TAG)} for id_ in ref.IDS}
        del world,found
        material=writer.material();material_path=material.get_path_name();del material
        # Persist and reload before any component override; prove old source bindings/asset bytes survived authoring.
        reload_map();found=components(u,contract["woodIds"])
        require(snapshot(u,found)==before,"Source wood state changed before material activation")
        report["stagedMaterialProof"]=material_proof(u,u.load_object(None,material_path),contract)
        new_material=u.load_object(None,material_path);require(new_material is not None,"Saved oak material missing")
        mutated=True;report["activationStarted"]=True
        for id_ in ref.IDS:
            actor,c=found[id_]
            if not previous_metadata[id_][ORIGINAL]:assets.set_metadata_tag(actor,ORIGINAL,json.dumps(before["components"][id_]["overrides"]))
            assets.set_metadata_tag(actor,REVISION_TAG,REVISION)
            c.set_material(0,new_material)
            require(c.get_material(0).get_path_name()==material_path,"Cabinet material override failed")
        del found,new_material
        reload_map();found=components(u,contract["woodIds"]);guard_native_targets(u,found,contract)
        after=snapshot(u,found)
        for id_,initial in before["components"].items():
            expected=dict(initial)
            if id_ in ref.IDS:expected.update(effectiveMaterial=material_path,overrides=[material_path])
            require(after["components"][id_]==expected,"Saved source wood geometry/collision/UV/other material changed: "+id_)
        # Newly effective candidate assets add hashes; every pre-existing source asset must remain identical.
        current_source_hashes=_asset_hashes([value["mesh"] for value in before["components"].values()]+[value["effectiveMaterial"] for value in before["components"].values()])
        require(current_source_hashes==before["assetHashes"],"Canonical wood mesh/material asset bytes changed")
        report["savedReloadMaterialProof"]=material_proof(u,u.load_object(None,material_path),contract)
        report.update(nativeApplied=True,assetHashes=_asset_hashes(writer.paths),
            canonicalAssetHashes=current_source_hashes,bindings=[{"objectId":i,"sourceId":contract["records"][i]["sourceId"],"sourceSlot":"MAT_0078",
                "material":found[i][1].get_material(0).get_path_name(),"priorOverrides":before["components"][i]["overrides"],"savedReloadVerified":True} for i in sorted(ref.IDS)],
            verification={"nativeGraphGetters":True,"newAssetsSavedBeforeActivation":True,"twoMapReloads":True,"other155WoodBindingsUnchanged":True,
                          "sourceMeshUvCollisionAndAssetBytesUnchanged":True,"geometryChanged":False,"sourceWebTexturesChanged":False})
        write("native-tv-oak-saved-reload-validated");return report
    except Exception as error:
        report["error"]=str(error);rollback=[]
        report.update(rollbackRequired=mutated,retainedGeneratedAssetPaths=sorted(writer.paths),sourceStateVerifiedOnFailure=False)
        if mutated and before and map_path:
            report["rollbackAttempted"]=True
            try:
                if u.EditorLevelLibrary.get_editor_world().get_path_name().split(".")[0]!=map_path:require(levels.load_level(map_path),"Rollback map load failed")
                found=components(u,contract["woodIds"])
                for id_ in ref.IDS:
                    actor,c=found[id_];set_overrides(u,c,before["components"][id_]["overrides"])
                    for key,value in previous_metadata[id_].items():assets.set_metadata_tag(actor,key,value)
                reload_map();require(snapshot(u,components(u,contract["woodIds"]))==before,"Oak rollback did not restore source state")
                report.update(rollbackVerified=True,sourceStateVerifiedOnFailure=True,sourceStateCheckStage="saved-reloaded-rollback")
            except Exception as rollback_error:rollback.append(str(rollback_error))
        elif before:
            # An asset graph failure precedes component activation. Verify the
            # live source state explicitly; do not label no-op as a rollback.
            try:
                require(u.EditorLevelLibrary.get_editor_world().get_path_name().split(".")[0]==map_path,"Oak failure left another world loaded")
                found=components(u,contract["woodIds"])
                require(snapshot(u,found)==before,"Oak source state changed before activation")
                require(all(assets.get_metadata_tag(found[i][0],k)==v for i,values in previous_metadata.items() for k,v in values.items()),"Oak source metadata changed before activation")
                report.update(sourceStateVerifiedOnFailure=True,sourceStateCheckStage="live-after-preactivation-failure")
            except Exception as state_error:report["failureStateVerificationError"]=str(state_error)
        report.update(nativeApplied=False,rollbackErrors=rollback);write("failed");raise


def restore_tv_oak(scene,geometry_dir):
    """Explicit reversal, restricted to the three owned overrides; save/reload proof."""
    import unreal as u
    ref=reference();contract=ref.verify_inputs(scene,geometry_dir);assets=u.EditorAssetLibrary
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem);world=u.EditorLevelLibrary.get_editor_world()
    path=world.get_path_name().split(".")[0]
    require(path=="/Game/Brezi/Maps/Brezi" and assets.get_metadata_tag(world,"BreziGeneratedBy")=="scripts/unreal/import_scene.py","Expected owned Brezi map")
    found=components(u,contract["woodIds"]);expected={};before=snapshot(u,found);metadata={}
    # Preflight all three before writing any reversal.
    for id_ in ref.IDS:
        actor,c=found[id_];value=assets.get_metadata_tag(actor,ORIGINAL)
        metadata[id_]={key:assets.get_metadata_tag(actor,key) for key in (ORIGINAL,REVISION_TAG)}
        require(value and assets.get_metadata_tag(actor,REVISION_TAG)==REVISION,"No owned oak override to restore: "+id_)
        require(assets.get_metadata_tag(c.get_material(0),"BreziGeneratedBy")==OWNER,"Refusing to remove an unrelated material override")
        expected[id_]=json.loads(value)
        require(isinstance(expected[id_],list),"Invalid saved material override recipe")
        for previous in expected[id_]:require(previous is None or u.load_object(None,previous) is not None,"Missing original override asset")
    def reload_map():
        require(levels.save_current_level(),"Restored oak map save failed")
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False) and levels.load_level(path),"Restored oak map reload failed")
    try:
        for id_ in ref.IDS:
            actor,c=found[id_];set_overrides(u,c,expected[id_]);assets.set_metadata_tag(actor,ORIGINAL,"");assets.set_metadata_tag(actor,REVISION_TAG,"")
        del world,found
        reload_map();found=components(u,contract["woodIds"]);after=snapshot(u,found)
        for id_,initial in before["components"].items():
            wanted=dict(initial)
            if id_ in ref.IDS:
                restored=expected[id_]
                effective=restored[0] if restored and restored[0] else initial["meshMaterial"]
                wanted.update(overrides=restored,effectiveMaterial=effective)
            require(after["components"][id_]==wanted,"Restored oak state differs: "+id_)
        from materials import _asset_hashes
        prior_paths=[value[key] for value in before["components"].values() for key in ("mesh","effectiveMaterial")]
        require(_asset_hashes(prior_paths)==before["assetHashes"],"Oak reversal changed source/native material bytes")
        (Path(geometry_dir).parent/"tv-oak-report.json").write_text(json.dumps({"status":"source-overrides-restored","nativeApplied":False,
            "revision":REVISION,"selectedIds":sorted(ref.IDS),"savedReloadVerified":True,"other155WoodBindingsUnchanged":True},indent=2)+"\n")
    except Exception as error:
        rollback_errors=[]
        try:
            if u.EditorLevelLibrary.get_editor_world().get_path_name().split(".")[0]!=path:require(levels.load_level(path),"Reversal rollback map load failed")
            found=components(u,contract["woodIds"])
            for id_ in ref.IDS:
                actor,c=found[id_];set_overrides(u,c,before["components"][id_]["overrides"])
                for key,value in metadata[id_].items():assets.set_metadata_tag(actor,key,value)
            reload_map();require(snapshot(u,components(u,contract["woodIds"]))==before,"Reversal rollback state differs")
        except Exception as rollback_error:rollback_errors.append(str(rollback_error))
        (Path(geometry_dir).parent/"tv-oak-report.json").write_text(json.dumps({"status":"restore-failed","error":str(error),"rollbackErrors":rollback_errors},indent=2)+"\n")
        raise
