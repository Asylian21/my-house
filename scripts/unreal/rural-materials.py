"""Native rural-context materials; no changes to the canonical house.

Call ``build_materials(road_yaw_degrees=0)`` inside Unreal. Returned keys are
road, soil, field, curb, iron, steel, marker, drygrass, weed, leaf, bark, lamp.
World-position coordinates are UE centimetres. The road's yaw is in the UE XY
plane and aligns the LONG paver edge; positive yaw rotates X towards Y.

These are authored visual approximations, not measured material specimens.
The photographic CC0 detail uses existing hash-checked Poly Haven
gravel_floor_02 and concrete_pavement inputs. Plant materials assume opaque
leaf/blade geometry, not rectangular alpha cards. No WPO, displacement,
collision, actor transforms or landscape heights are changed here.
"""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = "scripts/unreal/rural-materials.py"
PREFIX = "/Game/Brezi/Rural20260923"
KEYS = ("road", "soil", "field", "curb", "iron", "steel", "marker",
        "drygrass", "weed", "leaf", "bark", "lamp")
PAVER_FACE_CM = (20.0, 10.0)
PAVER_JOINT_CM = 0.3


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def enum_value(kind, token):
    # Python's camel-case enum spelling differs across UE distributions.
    names = [name for name in dir(kind) if name.replace("_", "").replace("MSM", "").replace("MATUSAGE", "") == token]
    require(len(names) == 1, "Unresolved rural material enum: " + token)
    return getattr(kind, names[0])


def gravel_inputs():
    """Verify existing project provenance before importing any texture."""
    lock = json.loads((ROOT / "scripts/archviz/assets.lock.json").read_text())
    require(lock["license"] == "CC0-1.0", "Unexpected gravel license")
    source = lock["assets"]["gravel_floor_02"]
    require(source["tileSizeMetres"] == 2, "Unexpected gravel scan metric scale")
    maps = {}
    for role in ("diffuse", "normal", "roughness"):
        spec = source["maps"][role]
        path = ROOT / "output/archviz/assets" / spec["path"]
        require(path.resolve().is_relative_to(ROOT) and path.is_file(),
                "Missing local gravel scan: " + str(path))
        data = path.read_bytes()
        require(len(data) == spec["size"] and hashlib.md5(data).hexdigest() == spec["md5"],
                "Gravel scan differs from project lock: " + str(path))
        maps[role] = {"path": str(path), "sha256": hashlib.sha256(data).hexdigest()}
    return {"license": lock["license"], "page": source["page"],
            "authors": source["authors"], "periodCm": 200.0, "maps": maps}


def concrete_inputs():
    """Use the existing pinned concrete scan, not its photographed tile grid."""
    source = json.loads((ROOT / "scripts/unreal/archviz-material-inputs.json").read_text())["assets"]["concrete_pavement"]
    require(source["license"] == "CC0-1.0", "Unexpected concrete scan license")
    maps = {}
    for role, original in (("diffuse", "albedo"), ("normal", "normal"), ("roughness", "roughness")):
        spec = source["maps"][original]
        path = ROOT / spec["path"]
        require(path.resolve().is_relative_to(ROOT) and path.is_file(), "Missing local concrete scan")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == spec["sha256"], "Concrete scan differs from source pin")
        maps[role] = {"path": str(path), "sha256": spec["sha256"]}
    return {"license": source["license"], "page": source["page"], "authors": source["authors"],
            "periodCm": 180.0, "maps": maps, "sampleRegion": "20x10cm crop inside 60x30cm source slabs; photographed joints excluded"}


# Smooth value noise is authored here. No downloaded shader or texture is
# assigned photographic provenance. All microstructure fades before aliasing.
NOISE = r"""
struct RuralNoise {
    float hash(float2 p) {
        float3 p3=frac(float3(p.xyx)*.1031);
        p3+=dot(p3,p3.yzx+33.33);
        return frac((p3.x+p3.y)*p3.z);
    }
    float value(float2 p) {
        float2 i=floor(p),f=frac(p); f=f*f*(3.0-2.0*f);
        return lerp(lerp(hash(i),hash(i+float2(1,0)),f.x),
                    lerp(hash(i+float2(0,1)),hash(i+float2(1,1)),f.x),f.y);
    }
}; RuralNoise rn;
"""

