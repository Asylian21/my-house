"""Owned R6 firebox surfaces; no mutation of original materials or bindings.

The importer owns texture copying and five visual mesh bindings. This helper
only reads those two proven textures, reuses the exact shell material, and
creates four materials. The Blender study imports RECIPE and frame_state so
the reviewed animation and Unreal shader share frame selection and shaping.
Emission values are authored relative units, not measured fire photometry.
"""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/realism-stove-materials.py'
PREFIX = '/Game/Brezi/Realism/Stove/Materials'
TEXTURE_PREFIX = '/Game/Brezi/Realism/Stove/Fire/Textures'
TAG = 'BreziRealismStove:'
PROBE = ROOT/'output/unreal/realism-fire-texture-probe-20260926-r1/native-report.json'
SOURCE_IDS = [f'DOM_{i:05d}' for i in range(553, 572)]
RECIPE = {
    'kind': 'dual-phase-textured-additive-fire-v1', 'atlasGrid': 6,
    'frameMin': 0, 'frameMax': 35, 'cycleHz': .45, 'cardPhaseStep': .271,
    'phaseOffset': .5, 'uvInset': .006, 'uvScaleU': .988, 'uvScaleV': .954,
    'tipPower': .65, 'taperSlope': .45, 'taperStrength': 6,
    'rootFadeStart': .08, 'rootFadeEnd': .20, 'emissionStrength': 3,
    'tintStops': [[.015, [.12, .008, .0005]], [.25, [1, .1, .003]], [.85, [1, .7, .18]]],
    'nativeBlend': 'ADDITIVE', 'opacity': 1, 'textureAlphaUsed': False,
    'textureTransfer': 'sRGB decoded once by color sampler',
    'uvConvention': 'U=card*2+localU; V=0 bottom,1 top; atlas top-left',
    'worldPositionOffset': False, 'newLights': False,
}
SURFACES = {
    'chamber': {'baseLinear': [.009, .007, .006], 'roughness': .95, 'specular': .25, 'metallic': 0},
    'logs': {'baseLinear': [.014, .010, .008], 'roughness': .96, 'specular': .25, 'metallic': 0,
             'charCrackMultiplier': .35, 'crackEmission': 0, 'proceduralNotScan': True},
    'embers': {'baseLinear': [.016, .004, .001], 'roughness': .98, 'specular': .2, 'metallic': 0,
               'emissionLinear': [1, .025, .0006], 'maxEmission': .45,
               'texturePeriodCm': 7, 'maskStart': .035, 'maskEnd': .32},
}
TEXTURES = {
    'T_Fire_SubUV': {'size': [1024, 1024], 'sha256': '865a10d77419a7a5c80a89abbf2a738168cd79bfad1aab1397d3d5802ac6f33c'},
    'T_Fire_Tiled_D': {'size': [512, 512], 'sha256': '5fddf6ab9c5a32516248bdfce3cc9f2426a3b734d57f2c5bd1d26a93c6381252'},
}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def saturate(value):
    return max(0., min(1., value))


def smoothstep(low, high, value):
    t = saturate((value-low)/(high-low))
    return t*t*(3-2*t)


def frame_state(seconds, card=0):
    """Two adjacent-frame pairs; endpoint phases have zero contribution."""
    require(math.isfinite(seconds) and isinstance(card, int) and 0 <= card <= 2, 'Invalid flame time/card')
    result = []
    for offset in (0, RECIPE['phaseOffset']):
        p = (seconds*RECIPE['cycleHz']+card*RECIPE['cardPhaseStep']+offset) % 1
        frame = RECIPE['frameMin']+p*(RECIPE['frameMax']-RECIPE['frameMin'])
        low = math.floor(frame)
        result.append({'phase': p, 'low': low, 'high': min(low+1, RECIPE['frameMax']),
                       'fraction': frame-low, 'weight': math.sin(math.pi*p)**2})
    return result


