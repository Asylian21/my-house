"""Bounded native graph API smoke: four stove materials, no map/mesh mutation."""
import hashlib
import json
import sys
import uuid
from pathlib import Path
import unreal

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"scripts/unreal"))
from stove_visuals import Writer,require,sha,validate_flame_material

token=uuid.uuid4().hex[:12]
output=ROOT/"output/unreal/stove-material-smoke"/token
output.mkdir(parents=True,exist_ok=True)
prefix="/Game/Brezi/VisualDetails/Stove/MaterialSmoke_"+token
map_file=ROOT/"unreal/BreziTwin/Content/Brezi/Maps/Brezi.umap"
state={"schemaVersion":1,"status":"pending","namespace":prefix,"mapFileSha256Before":sha(map_file),
       "writerSha256":sha(ROOT/"scripts/unreal/stove_visuals.py"),"smokeScriptSha256":sha(__file__),
       "nativeGraphApiVerified":False,"cookedMetalVerified":False,"renderedVerified":False,"passes":[]}
lib=unreal.MaterialEditingLibrary


def save():
    (output/"report.json").write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n")


def inspect(material,role):
    expressions=list(lib.get_material_expressions(material))
    properties=("EMISSIVE_COLOR","OPACITY") if role=="flames" else ("BASE_COLOR","ROUGHNESS","METALLIC")+(("EMISSIVE_COLOR",) if role=="logs" else ())
    outputs={}
    for name in properties:
        source=lib.get_material_property_input_node(material,getattr(unreal.MaterialProperty,"MP_"+name))
        require(source is not None,"Native material property is unbound: "+role+"/"+name)
        outputs[name]=source.get_class().get_name()
    customs=[e for e in expressions if isinstance(e,unreal.MaterialExpressionCustom)]
    require(len(customs)==(1 if role in ("logs","flames") else 0),"Unexpected native Custom node count")
    nodes=[]
    for expression in expressions:
        names=list(lib.get_material_expression_input_names(expression))
        inputs=list(lib.get_inputs_for_material_expression(material,expression))
        require(len(names)==len(inputs),"Native expression input readback differs")
        if isinstance(expression,(unreal.MaterialExpressionCustom,unreal.MaterialExpressionComponentMask,unreal.MaterialExpressionMultiply)):
            require(inputs and all(value is not None for value in inputs),"Native graph has an unbound required expression input")
        if isinstance(expression,unreal.MaterialExpressionComponentMask):
            require(len(inputs)==1 and inputs[0] in customs,"Mask is not connected to the intended Custom output")
        nodes.append({"type":expression.get_class().get_name(),"inputNames":names,
                      "inputSources":[value.get_class().get_name() if value else None for value in inputs],
                      "outputNames":list(lib.get_material_expression_output_names(expression))})
    errors=list(lib.recompile_material(material)); require(not errors,"Native graph recompile failed: "+str(errors))
    flame_material=validate_flame_material(unreal,material) if role=="flames" else None
    return {"role":role,"asset":material.get_path_name(),"expressionCount":len(expressions),"outputs":outputs,"nodes":nodes,"compileErrors":errors,
            **({"flameMaterial":flame_material} if flame_material else {})}


save()
try:
    writer=Writer(unreal,prefix)
    for iteration in (1,2):
        graphs=[]
        for role in ("shell","chamber","logs","flames"):
            graphs.append(inspect(writer.material(role),role))
        state["passes"].append({"iteration":iteration,"graphs":graphs}); save()
    require([g["expressionCount"] for g in state["passes"][0]["graphs"]]==[g["expressionCount"] for g in state["passes"][1]["graphs"]],"Repeated material generation grew the graphs")
    state["mapFileSha256After"]=sha(map_file)
    require(state["mapFileSha256After"]==state["mapFileSha256Before"],"Material-only smoke changed the map")
    state.update(status="native-stove-graph-api-smoke-validated",nativeGraphApiVerified=True)
    save(); unreal.log("BREZI_STOVE_MATERIAL_SMOKE "+json.dumps({"status":state["status"],"report":str(output/"report.json"),"graphs":4,"passes":2}))
except Exception as error:
    state.update(status="failed",error=str(error));save();raise