ROAD_COORDS = r"""
float a=YawDegrees*.017453292519943295;
float3 T=float3(cos(a),sin(a),0),B=float3(-sin(a),cos(a),0);
float2 q=float2(dot(Position,T),dot(Position,B));
// Nominal paver FACE 200 x 100 mm, with an additional 3 mm sand joint.
float2 pitch=float2(20.3,10.3);
float row=floor(q.y/pitch.y);
float2 staggered=float2(q.x+frac(row*.5)*pitch.x,q.y);
float2 cell=floor(staggered/pitch),p=frac(staggered/pitch)*pitch;
float2 edge=min(p,pitch-p);
float d=min(edge.x,edge.y);
float pixelCm=max(max(fwidth(q.x),fwidth(q.y)),.002);
float brick=smoothstep(.15-pixelCm*.5-.035,.15+pixelCm*.5+.035,d);
float resolved=1.0-smoothstep(2.0,9.0,pixelCm);
// Limit under-resolved joints to their area coverage instead of moire.
float areaCoverage=(20.0*10.0)/(20.3*10.3);
brick=lerp(areaCoverage,brick,resolved);
"""

ROAD_COLOR = NOISE + ROAD_COORDS + r"""
float variation=(rn.hash(cell+float2(37,91))-.5)*.40*resolved;
float weather=(rn.value(q/95.0)-.5)*.13;
// Preserve photographed aggregate contrast, with a neutral concrete tint.
float3 scanned=clamp(Scan/float3(.21696059,.17902882,.13719591),.28,2.25);
float3 concrete=float3(.238,.241,.235)*lerp(float3(1,1,1),scanned,.72)*(1.0+variation+weather);
float dust=smoothstep(.56,.83,rn.value(q/72.0+17.0))*.24;
concrete=lerp(concrete,float3(.28,.253,.213),dust);
float edgeWear=(1.0-smoothstep(.14,.57,d))*.17*resolved;
concrete=lerp(concrete,float3(.30,.292,.271),edgeWear);
float3 sand=float3(.114,.102,.082)*(1.0+(rn.value(q*1.7)-.5)*.26);
return lerp(sand,concrete,brick);
"""

ROAD_SCAN_UV = NOISE + ROAD_COORDS + r"""
float sourceRow=floor(rn.hash(cell+float2(17,39))*6.0);
float sourceCol=floor(rn.hash(cell+float2(53,7))*3.0);
float stagger=(1.0-frac(sourceRow*.5)*2.0)*.5;
float2 offset=float2(.036+rn.hash(cell+2.0)*.11,.035+rn.hash(cell+5.0)*.016);
return float2((sourceCol+stagger)/3.0,sourceRow/6.0)+offset+p/180.0;
"""

ROAD_NORMAL = NOISE + ROAD_COORDS + r"""
float2 direction=(edge.x<edge.y)?float2(p.x<pitch.x*.5?1:-1,0)
                                     :float2(0,p.y<pitch.y*.5?1:-1);
float bevel=smoothstep(.08,.19,d)*(1.0-smoothstep(.19,.48,d));
float bevelFade=1.0-smoothstep(.12,.85,pixelCm);
float2 fine=q*6.0;
float2 grain=float2(rn.value(fine+float2(.2,0))-rn.value(fine-float2(.2,0)),
                    rn.value(fine+float2(0,.2))-rn.value(fine-float2(0,.2)));
float microFade=1.0-smoothstep(.04,.16,pixelCm);
float2 slope=direction*bevel*.30*bevelFade+grain*.13*microFade;
float strength=.48*brick;
return normalize(NormalWS*max(MapNormal.z,.45)+T*(MapNormal.x*strength-slope.x)+B*(MapNormal.y*strength-slope.y));
"""

