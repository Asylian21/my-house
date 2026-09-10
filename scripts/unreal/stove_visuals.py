"""Explicit editor-only stove visual revision with neutral flame study controls.

The default emission scale 1 and study time -1 preserve the animated material.
The owning writer saves/reloads the map twice and verifies source geometry,
collision, native graph links and the optional parameters before returning.
"""
import hashlib
import importlib.util
import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = "scripts/unreal/stove_visuals.py"
PREFIX = "/Game/Brezi/VisualDetails/Stove"
TAG = "BreziStoveVisualDetail"
FLAGS = ("visible","hidden_in_game","cast_shadow","cast_hidden_shadow","visible_in_ray_tracing",
         "affect_distance_field_lighting","affect_dynamic_indirect_lighting","affect_indirect_lighting_while_hidden")
HIDDEN = {key: key == "hidden_in_game" for key in FLAGS}
# Python 3.9 and the engine's Python 3.11 hypot implementations can differ by
# one binary64 ULP (observed 2.842170943040401e-14 mm). This tolerance applies
# only to recomputed summary numbers, never to vertex containment thresholds.
SUMMARY_TOLERANCE_MM = 1e-10
FLAME_SHADER_SHA256 = "45b0871f6776cc197686ff19cb8e7253babdc0c1ca41943d479f504a76f137bc"
PREVIOUS_FLAME_SHADER_SHA256 = "08a70ffa9d33bdddad0842b8d4a01e5737748acd6ff32cb21c4cc4ea3268172a"
FLAME_PARAMETERS = {"BreziFlameEmissionScale":1.0,"BreziFlameStudyTimeSeconds":-1.0}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def generator():
    spec=importlib.util.spec_from_file_location("brezi_stove_geometry",Path(__file__).with_name("stove-visuals")/"generate.py")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def validate_summary(actual, expected):
    require(isinstance(expected,dict) and actual.keys()==expected.keys(),"Stove vertex summary mesh coverage differs")
    measured_keys={"maximumRadiusMm","minElevationMm","maxElevationMm"}
    maximum_error=0.0
    for id_,computed in actual.items():
        saved=expected[id_]
        require(isinstance(saved,dict) and saved.keys()==computed.keys()==measured_keys|{"triangles"},"Stove vertex summary schema differs")
        require(type(saved["triangles"]) is int and saved["triangles"]==computed["triangles"],"Stove vertex summary triangle count differs")
        for key in measured_keys:
            a,b=computed[key],saved[key]
            require(type(b) in (int,float) and math.isfinite(a) and math.isfinite(b),"Nonfinite stove vertex summary")
            error=abs(a-b); maximum_error=max(maximum_error,error)
            require(error<=SUMMARY_TOLERANCE_MM,
                    f"Stove vertex summary {id_}/{key} differs by {error:.17g} mm (limit {SUMMARY_TOLERANCE_MM:g} mm)")
    return maximum_error


def verify_inputs(scene, directory):
    directory=Path(directory); output=directory.parent/"stove-visuals"
    gen=generator(); current,records,_,_=gen.verify_source(directory)
    report=json.loads((output/"stove-visuals.json").read_text())
    require(current == scene and report["schemaVersion"] == 1 and report["revision"] == gen.REVISION
            and report["status"] == "stove-visual-geometry-validated", "Invalid stove derivative/source revision")
    require(report["sourceManifestSha256"] == sha(directory/"scene.json")
            and report["sourceObjSha256"] == sha(directory/"dom-mm.obj") == scene["objSha256"]
            and report["generatorSha256"] == sha(Path(gen.__file__))
            and report["sha256"] == sha(output/report["file"]), "Stale stove derivative inputs")
    require(report["sourceRecords"] == records and report["sourceRecordHashes"] == {k:gen.canonical_hash(v) for k,v in records.items()}
            and report["hiddenProxyIds"] == sorted(gen.GUARDS), "Stove replacement scope changed")
    issues=report["khronosValidation"]
    require(issues["numErrors"] == 0 and issues["numWarnings"] == 0 and not issues["truncated"], "Stove GLB is not validated")
    require({o["id"] for o in report["objects"]} == {"STOVEV_SHELL","STOVEV_CHAMBER","STOVEV_LOGS","STOVEV_FLAMES"}, "Unexpected derivative mesh scope")
    meshes=[]
    decoded=gen.read_glb_positions(output/report["file"],report["stoveAxisSourceMm"])
    maximum_error=0.0
    for record in report["objects"]:
        mesh=gen.Mesh(record["id"],record["role"]); mesh.positions=record["sourceRelativeVerticesMm"]
        mesh.indices=list(range(len(mesh.positions))); meshes.append(mesh)
        require(record["triangles"]*3 == len(mesh.positions) == record["vertices"], "Invalid derivative vertex count")
        require(record["id"] in decoded and len(decoded[record["id"]])==len(mesh.positions),"Stove GLB geometry coverage differs")
        maximum_error=max(maximum_error,max(abs(a-b) for p,q in zip(mesh.positions,decoded[record["id"]]) for a,b in zip(p,q)))
    # Validate actual vertices first with unchanged physical thresholds; only
    # the separately serialized derived summaries receive numerical tolerance.
    validate_summary(gen.validate_vertices(meshes),report["vertexValidation"])
    saved_error=report["maximumGlbPositionErrorMm"]
    require(type(saved_error) in (int,float) and math.isfinite(saved_error)
            and abs(maximum_error-saved_error)<=SUMMARY_TOLERANCE_MM
            and maximum_error<=0.002 and 0<=saved_error<=0.002,"Stove GLB geometry differs from derivative contract")
    return report, output


