"""Bounded finish corrections on an inherited, validated C/B/B world.

Only component material bindings change. Existing meshes, collisions, textures
and material packages remain immutable. New material packages are owned by this
stage; the caller saves/reloads the map and calls verify().
"""
import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/realism-materials.py'
PREFIX = '/Game/Brezi/Realism/Materials'
TAG = 'BreziRealism:'
DESIGN = {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
OAK = {'Kitchen 2026 · prírodný dub', 'Living warm oak | real-interior-kitchen-front'}
PLASTER = {'real-wall', 'real-soffit', 'real-interior-plaster', 'real-interior-ceiling'}
# Exact, audited generic pbr()/pbrMaterial() hex inputs; never apply a blanket
# transfer to the exported scene: kitchen and window-frame values are linear.
SRGB_SOURCES = {
    'real-interior-black-glass': ('#0c0e10', 'lib/babylon-interior.ts', 'black-glass'),
    'real-interior-fireplace': ('#1d2022', 'lib/babylon-interior.ts', 'coated-metal'),
    'real-office-desk-black-steel': ('#18191b', 'lib/babylon-interior.ts', 'coated-metal'),
    'real-sanitary-ceramic': ('#f8f8f5', 'lib/babylon-interior.ts', 'ceramic'),
    'real-bathroom-black-ceramic': ('#08090a', 'lib/babylon-interior.ts', 'ceramic'),
    'real-bathroom-appliance-white': ('#fafaf7', 'lib/babylon-interior.ts', 'enamel'),
    'real-fabric': ('#e6e2d8', 'lib/babylon-scene.ts', 'existing-linen'),
    'real-upholstery-dark': ('#22292a', 'lib/babylon-scene.ts', 'existing-linen'),
}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def decode_srgb(value):
    require(math.isfinite(value) and 0 <= value <= 1, 'Invalid sRGB channel')
    return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4


def hex_channels(value):
    return [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def recipe(source):
    """Semantic scope, with a fail-closed check for known nonlinear swatches."""
    name = source['name']
    artificial_ceiling = name == 'real-interior-ceiling'
    if source['alpha'] < .999 or (any(source['emission']) and not artificial_ceiling):
        return None
    if name in OAK:
        return {'kind': 'coherent-natural-oak', 'sourceName': name,
                'asset': 'oak_veneer_01', 'paletteLinear': [.32, .235, .157],
                'contrast': .60, 'normalStrength': .22, 'roughness': .55,
                'roughnessAmplitude': .12, 'specular': .45,
                'projection': 'world centimetres; vertical face grain; per-component phase',
                'physicalPeriodCm': 183.00000429153442}
    if name in PLASTER:
        result = {'kind': 'quiet-mineral-plaster', 'sourceName': name,
                'asset': 'white_plaster_02', 'paletteLinear': [.78, .765, .73],
                'contrast': .012, 'normalStrength': .065, 'roughness': .88,
                'roughnessAmplitude': .055, 'specular': .35,
                'projection': 'world centimetres; original stretched source albedo removed',
                'physicalPeriodCm': 100.0}
        if artificial_ceiling:
            expected = hex_channels('#f6f5f1')
            require(source.get('texture') is None and all(abs(a-b)<1e-8 for a,b in zip(source['color'], expected))
                    and all(abs(a-b)<1e-8 for a,b in zip(source['emission'], hex_channels('#9a9995'))),
                    'Artificial source ceiling swatch/emission changed')
            result.update(paletteLinear=[decode_srgb(v) for v in expected], sourceSrgbHex='#f6f5f1',
                          provenance='lib/babylon-interior.ts', removeArtificialEmission=True,
                          previousEmission=source['emission'])
        return result
    if name not in SRGB_SOURCES:
        return None
    swatch, path, kind = SRGB_SOURCES[name]
    encoded = hex_channels(swatch)
    require(source.get('texture') is None and len(source['color']) == 3
            and all(abs(a-b) < 1e-8 for a, b in zip(source['color'], encoded)),
            'Known sRGB swatch is no longer an unconverted constant: ' + name)
    linear = [decode_srgb(v) for v in encoded]
    result = {'kind': kind, 'sourceName': name, 'sourceSrgbHex': swatch,
              'provenance': path, 'originalLinearInterpretation': encoded,
              'decodedLinear': linear, 'correctionRatio': [a/b for a, b in zip(linear, encoded)],
              'colorTransfer': 'IEC 61966-2-1 sRGB decoded exactly once'}
    if kind in {'black-glass', 'ceramic', 'enamel', 'coated-metal'}:
        result['metallic'] = 0.0  # The visible pigmented/glazed layer is dielectric.
    if kind == 'black-glass':
        result.update(roughness=.065, specular=.5)
    return result


def helper():
    spec = importlib.util.spec_from_file_location('realism_snapshot_helper', ROOT/'scripts/unreal/photoreal-exterior.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASIS = '''float3 N=normalize(NormalWS); float3 A=abs(N),T,V;
if(A.x>=A.y && A.x>=A.z){T=float3(0,-sign(N.x),0);V=float3(0,0,-1);}
else if(A.y>=A.z){T=float3(sign(N.y),0,0);V=float3(0,0,-1);}
else{T=float3(0,sign(N.z),0);V=float3(-1,0,0);}
'''
UV = BASIS + '''float2 uv=float2(dot(Position,T),dot(Position,V))/PeriodCm;
// ObjectPositionWS is constant over each panel, including its bevel surface.
// Phase changes only at the physical panel boundary; all PBR maps share it.
float h=frac(sin(dot(ObjectCenter.xy,float2(.0713,.0537)))*43758.5453);
return uv+PhaseWeight*float2(h*.73,frac(h*7.31)*.41);'''
NORMAL = BASIS + '''float3 d=normalize(float3(MapNormal.xy*Strength,max(MapNormal.z,.1)));
return normalize(T*d.x+V*d.y+N*d.z)*FaceSign;'''
COLOR = '''float3 ratio=Scan/max(Mean,float3(.001,.001,.001));
return saturate(Palette*clamp(1+Contrast*(ratio-1),.55,1.55));'''
ROUGHNESS = 'return clamp(Base+(Sample-Mean)*Amplitude,.08,.98);'


class Writer:
    def __init__(self, u, inputs):
        self.u = u
        self.assets = u.EditorAssetLibrary
        self.lib = u.MaterialEditingLibrary
        self.inputs = inputs
        self.textures = {}

    def node(self, m, role, cls, **props):
        n = self.lib.create_material_expression(m, cls, -800, 0)
        require(n is not None, 'Could not create realism material node ' + role)
        n.set_editor_property('desc', TAG + role)
        for key, value in props.items():
            n.set_editor_property(key, value)
        return n

    def scalar(self, m, role, value):
        return self.node(m, role, self.u.MaterialExpressionConstant, r=float(value))

    def vector(self, m, role, value):
        return self.node(m, role, self.u.MaterialExpressionConstant3Vector, constant=self.u.LinearColor(*value, 1))

    def connect(self, a, channel, b, pin):
        require(self.lib.connect_material_expressions(a, channel, b, pin), 'Realism graph connection failed: ' + pin)

    def out(self, node, channel, prop):
        require(self.lib.connect_material_property(node, channel, getattr(self.u.MaterialProperty, 'MP_' + prop)),
                'Realism graph output failed: ' + prop)

    def custom(self, m, role, code, pins, kind):
        inputs = []
        for key in pins:
            item = self.u.CustomInput()
            item.set_editor_property('input_name', key)
            inputs.append(item)
        n = self.node(m, role, self.u.MaterialExpressionCustom, inputs=inputs, code=code,
                      description=TAG + role, output_type=kind)
        for key, (source, channel) in pins.items():
            self.connect(source, channel, n, key)
        return n

    def sample(self, m, asset, role, uv):
        spec = self.inputs['assets'][asset]['maps'][role]
        path = '/Game/Brezi/Archviz/Textures/T_' + asset + '_' + role + '_' + spec['sha256'][:12]
        texture = self.assets.load_asset(path)
        compression = {'albedo': self.u.TextureCompressionSettings.TC_DEFAULT,
                       'normal': self.u.TextureCompressionSettings.TC_NORMALMAP,
                       'roughness': self.u.TextureCompressionSettings.TC_MASKS}[role]
        require(texture is not None and self.assets.get_metadata_tag(texture, 'source_sha256') == spec['sha256']
                and texture.get_editor_property('srgb') == (role == 'albedo')
                and texture.get_editor_property('compression_settings') == compression
                and texture.get_editor_property('flip_green_channel') == (role == 'normal'),
                'Existing scan interpretation/provenance differs: ' + path)
        self.textures[path] = {'asset': texture.get_path_name(), 'sha256': spec['sha256'],
                               'source': spec['path'], 'role': role, 'srgb': role == 'albedo',
                               'flipGreen': role == 'normal', 'compression': str(compression)}
        sampler = {'albedo': self.u.MaterialSamplerType.SAMPLERTYPE_COLOR,
                   'normal': self.u.MaterialSamplerType.SAMPLERTYPE_NORMAL,
                   'roughness': self.u.MaterialSamplerType.SAMPLERTYPE_MASKS}[role]
        n = self.node(m, 'coherent-scan-' + role, self.u.MaterialExpressionTextureSample,
                      texture=texture, sampler_type=sampler)
        self.connect(uv, '', n, 'UVs')
        return n

    def scan_finish(self, m, r):
        u = self.u
        t = u.CustomMaterialOutputType
        asset = self.inputs['assets'][r['asset']]
        require(abs(asset['periodCm'] - r['physicalPeriodCm']) < .0001, 'Photograph physical scale changed')
        pos = self.node(m, 'position-cm', u.MaterialExpressionWorldPosition)
        normal = self.node(m, 'geometric-normal', u.MaterialExpressionVertexNormalWS)
        center = self.node(m, 'object-center', u.MaterialExpressionObjectPositionWS)
        face = self.node(m, 'face-sign', u.MaterialExpressionTwoSidedSign)
        coords = {'Position': (pos, ''), 'NormalWS': (normal, '')}
        uv = self.custom(m, 'coherent-metric-uv', UV,
                         {**coords, 'ObjectCenter': (center, ''),
                          'PeriodCm': (self.scalar(m, 'scan-period', r['physicalPeriodCm']), ''),
                          'PhaseWeight': (self.scalar(m, 'panel-phase', 1 if r['sourceName'] in OAK else 0), '')}, t.CMOT_FLOAT2)
        color, normalmap, rough = [self.sample(m, r['asset'], role, uv) for role in ('albedo', 'normal', 'roughness')]
        result = self.custom(m, 'quiet-scan-color', COLOR,
                             {'Scan': (color, 'RGB'), 'Mean': (self.vector(m, 'scan-mean', asset['maps']['albedo']['meanLinearRGB']), ''),
                              'Palette': (self.vector(m, 'finish-palette', r['paletteLinear']), ''),
                              'Contrast': (self.scalar(m, 'finish-contrast', r['contrast']), '')}, t.CMOT_FLOAT3)
        self.out(result, '', 'BASE_COLOR')
        result = self.custom(m, 'coherent-scan-normal', NORMAL,
                             {'NormalWS': (normal, ''), 'MapNormal': (normalmap, 'RGB'),
                              'Strength': (self.scalar(m, 'normal-strength', r['normalStrength']), ''),
                              'FaceSign': (face, '')}, t.CMOT_FLOAT3)
        self.out(result, '', 'NORMAL')
        result = self.custom(m, 'coherent-scan-roughness', ROUGHNESS,
                             {'Sample': (rough, 'R'), 'Mean': (self.scalar(m, 'roughness-mean', asset['maps']['roughness']['meanDataR']), ''),
                              'Base': (self.scalar(m, 'finish-roughness', r['roughness']), ''),
                              'Amplitude': (self.scalar(m, 'roughness-amplitude', r['roughnessAmplitude']), '')}, t.CMOT_FLOAT1)
        self.out(result, '', 'ROUGHNESS')
        self.out(self.scalar(m, 'dielectric-metallic', 0), '', 'METALLIC')
        self.out(self.scalar(m, 'dielectric-specular', r['specular']), '', 'SPECULAR')
        if r.get('removeArtificialEmission'):
            self.out(self.vector(m, 'remove-artificial-ceiling-emission', [0, 0, 0]), '', 'EMISSIVE_COLOR')
        m.set_editor_property('tangent_space_normal', False)

    def swatch_finish(self, m, r):
        # Multiply existing roots so linen weave, fuzz and every previously
        # authored normal/roughness node survive the color-space correction.
        ratio = self.vector(m, 'swatch-srgb-to-linear', r['correctionRatio'])
        for prop in ('BASE_COLOR', 'SUBSURFACE_COLOR'):
            p = getattr(self.u.MaterialProperty, 'MP_' + prop)
            original = self.lib.get_material_property_input_node(m, p)
            if original:
                channel = str(self.lib.get_material_property_input_node_output_name(m, p))
                if channel == 'None':
                    channel = ''
                multiply = self.node(m, 'corrected-' + prop.lower(), self.u.MaterialExpressionMultiply)
                self.connect(original, channel, multiply, 'A')
                self.connect(ratio, '', multiply, 'B')
                self.out(multiply, '', prop)
        for prop in ('metallic', 'roughness', 'specular'):
            if prop in r:
                self.out(self.scalar(m, 'corrected-' + prop, r[prop]), '', prop.upper())

    def material(self, original, r):
        path = PREFIX + '/M_' + r['kind'].replace('-', '_') + '_' + digest({'original': original.get_path_name(), 'recipe': r})[:16]
        require(not self.assets.does_asset_exist(path), 'Use a fresh realism output: ' + path)
        m = self.assets.duplicate_asset(original.get_path_name(), path)
        require(m is not None, 'Could not duplicate material for realism')
        if r['kind'] in {'coherent-natural-oak', 'quiet-mineral-plaster'}:
            self.scan_finish(m, r)
        else:
            self.swatch_finish(m, r)
        self.lib.set_base_material_usage(m, self.u.MaterialUsage.MATUSAGE_NANITE, True)
        require(not list(self.lib.recompile_material(m)), 'Realism material compile failed: ' + path)
        self.assets.set_metadata_tag(m, 'BreziGeneratedBy', OWNER)
        self.assets.set_metadata_tag(m, 'BreziRealismRecipe', json.dumps(r, sort_keys=True))
        require(self.assets.save_loaded_asset(m, only_if_is_dirty=False), 'Realism material save failed: ' + path)
        return m


def actor_list(actors):
    return actors.get_all_level_actors() if hasattr(actors, 'get_all_level_actors') else list(actors)


def apply(u, actors, output):
    output = Path(output)
    scene_path = output/'geometry/scene.json'
    scene = json.loads(scene_path.read_text())
    require(scene['activeDesign'] == DESIGN, 'Realism requires canonical C/B/B')
    source_by_name = {v['name']: v for v in scene['materials'].values()}
    require(len(source_by_name) == len(scene['materials']), 'Material semantic names are ambiguous')
    inputs_path = ROOT/'scripts/unreal/archviz-material-inputs.json'
    inputs = json.loads(inputs_path.read_text())
    pipeline = {OWNER: sha(__file__), 'scripts/unreal/photoreal-exterior.py': sha(ROOT/'scripts/unreal/photoreal-exterior.py')}
    input_files = {'scripts/unreal/archviz-material-inputs.json': sha(inputs_path)}
    for path in {entry[1] for entry in SRGB_SOURCES.values()}:
        text = (ROOT/path).read_text()
        require('material.albedoColor = Color3.FromHexString(color);' in text,
                'Generic source color helper changed; re-audit sRGB correction: ' + path)
        for name, (swatch, source_path, _) in SRGB_SOURCES.items():
            if source_path == path:
                require(re.search(r'\b(?:pbr|pbrMaterial)\(\s*(?:scene|this\.scene),\s*"' + re.escape(name)
                                  + r'",\s*"' + re.escape(swatch) + r'"', text),
                        'Known source swatch disappeared: ' + name)
        input_files[path] = sha(ROOT/path)
    for asset_name in ('oak_veneer_01', 'white_plaster_02'):
        asset = inputs['assets'][asset_name]
        require(asset['license'] == 'CC0-1.0', 'Unreviewed scan license')
        for spec in asset['maps'].values():
            require(sha(ROOT/spec['path']) == spec['sha256'], 'Pinned scan bytes changed')
            input_files[spec['path']] = spec['sha256']
    planned, originals = [], {}
    snapshot = helper().graph_snapshot
    for actor in actor_list(actors):
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            for slot in range(c.get_num_materials()):
                original = c.get_material(slot)
                if not original:
                    continue
                name = str(u.EditorAssetLibrary.get_metadata_tag(original, 'source_material_name'))
                if name not in source_by_name:
                    continue
                r = recipe(source_by_name[name])
                if not r:
                    continue
                require(original.get_path_name().startswith(('/Game/Brezi/ModelRefresh/', '/Game/Brezi/Photoreal/')),
                        'Refusing unknown original material owner: ' + original.get_path_name())
                require(str(u.EditorAssetLibrary.get_metadata_tag(original, 'BreziGeneratedBy')) in
                        {'scripts/unreal/model-refresh-import.py', 'scripts/unreal/photoreal-interior.py'},
                        'Unreviewed source material owner')
                planned.append((actor, c, slot, original, r))
                originals[original.get_path_name()] = snapshot(u, original)
    require(planned and {'coherent-natural-oak', 'quiet-mineral-plaster', 'black-glass'} <= {p[4]['kind'] for p in planned},
            'Realism target coverage incomplete')
    writer = Writer(u, inputs)
    report = {'schemaVersion': 1, 'status': 'authored-reload-pending', 'owner': OWNER,
              'pipelineFiles': pipeline, 'inputFiles': input_files,
              'sourceManifestSha256': sha(scene_path), 'bindingChanges': [], 'ownedAssets': [],
              'materials': {}, 'originalGraphs': originals, 'reusedTextures': [],
              'geometryModified': False, 'collisionModified': False, 'nativeRenderedVerified': False,
              'limitations': ['Finish palette/roughness are authored appearance choices, not measured installed products.',
                             'Only explicitly proven generic hex constants are decoded; other exported colors are untouched.',
                             'Photographed oak and plaster use one coherent PBR map set; no new geometry or displacement.',
                             'Native Metal day/night stills and moving views remain a separate acceptance gate.']}
    cache = {}
    for actor, c, slot, original, r in planned:
        key = digest({'source': original.get_path_name(), 'recipe': r})
        if key not in cache:
            m = writer.material(original, r)
            cache[key] = m
            report['ownedAssets'].append(m.get_path_name())
            report['materials'][m.get_path_name()] = {'recipe': r, 'originalAsset': original.get_path_name(), 'graph': snapshot(u, m)}
        m = cache[key]
        c.set_material(slot, m)
        report['bindingChanges'].append({'actor': actor.get_path_name(), 'component': c.get_path_name(), 'slot': slot,
                                         'before': original.get_path_name(), 'after': m.get_path_name(), 'sourceName': r['sourceName']})
    report['reusedTextures'] = list(writer.textures.values())
    require(all(snapshot(u, u.EditorAssetLibrary.load_asset(path)) == graph for path, graph in originals.items()),
            'An original material graph changed')
    return report


def verify(u, actors, report):
    snapshot = helper().graph_snapshot
    components = {c.get_path_name(): c for a in actor_list(actors) for c in a.get_components_by_class(u.StaticMeshComponent)}
    for change in report['bindingChanges']:
        c = components.get(change['component'])
        require(c and c.get_material(change['slot']) and c.get_material(change['slot']).get_path_name() == change['after'],
                'Reloaded realism material binding differs: ' + change['component'])
    for path, entry in report['materials'].items():
        m = u.EditorAssetLibrary.load_asset(path)
        require(m and u.EditorAssetLibrary.get_metadata_tag(m, 'BreziGeneratedBy') == OWNER
                and u.EditorAssetLibrary.get_metadata_tag(m, 'BreziRealismRecipe') == json.dumps(entry['recipe'], sort_keys=True)
                and snapshot(u, m) == entry['graph'], 'Reloaded realism graph/ownership differs: ' + path)
    for path, graph in report['originalGraphs'].items():
        require(snapshot(u, u.EditorAssetLibrary.load_asset(path)) == graph, 'Original graph changed after realism: ' + path)
    for entry in report['reusedTextures']:
        texture = u.EditorAssetLibrary.load_asset(entry['asset'])
        require(texture and u.EditorAssetLibrary.get_metadata_tag(texture, 'source_sha256') == entry['sha256']
                and texture.get_editor_property('srgb') == entry['srgb']
                and texture.get_editor_property('flip_green_channel') == entry['flipGreen']
                and str(texture.get_editor_property('compression_settings')) == entry['compression'],
                'Reused texture changed: ' + entry['asset'])
    return {**report, 'status': 'saved-reloaded-validated', 'savedReloaded': True}