ROAD_ROUGH = NOISE + ROAD_COORDS + r"""
return clamp(.76+RoughnessScan.r*.14+(rn.hash(cell)-.5)*.045*resolved+(1.0-brick)*.07,.79,.97);
"""

ROAD_AO = ROAD_COORDS + "return lerp(.76,1.0,brick);"

SOIL_BASE = NOISE + r"""
float2 q=Position.xy;
float patch=rn.value(q/240.0);
float broad=smoothstep(.23,.76,rn.value(q/470.0));
float grit=smoothstep(.50,.83,patch)*.38+.025;
float lum=dot(Scan,float3(.2126,.7152,.0722));
float3 earth=lerp(float3(.077,.054,.033),float3(.238,.181,.118),broad);
float clods=lerp(.70,1.17,rn.value(q/17.0));
float detail=lerp(.67,1.23,saturate(lum*2.3))*clods;
float3 soil=earth*detail;
float3 gravel=Scan*float3(.71,.61,.47);
return lerp(soil,gravel,grit);
"""

FIELD_BASE = NOISE + r"""
float2 q=Position.xy;
// Filter in each detail's physical coordinate space. At grazing angles a
// single pixel can span tens of metres; unfiltered noise then makes stripes.
float pixelCm=max(length(ddx(q)),length(ddy(q)));
float2 fieldUV=q/float2(7400.0,3600.0);
float fieldFootprint=max(length(ddx(fieldUV)),length(ddy(fieldUV)));
float fieldFade=1.0-smoothstep(.12,.42,fieldFootprint);
float2 broadUV=q/1400.0;
float broadFootprint=max(length(ddx(broadUV)),length(ddy(broadUV)));
float broadFade=1.0-smoothstep(.12,.42,broadFootprint);
float2 middleUV=q/250.0;
float middleFootprint=max(length(ddx(middleUV)),length(ddy(middleUV)));
float middleFade=1.0-smoothstep(.12,.42,middleFootprint);
float scanFade=1.0-smoothstep(1.5,16.0,pixelCm);
// A coherent agricultural ground color, not independent dark-earth / green
// cells. Macro variation is at most a few percent and stays subordinate to
// the real verge meshes, trees and their shadows, including from above.
float longVariation=(rn.value(fieldUV+float2(71,13))-.5)*.040*fieldFade;
float broadVariation=(rn.value(broadUV)-.5)*.030*broadFade;
float smallVariation=(rn.value(middleUV)-.5)*.030*middleFade;
float scanLum=saturate(dot(Scan,float3(.2126,.7152,.0722))*2.0);
float scanVariation=(scanLum-.5)*.060*scanFade;
// Sparse shallow cultivation at 72cm pitch, only while it is resolved.
// Its +/-1% contrast cannot become a conspicuous distant striped texture.
float rowCoordinate=dot(q,float2(.93969262,.34202014))/72.0;
float rowFootprint=max(abs(ddx(rowCoordinate)),abs(ddy(rowCoordinate)));
float rowFade=1.0-smoothstep(.12,.40,rowFootprint);
float cultivation=sin(rowCoordinate*6.28318530718)*.010*rowFade;
float variation=longVariation+broadVariation+smallVariation+scanVariation+cultivation;
return float3(.149,.139,.090)*(1.0+variation);
"""

FIELD_NORMAL = r"""
float3 N=normalize(NormalWS);
float3 T=normalize(float3(1,0,0)-N*N.x),B=normalize(cross(N,T));
float pixelCm=max(length(ddx(Position.xy)),length(ddy(Position.xy)));
float strength=.25*(1.0-smoothstep(1.5,16.0,pixelCm));
return normalize(N+T*MapNormal.x*strength+B*MapNormal.y*strength);
"""

FIELD_ROUGH = r"""
float pixelCm=max(length(ddx(Position.xy)),length(ddy(Position.xy)));
float scanFade=1.0-smoothstep(1.5,16.0,pixelCm);
return lerp(.94,clamp(.82+Scan.r*.14,.84,.98),scanFade);
"""