def flags(component):
    return {key:bool(component.get_editor_property(key)) for key in FLAGS}


def set_flags(component, values):
    for key,value in values.items():
        component.set_editor_property(key,value)
    require(flags(component) == values, "Stove visibility state did not persist in memory")


def source_components(unreal, ids):
    found={}
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        matches=[id_ for id_ in ids if actor.actor_has_tag(id_)]
        if matches:
            require(len(matches) == 1 and matches[0] not in found, "Ambiguous canonical stove actor")
            components=actor.get_components_by_class(unreal.StaticMeshComponent)
            require(len(components) == 1, "Canonical stove component count changed")
            found[matches[0]]=(actor,components[0])
    require(found.keys() == set(ids), "Missing canonical stove actor")
    return found


def invariants(unreal, originals):
    from materials import _asset_hashes
    result={}; paths=[]
    for id_,(actor,component) in originals.items():
        mesh=component.get_editor_property("static_mesh"); require(mesh is not None,"Missing canonical stove mesh")
        paths.append(mesh.get_path_name())
        transform=component.get_world_transform()
        result[id_]={"mesh":mesh.get_path_name(),"actorTags":[str(t) for t in actor.get_editor_property("tags")],
                     "componentTags":[str(t) for t in component.get_editor_property("component_tags")],
                     "translation":[float(getattr(transform.translation,k)) for k in ("x","y","z")],
                     "rotation":[float(getattr(transform.rotation,k)) for k in ("x","y","z","w")],
                     "scale":[float(getattr(transform.scale3d,k)) for k in ("x","y","z")],
                     "collision":str(component.get_collision_enabled()),"profile":str(component.get_collision_profile_name()),
                     "pawn":str(component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)),
                     "triangles":mesh.get_num_triangles(0)}
    return {"components":result,"assetHashes":_asset_hashes(paths)}


def flame_links():
    """Exact native shortened input names; all outputs select index zero."""
    return [("uv","custom","UV"),("choose","custom","Time"),("custom","rgb",""),("custom","alpha",""),
            ("rgb","emissive","A"),("scale","emissive","B"),("studyTime","choose","A"),("zero","choose","B"),
            ("studyTime","choose","A > B"),("studyTime","choose","A == B"),("time","choose","A < B")]


def build_flame_graph(writer, material):
    u=writer.u
    nodes={"uv":writer.node(material,"TextureCoordinate",coordinate_index=0),"time":writer.node(material,"Time"),
           "scale":writer.node(material,"ScalarParameter",parameter_name=u.Name("BreziFlameEmissionScale"),default_value=1.0),
           "studyTime":writer.node(material,"ScalarParameter",parameter_name=u.Name("BreziFlameStudyTimeSeconds"),default_value=-1.0),
           "zero":writer.node(material,"Constant",r=0.0),"choose":writer.node(material,"If",equals_threshold=0.0),
           "rgb":writer.node(material,"ComponentMask",r=True,g=True,b=True,a=False),
           "alpha":writer.node(material,"ComponentMask",r=False,g=False,b=False,a=True),"emissive":writer.node(material,"Multiply")}
    inputs=[]
    for name in ("UV","Time"):
        value=u.CustomInput();value.set_editor_property("input_name",name);inputs.append(value)
    nodes["custom"]=writer.node(material,"Custom",code=(Path(__file__).with_name("stove-visuals")/"flame.hlsl").read_text(),
                                inputs=inputs,output_type=u.CustomMaterialOutputType.CMOT_FLOAT4)
    for origin,dest,pin in flame_links():writer.connect(nodes[origin],"",nodes[dest],pin)
    writer.prop(nodes["emissive"],material,"EMISSIVE_COLOR");writer.prop(nodes["alpha"],material,"OPACITY")


