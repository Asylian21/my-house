"""Source-bounded short lawn, authored only in a fresh Photoreal profile.

Material and blade authors are separate modules. This coordinator seals their
inputs and validates both after a real native save/reload. The canonical lawn
remains the visible ground and walk surface underneath the additive blades.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/photoreal-lawn.py'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts/unreal'/filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def validate_pins(pins):
    for name, expected in pins.items():
        path = (ROOT/name).resolve()
        require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == expected,
                'Lawn input changed: ' + name)


def merge_pins(target, incoming):
    for name, expected in incoming.items():
        require(name not in target or target[name] == expected, 'Conflicting lawn input pin: ' + name)
        target[name] = expected


def save(geometry, report):
    (Path(geometry).parent/'photoreal-lawn-report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2)+'\n')


def apply_lawn(scene, geometry, baseline_material_report):
    geometry = Path(geometry)
    generated = geometry.parent/'lawn-geometry'
    require(generated.is_dir(), 'Generate the source-bounded lawn prototypes first')
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in sorted(generated.rglob('*')) if p.is_file()}
    require(inputs, 'Lawn geometry directory is empty')
    material_module = module('brezi_lawn_materials', 'lawn-materials.py')
    geometry_module = module('brezi_lawn_geometry', 'lawn-geometry.py')
    files = [Path(__file__), ROOT/'scripts/unreal/lawn-materials.py', ROOT/'scripts/unreal/lawn-geometry.py']
    pipeline = {str(p.relative_to(ROOT)): sha(p) for p in files}
    materials = material_module.apply_materials(scene, geometry, baseline_material_report)
    require(materials.get('sourceGroundRetained') is True, 'Lawn source ground witness failed')
    blade_material = materials['bladeMaterial']
    if isinstance(blade_material, dict):
        blade_material = blade_material['asset']
    require(isinstance(blade_material, str) and blade_material.startswith('/Game/Brezi/Photoreal/Lawn/'),
            'Blade material escaped the owned lawn namespace')
    details = geometry_module.apply_geometry(generated, geometry, blade_material)
    textures = materials.get('textures', [])
    for part in [materials, details]:
        merge_pins(pipeline, part.get('pipelineFiles', {}))
        merge_pins(inputs, part.get('inputFiles', {}))
    for texture in textures:
        if texture.get('source'):
            require(texture.get('sha256') == sha(ROOT/texture['source']), 'Lawn texture hash differs')
            merge_pins(inputs, {texture['source']: texture['sha256']})
    validate_pins(pipeline)
    validate_pins(inputs)
    report = {'schemaVersion': 1, 'owner': OWNER, 'status': 'authored-reload-pending',
              'sourceManifestSha256': sha(geometry/'scene.json'),
              'materials': materials, 'geometry': details, 'textures': textures,
              'pipelineFiles': pipeline, 'inputFiles': inputs,
              'sourceGroundRetained': True, 'savedReloaded': False, 'nativeRenderedVerified': False}
    save(geometry, report)
    return report


def verify_lawn(scene, geometry, report):
    geometry = Path(geometry)
    require(sha(geometry/'scene.json') == report['sourceManifestSha256'], 'Lawn source changed')
    validate_pins(report['pipelineFiles'])
    validate_pins(report['inputFiles'])
    report['materials'] = module('brezi_lawn_materials_verify', 'lawn-materials.py').verify_materials(
        scene, geometry, report['materials'])
    require(report['materials'].get('sourceGroundRetained') is True, 'Reloaded lawn source ground witness failed')
    report['geometry'] = module('brezi_lawn_geometry_verify', 'lawn-geometry.py').verify_geometry(
        geometry.parent/'lawn-geometry', geometry, report['geometry'])
    report.update(status='saved-reloaded-validated', savedReloaded=True)
    save(geometry, report)
    return report