SOIL_NORMAL = NOISE + r"""
float3 N=normalize(NormalWS);
float3 T=normalize(float3(1,0,0)-N*N.x),B=normalize(cross(N,T));
float patch=rn.value(Position.xy/240.0);
float strength=lerp(.13,.44,smoothstep(.43,.79,patch));
return normalize(N*max(MapNormal.z,.4)+T*MapNormal.x*strength+B*MapNormal.y*strength);
"""

SURFACE_DETAIL = NOISE + r"""
float3 N=normalize(NormalWS);
float3 A=abs(N.z)>.85?float3(1,0,0):float3(0,0,1);
float3 T=normalize(A-N*dot(A,N)),B=normalize(cross(N,T));
float2 q=float2(dot(Position,T),dot(Position,B));
float pixelCm=max(fwidth(q.x),fwidth(q.y));
float grainFade=1.0-smoothstep(.025,.11,pixelCm);
float2 g=float2(rn.value(q*7.0+float2(.2,0))-rn.value(q*7.0-float2(.2,0)),
                rn.value(q*7.0+float2(0,.2))-rn.value(q*7.0-float2(0,.2)));
return normalize(N-T*g.x*Strength*grainFade-B*g.y*Strength*grainFade)*FaceSign;
"""

PLANT_COLOR = NOISE + r"""
// Slow world variation plus per-instance variation, without vertex motion.
float variation=.84+rn.value(Position.xy/180.0)*.20+InstanceRandom*.12;
float veins=.98+.02*sin(Position.z*5.2+Position.x*1.3);
return Palette*variation*veins;
"""