def validate_flame_material(unreal, material):
    """Strict native getter proof, repeated by both existing saved-map checks."""
    lib=unreal.MaterialEditingLibrary
    require(material.get_editor_property("blend_mode")==unreal.BlendMode.BLEND_ADDITIVE
            and material.get_editor_property("shading_model")==unreal.MaterialShadingModel.MSM_UNLIT
            and material.get_editor_property("two_sided"),"Flame additive/unlit/sidedness policy differs")
    nodes=list(lib.get_material_expressions(material))
    require(len(nodes)==10,"Flame study graph must contain exactly ten nodes")
    roles={}
    for role,cls in {"uv":"TextureCoordinate","time":"Time","custom":"Custom","choose":"If","zero":"Constant","emissive":"Multiply"}.items():
        matches=[n for n in nodes if isinstance(n,getattr(unreal,"MaterialExpression"+cls))]
        require(len(matches)==1,"Flame study node role is ambiguous: "+role);roles[role]=matches[0]
    parameters=[n for n in nodes if isinstance(n,unreal.MaterialExpressionScalarParameter)]
    require(len(parameters)==2,"Flame scalar parameter coverage differs")
    defaults={}
    for name,expected in FLAME_PARAMETERS.items():
        matches=[n for n in parameters if str(n.get_editor_property("parameter_name"))==name]
        require(len(matches)==1 and float(matches[0].get_editor_property("default_value"))==expected,"Flame default parameter differs: "+name)
        roles["scale" if name=="BreziFlameEmissionScale" else "studyTime"]=matches[0];defaults[name]=float(matches[0].get_editor_property("default_value"))
    for role,channels in (("rgb",(True,True,True,False)),("alpha",(False,False,False,True))):
        matches=[n for n in nodes if isinstance(n,unreal.MaterialExpressionComponentMask)
                 and tuple(bool(n.get_editor_property(k)) for k in ("r","g","b","a"))==channels]
        require(len(matches)==1,"Flame unchanged channel mask differs: "+role);roles[role]=matches[0]
    require(len({n.get_path_name() for n in roles.values()})==len(nodes),"Flame study contains an unexpected graph node")
    require(float(roles["choose"].get_editor_property("equals_threshold"))==0.0
            and float(roles["zero"].get_editor_property("r"))==0.0,"Flame time selection is not an exact negative/nonnegative split")
    require(roles["uv"].get_editor_property("coordinate_index")==0
            and float(roles["uv"].get_editor_property("u_tiling"))==1.0 and float(roles["uv"].get_editor_property("v_tiling"))==1.0,
            "Flame source UV channel or tiling changed")
    require(not roles["time"].get_editor_property("ignore_pause") and not roles["time"].get_editor_property("override_period"),"Ordinary flame Time behavior changed")
    require(roles["custom"].get_editor_property("output_type")==unreal.CustomMaterialOutputType.CMOT_FLOAT4,"Flame Custom output type changed")
    code=str(roles["custom"].get_editor_property("code"))
    expected_code=(Path(__file__).with_name("stove-visuals")/"flame.hlsl").read_text()
    require(code==expected_code and hashlib.sha256(code.encode()).hexdigest()==FLAME_SHADER_SHA256,"Flame opacity/emission shader changed")
    connections=[];expected_inputs={role:{} for role in roles}
    for origin,dest,pin in flame_links():
        names=[str(v) for v in lib.get_material_expression_input_names(roles[dest])]
        sources=list(lib.get_inputs_for_material_expression(material,roles[dest]))
        index=0 if pin=="" else names.index(pin) if pin in names else -1
        require(len(names)==len(sources) and index>=0 and index<len(sources) and sources[index]==roles[origin],
                f"Flame graph input differs: {origin} -> {dest}.{pin}; nativeInputs={names}")
        available=[str(v) for v in lib.get_material_expression_output_names(roles[origin])]
        actual=lib.get_input_node_output_name_for_material_expression(roles[dest],roles[origin])
        if isinstance(actual,tuple) and len(actual)==2 and actual[0] is True:actual=actual[1]
        require(bool(available) and isinstance(actual,str) and actual==available[0],"Flame graph no longer uses unchanged output index zero: "+origin)
        expected_inputs[dest][index]=roles[origin]
        connections.append({"from":origin,"outputIndex":0,"outputNameNative":actual,"to":dest,"inputNameNative":names[index]})
    for role,node in roles.items():
        actual=list(lib.get_inputs_for_material_expression(material,node))
        require(len(actual)==len(expected_inputs[role]) and all(actual[i]==source for i,source in expected_inputs[role].items()),"Flame unexpected or unbound graph input: "+role)
    for name,role in (("EMISSIVE_COLOR","emissive"),("OPACITY","alpha")):
        require(lib.get_material_property_input_node(material,getattr(unreal.MaterialProperty,"MP_"+name))==roles[role],"Flame material output changed: "+name)
    require(lib.get_material_property_input_node(material,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET) is None,"Flame gained vertex displacement")
    return {"blendModeNative":str(material.get_editor_property("blend_mode")),"shadingModelNative":str(material.get_editor_property("shading_model")),
            "shaderCodeSha256":hashlib.sha256(code.encode()).hexdigest(),"timeConnected":True,"worldPositionOffsetConnected":False,
            "graphNodeCount":10,"defaultScalarParameters":defaults,"equalsThresholdNative":0.0,
            "graphConnectionsNative":connections,"graphExactConnectionsVerified":True,"opacityCustomAlphaDirect":True,
            "defaultOrdinaryTimeSelected":True,"emissionScaleAffectsOpacity":False,
            "emissionAndOpacityMatchPinnedShader":True,
            "alphaShapeChangedFromPreviousRevision":True,"previousShaderSha256":PREVIOUS_FLAME_SHADER_SHA256,
            "physicalFireBrightnessVerified":False}


