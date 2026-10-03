"""Root-owned read-only reflection probe. No imports, setters, map or asset saves."""
import hashlib
import json
import os
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[2]
DESTINATION = ROOT / 'output/unreal/exterior-20261002-r38a/texture-policy-reflection-probe-report-r1.json'
assert not DESTINATION.exists()
FIELDS = ('srgb', 'compression_none', 'compression_settings', 'mip_gen_settings', 'filter',
    'address_x', 'address_y', 'power_of_two_mode', 'resize_during_build_x', 'resize_during_build_y',
    'lod_bias', 'max_texture_size', 'never_stream', 'virtual_texture_streaming',
    'flip_green_channel', 'do_scale_mips_for_alpha_coverage', 'adjust_brightness',
    'adjust_brightness_curve', 'adjust_vibrance', 'adjust_saturation', 'adjust_rgb_curve',
    'adjust_hue', 'adjust_min_alpha', 'adjust_max_alpha', 'chroma_key_texture')

def observe(callback):
    try:
        return {'available': True, 'value': str(callback())}
    except Exception as error:
        return {'available': False, 'error': str(error)}

texture = u.get_default_object(u.Texture2D)
sample = u.get_default_object(u.MaterialExpressionTextureSample)
properties = {name: observe(lambda key=name: texture.get_editor_property(key)) for name in FIELDS}
for label, callback in {
    'source_color_settings.encoding_override': lambda: texture.get_editor_property('source_color_settings').get_editor_property('encoding_override'),
    'downscale.default': lambda: texture.get_editor_property('downscale').get_editor_property('default'),
    'downscale.per_platform': lambda: dict(texture.get_editor_property('downscale').get_editor_property('per_platform')),
    'alpha_coverage_thresholds': lambda: texture.get_editor_property('alpha_coverage_thresholds'),
}.items():
    properties[label] = observe(callback)
sampler = {name: observe(lambda key=name: sample.get_editor_property(key)) for name in
    ('sampler_source', 'sampler_type', 'mip_value_mode', 'automatic_view_mip_bias')}
enums = {}
for label in ('TextureCompressionSettings', 'MaterialSamplerType', 'TextureFilter', 'TextureMipGenSettings',
    'TextureAddress', 'TextureSourceEncoding', 'TexturePowerOfTwoSetting', 'SamplerSourceMode', 'TextureMipValueMode'):
    enum = getattr(u, label)
    enums[label] = {name: str(getattr(enum, name)) for name in dir(enum) if name.isupper() and not name.startswith('_')}
result = {'schema': 'brezi-r38-actual-read-only-texture-policy-reflection', 'schemaVersion': 1,
    'owner': str(Path(__file__)), 'ownerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'nativeProcessId': os.getpid(), 'textureClassDefaultProperties': properties,
    'textureSampleClassDefaultProperties': sampler, 'actualReflectedEnums': enums,
    'propertySettersCalled': False, 'assetsImported': False, 'mapLoadedOrSavedByProbe': False,
    'nativeApplied': False, 'setterAvailabilityVerified': False, 'nativeGpuPixelFormatVerified': False}
with DESTINATION.open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write(chr(10))
print(json.dumps({'report': str(DESTINATION), 'nativeProcessId': os.getpid(),
    'unavailableProperties': [key for key, value in properties.items() if not value['available']]}))