class Writer:
    def __init__(self, unreal_module, source, yaw, concrete):
        self.u = unreal_module
        self.assets = self.u.EditorAssetLibrary
        self.lib = self.u.MaterialEditingLibrary
        self.source = source
        self.concrete = concrete
        self.yaw = yaw
        self.textures = {}
        self.source_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

    def node(self, material, role, cls, **properties):
        node = self.lib.create_material_expression(material, cls, -600, 0)
        require(node is not None, "Cannot create rural material node: " + role)
        node.set_editor_property("desc", "BreziRural:" + role)
        for key, value in properties.items():
            node.set_editor_property(key, value)
        return node

    def scalar(self, material, value):
        return self.node(material, "scalar", self.u.MaterialExpressionConstant, r=float(value))

    def vector(self, material, value):
        return self.node(material, "palette", self.u.MaterialExpressionConstant3Vector,
                         constant=self.u.LinearColor(*value, 1))

    def connect(self, source, output, target, pin):
        require(self.lib.connect_material_expressions(source, output, target, pin),
                "Cannot connect rural material pin: " + pin)

    def out(self, node, prop, output=""):
        require(self.lib.connect_material_property(node, output, getattr(self.u.MaterialProperty, "MP_" + prop)),
                "Cannot connect rural material property: " + prop)

    def custom(self, material, role, code, inputs, dimensions=3):
        pins = []
        for name in inputs:
            entry = self.u.CustomInput()
            entry.set_editor_property("input_name", name)
            pins.append(entry)
        node = self.node(material, role, self.u.MaterialExpressionCustom, code=code,
                         description=role, inputs=pins,
                         output_type=getattr(self.u.CustomMaterialOutputType, "CMOT_FLOAT" + str(dimensions)))
        for name, (source, channel) in inputs.items():
            self.connect(source, channel, node, name)
        return node

    def texture(self, role, asset="gravel"):
        cache_key = (asset, role)
        if cache_key in self.textures:
            return self.textures[cache_key]
        u = self.u
        source = self.source if asset == "gravel" else self.concrete
        spec = source["maps"][role]
        name = "T_" + asset.title() + "_" + role + "_" + spec["sha256"][:12]
        path = PREFIX + "/Textures/" + name
        if self.assets.does_asset_exist(path):
            texture = self.assets.load_asset(path)
            require(self.assets.get_metadata_tag(texture, "BreziGeneratedBy") == OWNER
                    and self.assets.get_metadata_tag(texture, "source_sha256") == spec["sha256"],
                    "Refusing foreign rural texture: " + path)
        else:
            task = u.AssetImportTask()
            for key, value in {"filename": spec["path"], "destination_path": PREFIX + "/Textures",
                               "destination_name": name, "automated": True,
                               "replace_existing": False, "save": False}.items():
                task.set_editor_property(key, value)
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            texture = self.assets.load_asset(path)
            require(isinstance(texture, u.Texture2D), "Gravel scan import failed: " + role)
            compression = (u.TextureCompressionSettings.TC_NORMALMAP if role == "normal" else
                           u.TextureCompressionSettings.TC_DEFAULT if role == "diffuse" else
                           u.TextureCompressionSettings.TC_MASKS)
            for key, value in {"srgb": role == "diffuse", "flip_green_channel": role == "normal",
                               "compression_settings": compression, "address_x": u.TextureAddress.TA_WRAP,
                               "address_y": u.TextureAddress.TA_WRAP, "lod_bias": 0,
                               "mip_gen_settings": u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP}.items():
                texture.set_editor_property(key, value)
            self.assets.set_metadata_tag(texture, "BreziGeneratedBy", OWNER)
            self.assets.set_metadata_tag(texture, "source_sha256", spec["sha256"])
            self.assets.set_metadata_tag(texture, "BreziSourceLicense", "CC0-1.0")
            self.assets.set_metadata_tag(texture, "BreziSourcePage", source["page"])
            require(self.assets.save_loaded_asset(texture, only_if_is_dirty=False), "Cannot save rural texture")
        self.textures[cache_key] = texture
        return texture

    def sample(self, material, role, uv, asset="gravel", derivatives=None):
        u = self.u
        sampler = (u.MaterialSamplerType.SAMPLERTYPE_COLOR if role == "diffuse" else
                   u.MaterialSamplerType.SAMPLERTYPE_NORMAL if role == "normal" else
                   u.MaterialSamplerType.SAMPLERTYPE_MASKS)
        node = self.node(material, asset + "-" + role, u.MaterialExpressionTextureSample,
                         texture=self.texture(role, asset), sampler_type=sampler)
        self.connect(uv, "", node, "UVs")
        if derivatives:
            node.set_editor_property("mip_value_mode", u.TextureMipValueMode.TMVM_DERIVATIVE)
            self.connect(derivatives[0], "", node, "DDX(UVs)")
            self.connect(derivatives[1], "", node, "DDY(UVs)")
        return node

    def create(self, key):
        u = self.u
        recipe = {"key": key, "sourceSha256": self.source_sha,
                  "provenance": "Project-authored procedural approximation",
                  "coordinateUnits": "UE centimetres"}
        if key == "road":
            recipe.update(yawDegrees=self.yaw, paverFaceCm=PAVER_FACE_CM,
                          sandJointCm=PAVER_JOINT_CM, bond="running-half", normal="scan aggregate and shaded bevel, no displacement",
                          concreteScan=self.concrete, paverToneRange=[.80, 1.20],
                          provenance="Authored 200x100mm paving with CC0 concrete scan cropped to exclude photographed joints")
        if key in ("soil", "field"):
            recipe.update(gravelScan=self.source, provenance="Authored earth palette mixed with CC0 gravel scan")
        encoded = json.dumps(recipe, sort_keys=True)
        name = "M_Rural_" + key + "_" + digest(recipe)[:12]
        path = PREFIX + "/Materials/" + name
        if self.assets.does_asset_exist(path):
            existing = self.assets.load_asset(path)
            require(self.assets.get_metadata_tag(existing, "BreziGeneratedBy") == OWNER
                    and self.assets.get_metadata_tag(existing, "BreziRuralRecipe") == encoded,
                    "Refusing foreign rural material: " + path)
            return existing
        material = u.AssetToolsHelpers.get_asset_tools().create_asset(
            name, PREFIX + "/Materials", u.Material, u.MaterialFactoryNew())
        require(material is not None, "Cannot create rural material: " + key)
        foliage = key in ("drygrass", "weed", "leaf")
        for prop, value in {"blend_mode": u.BlendMode.BLEND_OPAQUE,
                            "shading_model": enum_value(u.MaterialShadingModel, "TWOSIDEDFOLIAGE") if foliage else u.MaterialShadingModel.MSM_DEFAULT_LIT,
                            "two_sided": foliage, "tangent_space_normal": False}.items():
            material.set_editor_property(prop, value)
        self.lib.set_base_material_usage(material, enum_value(u.MaterialUsage, "INSTANCEDSTATICMESHES"), True)
        if not foliage:
            self.lib.set_base_material_usage(material, u.MaterialUsage.MATUSAGE_NANITE, True)
        pos = self.node(material, "world-position-cm", u.MaterialExpressionWorldPosition)
        normal = self.node(material, "vertex-normal", u.MaterialExpressionVertexNormalWS)
        c = {"Position": (pos, ""), "NormalWS": (normal, "")}
        if key == "road":
            args = {**c, "YawDegrees": (self.scalar(material, self.yaw), "")}
            uv = self.custom(material, "concrete-face-crop", ROAD_SCAN_UV, args, 2)
            dx = self.custom(material, "metric-concrete-ddx", ROAD_COORDS + "return ddx(q)/180.0;", args, 2)
            dy = self.custom(material, "metric-concrete-ddy", ROAD_COORDS + "return ddy(q)/180.0;", args, 2)
            scan = self.sample(material, "diffuse", uv, "concrete", (dx, dy))
            bump = self.sample(material, "normal", uv, "concrete", (dx, dy))
            rough = self.sample(material, "roughness", uv, "concrete", (dx, dy))
            args = {**args, "Scan": (scan, "RGB"), "MapNormal": (bump, "RGB"), "RoughnessScan": (rough, "RGB")}
            for prop, code, dims in (("BASE_COLOR", ROAD_COLOR, 3), ("NORMAL", ROAD_NORMAL, 3),
                                     ("ROUGHNESS", ROAD_ROUGH, 1), ("AMBIENT_OCCLUSION", ROAD_AO, 1)):
                self.out(self.custom(material, "paver-" + prop.lower(), code, args, dims), prop)
        elif key in ("soil", "field"):
            uv = self.custom(material, "metric-gravel-uv", "return Position.xy/200.0;", {"Position": (pos, "")}, 2)
            scan = self.sample(material, "diffuse", uv)
            bump = self.sample(material, "normal", uv)
            rough = self.sample(material, "roughness", uv)
            self.out(self.custom(material, "dry-earth-color", SOIL_BASE if key == "soil" else FIELD_BASE,
                                 {**c, "Scan": (scan, "RGB")}), "BASE_COLOR")
            self.out(self.custom(material, "aggregate-normal", FIELD_NORMAL if key == "field" else SOIL_NORMAL,
                                 {**c, "MapNormal": (bump, "RGB")}), "NORMAL")
            rough_inputs = {"Scan": (rough, "RGB")}
            if key == "field":
                rough_inputs["Position"] = (pos, "")
            self.out(self.custom(material, "dry-earth-roughness", FIELD_ROUGH if key == "field" else "return clamp(.82+Scan.r*.14,.84,.98);",
                                 rough_inputs, 1), "ROUGHNESS")
        else:
            # Scene-linear palette; deliberately matte dry vegetation and concrete.
            palettes = {"curb": ((.34, .337, .315), .88, 0),
                        "iron": ((.102, .099, .090), .73, .70),
                        "steel": ((.48, .50, .52), .53, .93),
                        "marker": ((.78, .24, .016), .79, 0),
                        "drygrass": ((.285, .221, .092), .93, 0),
                        "weed": ((.128, .148, .043), .87, 0),
                        "leaf": ((.080, .133, .035), .76, 0),
                        "bark": ((.100, .071, .041), .96, 0),
                        "lamp": ((.61, .65, .67), .45, 0)}
            palette, roughness, metallic = palettes[key]
            color = self.vector(material, palette)
            if foliage:
                rnd = self.node(material, "instance-random", u.MaterialExpressionPerInstanceRandom)
                color = self.custom(material, "natural-leaf-variation", PLANT_COLOR,
                                    {**c, "Palette": (color, ""), "InstanceRandom": (rnd, "")})
                self.out(self.vector(material, tuple(v * .55 for v in palette)), "SUBSURFACE_COLOR")
                self.out(self.scalar(material, .45), "OPACITY")
            elif key == "iron":
                code = NOISE + r"""
float patina=rn.value(Position.xy/3.4),pits=rn.value(Position.xy*2.0);
float top=saturate(NormalWS.z);
float3 cast=Palette*(.66+.32*patina+.16*pits);
float wear=smoothstep(.52,.81,rn.value(Position.xy/.57))*top;
return lerp(cast,float3(.145,.148,.144),wear*.43);
"""
                color = self.custom(material, "weathered-cast-iron", code, {**c, "Palette": (color, "")})
            elif key in ("curb", "bark"):
                code = NOISE + "return Palette*(.87+.18*rn.value(Position.xy/17.0)+.07*rn.value(Position.xz/2.4));"
                color = self.custom(material, "surface-variation", code, {**c, "Palette": (color, "")})
            self.out(color, "BASE_COLOR")
            if key == "iron":
                code = NOISE + "return clamp(.70+.16*rn.value(Position.xy/2.7)-.11*saturate(NormalWS.z)*rn.value(Position.xy/.57),.58,.88);"
                self.out(self.custom(material, "cast-iron-roughness", code, c, 1), "ROUGHNESS")
            else:
                self.out(self.scalar(material, roughness), "ROUGHNESS")
            self.out(self.scalar(material, metallic), "METALLIC")
            sign = self.node(material, "face-sign", u.MaterialExpressionTwoSidedSign)
            detail_code = SURFACE_DETAIL
            if key == "iron":
                detail_code = detail_code.replace("q*7.0", "q*1.4").replace("smoothstep(.025,.11,pixelCm)", "smoothstep(.07,.42,pixelCm)")
            detail = self.custom(material, "subtle-microsurface", detail_code,
                                 {**c, "Strength": (self.scalar(material, .08 if foliage else .38 if key == "iron" else .20), ""),
                                  "FaceSign": (sign, "")})
            self.out(detail, "NORMAL")
        if key in ("road", "soil", "field"):
            self.out(self.scalar(material, 0), "METALLIC")
        self.out(self.scalar(material, .35 if key in ("road", "soil", "field", "curb") else .5), "SPECULAR")
        errors = list(self.lib.recompile_material(material) or [])
        require(not errors, "Rural shader failed to compile: " + key + ": " + str(errors))
        self.assets.set_metadata_tag(material, "BreziGeneratedBy", OWNER)
        self.assets.set_metadata_tag(material, "BreziRuralRecipe", encoded)
        require(self.assets.save_loaded_asset(material, only_if_is_dirty=False), "Cannot save rural material: " + key)
        return material