class Writer:
    def __init__(self, unreal, prefix):
        self.u,self.prefix=unreal,prefix
        self.assets=unreal.EditorAssetLibrary; self.lib=unreal.MaterialEditingLibrary
        self.paths=set(); self.materials={}
        self.current_role="unassigned"

    def owned(self,path):
        asset=self.assets.load_asset(path) if self.assets.does_asset_exist(path) else None
        if asset: require(self.assets.get_metadata_tag(asset,"BreziGeneratedBy") == OWNER,"Refusing unowned stove asset: "+path)
        return asset

    def save(self,asset):
        require(asset.get_path_name().startswith(self.prefix+"/"),"Stove asset escaped namespace")
        self.assets.set_metadata_tag(asset,"BreziGeneratedBy",OWNER)
        self.assets.set_metadata_tag(asset,"writer_sha256",sha(__file__))
        require(self.assets.save_loaded_asset(asset,only_if_is_dirty=False),"Stove asset save failed")
        self.paths.add(asset.get_path_name())

    def node(self,material,name,**properties):
        node=self.lib.create_material_expression(material,getattr(self.u,"MaterialExpression"+name))
        require(node is not None,"Stove material node unavailable: "+name)
        for key,value in properties.items(): node.set_editor_property(key,value)
        return node

    def connect(self,a,output,b,input_):
        available_inputs=[str(v) for v in self.lib.get_material_expression_input_names(b)]
        available_outputs=[str(v) for v in self.lib.get_material_expression_output_names(a)]
        require(bool(available_inputs) and (input_=="" or input_ in available_inputs)
                and bool(available_outputs) and (output=="" or output in available_outputs),
                f"Stove reflected pin preflight failed: role={self.current_role}; output={output!r}; input={input_!r}; availableInputs={available_inputs}; availableOutputs={available_outputs}")
        if not self.lib.connect_material_expressions(a,output,b,input_):
            details={"role":self.current_role,"from":a.get_class().get_name(),"fromNode":a.get_name(),
                     "requestedOutput":output,"availableOutputs":list(self.lib.get_material_expression_output_names(a)),
                     "to":b.get_class().get_name(),"toNode":b.get_name(),"requestedInput":input_,
                     "availableInputs":list(self.lib.get_material_expression_input_names(b))}
            raise RuntimeError("Stove material connection failed: "+json.dumps(details,ensure_ascii=False))

    def prop(self,node,material,name):
        require(self.lib.connect_material_property(node,"",getattr(self.u.MaterialProperty,"MP_"+name)),
                "Stove material output failed: role="+self.current_role+" node="+node.get_class().get_name()+" output='' property="+name)

    def scalar(self,material,value): return self.node(material,"Constant",r=value)

    def color(self,material,value): return self.node(material,"Constant3Vector",constant=self.u.LinearColor(*value,1))

    def custom(self,material,code,inputs,scalar=False):
        node=self.node(material,"Custom",code=code,output_type=self.u.CustomMaterialOutputType.CMOT_FLOAT1 if scalar else self.u.CustomMaterialOutputType.CMOT_FLOAT4)
        custom_inputs=[]
        for name in inputs:
            input_=self.u.CustomInput(); input_.set_editor_property("input_name",name); custom_inputs.append(input_)
        node.set_editor_property("inputs",custom_inputs)
        for name,source in inputs.items(): self.connect(source,"",node,name)
        return node

    def material(self,role):
        self.current_role=role
        path=self.prefix+"/Materials/M_Stove_"+role
        material=self.owned(path)
        if material is None:
            material=self.u.AssetToolsHelpers.get_asset_tools().create_asset(path.rsplit("/",1)[1],path.rsplit("/",1)[0],self.u.Material,self.u.MaterialFactoryNew())
        require(isinstance(material,self.u.Material),"Stove material creation failed")
        self.assets.set_metadata_tag(material,"BreziGeneratedBy",OWNER)
        for expr in list(self.lib.get_material_expressions(material)): self.lib.delete_material_expression(material,expr)
        require(not list(self.lib.get_material_expressions(material)),"Stove graph did not clear")
        material.set_editor_property("two_sided",role in ("flames","chamber"))
        if role == "flames":
            # Neutral defaults retain the existing authored 3–8 emission, alpha
            # and Time animation. Transient study controls require native QA.
            material.set_editor_property("blend_mode",self.u.BlendMode.BLEND_ADDITIVE)
            material.set_editor_property("shading_model",self.u.MaterialShadingModel.MSM_UNLIT)
            build_flame_graph(self,material)
        else:
            material.set_editor_property("blend_mode",self.u.BlendMode.BLEND_OPAQUE)
            material.set_editor_property("shading_model",self.u.MaterialShadingModel.MSM_DEFAULT_LIT)
            self.prop(self.color(material,{"shell":(0.012,0.014,0.016),"chamber":(0.009,0.008,0.007),"logs":(0.017,0.012,0.009)}[role]),material,"BASE_COLOR")
            self.prop(self.scalar(material,{"shell":0.68,"chamber":0.94,"logs":0.91}[role]),material,"ROUGHNESS")
            self.prop(self.scalar(material,0.12 if role == "shell" else 0),material,"METALLIC")
            if role == "logs":
                custom=self.custom(material,(Path(__file__).with_name("stove-visuals")/"char.hlsl").read_text(),{"UV":self.node(material,"TextureCoordinate",coordinate_index=0)},scalar=True)
                mult=self.node(material,"Multiply"); self.connect(custom,"",mult,"A"); self.connect(self.color(material,(0.18,0.014,0.001)),"",mult,"B"); self.prop(mult,material,"EMISSIVE_COLOR")
        errors=list(self.lib.recompile_material(material)); require(not errors,"Stove material compile errors: "+str(errors))
        if role=="flames": validate_flame_material(self.u,material)
        self.assets.set_metadata_tag(material,"BreziStoveRole",role); self.save(material); self.materials[role]=material
        return material