def atlas_uv(frame, u, v):
    require(isinstance(frame, int) and 0 <= frame <= RECIPE['frameMax'], 'Invalid atlas frame')
    require(all(math.isfinite(x) and 0 <= x <= 1 for x in (u, v)), 'Invalid local flame UV')
    n = RECIPE['atlasGrid']
    return ((frame % n+RECIPE['uvInset']+u*RECIPE['uvScaleU'])/n,
            (frame//n+RECIPE['uvInset']+(1-v)*RECIPE['uvScaleV'])/n)


def envelope(u, v):
    return (max(1-v, 0)**RECIPE['tipPower']
            * saturate(RECIPE['taperStrength']*((1-RECIPE['taperSlope']*v)-abs(2*u-1)))
            * smoothstep(RECIPE['rootFadeStart'], RECIPE['rootFadeEnd'], v))


def flame_rgb(density):
    """Scene-linear, density-premultiplied additive emission; black stays zero."""
    d = saturate(density)
    stops = RECIPE['tintStops']
    if d <= stops[0][0]:
        tint = stops[0][1]
    elif d >= stops[-1][0]:
        tint = stops[-1][1]
    else:
        a, b = next((a, b) for a, b in zip(stops, stops[1:]) if a[0] <= d <= b[0])
        f = (d-a[0])/(b[0]-a[0])
        tint = [x+(y-x)*f for x, y in zip(a[1], b[1])]
    return tuple(d*RECIPE['emissionStrength']*c for c in tint)


def evaluate_flame(seconds, card, u, v, sample_linear):
    density = 0
    for phase in frame_state(seconds, card):
        low = sample_linear(*atlas_uv(phase['low'], u, v))
        high = sample_linear(*atlas_uv(phase['high'], u, v))
        density += (low+(high-low)*phase['fraction'])*phase['weight']
    return flame_rgb(density*envelope(u, v))


def hlsl_float(value):
    return repr(float(value))


def frame_uv_hlsl(phase, next_frame):
    r = RECIPE
    return f'''float card = floor(UV.x * 0.5);
float2 local = float2(UV.x-card*2.0,UV.y);
float phase = frac(Time*{hlsl_float(r['cycleHz'])}+card*{hlsl_float(r['cardPhaseStep'])}+{hlsl_float(phase*r['phaseOffset'])});
float frame = min(floor(phase*{hlsl_float(r['frameMax'])})+{hlsl_float(next_frame)},{hlsl_float(r['frameMax'])});
return (float2(fmod(frame,6.0),floor(frame/6.0)) + float2({hlsl_float(r['uvInset'])}+local.x*{hlsl_float(r['uvScaleU'])}, {hlsl_float(r['uvInset'])}+(1.0-local.y)*{hlsl_float(r['uvScaleV'])}))/6.0;'''


def density_hlsl():
    r = RECIPE
    return f'''float card = floor(UV.x*0.5);
float2 local = float2(UV.x-card*2.0,UV.y);
float p = frac(Time*{hlsl_float(r['cycleHz'])}+card*{hlsl_float(r['cardPhaseStep'])});
float q = frac(p+0.5);
float w = sin(p*3.14159265358979323846); w *= w;
float wq = sin(q*3.14159265358979323846); wq *= wq;
float d = lerp(A.r,B.r,frac(p*35.0))*w+lerp(C.r,D.r,frac(q*35.0))*wq;
float tip = pow(max(1.0-local.y,0.0),{hlsl_float(r['tipPower'])});
float taper = saturate({hlsl_float(r['taperStrength'])}*((1.0-{hlsl_float(r['taperSlope'])}*local.y)-abs(2.0*local.x-1.0)));
float root = smoothstep({hlsl_float(r['rootFadeStart'])},{hlsl_float(r['rootFadeEnd'])},local.y);
return saturate(d*tip*taper*root);'''


def emission_hlsl():
    stops = RECIPE['tintStops']
    def color(index):
        return 'float3('+','.join(map(hlsl_float, stops[index][1]))+')'
    a, b, c = (hlsl_float(s[0]) for s in stops)
    return f'''float3 warm = lerp({color(0)},{color(1)},saturate((Density-{a})/({b}-{a})));
float3 tint = lerp(warm,{color(2)},saturate((Density-{b})/({c}-{b})));
return tint*Density*{hlsl_float(RECIPE['emissionStrength'])};'''


CHAR_CRACKS = '''float a=UV.x*29.0+0.17*sin(UV.y*18.0);
float b=UV.y*19.0+0.12*sin(UV.x*43.0);
float stripe=abs(sin(a*3.14159265));
float crossGrain=abs(sin(b*3.14159265));
float aa=max(fwidth(stripe),0.01);
float crack=1.0-smoothstep(0.025-aa,0.07+aa,stripe);
return saturate(crack*(0.28+0.72*(1.0-smoothstep(0.08,0.38,crossGrain))));'''


def actor_list(actors):
    return actors.get_all_level_actors() if hasattr(actors, 'get_all_level_actors') else list(actors)


def graph_snapshot(u, material):
    path = ROOT/'scripts/unreal/photoreal-exterior.py'
    spec = importlib.util.spec_from_file_location('stove_graph_witness', path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    graph = helper.graph_snapshot(u, material)
    graph['useMaterialAttributes'] = bool(material.get_editor_property('use_material_attributes'))
    extended = {
        'MaterialExpressionTime': ['ignore_pause', 'override_period', 'period'],
        'MaterialExpressionTextureCoordinate': ['coordinate_index', 'u_tiling', 'v_tiling', 'un_mirror_u', 'un_mirror_v'],
    }
    nodes = {str(n.get_editor_property('desc')): n for n in u.MaterialEditingLibrary.get_material_expressions(material)}
    for row in graph['nodes']:
        if row['class'] in extended:
            node = nodes[str(row['role'])]
            row['values'].update({key: node.get_editor_property(key) for key in extended[row['class']]})
    return graph


def native_sources(u, actors):
    sources = {}
    for actor in actor_list(actors):
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = component.get_editor_property('static_mesh')
            id_ = str(u.EditorAssetLibrary.get_metadata_tag(mesh, 'source_object_id')) if mesh else ''
            if id_ not in SOURCE_IDS:
                continue
            require(id_ not in sources and component.get_num_materials() == 1, 'Ambiguous original stove material identity')
            material = component.get_material(0)
            require(material and not material.get_path_name().startswith('/Game/Brezi/Realism/Stove/'), 'Unknown stove source material')
            sources[id_] = {'actor': actor.get_path_name(), 'component': component.get_path_name(),
                            'slot': 0, 'material': material.get_path_name()}
    require(sorted(sources) == SOURCE_IDS, 'Original stove source coverage incomplete')
    return sources


def native_texture(u, name):
    texture = u.EditorAssetLibrary.load_asset(TEXTURE_PREFIX+'/'+name)
    expected = TEXTURES[name]
    require(isinstance(texture, u.Texture2D), 'Missing owned copied fire texture: '+name)
    size = [int(texture.blueprint_get_size_x()), int(texture.blueprint_get_size_y())]
    require(size == expected['size'], 'Fire texture size differs: '+name)
    require(texture.get_editor_property('srgb')
            and texture.get_editor_property('compression_settings') == u.TextureCompressionSettings.TC_DEFAULT
            and not texture.get_editor_property('virtual_texture_streaming')
            and texture.get_editor_property('lod_bias') == 0
            and texture.get_editor_property('max_texture_size') == 0, 'Fire texture interpretation differs: '+name)
    return texture, {'asset': texture.get_path_name(), 'size': size, 'srgb': True,
                     'compression': 'TC_DEFAULT', 'sourceSha256': expected['sha256']}


class Writer:
    def __init__(self, u, textures):
        self.u, self.textures = u, textures
        self.lib, self.assets = u.MaterialEditingLibrary, u.EditorAssetLibrary

    def node(self, m, role, cls, **props):
        node = self.lib.create_material_expression(m, cls, -800, 0)
        require(node is not None, 'Cannot create stove expression: '+role)
        node.set_editor_property('desc', TAG+role)
        for key, value in props.items():
            node.set_editor_property(key, value)
        return node

    def scalar(self, m, role, value):
        return self.node(m, role, self.u.MaterialExpressionConstant, r=float(value))

    def vector(self, m, role, value):
        return self.node(m, role, self.u.MaterialExpressionConstant3Vector, constant=self.u.LinearColor(*value, 1))

    def connect(self, source, channel, target, pin):
        require(self.lib.connect_material_expressions(source, channel, target, pin), 'Cannot connect stove pin: '+pin)

    def out(self, node, prop):
        require(self.lib.connect_material_property(node, '', getattr(self.u.MaterialProperty, 'MP_'+prop)), 'Cannot connect stove output: '+prop)

    def custom(self, m, role, code, sources, width):
        inputs = []
        for key in sources:
            pin = self.u.CustomInput()
            pin.set_editor_property('input_name', key)
            inputs.append(pin)
        node = self.node(m, role, self.u.MaterialExpressionCustom, inputs=inputs, code=code, description=TAG+role,
                         output_type=getattr(self.u.CustomMaterialOutputType, 'CMOT_FLOAT'+str(width)))
        for pin, (source, channel) in sources.items():
            self.connect(source, channel, node, pin)
        return node

    def texture_sample(self, m, role, texture, uv, derivatives=None):
        props = {'texture': texture, 'sampler_type': self.u.MaterialSamplerType.SAMPLERTYPE_COLOR}
        if derivatives:
            props['mip_value_mode'] = self.u.TextureMipValueMode.TMVM_DERIVATIVE
        node = self.node(m, role, self.u.MaterialExpressionTextureSample, **props)
        self.connect(uv, '', node, 'UVs')
        if derivatives:
            for deriv, pin in zip(derivatives, ('DDX(UVs)', 'DDY(UVs)')):
                self.connect(deriv, '', node, pin)
        return node

    def flames(self, m):
        u = self.u
        m.set_editor_property('blend_mode', u.BlendMode.BLEND_ADDITIVE)
        m.set_editor_property('shading_model', u.MaterialShadingModel.MSM_UNLIT)
        m.set_editor_property('two_sided', True)
        uv = self.node(m, 'flame-card-uv', u.MaterialExpressionTextureCoordinate, coordinate_index=0, u_tiling=1., v_tiling=1., un_mirror_u=False, un_mirror_v=False)
        time = self.node(m, 'flame-clock', u.MaterialExpressionTime, ignore_pause=False, override_period=False, period=0.)
        pins = {'UV': (uv, ''), 'Time': (time, '')}
        # Explicit screen derivatives exclude animated frame offsets from mip
        # selection and avoid cross-tile derivatives at card/phase transitions.
        derivatives = [self.custom(m, 'atlas-'+op, f'return {op}(UV)*float2({RECIPE["uvScaleU"]},-{RECIPE["uvScaleV"]})/6.0;', {'UV': (uv, '')}, 2)
                       for op in ('ddx', 'ddy')]
        samples = {}
        for index, (phase, next_frame) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
            atlas = self.custom(m, 'atlas-uv-'+str(index), frame_uv_hlsl(phase, next_frame), pins, 2)
            sample = self.texture_sample(m, 'atlas-sample-'+str(index), self.textures['T_Fire_SubUV'], atlas, derivatives)
            samples['ABCD'[index]] = (sample, 'RGB')
        density = self.custom(m, 'continuous-flame-density', density_hlsl(), {**pins, **samples}, 1)
        emission = self.custom(m, 'density-weighted-fire-emission', emission_hlsl(), {'Density': (density, '')}, 3)
        self.out(emission, 'EMISSIVE_COLOR')
        self.out(self.scalar(m, 'additive-opacity', 1), 'OPACITY')

    def opaque(self, m, role):
        u, spec = self.u, SURFACES[role]
        m.set_editor_property('blend_mode', u.BlendMode.BLEND_OPAQUE)
        m.set_editor_property('shading_model', u.MaterialShadingModel.MSM_DEFAULT_LIT)
        m.set_editor_property('two_sided', False)
        color = self.vector(m, 'surface-linear-color', spec['baseLinear'])
        if role == 'logs':
            uv = self.node(m, 'log-longitudinal-uv', u.MaterialExpressionTextureCoordinate, coordinate_index=0)
            crack = self.custom(m, 'irregular-char-cracks', CHAR_CRACKS, {'UV': (uv, '')}, 1)
            color = self.custom(m, 'charred-wood-color', 'return Color*lerp(1.0,0.35,Crack);', {'Color': (color, ''), 'Crack': (crack, '')}, 3)
        if role == 'embers':
            pos = self.node(m, 'ember-world-cm', u.MaterialExpressionWorldPosition)
            uv = self.custom(m, 'ember-metric-uv', 'return Position.xy/7.0;', {'Position': (pos, '')}, 2)
            sample = self.texture_sample(m, 'ember-fracture-texture', self.textures['T_Fire_Tiled_D'], uv)
            code = 'float mask=smoothstep(0.035,0.32,Scan.r); return float3(1.0,0.025,0.0006)*mask*0.45;'
            emission = self.custom(m, 'restrained-ember-emission', code, {'Scan': (sample, 'RGB')}, 3)
            self.out(emission, 'EMISSIVE_COLOR')
        else:
            self.out(self.vector(m, 'non-emissive-surface', [0, 0, 0]), 'EMISSIVE_COLOR')
        self.out(color, 'BASE_COLOR')
        for key in ('roughness', 'specular', 'metallic'):
            self.out(self.scalar(m, 'surface-'+key, spec[key]), key.upper())

    def create(self, role):
        name = 'M_Stove_'+role.title()
        require(not self.assets.does_asset_exist(PREFIX+'/'+name), 'Refusing to replace a stove material')
        m = self.u.AssetToolsHelpers.get_asset_tools().create_asset(name, PREFIX, self.u.Material, self.u.MaterialFactoryNew())
        require(m is not None, 'Cannot create owned stove material')
        if role == 'flames':
            self.flames(m)
        else:
            self.opaque(m, role)
        errors = list(self.lib.recompile_material(m))
        require(not errors, 'Stove shader compile failed: '+str(errors))
        spec = RECIPE if role == 'flames' else SURFACES[role]
        self.assets.set_metadata_tag(m, 'BreziGeneratedBy', OWNER)
        self.assets.set_metadata_tag(m, 'BreziRealismStoveRecipe', json.dumps(spec, sort_keys=True))
        self.assets.set_metadata_tag(m, 'BreziRealismStoveRole', role)
        require(self.assets.save_loaded_asset(m, only_if_is_dirty=False), 'Cannot save owned stove material')
        return m


def apply(u, actors, output):
    output = Path(output)
    scene_path = output/'geometry/scene.json'
    scene = json.loads(scene_path.read_text())
    require(scene['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'Stove requires C/B/B')
    records = {r['id']: r for r in scene['objects']}
    require(all(id_ in records and records[id_]['name'].startswith('FIREPLACE-STOVE-B-2026-09-11 · ') for id_ in SOURCE_IDS), 'Stove source cohort changed')
    sources = native_sources(u, actors)
    originals = {row['material']: graph_snapshot(u, u.EditorAssetLibrary.load_asset(row['material'])) for row in sources.values()}
    textures, texture_report = {}, {}
    for name in TEXTURES:
        textures[name], texture_report[name] = native_texture(u, name)
        path = output/'Project/BreziTwin/Content/Brezi/Realism/Stove/Fire/Textures'/(name+'.uasset')
        require(sha(path) == TEXTURES[name]['sha256'], 'Copied source fire texture bytes differ')
        texture_report[name]['packageFile'] = str(path.resolve())
    report = {'schemaVersion': 1, 'status': 'authored-reload-pending', 'owner': OWNER,
              'pipelineFiles': {str(ROOT/OWNER): sha(__file__), str(ROOT/'scripts/unreal/photoreal-exterior.py'): sha(ROOT/'scripts/unreal/photoreal-exterior.py')},
              'inputFiles': {str(scene_path.resolve()): sha(scene_path), str(PROBE): sha(PROBE)},
              'sourceBindings': sources, 'originalGraphs': originals, 'protectedGraphs': copy.deepcopy(originals),
              'materials': {'shell': sources['DOM_00553']['material']}, 'graphs': {}, 'ownedAssets': [],
              'textures': texture_report, 'recipe': copy.deepcopy(RECIPE), 'surfaces': copy.deepcopy(SURFACES),
              'bindingChanges': [], 'geometryModified': False, 'collisionModified': False,
              'lightingModified': False, 'nativeRenderedVerified': False,
              'limitations': ['Authored procedural char and relative ember/fire emission are not calibrated fire photometry.',
                              'Additive translucency and retained stove glass require native Metal still and motion review.']}
    writer = Writer(u, textures)
    for role in ('chamber', 'logs', 'flames', 'embers'):
        material = writer.create(role)
        path = material.get_path_name()
        report['materials'][role] = path
        report['ownedAssets'].append(path)
        report['graphs'][path] = graph_snapshot(u, material)
    require(native_sources(u, actors) == sources, 'Material authoring changed a protected source binding')
    for path, graph in originals.items():
        require(graph_snapshot(u, u.EditorAssetLibrary.load_asset(path)) == graph, 'Original stove material graph changed')
    return report


def verify(u, actors, report):
    require(native_sources(u, actors) == report['sourceBindings'], 'Saved original stove bindings changed')
    require(report['materials']['shell'] == report['sourceBindings']['DOM_00553']['material'], 'Shell material was replaced')
    for role, path in report['materials'].items():
        material = u.EditorAssetLibrary.load_asset(path)
        require(material is not None, 'Saved stove material missing')
        if role == 'shell':
            continue
        spec = RECIPE if role == 'flames' else SURFACES[role]
        require(u.EditorAssetLibrary.get_metadata_tag(material, 'BreziGeneratedBy') == OWNER
                and u.EditorAssetLibrary.get_metadata_tag(material, 'BreziRealismStoveRole') == role
                and u.EditorAssetLibrary.get_metadata_tag(material, 'BreziRealismStoveRecipe') == json.dumps(spec, sort_keys=True), 'Saved stove material ownership/recipe changed')
        require(graph_snapshot(u, material) == report['graphs'][path], 'Saved stove material graph changed')
    for path, graph in report['originalGraphs'].items():
        require(graph_snapshot(u, u.EditorAssetLibrary.load_asset(path)) == graph, 'Saved original stove graph changed')
    for name, row in report['textures'].items():
        _, current = native_texture(u, name)
        require(all(current[key] == row[key] for key in current)
                and sha(row['packageFile']) == TEXTURES[name]['sha256'], 'Read-only fire texture changed')
    return {**report, 'status': 'saved-reloaded-validated', 'savedReloaded': True}