def build_materials(road_yaw_degrees=0):
    """Create/reuse owned native assets and return the semantic material map.

    Does not launch an engine, mutate a level, or bind materials to existing
    house meshes. Native shader compilation errors fail the operation. A source
    or recipe change creates new assets rather than overwriting prior runs.
    """
    yaw = float(road_yaw_degrees)
    require(math.isfinite(yaw), "Road yaw must be finite")
    source = gravel_inputs()
    concrete = concrete_inputs()
    import unreal
    writer = Writer(unreal, source, yaw % 360.0, concrete)
    return {key: writer.create(key) for key in KEYS}


def verify_materials(materials):
    """Verify loaded materials; input is ``{key: asset_path_or_UObject}``.

    Call after saving and reloading the level/packages. Returns JSON-safe
    evidence; missing or foreign assets, disconnected graph roots and changed
    usage/shading/texture settings fail immediately. This is persistence proof,
    not a claim that the resulting rendered scene has passed visual review.
    """
    import unreal as u
    require(set(materials) == set(KEYS), "Rural material semantic coverage changed")
    assets, lib = u.EditorAssetLibrary, u.MaterialEditingLibrary
    source_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    results = {}
    for key in KEYS:
        material = assets.load_asset(materials[key]) if isinstance(materials[key], str) else materials[key]
        require(isinstance(material, u.Material), "Missing native rural material: " + key)
        require(material.get_path_name().startswith(PREFIX + "/Materials/"), "Rural material escaped owned namespace")
        require(assets.get_metadata_tag(material, "BreziGeneratedBy") == OWNER, "Foreign rural material: " + key)
        recipe = json.loads(assets.get_metadata_tag(material, "BreziRuralRecipe"))
        require(recipe["key"] == key and recipe["sourceSha256"] == source_sha, "Stale rural material recipe: " + key)
        foliage = key in ("drygrass", "weed", "leaf")
        flags = {"blend_mode": u.BlendMode.BLEND_OPAQUE, "two_sided": foliage,
                 "tangent_space_normal": False,
                 "shading_model": enum_value(u.MaterialShadingModel, "TWOSIDEDFOLIAGE") if foliage else u.MaterialShadingModel.MSM_DEFAULT_LIT}
        for prop, expected in flags.items():
            require(material.get_editor_property(prop) == expected, "Rural material flag mismatch: " + key + "/" + prop)
        instanced = lib.has_material_usage(material, enum_value(u.MaterialUsage, "INSTANCEDSTATICMESHES"))
        nanite = lib.has_material_usage(material, u.MaterialUsage.MATUSAGE_NANITE)
        require(instanced and (foliage or nanite), "Rural material usage flags missing: " + key)
        properties = ["BASE_COLOR", "ROUGHNESS", "NORMAL", "METALLIC", "SPECULAR"]
        if foliage:
            properties += ["SUBSURFACE_COLOR", "OPACITY"]
        if key == "road":
            require(recipe["paverFaceCm"] == [20.0, 10.0] and recipe["sandJointCm"] == .3,
                    "Native road physical paver scale changed")
            properties += ["AMBIENT_OCCLUSION"]
        roots = {}
        for prop in properties:
            node = lib.get_material_property_input_node(material, getattr(u.MaterialProperty, "MP_" + prop))
            require(node is not None, "Disconnected rural material property: " + key + "/" + prop)
            roots[prop] = node.get_editor_property("desc")
        textures = []
        if key in ("soil", "field", "road"):
            scan_key = "concreteScan" if key == "road" else "gravelScan"
            scan_tag = "concrete" if key == "road" else "gravel"
            for node in lib.get_material_expressions(material):
                if not isinstance(node, u.MaterialExpressionTextureSample):
                    continue
                texture = node.get_editor_property("texture")
                require(texture is not None, "Missing rural texture after reload")
                role = str(node.get_editor_property("desc")).removeprefix("BreziRural:" + scan_tag + "-")
                require(role in recipe[scan_key]["maps"], "Unexpected rural surface texture")
                spec = recipe[scan_key]["maps"][role]
                require(assets.get_metadata_tag(texture, "source_sha256") == spec["sha256"], "Rural texture identity changed")
                require(texture.get_editor_property("srgb") == (role == "diffuse")
                        and texture.get_editor_property("flip_green_channel") == (role == "normal"),
                        "Rural scan color/normal interpretation changed")
                if key == "road":
                    require(node.get_editor_property("mip_value_mode") == u.TextureMipValueMode.TMVM_DERIVATIVE,
                            "Paver scan lost continuous metric derivatives")
                textures.append({"role": role, "asset": texture.get_path_name(), "sha256": spec["sha256"]})
            require({item["role"] for item in textures} == {"diffuse", "normal", "roughness"}, "Rural texture coverage incomplete")
        results[key] = {"asset": material.get_path_name(), "instancedUsage": bool(instanced),
                        "naniteUsage": bool(nanite), "twoSided": foliage, "recipe": recipe,
                        "roots": roots, "textures": textures}
    return {"status": "verified-loaded-rural-materials", "materials": results,
            "visualAcceptance": "separate native render review required"}