def apply_stove_visuals(scene, geometry_dir):
    import unreal
    from materials import _asset_hashes
    from hidden_collision import triangle_error
    directory=Path(geometry_dir); report_path=directory.parent/"stove-visuals-report.json"
    report={"schemaVersion":1,"status":"pending","nativeApplied":False,"renderedVerified":False,"packagedVerified":False}
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem); levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assets=unreal.EditorAssetLibrary; transaction="BreziStoveTransaction="+uuid.uuid4().hex
    before_flags={}; before_metadata={}; before=None; previous=[]; map_path=None

    def write(status):
        report.update(status=status,generatedAt=datetime.now(timezone.utc).isoformat())
        temporary=report_path.with_suffix(".tmp"); temporary.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n"); temporary.replace(report_path)

    def reload_map():
        require(levels.save_current_level(),"Stove map save failed")
        require(unreal.EditorLoadingAndSavingUtils.new_blank_map(False),"Stove staging map unload failed")
        require(levels.load_level(map_path),"Stove staging map reload failed")

    def transaction_actors():
        return [a for a in actors.get_all_level_actors() if a.actor_has_tag(transaction)]

    def measure(active):
        originals=source_components(unreal,detail["sourceRecords"])
        require(invariants(unreal,originals) == before,"Canonical stove mesh/transform/tags/collision changed")
        for id_,(_,component) in originals.items():
            expected=HIDDEN if active and id_ in detail["hiddenProxyIds"] else before_flags[id_]
            require(flags(component) == expected,"Canonical stove visibility differs: "+id_)
        found={}; evidence=[]
        for actor in transaction_actors():
            require(actor.actor_has_tag(TAG) and assets.get_metadata_tag(actor,"BreziGeneratedBy") == OWNER,"Stove actor ownership missing")
            components=actor.get_components_by_class(unreal.StaticMeshComponent); require(len(components)==1,"Stove derivative component count differs")
            component=components[0]; mesh=component.get_editor_property("static_mesh")
            id_=assets.get_metadata_tag(actor,"BreziStoveMeshId"); require(id_ in records and id_ not in found,"Unexpected stove visual ID")
            record=records[id_]; found[id_]=actor
            require(mesh and mesh.get_path_name() == mesh_paths[id_] and assets.get_metadata_tag(mesh,"BreziGeneratedBy") == OWNER,"Stove saved mesh binding differs")
            require(str(component.get_collision_profile_name()) == "NoCollision" and component.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION
                    and not component.get_editor_property("can_ever_affect_navigation") and not mesh.get_editor_property("has_navigation_data"),"Stove visual gained collision/navigation")
            tags=[str(t) for t in actor.get_editor_property("tags")]+[str(t) for t in component.get_editor_property("component_tags")]
            require(not any(t.startswith(("DOM_","BreziSourceObjectId=","COLL_","BreziWalkSurface")) for t in tags),"Stove visual acquired a canonical collision identity")
            require(bool(component.get_editor_property("visible")) is active and bool(component.get_editor_property("hidden_in_game")) is (not active),"Stove derivative visibility differs")
            require(mesh.get_num_triangles(0)==record["triangles"] and mesh.get_num_tex_coords(0)>=1
                    and not mesh.get_editor_property("nanite_settings").get_editor_property("enabled"),"Stove native topology/UV/build settings differ")
            material=mesh.get_material(0)
            require(material and material.get_path_name()==material_paths[record["role"]]
                    and assets.get_metadata_tag(material,"BreziStoveRole")==record["role"],"Stove saved material binding differs")
            flame_material=validate_flame_material(unreal,material) if record["role"]=="flames" else None
            local=list(unreal.BreziCollisionAudit.read_lod0_triangles(mesh))
            require(len(local)==record["triangles"]*3,"Stove read-only native triangle reader unavailable/incomplete")
            transform=component.get_world_transform()
            points=[unreal.MathLibrary.transform_location(transform,p) for p in local]
            actual=[(float(p.x),float(p.y),float(p.z)) for p in points]
            cx,cy=detail["stoveAxisSourceMm"]
            expected=[((p[0]+cx)/10,-(p[1]+cy)/10,p[2]/10) for p in record["sourceRelativeVerticesMm"]]
            error=triangle_error([tuple(expected[i:i+3]) for i in range(0,len(expected),3)],
                                 [tuple(actual[i:i+3]) for i in range(0,len(actual),3)],tolerance=0.005)
            # Reapply actual native vertex containment independently of bounds.
            check=generator().Mesh(id_,record["role"]); check.positions=[(p[0]*10-cx,-p[1]*10-cy,p[2]*10) for p in actual]; check.indices=list(range(len(actual)))
            generator().validate_vertices([check])
            evidence.append({"id":id_,"mesh":mesh.get_path_name(),"material":material.get_path_name(),"triangles":record["triangles"],"maxNativeTriangleErrorCm":error,"collision":"NoCollision","navigation":False,
                             **({"flameMaterial":flame_material} if flame_material else {})})
        require(found.keys()==records.keys(),"Saved stove derivative coverage differs")
        return evidence

    write("pending")
    try:
        detail,output=verify_inputs(scene,directory); records={r["id"]:r for r in detail["objects"]}
        pipeline_files=[Path(__file__),Path(__file__).with_name("stove-visuals")/"generate.py",Path(__file__).with_name("stove-visuals")/"flame.hlsl",
                        Path(__file__).with_name("stove-visuals")/"char.hlsl",output/"stove-visuals.json",output/detail["file"],
                        ROOT/"unreal/BreziTwin/Source/BreziTwin/BreziCollisionAudit.h",ROOT/"unreal/BreziTwin/Source/BreziTwin/BreziCollisionAudit.cpp"]
        hashes={str(p.relative_to(ROOT)):sha(p) for p in pipeline_files}
        version=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()[:16]
        writer=Writer(unreal,PREFIX+"/V_"+version)
        originals=source_components(unreal,detail["sourceRecords"])
        before=invariants(unreal,originals); before_flags={id_:flags(c) for id_,(_,c) in originals.items()}
        before_metadata={id_:{key:assets.get_metadata_tag(actor,key) for key in ("BreziStoveOriginalFlags","BreziStoveVisualRevision")}
                         for id_,(actor,_) in originals.items()}
        for actor in actors.get_all_level_actors():
            if actor.actor_has_tag(TAG):
                require(assets.get_metadata_tag(actor,"BreziGeneratedBy")==OWNER,"Unowned prior stove visual layer")
                previous.append((actor.get_path_name(),flags(actor.get_component_by_class(unreal.StaticMeshComponent))))
        world=unreal.EditorLevelLibrary.get_editor_world(); map_path=world.get_path_name().split(".")[0]
        require(map_path=="/Game/Brezi/Maps/Brezi","Stove stage requires saved owned Brezi map")
        require(assets.get_metadata_tag(world,"BreziGeneratedBy")=="scripts/unreal/import_scene.py","Refusing to save an unowned map")
        del world,originals
        registry=unreal.AssetRegistryHelpers.get_asset_registry(); registry.scan_paths_synchronous([writer.prefix,"/Interchange/Pipelines"],force_rescan=True)
        for path in assets.list_assets(writer.prefix,recursive=True,include_folder=False): writer.owned(path)
        for role in ("shell","chamber","logs","flames"): writer.material(role)
        material_paths={role:m.get_path_name() for role,m in writer.materials.items()}
        pipeline_path=writer.prefix+"/Pipeline/StoveAssets"
        pipeline=writer.owned(pipeline_path)
        if pipeline is None: pipeline=assets.duplicate_asset("/Interchange/Pipelines/DefaultGLTFSceneAssetsPipeline.DefaultGLTFSceneAssetsPipeline",pipeline_path)
        require(pipeline is not None,"Stove Interchange pipeline unavailable")
        assets.set_metadata_tag(pipeline,"BreziGeneratedBy",OWNER)
        pipeline.set_editor_property("use_source_name_for_asset",False)
        mp=pipeline.get_editor_property("mesh_pipeline")
        for key,value in {"combine_static_meshes_behavior":unreal.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE,"collision":False,"build_nanite":False,"generate_lightmap_u_vs":False}.items(): mp.set_editor_property(key,value)
        common=pipeline.get_editor_property("common_meshes_properties")
        for key,value in {"remove_degenerates":False,"recompute_normals":False,"recompute_tangents":True,"use_high_precision_tangent_basis":True,"use_full_precision_u_vs":True}.items(): common.set_editor_property(key,value)
        pipeline.get_editor_property("material_pipeline").set_editor_property("import_materials",False)
        pipeline.get_editor_property("material_pipeline").get_editor_property("texture_pipeline").set_editor_property("import_textures",False)
        writer.save(pipeline)
        manager=unreal.InterchangeManager.get_interchange_manager_scripted(); params=unreal.ImportAssetParameters()
        for key,value in {"is_automated":True,"replace_existing":True,"force_show_dialog":False,"override_pipelines":[unreal.SoftObjectPath(pipeline.get_path_name())]}.items(): params.set_editor_property(key,value)
        before_actors={a.get_path_name() for a in actors.get_all_level_actors()}
        require(manager.import_asset(writer.prefix+"/Meshes",manager.create_source_data(str(output/detail["file"])),params),"Stove asset-only import failed")
        require(before_actors=={a.get_path_name() for a in actors.get_all_level_actors()},"Stove asset import spawned unauthorized actors")
        registry.scan_paths_synchronous([writer.prefix],force_rescan=True); mesh_paths={}
        for path in assets.list_assets(writer.prefix+"/Meshes",recursive=True,include_folder=False):
            mesh=assets.load_asset(path); require(isinstance(mesh,unreal.StaticMesh),"Unexpected stove imported asset")
            writer.save(mesh) # Claim fresh import before subsequent checks can fail.
            matches=[id_ for id_ in records if id_ in mesh.get_name()]
            require(len(matches)==1 and matches[0] not in mesh_paths,"Merged/unexpected stove mesh")
            id_=matches[0]; mesh_paths[id_]=mesh.get_path_name(); record=records[id_]
            mesh.set_editor_property("has_navigation_data",False); mesh.set_material(0,writer.materials[record["role"]]); writer.save(mesh)
            actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(),unreal.Rotator()); require(actor is not None,"Stove visual spawn failed")
            actor.set_editor_property("tags",[unreal.Name(t) for t in ("BreziGenerated",TAG,transaction,detail["revision"])])
            actor.set_actor_label("Kachle · "+record["role"]); actor.set_folder_path("Brezi/VisualDetails/Stove")
            assets.set_metadata_tag(actor,"BreziGeneratedBy",OWNER); assets.set_metadata_tag(actor,"BreziStoveMeshId",id_)
            assets.set_metadata_tag(actor,"BreziVisualOf",json.dumps(detail["hiddenProxyIds"]))
            component=actor.get_component_by_class(unreal.StaticMeshComponent)
            component.set_visibility(False); component.set_hidden_in_game(True)
            component.set_collision_profile_name("NoCollision"); component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            component.set_editor_property("can_ever_affect_navigation",False); component.set_static_mesh(mesh)
            component.set_mobility(unreal.ComponentMobility.STATIC)
            if record["role"]=="flames":
                for key in ("cast_shadow","cast_hidden_shadow","affect_dynamic_indirect_lighting","affect_distance_field_lighting","affect_indirect_lighting_while_hidden"):
                    component.set_editor_property(key,False)
        require(mesh_paths.keys()==records.keys(),"Stove derivative import coverage differs")
        del actor,component
        # Stage must survive a real map unload/reload while all original visual
        # components keep their exact previous flags and query collision.
        reload_map(); report["stagedReloadEvidence"]=measure(False)
        for id_,(actor,component) in source_components(unreal,detail["sourceRecords"]).items():
            if id_ in detail["hiddenProxyIds"]:
                if not assets.get_metadata_tag(actor,"BreziStoveOriginalFlags"):
                    assets.set_metadata_tag(actor,"BreziStoveOriginalFlags",json.dumps(before_flags[id_],sort_keys=True))
                assets.set_metadata_tag(actor,"BreziStoveVisualRevision",detail["revision"]); set_flags(component,HIDDEN)
        for actor in transaction_actors():
            component=actor.get_component_by_class(unreal.StaticMeshComponent); component.set_hidden_in_game(False); component.set_visibility(True)
        for actor in actors.get_all_level_actors():
            if actor.get_path_name() in {path for path,_ in previous}:
                c=actor.get_component_by_class(unreal.StaticMeshComponent); c.set_visibility(False); c.set_hidden_in_game(True)
                del c
        del actor,component
        reload_map(); report["activeReloadEvidence"]=measure(True)
        # Keep prior owned layers hidden so rollback never needs to recreate an
        # actor that was deleted after the final successful verification.
        require(invariants(unreal,source_components(unreal,detail["sourceRecords"]))==before,"Stove commit changed canonical geometry/collision")
        report.update(nativeApplied=True,revision=detail["revision"],sourceManifestSha256=detail["sourceManifestSha256"],sourceObjSha256=detail["sourceObjSha256"],
                      sourceObjectIds=detail["hiddenProxyIds"],originalObjectsDeleted=0,originalProxyObjectsHidden=7,derivativeObjects=4,
                      previousLayersRetainedHidden=len(previous),
                      collisionAuthorityPreserved=True,canonicalInvariants=before,originalVisibilityBefore=before_flags,
                      assetHashes=_asset_hashes(writer.paths),pipelineFiles=hashes,savedReloaded=True,transactionTag=transaction,
                      limitations=detail["limitations"]+["No calibrated fire light is added; emitted scalar values are an authored appearance approximation."])
        write("stove-visuals-saved-reloaded-validated"); return report
    except Exception as error:
        rollback_errors=[]
        try:
            if map_path and unreal.EditorLevelLibrary.get_editor_world().get_path_name().split(".")[0]!=map_path: require(levels.load_level(map_path),"Rollback map load failed")
            for id_,(actor,component) in source_components(unreal,before_flags).items():
                set_flags(component,before_flags[id_])
                for key,value in before_metadata.get(id_,{}).items(): assets.set_metadata_tag(actor,key,value)
            for actor in list(actors.get_all_level_actors()):
                if actor.actor_has_tag(transaction): require(actors.destroy_actor(actor),"Rollback derivative destroy failed")
                for path,previous_flags in previous:
                    if actor.get_path_name()==path: set_flags(actor.get_component_by_class(unreal.StaticMeshComponent),previous_flags)
            if map_path: require(levels.save_current_level(),"Rollback map save failed")
        except Exception as rollback_error: rollback_errors.append(str(rollback_error))
        report.update(error=str(error),rollbackErrors=rollback_errors,nativeApplied=False); write("failed"); raise


