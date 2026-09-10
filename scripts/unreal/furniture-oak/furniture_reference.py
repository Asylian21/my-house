"""CPU-only exact nine-box contract; no geometry generation or Unreal imports."""
import hashlib
import importlib.util
import json
from functools import lru_cache
from pathlib import Path

ROOT=next(p for p in Path(__file__).resolve().parents if (p/"lib/twin-site.ts").is_file())
OWNER="scripts/unreal/furniture-oak/furniture_oak.py"
STUDY=ROOT/"output/unreal/furniture-detail-study/roof-surface-transfer-v3"
CANDIDATE_SHA="bbe532c50d6a0ca98472d48871fd3f7b589e8cb3780beddd1a3abe81be12742d"
KITCHEN_IDS=frozenset({"DOM_00613","DOM_00643","DOM_00647","DOM_00650"})
DINING_IDS=frozenset({"DOM_01328","DOM_01345","DOM_01354","DOM_01363","DOM_01372"})
IDS=KITCHEN_IDS|DINING_IDS
SLOTS={i:"MAT_0039" if i in KITCHEN_IDS else "MAT_0080" for i in IDS}
TV_IDS=frozenset({"DOM_01293","DOM_01296","DOM_01300"})
PERIOD_CM=183.00000429153442
ROUGH_MEAN=.5304041633418962
ROUGH_AMPLITUDE=.12
NORMAL_STRENGTH=.25


@lru_cache(maxsize=2)
def load_tv(name):
    path=Path(__file__).parent.parent/"tv-oak"/(name+".py")
    spec=importlib.util.spec_from_file_location("brezi_furniture_dependency_"+name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def require(value,message):
    if not value:raise ValueError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def basis(normal,grain):
    common=load_tv("oak_reference");n=common.normalize(normal)
    require(sum(abs(x)>1e-8 for x in n)==1,"Only the exact axial source boxes are supported")
    require(grain in ("verticalZ","longitudinalX"),"Unknown grain orientation")
    if grain=="verticalZ":return common.basis(n)
    axis=max(range(3),key=lambda i:abs(n[i]));sign=1 if n[axis]>0 else -1
    if axis==0:t,v=(0,-sign,0),(0,0,-1)
    elif axis==1:t,v=(0,0,sign),(1,0,0)
    else:t,v=(0,-sign,0),(1,0,0)
    require(common.cross(t,v)==n,"Longitudinal tangent basis is mirrored")
    return t,v,n


def project(position_cm,normal,anchor_cm,grain):
    common=load_tv("oak_reference");t,v,_=basis(normal,grain)
    p=tuple(a-b for a,b in zip(position_cm,anchor_cm))
    return common.dot(p,t)/PERIOD_CM,common.dot(p,v)/PERIOD_CM


def projected_normal(gl_normal,normal,grain,strength=NORMAL_STRENGTH):
    common=load_tv("oak_reference");t,v,n=basis(normal,grain)
    decoded=(gl_normal[0],-gl_normal[1],gl_normal[2])
    return common.normalize(tuple(t[i]*decoded[0]*strength+v[i]*decoded[1]*strength+n[i]*max(decoded[2],.001) for i in range(3)))


def material_profiles(candidate):
    common=load_tv("tv_oak")
    vertical=common.material_profile()["basisCode"]
    horizontal=Path(__file__).with_name("longitudinal-basis.hlsl").read_text()
    return {name:{"owner":OWNER,"materialName":material,"palette":candidate["materials"][slot]["paletteLinearMultiplier"],"basisCode":code}
            for name,material,slot,code in (("kitchen","M_KitchenPhotoOak","MAT_0039",vertical),
                                          ("dining","M_DiningPhotoOak","MAT_0080",horizontal))}


def verify_inputs(scene=None,geometry_dir=None):
    common=load_tv("oak_reference")
    geometry=Path(geometry_dir) if geometry_dir else ROOT/"output/unreal/geometry"
    base=common.verify_inputs(scene,geometry)
    path=STUDY/"candidate.json";require(sha(path)==CANDIDATE_SHA,"Pinned furniture proposal bytes differ")
    candidate=json.loads(path.read_text())
    require(set(candidate["scope"]["photoOverrideIds"])==IDS and candidate["scope"]["uniqueCandidateObjects"]==13,"Exact furniture material scope differs")
    require(set(candidate["scope"]["alreadyActiveTVOverridesToPreserve"])==TV_IDS,"Existing TV exclusions differ")
    for name in ("sourceBuilder","nativeMaterialRecipe"):
        source=candidate["pinnedInputs"][name]
        require(sha(ROOT/source["path"])==source["sha256"],"Pinned source authoring changed: "+name)
    plans={o["id"]:o for o in candidate["objects"]}
    for id_ in IDS:
        record=base["records"][id_]
        require(digest(record)==plans[id_]["sourceRecordSha256"],"Exact furniture record changed: "+id_)
        require(record["materialSlots"]==[SLOTS[id_]] and record["enabled"] is True and record["instances"]==1,"Furniture source slot/enabled/instance differs")
    for slot in ("MAT_0039","MAT_0080"):
        source=base["scene"]["materials"][slot];recipe=candidate["materials"][slot]
        require(digest(source)==recipe["sourceMaterialSha256"],"Source wood material changed")
        require(sha(ROOT/"public"/source["texture"].lstrip("/"))==recipe["sourceTextureSha256"],"Source wood texture bytes changed")
        require(source["roughness"]==recipe["authoredRoughnessMean"],"Authored roughness changed")
    boxes=common.read_boxes(geometry/"dom-mm.obj",base["records"],IDS,SLOTS)
    groups={}
    for name,selected,slot,grain in (("kitchen",KITCHEN_IDS,"MAT_0039","verticalZ"),("dining",DINING_IDS,"MAT_0080","longitudinalX")):
        records=base["records"]
        anchor=(min(records[i]["boundsMm"]["min"][0] for i in selected)/10,
                -max(records[i]["boundsMm"]["max"][1] for i in selected)/10,
                min(records[i]["boundsMm"]["min"][2] for i in selected)/10)
        groups[name]={"candidate":base["candidate"],"sourceRoughness":base["scene"]["materials"][slot]["roughness"],
                      "anchorCm":anchor,"sourceSlot":slot,"grain":grain,"selectedIds":sorted(selected)}
    require(set(base["woodIds"])>=IDS|TV_IDS and len(base["woodIds"])-len(IDS)==149,"Existing wood preservation scope changed")
    return {**base,"selectedIds":sorted(IDS),"boxes":boxes,"groups":groups,"profiles":material_profiles(candidate),
            "plans":{i:plans[i] for i in sorted(IDS)},"proposal":candidate,"preservedWoodObjects":149}


def expected_components(before,bindings):
    """Pure exact exception policy reused by native saved-reload acceptance."""
    require(set(bindings)==IDS,"Material binding map must contain the exact nine objects")
    require(set(before)>=IDS|TV_IDS,"Before snapshot lacks selected or protected TV objects")
    result={i:dict(values) for i,values in before.items()}
    for id_,material in bindings.items():
        require(isinstance(material,str) and material.startswith("/Game/Brezi/MaterialStudies/FurniturePhotoOak/"),"Binding escaped owned furniture namespace")
        result[id_].update(effectiveMaterial=material,overrides=[material])
    return result