def restore_stove_source_visibility():
    """Explicit reversible visual-layer removal; keeps all generated asset files."""
    import unreal
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem); assets=unreal.EditorAssetLibrary
    world=unreal.EditorLevelLibrary.get_editor_world()
    require(world.get_path_name().split(".")[0]=="/Game/Brezi/Maps/Brezi"
            and assets.get_metadata_tag(world,"BreziGeneratedBy")=="scripts/unreal/import_scene.py","Refusing to restore an unowned map")
    found=source_components(unreal,generator().GUARDS)
    restorations=[]
    for _,(actor,component) in found.items():
        text=assets.get_metadata_tag(actor,"BreziStoveOriginalFlags")
        require(bool(text),"Missing owned original stove visibility state")
        original=json.loads(text); require(set(original)==set(FLAGS) and all(isinstance(v,bool) for v in original.values()),"Invalid original stove flags")
        restorations.append((component,original))
    layers=[]
    for actor in list(actors.get_all_level_actors()):
        if actor.actor_has_tag(TAG):
            require(assets.get_metadata_tag(actor,"BreziGeneratedBy")==OWNER,"Unowned stove layer cannot be removed")
            layers.append(actor)
    for component,original in restorations: set_flags(component,original)
    for actor in layers: require(actors.destroy_actor(actor),"Stove visual removal failed")
    require(unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(),"Restored stove map save failed")
    path=ROOT/"output/unreal/stove-visuals-report.json"
    path.write_text(json.dumps({"schemaVersion":1,"status":"source-visuals-restored","nativeApplied":False,
        "sourceProxiesRestored":len(restorations),"ownedVisualActorsRemoved":len(layers),
        "generatedAssetsDeleted":False,"parentImportReceiptMustBeRegenerated":True},indent=2)+"\n")
